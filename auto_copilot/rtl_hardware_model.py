# -*- coding: utf-8 -*-
"""
=============================================================================
AutoCopilot Silicon IP Core Cycle-Accurate Simulator & Financial Model
=============================================================================
Corresponds to Synthesizable RTL: Safety_Fast_Abort_Arbiter_Core (IEEE 1364)
Target Vendors: Infineon Technologies (AURIX), NXP Semiconductors (S32G)
=============================================================================
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, Any, List


class RTLTripReason(IntEnum):
    REASON_NONE = 0
    REASON_CRC_ERR = 1
    REASON_CNT_ERR = 2
    REASON_OVERTORQUE = 3
    REASON_EXT_FAULT = 4


@dataclass
class RTLSimulationStep:
    clock_cycle: int
    timestamp_ns: float
    power_stage_en: bool
    safe_state_tripped: bool
    nmi_irq: bool
    trip_reason: RTLTripReason
    latency_cycles: int


class SafetyFastAbortArbiterModel:
    """
    Python bit-level and cycle-accurate model of the synthesizable Verilog RTL.
    Clock: 400 MHz (2.5 ns per clock tick).
    """
    HSM_UNLOCK_MAGIC = 0xA55ABEEF

    def __init__(self, clock_freq_mhz: int = 400):
        self.clock_freq_mhz = clock_freq_mhz
        self.clock_period_ns = 1000.0 / clock_freq_mhz  # 2.5ns @ 400MHz
        
        # Internal Registers
        self.cycle_count = 0
        self.power_stage_en = False
        self.safe_state_tripped = True  # Reset state
        self.nmi_irq = False
        self.trip_reason = RTLTripReason.REASON_NONE
        self.latency_cycles = 0

    def reset(self):
        self.power_stage_en = False
        self.safe_state_tripped = True
        self.nmi_irq = False
        self.trip_reason = RTLTripReason.REASON_NONE
        self.latency_cycles = 0

    def clock_step(
        self,
        torque_cmd: int = 0,
        torque_valid: bool = False,
        envelope_max: int = 100,
        e2e_crc_err: bool = False,
        roll_cnt_err: bool = False,
        ext_fault_n: bool = True,
        hsm_unlock_key: int = 0,
        hsm_clear_trip: bool = False
    ) -> RTLSimulationStep:
        self.cycle_count += 1
        current_time_ns = self.cycle_count * self.clock_period_ns

        # Combinational evaluation
        is_overtorque = torque_valid and (torque_cmd > envelope_max)
        fault_detected = (
            e2e_crc_err or
            roll_cnt_err or
            (not ext_fault_n) or
            is_overtorque
        )

        if e2e_crc_err:
            cause = RTLTripReason.REASON_CRC_ERR
        elif roll_cnt_err:
            cause = RTLTripReason.REASON_CNT_ERR
        elif not ext_fault_n:
            cause = RTLTripReason.REASON_EXT_FAULT
        elif is_overtorque:
            cause = RTLTripReason.REASON_OVERTORQUE
        else:
            cause = RTLTripReason.REASON_NONE

        # Synchronous Clock Edge
        if fault_detected:
            self.power_stage_en = False
            self.safe_state_tripped = True
            self.nmi_irq = True
            self.trip_reason = cause
            self.latency_cycles = 1  # Guaranteed single cycle
        elif self.safe_state_tripped:
            self.power_stage_en = False
            self.nmi_irq = False
            if hsm_clear_trip and (hsm_unlock_key == self.HSM_UNLOCK_MAGIC):
                self.safe_state_tripped = False
                self.trip_reason = RTLTripReason.REASON_NONE
                self.power_stage_en = True
                self.latency_cycles = 0
        else:
            self.power_stage_en = True
            self.safe_state_tripped = False
            self.nmi_irq = False
            self.trip_reason = RTLTripReason.REASON_NONE
            self.latency_cycles = 0

        return RTLSimulationStep(
            clock_cycle=self.cycle_count,
            timestamp_ns=current_time_ns,
            power_stage_en=self.power_stage_en,
            safe_state_tripped=self.safe_state_tripped,
            nmi_irq=self.nmi_irq,
            trip_reason=self.trip_reason,
            latency_cycles=self.latency_cycles
        )


class SiliconRoyaltyCalculator:
    """
    Financial Modeling Engine for Hardened RTL IP Core Licensing to Silicon Vendors.
    """
    @staticmethod
    def calculate_royalty(
        units_shipped: int,
        royalty_per_die_usd: float = 0.25,
        nre_upfront_usd: float = 2_500_000.0,
        maintenance_annual_usd: float = 350_000.0
    ) -> Dict[str, Any]:
        variable_royalty = units_shipped * royalty_per_die_usd
        total_gross = nre_upfront_usd + variable_royalty + maintenance_annual_usd
        gross_margin_pct = 94.5  # Pure IP revenue has near-zero COGS
        return {
            "units_shipped": units_shipped,
            "royalty_per_die_usd": royalty_per_die_usd,
            "nre_upfront_usd": nre_upfront_usd,
            "annual_maintenance_usd": maintenance_annual_usd,
            "variable_royalty_usd": variable_royalty,
            "total_gross_usd": total_gross,
            "net_margin_pct": gross_margin_pct,
            "pure_profit_usd": total_gross * (gross_margin_pct / 100.0)
        }

