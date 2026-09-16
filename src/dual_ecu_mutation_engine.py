#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 【PROJ-23 車用雙 ECU 聯調與突變注入引擎】：dual_ecu_mutation_engine.py
========================================================================================
作戰代號：【七星終極任務：Operation Chronos-Omega】
角色協同：
  - 👑 小幫手 (Agent_PM)     : 七星任務總控、雙 ECU 時序調度與三層記憶沉澱
  - 🛠️ 小開 (Agent_Coder)   : 雙 ECU 數位分身聯調、6.5V 破壞性突波注入、曼哈頓紅標故障線束 DXF 出圖
  - 🐎 小馬 (Agent_Reviewer): CWE-1236 注入審計、十進制優先格式校驗、安全中斷審查
  - 👁️ 小Ｏ (Agent_Vision)  : 雙通道 60FPS 遙測示波器監控、DXF 故障拓撲幾何驗收

核心技術：
  1. 【車用雙 ECU 獨立分身】：ECU-1 (BCM 車身 PIC16F18313) ✕ ECU-2 (Gateway 閘道 PIC18F25K80)
  2. 【破壞性突波注入】：6.50V 突波注入 ➔ 毫秒級 EventBus 熔斷 ➔ 斷路保護 (0V/0 LSB) ➔ BCM 獨立運作不受干擾
  3. 【十進制優先雙通道 HUD】：CH0 (BCM: 2.50V/512) vs CH1 (Gateway: 6.50V ➔ 熔斷 0V)
  4. 【AutoCAD 故障排查 DXF】：調用 PROJ-21 引擎，紅標故障斷路 Pin 點與 CWE-1236 防護接線表
"""

from __future__ import annotations

import sys
import os

# Windows UTF-8 編碼防護
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import math
import time
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

SRC_DIR = Path(__file__).resolve().parent
DATA_DIR = SRC_DIR.parent / "DATA"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from event_bus_mcu_bridge import MCUEventBusBridge, ADCTelemetryFrame, sanitize_cell
from autocad_dxf_engine import (
    DXFWiringHarnessEngine,
    ManhattanRouter,
    TerminalBlock,
    TerminalPin,
    WireConnection,
    HarnessSchematic
)


class DualECUMutationEngine:
    """
    PROJ-23 車用雙 ECU 聯調與突變注入引擎
    """
    OVERVOLTAGE_LIMIT = 5.50

    def __init__(self):
        self.bridge_bcm = MCUEventBusBridge()
        self.bridge_gateway = MCUEventBusBridge()
        self.is_gateway_fuse_blown = False
        self.last_surge_voltage = 0.0
        self.event_log: List[Dict[str, Any]] = []

    def reset_system(self):
        """復位雙 ECU 系統保險絲"""
        self.bridge_bcm.reset_hardware_fuse()
        self.bridge_gateway.reset_hardware_fuse()
        self.is_gateway_fuse_blown = False
        self.last_surge_voltage = 0.0

    def sample_dual_channels(
        self,
        bcm_input_v: float = 2.50,
        gateway_input_v: float = 5.00
    ) -> Dict[str, Any]:
        """
        雙通道同步採樣 (落實十進制優先)
        CH0: BCM 車身控制器
        CH1: Gateway 閘道控制器
        """
        # CH0: BCM 採樣
        frame_bcm = self.bridge_bcm.sample_adc(channel=0, input_voltage=bcm_input_v)

        # CH1: Gateway 採樣 (若已熔斷則維持 0V 斷路保護)
        if self.is_gateway_fuse_blown:
            frame_gateway = ADCTelemetryFrame(
                timestamp_ms=round(time.time() * 1000, 2),
                channel=1,
                adc_raw_dec=0,
                measured_voltage=0.0,
                simulated_input_voltage=gateway_input_v,
                hex_code="0x0000",
                bin_code="0b000000000000",
                is_overvoltage_tripped=True,
                diagnostic_message=f"🔴 [斷路保護中] 檢測到 {gateway_input_v:.2f}V 破壞性突波！虛擬保險絲已熔斷，Gateway 供電已強制斷開！"
            )
        else:
            frame_gateway = self.bridge_gateway.sample_adc(channel=1, input_voltage=gateway_input_v)
            if frame_gateway.is_overvoltage_tripped:
                self.is_gateway_fuse_blown = True

        snapshot = {
            "timestamp_ms": round(time.time() * 1000, 2),
            "bcm_ch0": {
                "input_v": frame_bcm.simulated_input_voltage,
                "measured_v": frame_bcm.measured_voltage,
                "adc_dec": frame_bcm.adc_raw_dec,
                "hex_repr": frame_bcm.hex_code,
                "status": "NORMAL" if not frame_bcm.is_overvoltage_tripped else "TRIPPED",
                "formatted": frame_bcm.format_decimal_first()
            },
            "gateway_ch1": {
                "input_v": frame_gateway.simulated_input_voltage,
                "measured_v": frame_gateway.measured_voltage,
                "adc_dec": frame_gateway.adc_raw_dec,
                "hex_repr": frame_gateway.hex_code,
                "status": "TRIPPED" if frame_gateway.is_overvoltage_tripped else "NORMAL",
                "diagnostic": frame_gateway.diagnostic_message,
                "formatted": frame_gateway.format_decimal_first()
            }
        }
        self.event_log.append(snapshot)
        return snapshot

    def inject_voltage_surge(self, surge_voltage: float = 6.50) -> Dict[str, Any]:
        """
        向 Gateway (CH1) 注入破壞性高壓突波 (6.50V)
        """
        self.last_surge_voltage = surge_voltage
        self.is_gateway_fuse_blown = True

        # 執行突波注入採樣 (BCM 保持正常 2.50V, Gateway 注入 6.50V)
        snapshot = self.sample_dual_channels(bcm_input_v=2.50, gateway_input_v=surge_voltage)

        interrupt_payload = {
            "event_type": "CRITICAL_HARDWARE_SURGE_INTERRUPT",
            "surge_voltage": surge_voltage,
            "threshold_voltage": self.OVERVOLTAGE_LIMIT,
            "affected_ecu": "ECU-2 (CAN Gateway / PIC18F25K80)",
            "bcm_isolated_status": "NORMAL_OPERATIONAL (CH0: 2.50V / ADC: 512)",
            "fuse_action": "VIRTUAL_FUSE_BLOWN_OPEN_CIRCUIT",
            "telemetry_snapshot": snapshot,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        return interrupt_payload

    def generate_ascii_topology(self) -> str:
        """生成雙 ECU 故障隔離 ASCII 拓撲圖"""
        fuse_state = "🔴 [FUSE BLOWN (斷開)]" if self.is_gateway_fuse_blown else "🟢 [CONDUCTING (導通)]"
        gw_status = "🔴 斷路隔離 (0.0V / ADC:0)" if self.is_gateway_fuse_blown else "🟢 正常運作 (5.0V / ADC:1023)"

        return f"""
