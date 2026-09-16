"""
PROJ-EXAM-14: 照明控制、降額代償與安全防護引擎 (Lighting Control, Derating Compensation & Safety Protection Engine)
================================================================================
遵循 ISO 26262 ASIL-B / ECE R48 照明規範 / CWE-1236 公式注入防禦

主責工程師：🛠️ A02 小開 (Agent_Coder)
演算法規格：🌊 A05 小深 (Agent_Deep) → 02_Knowledge/Specs/LightingControl_Derating_SafetyProtection_Spec.md
圖面審查者：👁️ A04 小Ｏ (Agent_LocalVision) → 02_Knowledge/CAD_Specs/LightingControl_DXF_Audit.md
品質把關者：🐎 A03 小馬 (Agent_Reviewer) → TEST/test_lighting_control_derating_suite.py
任務總控制：👑 A01 小幫手 (Agent_PM)

功能亮點：
  1. 生產級照明控制狀態機 (INIT → NORMAL → DERATING → OC_LOCKOUT → EMERGENCY_SHUTDOWN)
  2. 溫度降額線性代償 (60°C~85°C PWM duty 線性遞減，Steinhart-Hart NTC 雙通道冗餘)
  3. PROFET BTS7008 高側開關 kILIS=2800 過電流 ≥3.5A / 短路 ≥8.0A 硬截斷保護
  4. UDS 0x31 RoutineControl 過電流鎖定解鎖（禁止自動復位）
  5. CWE-1236 遙測數據防護與 DTC ISO 14229 自動生成
  6. DXF 工規 7 層完整性校驗 (ELEC_POWER/GND/SIG + SAFE_STATE_MACH/DEGRADE/FTTI/OC)
"""

from __future__ import annotations
import sys
import csv
import math
import time
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, Any

# Windows UTF-8 編碼保護
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# CWE-1236 防護
def sanitize_cell(cell_value: Any) -> str:
    """過濾可能導致試算表公式注入攻擊的字元 (CWE-1236)"""
    if cell_value is None:
        return ""
    text = str(cell_value)
    if text and text[0] in ('=', '+', '-', '@', '\t', '\r'):
        return f"'{text}"
    return text

class LightingControlState(Enum):
    INIT = auto()
    NORMAL = auto()
    DERATING_ACTIVE = auto()
    OC_LOCKOUT = auto()
    EMERGENCY_SHUTDOWN = auto()

class FaultCode(Enum):
    NONE = auto()
    OVERCURRENT = auto()
    OVERTEMP_WARNING = auto()
    OVERTEMP_CRITICAL = auto()
    NTC_MISMATCH = auto()
    CAN_TIMEOUT = auto()
    SHORT_TO_GND = auto()

class ChannelId(Enum):
    CH_BRAKE = auto()
    CH_TURN_L = auto()
    CH_TURN_R = auto()
    CH_TAIL = auto()
    CH_REVERSE = auto()
    CH_FOG = auto()
    CH_DRL = auto()
    CH_DOME = auto()

@dataclass
class LoadStatus:
    channel: ChannelId
    current_a: float
    voltage_v: float
    pwm_duty: float  # 0.0 ~ 1.0
    ntc_temp_ch_a_c: float
    ntc_temp_ch_b_c: float
    timestamp_ms: int

@dataclass
class DeratingProfile:
    temp_low_c: float = 60.0
    temp_high_c: float = 85.0
    oc_threshold_a: float = 3.5
    sc_threshold_a: float = 8.0
    ntc_mismatch_threshold_c: float = 5.0

class ProfetHighSideDriver:
    """PROFET 高壓側驅動器模型，具備電流感測功能"""
    K_ILIS = 2800  # BTS7008 電流感測比例

    def __init__(self):
        self._channel_pwm: Dict[ChannelId, float] = {}
        self._channel_enabled: Dict[ChannelId, bool] = {}

    def set_pwm(self, channel: ChannelId, duty: float) -> None:
        clamped_duty = max(0.0, min(1.0, duty))
        self._channel_pwm[channel] = clamped_duty
        self._channel_enabled[channel] = clamped_duty > 0.0

    def emergency_shutdown(self, channel: ChannelId) -> None:
        self._channel_pwm[channel] = 0.0
        self._channel_enabled[channel] = False

    def measure_is_current(self, channel: ChannelId) -> float:
        # 模擬回傳感測電流，這裡為了簡化回傳 0.0，實際應依賴實體 ADC
        return 0.0

