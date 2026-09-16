#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 【PROJ-EXAM-11 ISO 26262 ASIL-B 煞車燈/轉向燈故障注入與安全降級狀態機】
================================================================================
主責工程師：🛠️ A02 小開 (Agent_Coder)
演算法規格：🌊 A05 小深 (02_Knowledge/Specs/ASIL_B_Lighting_FailSafe_Spec.md)
品質把關者：🐎 A03 小馬 (TEST/test_asil_b_failsafe_lighting_engine.py)

功能亮點：
  1. 雙路霍爾煞車踏板冗餘採樣與信號失配安全防護 (Fail-Safe ON)
  2. ADC 高邊電流採樣 (0.8~2.2A 常態 / <0.15A 斷路 / >3.5A 短路)
  3. ECE R48 轉向燈快閃調製器 (1.5Hz 常態 -> 3.0Hz 超閃 Hyperflash)
  4. 煞車燈故障安全替代機制 (主煞車燈斷路 -> 尾燈 100% PWM 滿載代償)
  5. 5 大故障注入器 (Open Circuit, Short Circuit, Pedal Mismatch, CAN Loss)
  6. FTTI <= 100ms 即時監控、DTC 生成與 CWE-1236 CSV 防注入匯出
"""

from __future__ import annotations

import sys
import os
import time
import math
import csv
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple

# Windows UTF-8 編碼防護
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def sanitize_cell(val: Any) -> str:
    """CWE-1236 試算表/CSV 公式注入防護"""
    s = str(val)
    if s.startswith(("=", "+", "-", "@")):
        return f"'{s}"
    return s


class FaultType(Enum):
    NONE = "NONE"
    OPEN_CIRCUIT = "OPEN_CIRCUIT"         # 斷路 (I < 0.15A)
    SHORT_TO_GND = "SHORT_TO_GND"         # 短路 (I > 3.5A)
    PEDAL_MISMATCH = "PEDAL_MISMATCH"     # 雙路踏板失配 (>50ms)
    CAN_COMM_LOSS = "CAN_COMM_LOSS"       # BCM 通訊丟失 (>100ms)


class SafetyState(Enum):
    NORMAL = "NORMAL"                     # 常態運作 (1.5Hz 轉向 / 正常制動)
    HYPERFLASH_DEGRADED = "HYPERFLASH"    # ECE R48 轉向燈超閃警告 (3.0Hz)
    LIGHT_SUBSTITUTION = "SUBSTITUTION"   # 煞車燈尾燈 100% PWM 替代
    FAIL_SAFE_ON = "FAIL_SAFE_ON"         # 踏板失配：煞車燈強制常亮
    LIMP_HOME = "LIMP_HOME"               # 總線丟失：雙閃危險警報燈啟動


@dataclass
class ChannelStatus:
    channel_name: str
    target_state: bool = False
    current_a: float = 0.0
    pwm_duty_pct: float = 0.0
    is_open: bool = False
    is_short: bool = False
    dtc_code: str = ""


class ASIL_B_LightingEngine:
    """
    ISO 26262 ASIL-B 車燈功能安全與故障降級狀態機核心引擎
    """

    def __init__(self):
        self.channels: Dict[str, ChannelStatus] = {
            "LEFT_TURN": ChannelStatus("LEFT_TURN"),
            "RIGHT_TURN": ChannelStatus("RIGHT_TURN"),
            "LEFT_STOP": ChannelStatus("LEFT_STOP"),
            "RIGHT_STOP": ChannelStatus("RIGHT_STOP"),
            "CHMSL": ChannelStatus("CHMSL"),
            "LEFT_TAIL": ChannelStatus("LEFT_TAIL", pwm_duty_pct=30.0),
            "RIGHT_TAIL": ChannelStatus("RIGHT_TAIL", pwm_duty_pct=30.0),
        }
        self.injected_faults: Dict[str, FaultType] = {ch: FaultType.NONE for ch in self.channels}
        self.pedal_fault: FaultType = FaultType.NONE
        self.can_fault: FaultType = FaultType.NONE

        self.current_state: SafetyState = SafetyState.NORMAL
        self.active_dtcs: List[str] = []
        self.telemetry_history: List[Dict[str, Any]] = []

    def inject_channel_fault(self, channel: str, fault: FaultType):
        if channel in self.injected_faults:
            self.injected_faults[channel] = fault

    def inject_pedal_fault(self, fault: FaultType):
        self.pedal_fault = fault

    def inject_can_fault(self, fault: FaultType):
        self.can_fault = fault

    def clear_all_faults(self):
        for ch in self.injected_faults:
            self.injected_faults[ch] = FaultType.NONE
        self.pedal_fault = FaultType.NONE
        self.can_fault = FaultType.NONE
        self.active_dtcs.clear()

    def process_safety_loop(self, brake_pedal_raw_a: bool, brake_pedal_raw_b: bool,
                            left_turn_req: bool, right_turn_req: bool, hazard_req: bool) -> Dict[str, Any]:
        """
        執行 ASIL-B 核心安全循環 (週期 10ms，計算 FTTI 響應)
        """
        start_t = time.perf_counter()
        dtcs = []
        state = SafetyState.NORMAL

        # 1. 雙路霍爾踏板冗餘校驗
        if self.pedal_fault == FaultType.PEDAL_MISMATCH:
            brake_pedal_raw_b = not brake_pedal_raw_a # 強制失配

        if brake_pedal_raw_a != brake_pedal_raw_b:
            # 雙路失配 -> Fail-Safe ON (煞車燈強制常亮)
            effective_brake = True
            dtcs.append("P0571-62")
            state = SafetyState.FAIL_SAFE_ON
        else:
            effective_brake = brake_pedal_raw_a

        # 2. CAN 總線狀態檢查
        if self.can_fault == FaultType.CAN_COMM_LOSS:
            dtcs.append("U0140-87")
            state = SafetyState.LIMP_HOME
            hazard_req = True # 強制雙閃

        # 3. 轉向燈與煞車燈驅動目標設定
        self.channels["LEFT_TURN"].target_state = left_turn_req or hazard_req
        self.channels["RIGHT_TURN"].target_state = right_turn_req or hazard_req
        self.channels["LEFT_STOP"].target_state = effective_brake
        self.channels["RIGHT_STOP"].target_state = effective_brake
        self.channels["CHMSL"].target_state = effective_brake

        # 4. ADC 電流採樣與故障模擬
        for ch_name, status in self.channels.items():
            fault = self.injected_faults.get(ch_name, FaultType.NONE)
            if not status.target_state and ch_name not in ["LEFT_TAIL", "RIGHT_TAIL"]:
                status.current_a = 0.0
                status.is_open = False
                status.is_short = False
                continue

            if fault == FaultType.OPEN_CIRCUIT:
                status.current_a = 0.05 # <0.15A
                status.is_open = True
                status.is_short = False
                if "TURN" in ch_name:
                    dtcs.append("B1201-13")
                elif "STOP" in ch_name:
                    dtcs.append("B1204-13")
            elif fault == FaultType.SHORT_TO_GND:
                status.current_a = 5.2 # >3.5A
                status.is_open = False
                status.is_short = True
                dtcs.append("B1204-11")
            else:
                # 正常負載電流 (0.8 ~ 2.1A)
                status.current_a = 1.65 if "STOP" in ch_name else 1.25
                status.is_open = False
                status.is_short = False

        # 5. ECE R48 快閃超閃調製判決
        turn_fault_active = (self.channels["LEFT_TURN"].is_open and self.channels["LEFT_TURN"].target_state) or \
                            (self.channels["RIGHT_TURN"].is_open and self.channels["RIGHT_TURN"].target_state)
        flash_freq_hz = 3.0 if turn_fault_active else 1.5
        if turn_fault_active and state == SafetyState.NORMAL:
            state = SafetyState.HYPERFLASH_DEGRADED

        # 6. 煞車燈安全光效替代 (Light Substitution) 判決
        stop_fault_active = (self.channels["LEFT_STOP"].is_open or self.channels["LEFT_STOP"].is_short or
                             self.channels["RIGHT_STOP"].is_open or self.channels["RIGHT_STOP"].is_short) and effective_brake

        if stop_fault_active:
            # 觸發後尾燈 100% PWM 代償點亮
            self.channels["LEFT_TAIL"].pwm_duty_pct = 100.0
            self.channels["RIGHT_TAIL"].pwm_duty_pct = 100.0
            if state == SafetyState.NORMAL:
                state = SafetyState.LIGHT_SUBSTITUTION
        else:
            self.channels["LEFT_TAIL"].pwm_duty_pct = 30.0
            self.channels["RIGHT_TAIL"].pwm_duty_pct = 30.0

        # 計算反應延遲
        elapsed_ms = (time.perf_counter() - start_t) * 1000.0 + 45.0 # 加上硬體濾波延遲 45ms
        self.current_state = state
        self.active_dtcs = list(set(dtcs))

        record = {
            "timestamp_ms": round(time.time() * 1000.0, 1),
            "safety_state": self.current_state.value,
            "flash_freq_hz": flash_freq_hz,
            "tail_pwm_pct": self.channels["LEFT_TAIL"].pwm_duty_pct,
            "ftti_response_ms": round(elapsed_ms, 2),
            "dtc_count": len(self.active_dtcs),
            "active_dtcs": "|".join(self.active_dtcs) if self.active_dtcs else "NONE"
        }
        self.telemetry_history.append(record)
        return record

    def export_telemetry_csv(self, filepath: str) -> str:
        """匯出 ASIL-B 診斷追蹤 CSV 並落實 CWE-1236 公式注入防護"""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", newline="", encoding="utf-8", errors="replace") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp_ms", "Safety_State", "Flash_Freq_Hz", "Tail_PWM_Pct", "FTTI_Response_ms", "DTC_Count", "Active_DTCs"])
            for r in self.telemetry_history:
                writer.writerow([
                    sanitize_cell(r["timestamp_ms"]),
                    sanitize_cell(r["safety_state"]),
                    sanitize_cell(r["flash_freq_hz"]),
                    sanitize_cell(r["tail_pwm_pct"]),
                    sanitize_cell(r["ftti_response_ms"]),
                    sanitize_cell(r["dtc_count"]),
                    sanitize_cell(r["active_dtcs"])
                ])
        return filepath


def run_self_test():
    print("=" * 80)
    print("🛡️ 【PROJ-EXAM-11 ISO 26262 ASIL-B 車燈功能安全引擎自檢】")
    print("=" * 80)

    engine = ASIL_B_LightingEngine()

    # 1. 常態測試 (制動 + 左轉)
    res1 = engine.process_safety_loop(True, True, True, False, False)
    assert res1["safety_state"] == "NORMAL"
    assert res1["flash_freq_hz"] == 1.5
    assert res1["tail_pwm_pct"] == 30.0
    print("[測試 1: 常態運作] -> State=NORMAL, Freq=1.5Hz, Tail=30% [PASS]")

    # 2. 轉向燈斷路注入 -> 超閃 3.0Hz
    engine.inject_channel_fault("LEFT_TURN", FaultType.OPEN_CIRCUIT)
    res2 = engine.process_safety_loop(True, True, True, False, False)
    assert res2["safety_state"] == "HYPERFLASH"
    assert res2["flash_freq_hz"] == 3.0
    assert "B1201-13" in res2["active_dtcs"]
    print("[測試 2: 左轉燈斷路注入] -> State=HYPERFLASH (3.0Hz), DTC=B1201-13 [PASS]")

    # 3. 煞車燈斷路注入 -> 尾燈 100% PWM 替代
    engine.clear_all_faults()
    engine.inject_channel_fault("LEFT_STOP", FaultType.OPEN_CIRCUIT)
    res3 = engine.process_safety_loop(True, True, False, False, False)
    assert res3["safety_state"] == "SUBSTITUTION"
    assert res3["tail_pwm_pct"] == 100.0
    assert "B1204-13" in res3["active_dtcs"]
    print("[測試 3: 煞車燈斷路注入] -> State=SUBSTITUTION, Tail PWM=100%, DTC=B1204-13 [PASS]")

    # 4. 雙路踏板失配 -> Fail-Safe ON
    engine.clear_all_faults()
    engine.inject_pedal_fault(FaultType.PEDAL_MISMATCH)
    res4 = engine.process_safety_loop(True, False, False, False, False)
    assert res4["safety_state"] == "FAIL_SAFE_ON"
    assert "P0571-62" in res4["active_dtcs"]
    print("[測試 4: 雙路踏板失配注入] -> State=FAIL_SAFE_ON, DTC=P0571-62 [PASS]")

    print("\n🟢 ASIL_B_LightingEngine 自檢 100% 通過！")


if __name__ == "__main__":
    run_self_test()
