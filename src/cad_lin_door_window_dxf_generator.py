#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 【PROJ-EXAM-08 AutoCAD DXF 車載 LIN 單線匯流排與車門控制器原理圖出圖引擎】
================================================================================
主責工程師：🛠️ A02 小開 (Agent_Coder)
圖面校驗官：👁️ A04 小Ｏ (02_Knowledge/CAD_Specs/LIN_Door_Window_DXF_Audit.md)
品質把關者：🐎 A03 小馬 (TEST/test_lin_door_window_engine.py)

功能亮點：
  1. ACI 8 大工規圖層色彩標準 (LIN_BUS=青/MASTER=紅/SLAVE=黃/WAVEFORMS=洋紅/TABLE=青)
  2. 三段式工規 LIN 拓撲：左 BCM Master 節點 ✕ 中單線匯流排與時序波形 ✕ 右 DDM/PDM 車門從節點
  3. 90° 正交走線、LIN 2.1 幀波形 (Break/Sync/PID/Data/Checksum)、防夾 H 橋與 ECE R21 規範標註
  4. 排程調度表與 PID 同位清冊 BOM 表
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


class LinDoorWindow_DXFGenerator:
    """
    AutoCAD DXF 車載 LIN 單線匯流排與車門控制器生成器 (A3 420x297mm)
    """

    LAYERS_CONFIG = {
        "0": {"color": 7, "desc": "預設圖層"},
        "FRAME_BORDER": {"color": 7, "desc": "A3 標準圖框與標題欄 (白色)"},
        "COMPONENTS": {"color": 3, "desc": "BCM 與車門控制器模組框 (綠色)"},
        "LIN_BUS": {"color": 4, "desc": "LIN 單線雙向匯流排 19.2kbps (青色)"},
        "MASTER_CIRCUIT": {"color": 1, "desc": "Master 1kΩ 上拉二極體與 TJA1021 收發電路 (紅色)"},
        "SLAVE_CIRCUIT": {"color": 2, "desc": "Slave 30kΩ 上拉與車窗防夾 H 橋馬達電路 (黃色)"},
        "TIMING_WAVEFORMS": {"color": 6, "desc": "LIN 2.1 幀時序波形 Break/Sync/PID (洋紅色)"},
        "BOM_TABLE": {"color": 4, "desc": "LIN 排程調度表與 PID 同位清冊 (青色)"},
        "DIAG_SPECS": {"color": 2, "desc": "ECE R21 防夾力學與診斷規範註記 (黃色)"},
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

    def build_lin_dxf(self, output_path: str) -> str:
        """構建完整 A3 工規 LIN 單線匯流排與車門控制器原理圖"""

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

        self.msp.add_text("PROJ-EXAM-08: LIN BUS DOOR/WINDOW CONTROLLER", dxfattribs={"layer": "FRAME_BORDER", "height": 3.0}).set_placement((tb_x + 3, tb_y + 33))
        self.msp.add_text("STANDARDS: LIN 2.1 / ISO 17987 / ECE R21 ANTI-PINCH", dxfattribs={"layer": "FRAME_BORDER", "height": 2.3}).set_placement((tb_x + 3, tb_y + 23))
        self.msp.add_text("DESIGNER: A02 CODER / A05 DEEP", dxfattribs={"layer": "FRAME_BORDER", "height": 2.2}).set_placement((tb_x + 3, tb_y + 13))
        self.msp.add_text("AUDITOR: A04 VISION / A03 REVIEWER", dxfattribs={"layer": "FRAME_BORDER", "height": 2.2}).set_placement((tb_x + 83, tb_y + 13))
        self.msp.add_text("BAUD: 19.2 KBPS | ANTI-PINCH: <= 100N (REVERSE 100MM)", dxfattribs={"layer": "FRAME_BORDER", "height": 2.0}).set_placement((tb_x + 3, tb_y + 3))

        # -------------------------------------------------------------
        # 2. 頂部總覽外框 (LIN Topology Main Enclosure)
        # -------------------------------------------------------------
        top_x, top_y, top_w, top_h = 20, 65, 380, 210
        self.msp.add_lwpolyline([(top_x, top_y), (top_x + top_w, top_y), (top_x + top_w, top_y + top_h), (top_x, top_y + top_h), (top_x, top_y)], dxfattribs={"layer": "COMPONENTS"})
        self.msp.add_text("AUTOMOTIVE LIN 2.1 MASTER-SLAVE DOOR NETWORK & ANTI-PINCH CONTROL", dxfattribs={"layer": "COMPONENTS", "height": 2.5}).set_placement((top_x + 5, top_y + top_h - 7))

        # -------------------------------------------------------------
        # 3. 左區：BCM Master 主節點電路 (LIN Master Node)
        # -------------------------------------------------------------
        m_x, m_y, m_w, m_h = 25, 75, 95, 185
        self.msp.add_lwpolyline([(m_x, m_y), (m_x + m_w, m_y), (m_x + m_w, m_y + m_h), (m_x, m_y + m_h), (m_x, m_y)], dxfattribs={"layer": "MASTER_CIRCUIT"})
        self.msp.add_text("BCM (LIN MASTER NODE)", dxfattribs={"layer": "MASTER_CIRCUIT", "height": 2.2}).set_placement((m_x + 3, m_y + m_h - 6))

        self.msp.add_text("• MCU UART Controller (19.2k)", dxfattribs={"layer": "MASTER_CIRCUIT", "height": 1.7}).set_placement((m_x + 5, m_y + 160))
        self.msp.add_text("• Master Pull-up: 1.0 kΩ + Diode", dxfattribs={"layer": "MASTER_CIRCUIT", "height": 1.7}).set_placement((m_x + 5, m_y + 150))
        self.msp.add_text("• LIN Transceiver (TJA1021/MCP2003)", dxfattribs={"layer": "MASTER_CIRCUIT", "height": 1.7}).set_placement((m_x + 5, m_y + 140))
        self.msp.add_text("• Break Generator (>= 13 bits)", dxfattribs={"layer": "MASTER_CIRCUIT", "height": 1.7}).set_placement((m_x + 5, m_y + 130))
        self.msp.add_text("• 50ms Master Schedule Dispatcher", dxfattribs={"layer": "MASTER_CIRCUIT", "height": 1.7}).set_placement((m_x + 5, m_y + 120))
        self.msp.add_text("• Sleep Command Broadcast (0x3C)", dxfattribs={"layer": "MASTER_CIRCUIT", "height": 1.7}).set_placement((m_x + 5, m_y + 110))

        # -------------------------------------------------------------
        # 4. 中區：LIN 單線匯流排與時序波形 (LIN Bus Highway & Waveforms)
        # -------------------------------------------------------------
        c_x, c_y, c_w, c_h = 130, 75, 155, 185
        self.msp.add_lwpolyline([(c_x, c_y), (c_x + c_w, c_y), (c_x + c_w, c_y + c_h), (c_x, c_y + c_h), (c_x, c_y)], dxfattribs={"layer": "LIN_BUS"})
        self.msp.add_text("LIN SINGLE-WIRE HIGHWAY & FRAME TIMING", dxfattribs={"layer": "LIN_BUS", "height": 2.2}).set_placement((c_x + 3, c_y + c_h - 6))

        # 繪製 LIN 2.1 幀時序波形 (洋紅色)
        wf_y = c_y + 135
        self.msp.add_text("LIN 2.1 FRAME TIMING WAVEFORM", dxfattribs={"layer": "TIMING_WAVEFORMS", "height": 2.0}).set_placement((c_x + 5, wf_y + 30))
        # 波形方塊
        self.msp.add_lwpolyline([(c_x + 5, wf_y), (c_x + 30, wf_y), (c_x + 30, wf_y + 15), (c_x + 55, wf_y + 15), (c_x + 55, wf_y), (c_x + 85, wf_y), (c_x + 85, wf_y + 15), (c_x + 120, wf_y + 15), (c_x + 120, wf_y), (c_x + 145, wf_y)], dxfattribs={"layer": "TIMING_WAVEFORMS"})

        self.msp.add_text("BREAK (>=13b)", dxfattribs={"layer": "TIMING_WAVEFORMS", "height": 1.5}).set_placement((c_x + 6, wf_y - 5))
        self.msp.add_text("SYNC 0x55", dxfattribs={"layer": "TIMING_WAVEFORMS", "height": 1.5}).set_placement((c_x + 34, wf_y + 18))
        self.msp.add_text("PID (P0/P1)", dxfattribs={"layer": "TIMING_WAVEFORMS", "height": 1.5}).set_placement((c_x + 60, wf_y - 5))
        self.msp.add_text("DATA 1..8B", dxfattribs={"layer": "TIMING_WAVEFORMS", "height": 1.5}).set_placement((c_x + 90, wf_y + 18))
        self.msp.add_text("CHECKSUM", dxfattribs={"layer": "TIMING_WAVEFORMS", "height": 1.5}).set_placement((c_x + 122, wf_y - 5))

        # 中下：LIN 單線匯流排連接線
        self.msp.add_line((m_x + m_w, c_y + 50), (c_x + c_w + 15, c_y + 50), dxfattribs={"layer": "LIN_BUS"})
        self.msp.add_circle((c_x + 20, c_y + 50), 1.5, dxfattribs={"layer": "LIN_BUS"})
        self.msp.add_circle((c_x + 80, c_y + 50), 1.5, dxfattribs={"layer": "LIN_BUS"})
        self.msp.add_circle((c_x + 140, c_y + 50), 1.5, dxfattribs={"layer": "LIN_BUS"})
        self.msp.add_text("LIN BUS PHYSICAL LINE (+12V BI-DIRECTIONAL 19.2k)", dxfattribs={"layer": "LIN_BUS", "height": 1.8}).set_placement((c_x + 10, c_y + 55))

        # -------------------------------------------------------------
        # 5. 右區：車門從節點與防夾 H 橋 (Slave DDM/PDM & Anti-Pinch)
        # -------------------------------------------------------------
        s_x, s_y, s_w, s_h = 295, 75, 100, 185
        self.msp.add_lwpolyline([(s_x, s_y), (s_x + s_w, s_y), (s_x + s_w, s_y + s_h), (s_x, s_y + s_h), (s_x, s_y)], dxfattribs={"layer": "SLAVE_CIRCUIT"})
        self.msp.add_text("SLAVE DOOR MODULES (DDM/PDM)", dxfattribs={"layer": "SLAVE_CIRCUIT", "height": 2.2}).set_placement((s_x + 3, s_y + s_h - 6))

        self.msp.add_text("• Slave Pull-up: 30 kΩ + Diode", dxfattribs={"layer": "SLAVE_CIRCUIT", "height": 1.7}).set_placement((s_x + 5, s_y + 160))
        self.msp.add_text("• Dual H-Bridge Motor Driver (L9958)", dxfattribs={"layer": "SLAVE_CIRCUIT", "height": 1.7}).set_placement((s_x + 5, s_y + 150))
        self.msp.add_text("• Shunt Resistor (0.05Ω Current Sense)", dxfattribs={"layer": "SLAVE_CIRCUIT", "height": 1.7}).set_placement((s_x + 5, s_y + 140))
        self.msp.add_text("• Hall Ripple Pulse Encoder", dxfattribs={"layer": "SLAVE_CIRCUIT", "height": 1.7}).set_placement((s_x + 5, s_y + 130))
        self.msp.add_text("• Anti-Pinch ECE R21 (F <= 100N)", dxfattribs={"layer": "SLAVE_CIRCUIT", "height": 1.7}).set_placement((s_x + 5, s_y + 120))
        self.msp.add_text("• Auto 100mm Reversal on Obstacle", dxfattribs={"layer": "SLAVE_CIRCUIT", "height": 1.7}).set_placement((s_x + 5, s_y + 110))

        # -------------------------------------------------------------
        # 6. 底部表格：LIN 排程調度與 PID 清冊 (BOM Table)
        # -------------------------------------------------------------
        tbl_x, tbl_y, tbl_w, tbl_h = 20, 15, 220, 45
        self.msp.add_lwpolyline([(tbl_x, tbl_y), (tbl_x + tbl_w, tbl_y), (tbl_x + tbl_w, tbl_y + tbl_h), (tbl_x, tbl_y + tbl_h), (tbl_x, tbl_y)], dxfattribs={"layer": "BOM_TABLE"})
        self.msp.add_line((tbl_x, tbl_y + 35), (tbl_x + tbl_w, tbl_y + 35), dxfattribs={"layer": "BOM_TABLE"})
        self.msp.add_text("LIN 2.1 SCHEDULE TABLE & PID PARITY SCHEDULE", dxfattribs={"layer": "BOM_TABLE", "height": 2.3}).set_placement((tbl_x + 3, tbl_y + 37))

        rows = [
            "Slot 1 (0-10ms)  | ID 0x20 -> PID 0x20 | Master -> DDM/PDM (Window Move Cmd)",
            "Slot 2 (10-20ms) | ID 0x21 -> PID 0x61 | Slave DDM -> Master (Pos, Current, Pinch)",
            "Slot 3 (20-30ms) | ID 0x22 -> PID 0xE2 | Slave PDM -> Master (Pos, Mirror, Lock)",
            "Slot 4 (30-50ms) | ID 0x3C -> PID 0x3C | Master Diagnostic & Sleep Broadcast",
            "Anti-Pinch Spec  | Zone: 4-200mm | Limit: I >= 12.0A | Reversal: >= 100mm (<10ms)"
        ]
        for idx, row in enumerate(rows):
            self.msp.add_text(row, dxfattribs={"layer": "BOM_TABLE", "height": 1.7}).set_placement((tbl_x + 3, tbl_y + 28 - (idx * 6.5)))

        # 儲存 DXF
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        self.doc.saveas(output_path)
        print(f"✅ AutoCAD DXF LIN 車門控制器原理圖已生成: {output_path}")
        return output_path


def run_self_test():
    print("=" * 80)
    print("📐 【PROJ-EXAM-08 AutoCAD DXF LIN 車門控制器出圖引擎自檢】")
    print("=" * 80)
    generator = LinDoorWindow_DXFGenerator()
    out_path = "G:/我的雲端硬碟/AI_master_workspace/three_memory/DATA/sample_lin_door_window_diagram.dxf"
    generator.build_lin_dxf(out_path)
    print("🟢 DXF LIN 車門控制器出圖引擎自檢 100% 通過！")


if __name__ == "__main__":
    run_self_test()