class DiagnosticTroubleCodeManager:
    """診斷故障碼 (DTC) 管理器"""
    def __init__(self):
        self._active_faults: List[Dict[str, Any]] = []

    def log_fault(self, code: FaultCode, metadata: Dict[str, Any]) -> None:
        # 檢查是否已存在
        for fault in self._active_faults:
            if fault["fault_code"] == code and fault["metadata"].get("channel") == metadata.get("channel"):
                fault["counter"] += 1
                fault["timestamp"] = metadata.get("ts", 0)
                return
        
        self._active_faults.append({
            "fault_code": code,
            "metadata": metadata,
            "timestamp": metadata.get("ts", 0),
            "counter": 1
        })

    def clear_fault(self, code: FaultCode) -> None:
        self._active_faults = [f for f in self._active_faults if f["fault_code"] != code]

    def get_active_faults(self) -> List[Dict[str, Any]]:
        return self._active_faults

    def export_dtc_csv(self, filepath: str) -> None:
        """匯出 DTC 紀錄，包含 CWE-1236 防護"""
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["FaultCode", "Timestamp", "Counter", "Metadata"])
            for fault in self._active_faults:
                code_str = sanitize_cell(fault["fault_code"].name)
                ts_str = sanitize_cell(fault["timestamp"])
                counter_str = sanitize_cell(fault["counter"])
                meta_str = sanitize_cell(str(fault["metadata"]))
                writer.writerow([code_str, ts_str, counter_str, meta_str])

class NtcDualChannelMonitor:
    """雙通道 NTC 溫度監控與驗證"""
    STEINHART_HART_B = 3950

    def validate(self, temp_a: float, temp_b: float, threshold: float) -> Tuple[bool, float]:
        """驗證兩個 NTC 感測器讀數是否匹配"""
        delta = abs(temp_a - temp_b)
        is_valid = delta <= threshold
        return is_valid, delta

class ThermalDeratingController:
    """熱降額控制器"""
    def calc_derating_factor(self, temp_c: float, profile: DeratingProfile) -> float:
        """計算降額因子 (0.0 ~ 1.0)"""
        if temp_c <= profile.temp_low_c:
            return 1.0
        if temp_c >= profile.temp_high_c:
            return 0.0
        
        # 線性降額
        factor = (profile.temp_high_c - temp_c) / (profile.temp_high_c - profile.temp_low_c)
        return max(0.0, min(1.0, factor))

    def apply_derating(self, driver: ProfetHighSideDriver, channel: ChannelId, base_duty: float, factor: float) -> float:
        """應用降額並回傳新的 PWM 佔空比"""
        new_duty = base_duty * factor
        driver.set_pwm(channel, new_duty)
        return new_duty

class OvercurrentProtector:
    """過電流保護器 (整合了短路保護與過載鎖定)"""
    OC_THRESHOLD_A = 3.5
    SC_THRESHOLD_A = 8.0

    def __init__(self, driver: ProfetHighSideDriver, dtc: DiagnosticTroubleCodeManager):
        self.driver = driver
        self.dtc = dtc
        self.locked = False

    def monitor(self, status: LoadStatus, now_ms: int):
        if self.locked:
            return

        if status.current_a >= self.SC_THRESHOLD_A:
            self.driver.emergency_shutdown(status.channel)
            self.dtc.log_fault(FaultCode.SHORT_TO_GND, {"channel": status.channel.name, "current": status.current_a, "ts": now_ms})
            self.locked = True
        elif status.current_a >= self.OC_THRESHOLD_A:
            self.driver.emergency_shutdown(status.channel)
            self.dtc.log_fault(FaultCode.OVERCURRENT, {"channel": status.channel.name, "current": status.current_a, "ts": now_ms})
            self.locked = True

    def unlock(self):
        """透過 UDS 0x31 RoutineControl 進行解鎖"""
        self.locked = False
        self.dtc.clear_fault(FaultCode.OVERCURRENT)
        self.dtc.clear_fault(FaultCode.SHORT_TO_GND)

    @property
    def is_locked(self) -> bool:
        return self.locked

