# -*- coding: utf-8 -*-
"""
=============================================================================
AutoCopilot Open SDV Core (Eclipse SDV / Linux Foundation AGL Compatible)
=============================================================================
License: Apache License, Version 2.0 (Open Source Edition)
Commercial Moat: Hardware FTTI Interlock, 100% MC/DC Suite & GSN Engine

This module provides the open-source foundational state machine, CAN/CAN-FD
frame parser abstraction, and basic vehicle telemetry logger. It serves as
the public entry point for the Eclipse SDV and SOAFEE ecosystems while
strictly isolating the proprietary ASIL-D certified hardware arbitration
and fast-abort IP.
=============================================================================
"""

from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Dict, Any, Optional, Callable


class OpenVehicleState(Enum):
    INIT = "INIT"
    STANDBY = "STANDBY"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    SAFE_STOP = "SAFE_STOP"


class LicenseTier(Enum):
    OPEN_APACHE2 = "OPEN_APACHE2"
    COMMERCIAL_ASIL_D = "COMMERCIAL_ASIL_D"


@dataclass
class OpenTelemetryFrame:
    timestamp: float
    bus_id: int
    data: bytes
    dlc: int
    is_fd: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class OpenVehicleStateMachine:
    """
    Open-Source Baseline Vehicle State Machine (Apache 2.0).
    Provides standard transitions, basic timeout tracking, and hook points
    for commercial ASIL-D extensions.
    """

    def __init__(self, license_tier: LicenseTier = LicenseTier.OPEN_APACHE2):
        self.state = OpenVehicleState.INIT
        self.license_tier = license_tier
        self.last_transition_time = time.time()
        self.transition_log = []
        self._commercial_arbiter_hook: Optional[Callable[[str, Dict[str, Any]], bool]] = None

    def register_commercial_hook(self, hook_fn: Callable[[str, Dict[str, Any]], bool]) -> None:
        """
        Allows binding the closed-source ASIL-D hardware arbiter and MC/DC
        verified safety cage when running under commercial license.
        """
        self._commercial_arbiter_hook = hook_fn

    def transition_to(self, new_state: OpenVehicleState, reason: str = "") -> bool:
        """
        Executes safe state transition with optional commercial hook interception.
        """
        if self._commercial_arbiter_hook:
            # Commercial hook can enforce hardware envelope or trigger fast abort
            allow = self._commercial_arbiter_hook(new_state.value, {"current_state": self.state.value, "reason": reason})
            if not allow:
                self.state = OpenVehicleState.SAFE_STOP
                self.transition_log.append((time.time(), OpenVehicleState.SAFE_STOP, f"COMMERCIAL_ABORT: {reason}"))
                return False

        old_state = self.state
        self.state = new_state
        self.last_transition_time = time.time()
        self.transition_log.append((self.last_transition_time, new_state, reason))
        return True

    def process_telemetry(self, frame: OpenTelemetryFrame) -> Dict[str, Any]:
        """
        Processes standard CAN/CAN-FD telemetry frames.
        """
        if self.state == OpenVehicleState.INIT:
            self.transition_to(OpenVehicleState.STANDBY, "Init completed")

        return {
            "processed": True,
            "state": self.state.value,
            "bus_id": frame.bus_id,
            "dlc": frame.dlc,
            "license": self.license_tier.value,
        }

    def get_audit_summary(self) -> Dict[str, Any]:
        return {
            "license_tier": self.license_tier.value,
            "current_state": self.state.value,
            "total_transitions": len(self.transition_log),
            "is_commercial_secured": self._commercial_arbiter_hook is not None,
        }

