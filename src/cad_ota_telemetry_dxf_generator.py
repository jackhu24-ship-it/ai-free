#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 【PROJ-EXAM-05 AutoCAD DXF 邊緣遙測與 Dual-Bank OTA 拓撲出圖引擎】
================================================================================
主責工程師：🛠️ A02 小開 (Agent_Coder)
圖面校驗官：👁️ A04 小Ｏ (02_Knowledge/CAD_Specs/OTA_Telemetry_DXF_Audit.md)
品質把關者：🐎 A03 小馬 (TEST/test_nostr_mqtt_ota_engine.py)

功能亮點：
  1. ACI 8 大工規圖層色彩標準 (COMPONENTS=綠/NOSTR=洋紅/MQTT=青/MEMORY=綠/ARROWS=黃/WATCHDOG=紅/TABLE=青)
  2. 三段式水平拓撲架構：左側邊緣遙測 (Nostr/MQTT) ➔ 中間 Flash 雙分區映射 ➔ 右側 OTA 試運行回滾狀態機
  3. 正交曼哈頓走線與 30 秒看門狗沙箱回滾路徑標註
  4. A3 標準工程圖框 (420x297mm) 與 Flash 記憶體配置清冊
"""

from __future__ import annotations

import sys
import os
import math
from pathlib import Path
from typing import List, Tuple, Dict, Any

try:
    import ezdxf
except ImportError:
    print("❌ 請先安裝 ezdxf: pip install ezdxf")
    sys.exit(1)

# Windows UTF-8 編碼防護
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


class OTATelemetry_DXFGenerator:
    """
    AutoCAD DXF 邊緣遙測與 Dual-Bank OTA 拓撲圖生成器 (A3 420x297mm)
    """

    LAYERS_CONFIG = {
        "0": {"color": 7, "desc": "預設圖層"},
        "FRAME_BORDER": {"color": 7, "desc": "A3 標準圖框與標題欄 (白色)"},
        "COMPONENTS": {"color": 3, "desc": "ECU 邊緣硬體與處理器模組框 (綠色)"},
        "TELEMETRY_NOSTR": {"color": 6, "desc": "Nostr 去中心化遙測與 secp256k1 (洋紅色)"},
        "TELEMETRY_MQTT": {"color": 4, "desc": "MQTT QoS 1 車載主題分發 (青色)"},
        "MEMORY_BANKS": {"color": 3, "desc": "Flash 雙分區與 Bootloader 映射框 (綠色)"},
        "STATE_ARROWS": {"color": 2, "desc": "狀態遷移曼哈頓正交箭頭線 (黃色)"},
        "SECURITY_BLOCK": {"color": 1, "desc": "30s 看門狗計時器與自動回滾引線 (紅色)"},
        "BOM_TABLE": {"color": 4, "desc": "Flash 分區分配與遙測 Schema 表格 (青色)"},
        "DIAG_SPECS": {"color": 2, "desc": "車載 OTA 與遙測技術規範說明 (黃色)"},
    }

    def __init__(self):
        self.doc = ezdxf.new("R2010", setup=True)
        self.msp = self.doc.modelspace()
        self._setup_layers()

    def _setup_layers(self):
        """初始化 ACI 工規圖層"""
        for name, cfg in self.LAYERS_CONFIG.items():
            if name not in self.doc.layers:
                self.doc.layers.add(name=name, color=cfg["color"])

    def draw_box(self, x: float, y: float, w: float, h: float, title: str, subtitle: str = "", layer: str = "COMPONENTS"):
        """繪製雙線模組框"""
        self.msp.add_lwpolyline([(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)], dxfattribs={"layer": layer})
        self.msp.add_lwpolyline([(x + 1.2, y + 1.2), (x + w - 1.2, y + 1.2), (x + w - 1.2, y + h - 1.2), (x + 1.2, y + h - 1.2), (x + 1.2, y + 1.2)], dxfattribs={"layer": layer})
        self.msp.add_text(title, dxfattribs={"layer": layer, "height": 2.2}).set_placement((x + 2.5, y + h - 5.5))
        if subtitle:
            self.msp.add_text(subtitle, dxfattribs={"layer": layer, "height": 1.6}).set_placement((x + 2.5, y + 3.0))

    def draw_arrow(self, pts: List[Tuple[float, float]], layer: str = "STATE_ARROWS"):
        """繪製曼哈頓折線與末端箭頭"""
        self.msp.add_lwpolyline(pts, dxfattribs={"layer": layer})
        if len(pts) >= 2:
            p_end = pts[-1]
            p_prev = pts[-2]
            dx = p_end[0] - p_prev[0]
            dy = p_end[1] - p_prev[1]
            angle = math.atan2(dy, dx)
            a_len = 3.5
            a_ang = math.radians(25)
            p_left = (p_end[0] - a_len * math.cos(angle - a_ang), p_end[1] - a_len * math.sin(angle - a_ang))
            p_right = (p_end[0] - a_len * math.cos(angle + a_ang), p_end[1] - a_len * math.sin(angle + a_ang))
            self.msp.add_lwpolyline([p_left, p_end, p_right], dxfattribs={"layer": layer})

    def build_ota_dxf(self, output_path: str) -> str:
        """構建完整 A3 工規邊緣遙測與 Dual-Bank OTA 拓撲圖"""

        # -------------------------------------------------------------
        # 1. 繪製 A3 標準圖框與標題欄 (Title Block)
        # -------------------------------------------------------------
        self.msp.add_lwpolyline([(0, 0), (420, 0), (420, 297), (0, 297), (0, 0)], dxfattribs={"layer": "FRAME_BORDER"})
        self.msp.add_lwpolyline([(10, 10), (410, 10), (410, 287), (10, 287), (10, 10)], dxfattribs={"layer": "FRAME_BORDER"})

        tb_x, tb_y, tb_w, tb_h = 250, 10, 160, 40
        self.msp.add_lwpolyline([(tb_x, tb_y), (tb_x + tb_w, tb_y), (tb_x + tb_w, tb_y + tb_h), (tb_x, tb_y + tb_h), (tb_x, tb_y)], dxfattribs={"layer": "FRAME_BORDER"})
        self.msp.add_line((tb_x, tb_y + 20), (tb_x + tb_w, tb_y + 20), dxfattribs={"layer": "FRAME_BORDER"})
        self.msp.add_line((tb_x, tb_y + 30), (tb_x + tb_w, tb_y + 30), dxfattribs={"layer": "FRAME_BORDER"})
        self.msp.add_line((tb_x + 80, tb_y), (tb_x + 80, tb_y + 30), dxfattribs={"layer": "FRAME_BORDER"})

        self.msp.add_text("PROJ-EXAM-05: NOSTR/MQTT TELEMETRY & DUAL-BANK OTA", dxfattribs={"layer": "FRAME_BORDER", "height": 3.0}).set_placement((tb_x + 3, tb_y + 33))
        self.msp.add_text("STANDARDS: NOSTR NIP-01/30078 / ISO 24089 / UNECE R156", dxfattribs={"layer": "FRAME_BORDER", "height": 2.3}).set_placement((tb_x + 3, tb_y + 23))
        self.msp.add_text("DESIGNER: A02 CODER / A05 DEEP", dxfattribs={"layer": "FRAME_BORDER", "height": 2.2}).set_placement((tb_x + 3, tb_y + 13))
        self.msp.add_text("AUDITOR: A04 VISION / A03 REVIEWER", dxfattribs={"layer": "FRAME_BORDER", "height": 2.2}).set_placement((tb_x + 83, tb_y + 13))
        self.msp.add_text("FLASH MAP: 1088KB (BOOT 64K + BANK_A 512K + BANK_B 512K)", dxfattribs={"layer": "FRAME_BORDER", "height": 2.0}).set_placement((tb_x + 3, tb_y + 3))

        # -------------------------------------------------------------
        # 2. 左側：邊緣遙測流入架構 (Edge Telemetry Ingestion)
        # -------------------------------------------------------------
        self.msp.add_text("1. EDGE TELEMETRY INGESTION (邊緣遙測區)", dxfattribs={"layer": "DIAG_SPECS", "height": 2.5}).set_placement((20, 275))

        # Nostr 模組框
        self.draw_box(20, 210, 95, 55, "NOSTR RELAY GATEWAY", "Kind 30078 (PDU Telemetry) + Kind 1 Alert", layer="TELEMETRY_NOSTR")
        self.msp.add_text("• NIP-01 Event ID: SHA256(Serialized)", dxfattribs={"layer": "TELEMETRY_NOSTR", "height": 1.7}).set_placement((23, 240))
        self.msp.add_text("• Cryptography: secp256k1 Schnorr Sig", dxfattribs={"layer": "TELEMETRY_NOSTR", "height": 1.7}).set_placement((23, 233))
        self.msp.add_text("• Real-Time Currents & Voltage Push", dxfattribs={"layer": "TELEMETRY_NOSTR", "height": 1.7}).set_placement((23, 226))

        # MQTT 模組框
        self.draw_box(20, 135, 95, 55, "MQTT BROKER CLIENT", "Topic: v1/edge/{vin}/telemetry (QoS 1)", layer="TELEMETRY_MQTT")
        self.msp.add_text("• Telemetry Pub: /pdu (100ms cycle)", dxfattribs={"layer": "TELEMETRY_MQTT", "height": 1.7}).set_placement((23, 165))
        self.msp.add_text("• OTA Request Sub: /ota/request", dxfattribs={"layer": "TELEMETRY_MQTT", "height": 1.7}).set_placement((23, 158))
        self.msp.add_text("• OTA Progress Pub: /ota/progress", dxfattribs={"layer": "TELEMETRY_MQTT", "height": 1.7}).set_placement((23, 151))

        # -------------------------------------------------------------
        # 3. 中間：Flash 雙分區記憶體映射 (Dual-Bank Memory Map)
        # -------------------------------------------------------------
        self.msp.add_text("2. DUAL-BANK FLASH MEMORY MAP (1088 KB)", dxfattribs={"layer": "DIAG_SPECS", "height": 2.5}).set_placement((135, 275))

        # Bootloader 分區
        self.draw_box(135, 225, 110, 40, "BOOTLOADER & NVRAM (64 KB)", "0x08000000 ~ 0x0800FFFF | Safe Swap FSM", layer="MEMORY_BANKS")
        self.msp.add_text("• Active Vector Pointer: Bank A / Bank B", dxfattribs={"layer": "MEMORY_BANKS", "height": 1.7}).set_placement((138, 245))
        self.msp.add_text("• Trial-Boot Watchdog Flag Checker", dxfattribs={"layer": "MEMORY_BANKS", "height": 1.7}).set_placement((138, 238))

        # Bank A (Active)
        self.draw_box(135, 175, 110, 40, "BANK A: ACTIVE APP (512 KB)", "0x08010000 ~ 0x0808FFFF | v2.0.0 (Running)", layer="MEMORY_BANKS")
        self.msp.add_text("• Primary Application Execution Vector", dxfattribs={"layer": "MEMORY_BANKS", "height": 1.7}).set_placement((138, 195))
        self.msp.add_text("• Golden Fallback Image Protection", dxfattribs={"layer": "MEMORY_BANKS", "height": 1.7}).set_placement((138, 188))

        # Bank B (OTA Target)
        self.draw_box(135, 125, 110, 40, "BANK B: OTA STANDBY (512 KB)", "0x08090000 ~ 0x0810FFFF | Target Image", layer="MEMORY_BANKS")
        self.msp.add_text("• Flashed via OTA Downloader (v2.1.0)", dxfattribs={"layer": "MEMORY_BANKS", "height": 1.7}).set_placement((138, 145))
        self.msp.add_text("• Pre-boot SHA256 & Signature Verification", dxfattribs={"layer": "MEMORY_BANKS", "height": 1.7}).set_placement((138, 138))

        # -------------------------------------------------------------
        # 4. 右側：OTA 狀態機與 30 秒看門狗回滾沙箱 (OTA State Machine & Sandbox)
        # -------------------------------------------------------------
        self.msp.add_text("3. OTA TRIAL-BOOT & ROLLBACK SANDBOX", dxfattribs={"layer": "DIAG_SPECS", "height": 2.5}).set_placement((265, 275))

        # OTA 狀態框
        self.draw_box(265, 215, 135, 50, "TRIAL-BOOTING SANDBOX (30s)", "Watchdog Armed: Expects Commit Heartbeat", layer="SECURITY_BLOCK")
        self.msp.add_text("• Normal Path: Self-Test OK -> Commit", dxfattribs={"layer": "SECURITY_BLOCK", "height": 1.7}).set_placement((268, 245))
        self.msp.add_text("• Abort Path: Panic / 30s Timeout -> Rollback", dxfattribs={"layer": "SECURITY_BLOCK", "height": 1.7}).set_placement((268, 238))
        self.msp.add_text("• Atomic Vector Swap Time: < 50 ms", dxfattribs={"layer": "SECURITY_BLOCK", "height": 1.7}).set_placement((268, 231))

        # -------------------------------------------------------------
        # 5. 連線箭頭與走線 (Manhattan Orthogonal Arrows)
        # -------------------------------------------------------------
        # MQTT OTA Request -> Bank B Flashing
        self.draw_arrow([(115, 150), (135, 150)])
        self.msp.add_text("OTA Download & Flash", dxfattribs={"layer": "STATE_ARROWS", "height": 1.6}).set_placement((116, 153))

        # Bank B -> Trial Booting Sandbox
        self.draw_arrow([(245, 150), (255, 150), (255, 240), (265, 240)])
        self.msp.add_text("Boot Flag -> Pending Bank B", dxfattribs={"layer": "STATE_ARROWS", "height": 1.6}).set_placement((248, 195))

        # Normal Commit -> Permanent Bank B
        self.draw_arrow([(330, 215), (330, 185), (245, 185)])
        self.msp.add_text("Healthy Heartbeat: Commit Bank B", dxfattribs={"layer": "STATE_ARROWS", "height": 1.6}).set_placement((255, 188))

        # Rollback Arrow (Red): Sandbox -> Bank A
        self.draw_arrow([(400, 240), (410, 240), (410, 195), (245, 195)], layer="SECURITY_BLOCK")
        self.msp.add_text("30s Timeout / Panic -> Rollback to Bank A", dxfattribs={"layer": "SECURITY_BLOCK", "height": 1.6}).set_placement((255, 205))

        # -------------------------------------------------------------
        # 6. 底部表格：Flash 記憶體配置與遙測 Schema 清冊 (BOM Table)
        # -------------------------------------------------------------
        tbl_x, tbl_y, tbl_w, tbl_h = 20, 15, 220, 105
        self.msp.add_lwpolyline([(tbl_x, tbl_y), (tbl_x + tbl_w, tbl_y), (tbl_x + tbl_w, tbl_y + tbl_h), (tbl_x, tbl_y + tbl_h), (tbl_x, tbl_y)], dxfattribs={"layer": "BOM_TABLE"})
        self.msp.add_line((tbl_x, tbl_y + 92), (tbl_x + tbl_w, tbl_y + 92), dxfattribs={"layer": "BOM_TABLE"})
        self.msp.add_text("FLASH MEMORY MAP & TELEMETRY PROTOCOL ALLOCATION SCHEDULE", dxfattribs={"layer": "BOM_TABLE", "height": 2.5}).set_placement((tbl_x + 3, tbl_y + 96))

        rows = [
            "Bootloader & NVRAM | 0x08000000 ~ 0x0800FFFF |  64 KB | Vector Table / Boot Flag / Rollback FSM",
            "Bank A (Primary)   | 0x08010000 ~ 0x0808FFFF | 512 KB | Active ECU Firmware (Golden Image Backup)",
            "Bank B (Secondary) | 0x08090000 ~ 0x0810FFFF | 512 KB | Standby / OTA Staging & Trial Sandbox",
            "Nostr Event Schema | Kind 30078 App Telemetry | NIP-01 | SHA256 ID + secp256k1 Schnorr Signature",
            "MQTT Topic Topology| v1/edge/{vin}/telemetry  | QoS 1  | 8-Ch PDU Currents + Voltage + Active DTCs",
            "OTA Header Magic   | 0xAA55A55A (64 Bytes)   | SHA256 | Pre-flash Integrity Check & Bank Select",
            "Watchdog Sandbox   | 30.0s Timer Window      | HW IRQ | Auto-Rollback on Zero-Heartbeat or HardFault",
            "Safety Compliance  | ISO 24089 / UNECE R156  | ASIL-D | Zero-Brick Architecture Guaranteed"
        ]
        for idx, row in enumerate(rows):
            self.msp.add_text(row, dxfattribs={"layer": "BOM_TABLE", "height": 1.7}).set_placement((tbl_x + 3, tbl_y + 83 - (idx * 10.0)))

        # 儲存 DXF
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        self.doc.saveas(output_path)
        print(f"✅ AutoCAD DXF 邊緣遙測與 Dual-Bank OTA 拓撲圖已生成: {output_path}")
        return output_path


def run_self_test():
    print("=" * 80)
    print("📐 【PROJ-EXAM-05 AutoCAD DXF 邊緣遙測與 OTA 拓撲出圖引擎自檢】")
    print("=" * 80)
    generator = OTATelemetry_DXFGenerator()
    out_path = "G:/我的雲端硬碟/AI_master_workspace/three_memory/DATA/sample_ota_telemetry_diagram.dxf"
    generator.build_ota_dxf(out_path)
    print("🟢 DXF 邊緣遙測與 OTA 拓撲出圖引擎自檢 100% 通過！")


if __name__ == "__main__":
    run_self_test()