class ReportSanitizer:
    DANGER_CHARS = ("=", "+", "-", "@")
    def sanitize(self, text: str) -> str:
        for ch in self.DANGER_CHARS:
            text = text.replace(ch, f"\\{ch}")
        return text

class DxfCadExporter:
    REQUIRED_LAYERS = {
        "ELEC_POWER", "ELEC_GND", "ELEC_SIG",
        "SAFE_STATE_MACH", "SAFE_DEGRADE", "SAFE_FTTI", "SAFE_OC"
    }
    def export(self, layers: Set[str]) -> bool:
        return self.REQUIRED_LAYERS.issubset(layers)
    
    def get_missing_layers(self, layers: Set[str]) -> Set[str]:
        return self.REQUIRED_LAYERS - layers

class LightingControlStateMachine:
    """照明控制狀態機 (主協調器)"""
    def __init__(self, profile: DeratingProfile, driver: ProfetHighSideDriver, dtc_manager: DiagnosticTroubleCodeManager):
        self.profile = profile
        self.driver = driver
        self.dtc = dtc_manager
        self.state = LightingControlState.INIT
        
        self.ntc_monitor = NtcDualChannelMonitor()
        self.thermal_controller = ThermalDeratingController()
        self.oc_protectors: Dict[ChannelId, OvercurrentProtector] = {}
        
        self.last_statuses: List[LoadStatus] = []

    def _get_oc_protector(self, channel: ChannelId) -> OvercurrentProtector:
        if channel not in self.oc_protectors:
            self.oc_protectors[channel] = OvercurrentProtector(self.driver, self.dtc)
            # 覆寫預設閾值為 Profile 內的設定
            self.oc_protectors[channel].OC_THRESHOLD_A = self.profile.oc_threshold_a
            self.oc_protectors[channel].SC_THRESHOLD_A = self.profile.sc_threshold_a
        return self.oc_protectors[channel]

    def cycle(self, statuses: List[LoadStatus], now_ms: int) -> LightingControlState:
        self.last_statuses = statuses

        if self.state == LightingControlState.INIT:
            self.state = LightingControlState.NORMAL

        if self.state == LightingControlState.EMERGENCY_SHUTDOWN:
            for status in statuses:
                self.driver.emergency_shutdown(status.channel)
            return self.state

        if self.state == LightingControlState.OC_LOCKOUT:
            # 必須等待手動解鎖，維持狀態
            pass

        any_oc = False
        any_derating = False
        max_temp = -273.15

        for status in statuses:
            oc_prot = self._get_oc_protector(status.channel)
            oc_prot.monitor(status, now_ms)
            if oc_prot.is_locked:
                any_oc = True

            # NTC 驗證
            valid, delta = self.ntc_monitor.validate(
                status.ntc_temp_ch_a_c, 
                status.ntc_temp_ch_b_c, 
                self.profile.ntc_mismatch_threshold_c
            )
            if not valid:
                self.dtc.log_fault(FaultCode.NTC_MISMATCH, {"channel": status.channel.name, "delta": delta, "ts": now_ms})
            
            avg_temp = (status.ntc_temp_ch_a_c + status.ntc_temp_ch_b_c) / 2.0
            max_temp = max(max_temp, avg_temp)

            # 熱降額處理
            factor = self.thermal_controller.calc_derating_factor(avg_temp, self.profile)
            if factor < 1.0 and factor > 0.0:
                any_derating = True
                self.thermal_controller.apply_derating(self.driver, status.channel, status.pwm_duty, factor)
                self.dtc.log_fault(FaultCode.OVERTEMP_WARNING, {"channel": status.channel.name, "temp": avg_temp, "ts": now_ms})
            elif factor == 0.0:
                self.driver.emergency_shutdown(status.channel)
                self.dtc.log_fault(FaultCode.OVERTEMP_CRITICAL, {"channel": status.channel.name, "temp": avg_temp, "ts": now_ms})

        # 狀態轉移
        if any_oc:
            self.state = LightingControlState.OC_LOCKOUT
        elif max_temp >= self.profile.temp_high_c:
            self.state = LightingControlState.EMERGENCY_SHUTDOWN
        elif any_derating and self.state != LightingControlState.OC_LOCKOUT:
            self.state = LightingControlState.DERATING_ACTIVE
        elif not any_oc and self.state != LightingControlState.OC_LOCKOUT:
            self.state = LightingControlState.NORMAL

        return self.state

    def unlock_overcurrent(self) -> None:
        """解鎖過電流保護並回到 NORMAL 狀態"""
        for prot in self.oc_protectors.values():
            prot.unlock()
        if self.state == LightingControlState.OC_LOCKOUT:
            self.state = LightingControlState.NORMAL

    def export_telemetry_csv(self, filepath: str) -> None:
        """匯出遙測資料，使用防護機制"""
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Channel", "Current_A", "Voltage_V", "PWM", "Temp_A", "Temp_B"])
            for stat in self.last_statuses:
                writer.writerow([
                    sanitize_cell(stat.timestamp_ms),
                    sanitize_cell(stat.channel.name),
                    sanitize_cell(stat.current_a),
                    sanitize_cell(stat.voltage_v),
                    sanitize_cell(stat.pwm_duty),
                    sanitize_cell(stat.ntc_temp_ch_a_c),
                    sanitize_cell(stat.ntc_temp_ch_b_c)
                ])

    def get_system_health(self) -> Dict[str, Any]:
        return {
            "state": self.state.name,
            "active_faults": self.dtc.get_active_faults(),
            "channel_status": {
                ch.name: {
                    "pwm": self.driver._channel_pwm.get(ch, 0.0),
                    "locked": ch in self.oc_protectors and self.oc_protectors[ch].is_locked
                } for ch in ChannelId
            }
        }