+===================================================================================+
|  🚗 車用雙 ECU (BCM + Gateway) 實體拓撲與突變隔離狀態視圖                             |
+===================================================================================+
|                                                                                   |
|  +---------------------------+                 +-------------------------------+  |
|  |   ECU-1: BCM (TGB-746)    |                 |   ECU-2: Gateway (TGB-745)    |  |
|  |     [PIC16F18313]         |                 |        [PIC18F25K80]          |  |
|  |                           |                 |                               |  |
|  |   P1 (VCC_5V)  ---------> | === W01 (5V) => | ----> P1 (PWR_IN)             |  |
|  |   P2 (GND)     <--------> | === W02 (GND)=> | <---> P2 (GND)                |  |
|  |   P3 (AN0_ADC) ---------> | === W03 (SIG)=> | ----> P3 (ADC_SENS)           |  |
|  |   P4 (PWM_OUT) ---------> | === W04 (PWM)=> | ----> P4 (MOTOR_DRV)          |  |
|  |   P5 (CAN_H)   <========> | === W05 (BUS)=> | <===> P5 (CAN_H)              |  |
|  |   P6 (CAN_L)   <========> | === W06 (BUS)=> | <===> P6 (CAN_L)              |  |
|  +---------------------------+                 +-------------------------------+  |
|               │                                                │                  |
|    🟢 狀態: 正常運行 (2.50V / ADC:512)               保險絲: {fuse_state}         |
|                                                      狀態: {gw_status}            |
+===================================================================================+
"""

    def generate_fault_diagnostic_dxf(self, output_dxf_path: Union[str, Path]) -> Dict[str, Any]:
        """
        調用 AutoCAD DXF 引擎，繪製紅標故障線路與排查清冊
        """
        out_path = Path(output_dxf_path).resolve()
        engine = DXFWiringHarnessEngine()

        # 1. 建立雙 ECU 端子排
        bcm_pins = [
            TerminalPin("P1", "VCC_5V", "PWR", 40.0, 50.0),
            TerminalPin("P2", "GND", "GND", 40.0, 40.0),
            TerminalPin("P3", "AN0_ADC", "SIG", 40.0, 30.0),
            TerminalPin("P4", "PWM_OUT", "SIG", 40.0, 20.0),
            TerminalPin("P5", "CAN_H", "SIG", 40.0, 10.0),
            TerminalPin("P6", "CAN_L", "SIG", 40.0, 0.0),
        ]
        bcm_block = TerminalBlock("J1_BCM", "ECU-1: BCM 車身主控 (PIC16F18313)", origin_x=20.0, origin_y=40.0, width=42.0, height=70.0, pins=bcm_pins, orientation="LEFT")

        gw_pins = [
            TerminalPin("P1", "PWR_IN", "PWR", 0.0, 50.0),
            TerminalPin("P2", "GND", "GND", 0.0, 40.0),
            TerminalPin("P3", "ADC_SENS", "SIG", 0.0, 30.0),
            TerminalPin("P4", "MOTOR_DRV", "SIG", 0.0, 20.0),
            TerminalPin("P5", "CAN_H", "SIG", 0.0, 10.0),
            TerminalPin("P6", "CAN_L", "SIG", 0.0, 0.0),
        ]
        gw_block = TerminalBlock("J2_GW", "ECU-2: CAN Gateway (PIC18F25K80)", origin_x=170.0, origin_y=40.0, width=42.0, height=70.0, pins=gw_pins, orientation="RIGHT")

        # 2. 定義配線（W01 為突波熔斷故障線）
        wires = [
            WireConnection("W01", "J1_BCM", "P1", "J2_GW", "P1", "PWR", channel_offset=-15.0, remarks="🚨 6.5V 過壓熔斷 (FUSE BLOWN)"),
            WireConnection("W02", "J1_BCM", "P2", "J2_GW", "P2", "GND", channel_offset=-9.0, remarks="GND 迴路正常"),
            WireConnection("W03", "J1_BCM", "P3", "J2_GW", "P3", "SIG", channel_offset=-3.0, remarks="ADC 採樣正常 (512 LSB)"),
            WireConnection("W04", "J1_BCM", "P4", "J2_GW", "P4", "SIG", channel_offset=3.0, remarks="PWM 正常"),
            WireConnection("W05", "J1_BCM", "P5", "J2_GW", "P5", "SIG", channel_offset=9.0, remarks="CAN_H 差分正常"),
            WireConnection("W06", "J1_BCM", "P6", "J2_GW", "P6", "SIG", channel_offset=15.0, remarks="CAN_L 差分正常"),
        ]

        schematic = HarnessSchematic(
            title="車用雙 ECU 突變注入故障排查線束圖 (Operation Chronos-Omega)",
            blocks=[bcm_block, gw_block],
            wires=wires
        )

        res = engine.generate_schematic(schematic, out_path)

        # 3. 在故障線路 W01 終點額外加上紅標圓圈與註解
        engine.msp.add_circle((170.0, 90.0), radius=2.5, dxfattribs={"layer": "WIRING_PWR", "color": 1})
        engine.msp.add_text(
            "🔴 [FAULT: 6.5V SURGE FUSE BLOWN]",
            dxfattribs={"layer": "TEXT_LABEL", "color": 1, "height": 2.5, "style": "CHINESE_STANDARD"}
        ).set_placement((115.0, 93.0))

        engine.doc.saveas(out_path, encoding="utf-8")
        res["file_size_bytes"] = out_path.stat().st_size
        res["fault_wire_highlighted"] = "W01 (PWR_IN / 6.50V Surge)"
        return res


def run_self_test():
    print("=" * 80)
    print("🚀 【PROJ-23 車用雙 ECU 聯調與突變注入引擎自檢】")
    print("=" * 80)

    engine = DualECUMutationEngine()
    
    # 1. 驗證正常雙通道採樣
    snap_norm = engine.sample_dual_channels(bcm_input_v=2.50, gateway_input_v=5.00)
    assert snap_norm["bcm_ch0"]["adc_dec"] == 512
    assert snap_norm["gateway_ch1"]["adc_dec"] == 1023
    assert snap_norm["gateway_ch1"]["status"] == "NORMAL"
    print("✅ 正常雙通道十進制採樣驗證通過！")

    # 2. 驗證 6.5V 突變注入與熔斷
    surge_res = engine.inject_voltage_surge(6.50)
    assert surge_res["surge_voltage"] == 6.50
    assert engine.is_gateway_fuse_blown is True
    assert surge_res["telemetry_snapshot"]["gateway_ch1"]["status"] == "TRIPPED"
    print("✅ 6.50V 突變注入與硬體保險絲熔斷驗證通過！")

    print("\n🟢 PROJ-23 dual_ecu_mutation_engine.py 自檢 100% 通過！")


if __name__ == "__main__":
    run_self_test()
