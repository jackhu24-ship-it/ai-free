#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 【PROJ-19 MCU 數位分身與 EventBus 橋接引擎】：event_bus_mcu_bridge.py
========================================================================================
角色分工：
  - 👑 小幫手 (Agent_PM)     : 作戰調度與規格總控
  - 🛠️ 小開 (Agent_Coder)   : 核心代碼開發、PROJ-18 引擎骨架與微創自癒
  - 🐎 小馬 (Agent_Reviewer): AST 語法審計、CWE-1236 防護與十進制優先校驗
  - 👁️ 小Ｏ (Agent_Vision)  : 10-bit ADC 遙測波形即時監控與 >5.5V 硬體過壓熔斷驗證

技術指標：
  1. 【十進制優先】：ADC: 512 (十進制) | 2.50V | 原始碼: 0x0200 (0b001000000000)
  2. 【10-bit ADC 線性轉換】：0~1023 階, Vref=5.00V, 解析度 4.8876mV/step
  3. 【硬體過壓熔斷】：Vin > 5.50V 觸發虛擬保險絲熔斷 (Virtual Fuse Blown) 與 EventBus 警報
  4. 【CWE-1236 防護】：試算表/CSV 輸出欄位強制 sanitize_cell 防公式注入
"""

from __future__ import annotations

import sys
import os

# Windows UTF-8 編碼跨平台防護
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import time
import math
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, AsyncGenerator
from dataclasses import dataclass, asdict

# 引入 EventBus 與 MCU 數位孿生
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from event_bus import AgentEventBus
except ImportError:
    try:
        from agent_event_bus import AgentEventBus
    except ImportError:
        AgentEventBus = None  # type: ignore

try:
    from mcu_digital_twin import MCUDigitalTwin
except ImportError:
    MCUDigitalTwin = None  # type: ignore


# ============================================================================
# CWE-1236 公式注入防禦過濾器 (小馬 Reviewer 嚴格合規)
# ============================================================================

def sanitize_cell(val: Any) -> Any:
    """CWE-1236 試算表公式注入防護：若開頭為 =, +, -, @ 則前置單引號"""
    if isinstance(val, str) and val.startswith(("=", "+", "-", "@")):
        return f"'{val}"
    return val


# ============================================================================
# 數據結構定義 (十進制優先資料契約)
# ============================================================================

@dataclass
class ADCTelemetryFrame:
    """
    10-bit ADC 遙測資料幀 (嚴格落實十進制優先規範)
    """
    timestamp_ms: float
    channel: int
    adc_raw_dec: int             # 十進制原始採樣值 (0 ~ 1023)
    measured_voltage: float      # 計算之物理電壓 (V)
    simulated_input_voltage: float  # 輸入模擬電壓 (V)
    hex_code: str                # 原始碼十六進制 (0x0200)
    bin_code: str                # 原始碼二進制 (0b001000000000)
    is_overvoltage_tripped: bool # 是否觸發 >5.5V 硬體過壓熔斷
    diagnostic_message: str      # 繁體中文自然語言診斷訊息

    def format_decimal_first(self) -> str:
        """格式化為十進制優先標準輸出"""
        status_tag = "🔴 [過壓熔斷]" if self.is_overvoltage_tripped else "🟢 [正常]"
        return (
            f"{status_tag} CH{self.channel} | "
            f"ADC: {self.adc_raw_dec} (十進制) | "
            f"{self.measured_voltage:.2f}V (輸入: {self.simulated_input_voltage:.2f}V) | "
            f"原始碼: {self.hex_code} ({self.bin_code})"
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================================
# 核心橋接引擎：MCUEventBusBridge
# ============================================================================

class MCUEventBusBridge:
    """
    PROJ-19 MCU 數位分身與 EventBus 橋接引擎
    """
    V_REF = 5.000                # 基準參考電壓 5.0V
    ADC_MAX_STEPS = 1023         # 10-bit 解析度上限
    OVERVOLTAGE_THRESHOLD = 5.50 # 硬體過壓熔斷閾值 (5.5V)

    def __init__(self, event_bus: Optional[Any] = None, digital_twin: Optional[Any] = None):
        self.event_bus = event_bus or (AgentEventBus() if AgentEventBus else None)
        self.digital_twin = digital_twin or (MCUDigitalTwin() if MCUDigitalTwin else None)
        self.is_fuse_blown = False
        self.sample_history: List[ADCTelemetryFrame] = []
        self.telemetry_callbacks = []

    def reset_hardware_fuse(self):
        """重設虛擬硬體保險絲"""
        self.is_fuse_blown = False

    def convert_voltage_to_adc_10bit(self, input_voltage: float) -> Tuple[int, float, bool]:
        """
        執行 10-bit ADC 轉換與過壓保護檢測
        回傳: (adc_raw_dec, measured_voltage, is_tripped)
        """
        # 1. 檢測是否超過 5.5V 安全閾值
        if input_voltage > self.OVERVOLTAGE_THRESHOLD:
            self.is_fuse_blown = True
            # 過壓熔斷：ADC 飽和並觸發保護
            return self.ADC_MAX_STEPS, self.V_REF, True

        if self.is_fuse_blown:
            # 保險絲已斷開，電壓採樣歸零
            return 0, 0.0, True

        # 2. 正常 10-bit 線性轉換
        clamped_voltage = max(0.0, min(input_voltage, self.V_REF))
        raw_steps = round((clamped_voltage / self.V_REF) * self.ADC_MAX_STEPS)
        adc_raw_dec = max(0, min(raw_steps, self.ADC_MAX_STEPS))
        measured_voltage = (adc_raw_dec / self.ADC_MAX_STEPS) * self.V_REF

        return adc_raw_dec, round(measured_voltage, 3), False

    def sample_adc(self, channel: int, input_voltage: float) -> ADCTelemetryFrame:
        """
        對指定通道進行採樣，生成遙測幀並處理熔斷邏輯
        """
        now_ms = round(time.time() * 1000, 2)
        adc_dec, measured_v, is_tripped = self.convert_voltage_to_adc_10bit(input_voltage)

        hex_repr = f"0x{adc_dec:04X}"
        bin_repr = f"0b{adc_dec:012b}"

        if is_tripped:
            diag_msg = (
                f"⚠️ [硬體過壓熔斷警報] 檢測到輸入電壓 {input_voltage:.2f}V 超過 5.50V 安全極限！"
                f"虛擬保險絲已強制斷開，系統已鉗位停機以防炸板！"
            )
        else:
            diag_msg = (
                f"✅ [採樣正常] 通道 CH{channel} 採樣電壓 {measured_v:.2f}V，"
                f"ADC 十進制讀數 {adc_dec}。"
            )

        frame = ADCTelemetryFrame(
            timestamp_ms=now_ms,
            channel=channel,
            adc_raw_dec=adc_dec,
            measured_voltage=measured_v,
            simulated_input_voltage=round(input_voltage, 3),
            hex_code=hex_repr,
            bin_code=bin_repr,
            is_overvoltage_tripped=is_tripped,
            diagnostic_message=diag_msg
        )

        self.sample_history.append(frame)
        return frame

    async def broadcast_telemetry(self, frame: ADCTelemetryFrame) -> Dict[str, Any]:
        """
        將遙測數據幀廣播至 EventBus
        """
        topic = "HARDWARE_OVERVOLTAGE_TRIP" if frame.is_overvoltage_tripped else "ADC_TELEMETRY_STREAM"
        priority = "CRITICAL" if frame.is_overvoltage_tripped else "NORMAL"

        payload = {
            "source": "MCUEventBusBridge",
            "topic": topic,
            "priority": priority,
            "frame": frame.to_dict(),
            "formatted_string": frame.format_decimal_first()
        }

        if self.event_bus:
            try:
                if hasattr(self.event_bus, "publish"):
                    await self.event_bus.publish(topic=topic, message=payload, priority=priority)
                elif hasattr(self.event_bus, "emit"):
                    await self.event_bus.emit(topic, payload)
            except Exception as e:
                payload["event_bus_error"] = str(e)

        return payload

    async def stream_telemetry_waveforms(
        self,
        voltages: List[float],
        channel: int = 0,
        interval_sec: float = 0.01
    ) -> AsyncGenerator[ADCTelemetryFrame, None]:
        """
        非同步波形採樣串流產生器 (供 小Ｏ Agent_Vision 進行波形檢視)
        """
        for v in voltages:
            frame = self.sample_adc(channel=channel, input_voltage=v)
            await self.broadcast_telemetry(frame)
            yield frame
            await asyncio.sleep(interval_sec)

    def export_telemetry_csv(self, file_path: Union[str, Path]) -> str:
        """
        匯出遙測歷史為 CSV，強制調用 sanitize_cell 防禦 CWE-1236 公式注入
        """
        path = Path(file_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        headers = [
            "timestamp_ms",
            "channel",
            "adc_raw_dec",
            "measured_voltage",
            "input_voltage",
            "hex_code",
            "bin_code",
            "is_tripped",
            "diagnostic_message"
        ]

        lines = [",".join(headers)]
        for f in self.sample_history:
            row = [
                str(sanitize_cell(f.timestamp_ms)),
                str(sanitize_cell(f.channel)),
                str(sanitize_cell(f.adc_raw_dec)),
                str(sanitize_cell(f.measured_voltage)),
                str(sanitize_cell(f.simulated_input_voltage)),
                str(sanitize_cell(f.hex_code)),
                str(sanitize_cell(f.bin_code)),
                str(sanitize_cell(f.is_overvoltage_tripped)),
                f'"{sanitize_cell(f.diagnostic_message)}"'
            ]
            lines.append(",".join(row))

        csv_content = "\n".join(lines)
        with open(path, "w", encoding="utf-8", errors="replace", newline="\n") as fp:
            fp.write(csv_content)

        return str(path)


# ============================================================================
# 自我驗證入口 (Self-Test CLI Harness)
# ============================================================================

async def run_self_test():
    print("=" * 80)
    print("🚀 【PROJ-19 MCU 數位分身與 EventBus 橋接引擎自檢】")
    print("=" * 80)

    bridge = MCUEventBusBridge()

    # 1. 驗證 10-bit 轉換 (2.5V 應為 512 階)
    f_mid = bridge.sample_adc(channel=0, input_voltage=2.50)
    assert f_mid.adc_raw_dec in (511, 512), f"2.5V 轉換異常: {f_mid.adc_raw_dec}"
    assert f_mid.is_overvoltage_tripped is False
    print(f"✅ 2.5V 採樣驗證成功: {f_mid.format_decimal_first()}")

    # 2. 驗證 5.0V 滿量程 (應為 1023 階)
    f_max = bridge.sample_adc(channel=0, input_voltage=5.00)
    assert f_max.adc_raw_dec == 1023, f"5.0V 轉換異常: {f_max.adc_raw_dec}"
    print(f"✅ 5.0V 滿量程驗證成功: {f_max.format_decimal_first()}")

    # 3. 驗證 >5.5V 硬體過壓熔斷
    f_trip = bridge.sample_adc(channel=0, input_voltage=6.00)
    assert f_trip.is_overvoltage_tripped is True
    assert "硬體過壓熔斷" in f_trip.diagnostic_message
    print(f"✅ 6.0V 過壓熔斷驗證成功: {f_trip.format_decimal_first()}")

    print("\n🟢 PROJ-19 event_bus_mcu_bridge.py 自檢 100% 通過！")


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        asyncio.run(run_self_test())