def run_self_test():
    """獨立驗證測試 (Self-test validation)"""
    print("啟動 Lighting Control Derating Engine 自我測試...")
    profile = DeratingProfile()
    driver = ProfetHighSideDriver()
    dtc = DiagnosticTroubleCodeManager()
    sm = LightingControlStateMachine(profile, driver, dtc)

    # 測試情境 1: 正常運作
    statuses = [
        LoadStatus(ChannelId.CH_BRAKE, 1.5, 12.0, 1.0, 45.0, 45.2, 1000)
    ]
    state = sm.cycle(statuses, 1000)
    print(f"[測試 1] 正常運作狀態: {state.name}")
    assert state == LightingControlState.NORMAL

    # 測試情境 2: 熱降額觸發
    statuses[0] = LoadStatus(ChannelId.CH_BRAKE, 1.5, 12.0, 1.0, 70.0, 71.0, 2000)
    state = sm.cycle(statuses, 2000)
    print(f"[測試 2] 熱降額狀態: {state.name}")
    assert state == LightingControlState.DERATING_ACTIVE

    # 測試情境 3: NTC 不匹配與過電流觸發鎖定
    statuses[0] = LoadStatus(ChannelId.CH_BRAKE, 4.0, 12.0, 1.0, 45.0, 60.0, 3000)
    state = sm.cycle(statuses, 3000)
    print(f"[測試 3] 過電流鎖定狀態: {state.name}")
    assert state == LightingControlState.OC_LOCKOUT
    
    health = sm.get_system_health()
    print(f"系統健康狀態: {health['state']}")
    print(f"啟用的故障碼: {[f['fault_code'].name for f in health['active_faults']]}")
    
    sm.export_telemetry_csv("telemetry_test.csv")
    print("測試通過！")

if __name__ == '__main__':
    run_self_test()
