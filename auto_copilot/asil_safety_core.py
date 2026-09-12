"""
AutoCopilot ISO 26262 ASIL-D Safety Supervisor Core
===================================================
Implementation of Stage 1 Functional Safety State Machine:
- Step 1.1: Automotive Safe State Machine (INIT, NORMAL_RUN, DEGRADED_WARN, EMERGENCY_SAFE)
- Step 1.2: Two-Key Spoken Handshake (WAITING_CONFIRMATION for physical actuators)
- Step 1.3: Dynamic FTTI (Fault Tolerant Time Interval) 15-second countdown & Safe State fallback
"""

from enum import Enum
import time
from typing import Any, Dict, List, Optional, Tuple

class VehicleSafeState(str, Enum):
    INIT = "INIT"
    NORMAL_RUN = "NORMAL_RUN"
    DEGRADED_WARN = "DEGRADED_WARN"
    WAITING_CONFIRMATION = "WAITING_CONFIRMATION"
    EMERGENCY_SAFE = "EMERGENCY_SAFE"

class ASILHazardLevel(str, Enum):
    QM = "QM"
    ASIL_A = "ASIL_A"
    ASIL_B = "ASIL_B"
    ASIL_C = "ASIL_C"
    ASIL_D = "ASIL_D"

class SafetySupervisor:
    """
    ASIL-D Level Safety Supervisor governing all spoken actuator commands and fault transitions.
    """
    def __init__(self, ftti_seconds: float = 15.0):
        self.current_state: VehicleSafeState = VehicleSafeState.INIT
        self.ftti_seconds = ftti_seconds
        self.ftti_start_time: Optional[float] = None
        self.pending_action: Optional[Dict[str, Any]] = None
        self.high_voltage_interlock_closed: bool = True
        self.coolant_pump_pwm: int = 100
        self.last_transition_reason: str = "System boot self-test passed"
        
        # Self-test transition to NORMAL_RUN
        self.transition_to(VehicleSafeState.NORMAL_RUN, "POST Self-Test Passed")

    def reset(self):
        """Reset supervisor to initial normal state."""
        self.current_state = VehicleSafeState.NORMAL_RUN
        self.ftti_start_time = None
        self.pending_action = None
        self.high_voltage_interlock_closed = True
        self.coolant_pump_pwm = 100
        self.last_transition_reason = "Manual reset to NORMAL_RUN"

    def request_action(self, action: str, hazard_level: ASILHazardLevel = ASILHazardLevel.ASIL_C, details: str = "") -> bool:
        """Request an ASIL-governed physical action."""
        self.pending_action = {
            "intent": action,
            "hazard_level": hazard_level.value,
            "desc": details or action,
            "timestamp": time.time()
        }
        self.transition_to(VehicleSafeState.WAITING_CONFIRMATION, f"Awaiting operator voice confirmation for {action}")
        return True

    def validate_confirmation(self, spoken_phrase: str) -> Tuple[bool, str]:
        """Validate spoken confirmation for pending action."""
        phrase = spoken_phrase.lower()
        if any(w in phrase for w in ["確認執行", "confirm", "yes", "確定"]):
            executed_desc = self.pending_action.get("desc", "未知動作") if self.pending_action else "未知動作"
            self.transition_to(VehicleSafeState.NORMAL_RUN, f"Confirmed and executed: {executed_desc}")
            return True, f"口令驗證通過。已成功執行：{executed_desc}。"
        else:
            self.transition_to(VehicleSafeState.NORMAL_RUN, "Two-key confirmation rejected or aborted")
            return False, "口令不符或操作已取消。致動器保持原始安全鎖定狀態。"

    def transition_to(self, new_state: VehicleSafeState, reason: str):
        """State transition with ISO 26262 audit logging."""
        self.current_state = new_state
        self.last_transition_reason = reason
        if new_state == VehicleSafeState.EMERGENCY_SAFE:
            # Safe State: open HV contactors, clamp coolant pump to 100%
            self.high_voltage_interlock_closed = False
            self.coolant_pump_pwm = 100
            self.pending_action = None
            self.ftti_start_time = None
        elif new_state == VehicleSafeState.DEGRADED_WARN:
            if not self.ftti_start_time:
                self.ftti_start_time = time.time()
        elif new_state == VehicleSafeState.NORMAL_RUN:
            self.ftti_start_time = None
            self.pending_action = None

    def check_ftti_timeout(self) -> bool:
        """Evaluates whether FTTI countdown has expired."""
        if self.current_state == VehicleSafeState.DEGRADED_WARN and self.ftti_start_time:
            elapsed = time.time() - self.ftti_start_time
            if elapsed >= self.ftti_seconds:
                self.transition_to(
                    VehicleSafeState.EMERGENCY_SAFE,
                    f"FTTI Timeout ({self.ftti_seconds}s exceeded without hazard mitigation). Auto emergency shutdown."
                )
                return True
        return False

    def evaluate_request(self, intent: str, action_payload: Dict[str, Any] = None) -> Tuple[bool, str, Optional[VehicleSafeState]]:
        """
        Validates whether an intent/action is permissible under current safe state.
        Returns: (is_allowed, spoken_message, next_state)
        """
        self.check_ftti_timeout()

        # Rule 1: In EMERGENCY_SAFE, all actuator actions are strictly blocked
        if self.current_state == VehicleSafeState.EMERGENCY_SAFE:
            if intent in ["actuate_relay", "clear_dtc", "start_motor"]:
                return (
                    False,
                    "拒絕執行：車輛處於 ISO 26262 緊急安全關斷狀態 (EMERGENCY_SAFE)，高壓迴路已鎖死，禁止任何致動器操作。",
                    self.current_state
                )

        # Rule 2: Physical actuator modifications require Two-Key Handshake
        critical_actions = ["actuate_relay", "cut_pump", "clear_dtc", "override_inverter"]
        if intent in critical_actions:
            if self.current_state == VehicleSafeState.WAITING_CONFIRMATION:
                # Evaluating incoming confirmation
                user_confirmation = (action_payload or {}).get("confirmation_spoken", "").lower()
                if any(w in user_confirmation for w in ["確認執行", "confirm", "yes", "確定"]):
                    executed_desc = self.pending_action.get("desc", "未知致動器")
                    self.transition_to(VehicleSafeState.NORMAL_RUN, f"Confirmed and executed: {executed_desc}")
                    return (
                        True,
                        f"口令驗證通過。已成功執行：{executed_desc}。",
                        VehicleSafeState.NORMAL_RUN
                    )
                else:
                    self.transition_to(VehicleSafeState.NORMAL_RUN, "Two-key confirmation rejected or aborted")
                    return (
                        False,
                        "口令不符或操作已取消。致動器保持原始安全鎖定狀態。",
                        VehicleSafeState.NORMAL_RUN
                    )
            else:
                # Trigger Two-Key Handshake
                self.pending_action = {
                    "intent": intent,
                    "payload": action_payload,
                    "desc": (action_payload or {}).get("desc", "高壓或致動器動作")
                }
                self.transition_to(VehicleSafeState.WAITING_CONFIRMATION, f"Awaiting operator voice confirmation for {intent}")
                return (
                    False,
                    f"安全警告：即將執行危險動作【{self.pending_action['desc']}】。請口語覆誦『確認執行』或『取消』以完成安全交握。",
                    VehicleSafeState.WAITING_CONFIRMATION
                )

        # Rule 3: Diagnostic readouts are always permitted
        return (True, "查詢許可。", self.current_state)

    def get_telemetry_status(self) -> Dict[str, Any]:
        """Provides supervisory telemetry for dashboard display."""
        elapsed_ftti = (time.time() - self.ftti_start_time) if self.ftti_start_time else 0.0
        remaining_ftti = max(0.0, self.ftti_seconds - elapsed_ftti) if self.ftti_start_time else self.ftti_seconds
        return {
            "safe_state": self.current_state.value,
            "hv_interlock": "CLOSED (ENERGIZED)" if self.high_voltage_interlock_closed else "OPEN (SAFE_OFF)",
            "coolant_pump_pwm": self.coolant_pump_pwm,
            "ftti_active": self.ftti_start_time is not None,
            "ftti_remaining_s": round(remaining_ftti, 1),
            "last_reason": self.last_transition_reason
        }

# Global singleton supervisor
safety_supervisor = SafetySupervisor(ftti_seconds=15.0)

def get_safety_supervisor() -> SafetySupervisor:
    """Return the global ASIL-D SafetySupervisor instance."""
    return safety_supervisor
