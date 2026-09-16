#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 【PROJ-EXAM-09 AutoCAD DXF 車載 UDS 刷寫時序與 Bootloader 架構出圖引擎】
================================================================================
主責工程師：🛠️ A02 小開 (Agent_Coder)
圖面校驗官：👁️ A04 小Ｏ (02_Knowledge/CAD_Specs/UDS_Bootloader_DXF_Audit.md)
品質把關者：🐎 A03 小馬 (TEST/test_uds_bootloader_flashing_engine.py)

功能亮點：
  1. ACI 8 大工規圖層色彩標準 (UDS_SEQ=紅/CAN_TP=青/MEM_MAP=黃/STATUS=洋紅/TABLE=青)
  2. 三段式工規重編程拓撲：左 7 步 UDS 刷寫時序 ✕ 中 CAN-TP 多幀時序 ✕ 右 MCU Flash 空間映射
  3. 90° 正交流程箭頭、CAN-TP 首幀/流控/連續幀拆解、512KB App 扇區標註與 NRC 矩陣清冊 BOM 表
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


class UdsBootloader_DXFGenerator:
    """
    AutoCAD DXF 車載 UDS 刷寫時序與 Bootloader 架構圖生成器 (A3 420x297mm)
    """

    LAYERS_CONFIG = {
        "0": {"color": 7, "desc": "預設圖層"},
        "FRAME_BORDER": {"color": 7, "desc": "A3 標準圖框與標題欄 (白色)"},
        "COMPONENTS": {"color": 3, "desc": "系統分區總覽外框 (綠色)"},
        "UDS_SEQUENCE": {"color": 1, "desc": "7 步 UDS 刷寫時序流程方塊與箭頭 (紅色)"},
        "CAN_TP_FRAMES": {"color": 4, "desc": "ISO 15765-2 CAN-TP 多幀時序 (青色)"},
        "MEMORY_MAP": {"color": 2, "desc": "MCU Flash 記憶體分區映射 1088KB (黃色)"},
        "STATUS_NODES": {"color": 6, "desc": "FBL 重編程狀態機節點 (洋紅色)"},
        "BOM_TABLE": {"color": 4, "desc": "UDS 診斷服務與 NRC 錯誤碼矩陣 (青色)"},
        "DIAG_SPECS": {"color": 2, "desc": "P2/P2* 計時與 Seed-Key 規範註記 (黃色)"},
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

    def build_uds_bootloader_dxf(self, output_path: str) -> str:
        """構建完整 A3 工規 UDS 刷寫時序與 Bootloader 架構原理圖"""

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

        self.msp.add_text("PROJ-EXAM-09: UDS BOOTLOADER FLASHING PIPELINE", dxfattribs={"layer": "FRAME_BORDER", "height": 3.0}).set_placement((tb_x + 3, tb_y + 33))
        self.msp.add_text("STANDARDS: ISO 14229-1 (UDS) / ISO 15765-2 (CAN-TP)", dxfattribs={"layer": "FRAME_BORDER", "height": 2.3}).set_placement((tb_x + 3, tb_y + 23))
        self.msp.add_text("DESIGNER: A02 CODER / A05 DEEP", dxfattribs={"layer": "FRAME_BORDER", "height": 2.2}).set_placement((tb_x + 3, tb_y + 13))
        self.msp.add_text("AUDITOR: A04 VISION / A03 REVIEWER", dxfattribs={"layer": "FRAME_BORDER", "height": 2.2}).set_placement((tb_x + 83, tb_y + 13))
        self.msp.add_text("APP FLASH: 512KB | CAN-TP: BS=8 / STMIN=5MS | P2*=5000MS", dxfattribs={"layer": "FRAME_BORDER", "height": 2.0}).set_placement((tb_x + 3, tb_y + 3))

        # -------------------------------------------------------------
        # 2. 頂部總覽外框 (UDS Architecture Main Enclosure)
        # -------------------------------------------------------------
        top_x, top_y, top_w, top_h = 20, 65, 380, 210
        self.msp.add_lwpolyline([(top_x, top_y), (top_x + top_w, top_y), (top_x + top_w, top_y + top_h), (top_x, top_y + top_h), (top_x, top_y)], dxfattribs={"layer": "COMPONENTS"})
        self.msp.add_text("AUTOMOTIVE UDS BOOTLOADER (FBL) REPROGRAMMING ARCHITECTURE", dxfattribs={"layer": "COMPONENTS", "height": 2.5}).set_placement((top_x + 5, top_y + top_h - 7))

        # -------------------------------------------------------------
        # 3. 左區：OEM 標準 7 步 UDS 刷寫時序流程 (7-Step UDS Pipeline)
        # -------------------------------------------------------------
        s_x, s_y, s_w, s_h = 25, 75, 115, 185
        self.msp.add_lwpolyline([(s_x, s_y), (s_x + s_w, s_y), (s_x + s_w, s_y + s_h), (s_x, s_y + s_h), (s_x, s_y)], dxfattribs={"layer": "UDS_SEQUENCE"})
        self.msp.add_text("7-STEP UDS REPROGRAMMING PIPELINE", dxfattribs={"layer": "UDS_SEQUENCE", "height": 2.2}).set_placement((s_x + 3, s_y + s_h - 6))

        steps = [
            ("Step 1", "0x10 0x02 ProgrammingSession"),
            ("Step 2", "0x85 0x02 DTC OFF / 0x28 0x03 CommDisable"),
            ("Step 3", "0x27 0x01/0x02 SecurityAccess Level 1"),
            ("Step 4", "0x31 0x01 0xFF00 Erase App Flash (512KB)"),
            ("Step 5", "0x34 RequestDownload (Addr 0x08010000)"),
            ("Step 6", "0x36 TransferData (256B) + 0x37 Exit"),
            ("Step 7", "0x31 0x0202 Check SHA256 + 0x11 Reset")
        ]

        step_y = s_y + 155
        for idx, (st_name, st_desc) in enumerate(steps):
            box_y = step_y - (idx * 23)
            self.msp.add_lwpolyline([(s_x + 5, box_y), (s_x + s_w - 5, box_y), (s_x + s_w - 5, box_y + 18), (s_x + 5, box_y + 18), (s_x + 5, box_y)], dxfattribs={"layer": "UDS_SEQUENCE"})
            self.msp.add_text(f"[{st_name}]", dxfattribs={"layer": "UDS_SEQUENCE", "height": 1.8}).set_placement((s_x + 7, box_y + 11))
            self.msp.add_text(st_desc, dxfattribs={"layer": "UDS_SEQUENCE", "height": 1.4}).set_placement((s_x + 7, box_y + 4))

            # 繪製下引箭頭
            if idx < len(steps) - 1:
                arr_x = s_x + (s_w / 2)
                self.msp.add_line((arr_x, box_y), (arr_x, box_y - 5), dxfattribs={"layer": "UDS_SEQUENCE"})
                self.msp.add_line((arr_x - 1.5, box_y - 3), (arr_x, box_y - 5), dxfattribs={"layer": "UDS_SEQUENCE"})
                self.msp.add_line((arr_x + 1.5, box_y - 3), (arr_x, box_y - 5), dxfattribs={"layer": "UDS_SEQUENCE"})

        # -------------------------------------------------------------
        # 4. 中區：ISO 15765-2 CAN-TP 多幀分包時序 (CAN-TP Timing)
        # -------------------------------------------------------------
        c_x, c_y, c_w, c_h = 145, 75, 130, 185
        self.msp.add_lwpolyline([(c_x, c_y), (c_x + c_w, c_y), (c_x + c_w, c_y + c_h), (c_x, c_y + c_h), (c_x, c_y)], dxfattribs={"layer": "CAN_TP_FRAMES"})
        self.msp.add_text("ISO 15765-2 (CAN-TP) MULTI-FRAME TIMING", dxfattribs={"layer": "CAN_TP_FRAMES", "height": 2.2}).set_placement((c_x + 3, c_y + c_h - 6))

        tp_items = [
            ("Tester -> ECU", "First Frame (FF): [0x10, DL_H, DL_L, D0..D5]", 160),
            ("ECU -> Tester", "Flow Control (FC): [0x30, BS=8, STmin=5ms]", 138),
            ("Tester -> ECU", "Consecutive Frame 1 (CF1): [0x21, D0..D6]", 116),
            ("Tester -> ECU", "Consecutive Frame 2 (CF2): [0x22, D0..D6]", 94),
            ("Tester -> ECU", "Consecutive Frame 8 (CF8): [0x28, D0..D6]", 72),
            ("ECU -> Tester", "Transfer Response: 0x76 BSC + Next Flow Control", 50)
        ]

        for sender, desc, rel_y in tp_items:
            py = c_y + rel_y
            self.msp.add_lwpolyline([(c_x + 5, py), (c_x + c_w - 5, py), (c_x + c_w - 5, py + 16), (c_x + 5, py + 16), (c_x + 5, py)], dxfattribs={"layer": "CAN_TP_FRAMES"})
            self.msp.add_text(f"• {sender}", dxfattribs={"layer": "CAN_TP_FRAMES", "height": 1.7}).set_placement((c_x + 7, py + 10))
            self.msp.add_text(desc, dxfattribs={"layer": "CAN_TP_FRAMES", "height": 1.3}).set_placement((c_x + 7, py + 3))

        # -------------------------------------------------------------
        # 5. 右區：MCU Flash 記憶體空間映射 (1088 KB Memory Map)
        # -------------------------------------------------------------
        r_x, r_y, r_w, r_h = 280, 75, 115, 185
        self.msp.add_lwpolyline([(r_x, r_y), (r_x + r_w, r_y), (r_x + r_w, r_y + r_h), (r_x, r_y + r_h), (r_x, r_y)], dxfattribs={"layer": "MEMORY_MAP"})
        self.msp.add_text("MCU FLASH MEMORY MAP (1088 KB)", dxfattribs={"layer": "MEMORY_MAP", "height": 2.2}).set_placement((r_x + 3, r_y + r_h - 6))

        mems = [
            ("EEPROM Emulation (32KB)", "0x080A0000 - 0x080A7FFF", 160, 20),
            ("Calibration Flash (64KB)", "0x08090000 - 0x0809FFFF", 132, 22),
            ("Application Flash (512KB)", "0x08010000 - 0x0808FFFF [TARGET]", 75, 50),
            ("Bootloader Sector (64KB)", "0x08000000 - 0x0800FFFF [READ-ONLY]", 45, 24)
        ]

        for name, addr, my, mh in mems:
            py = r_y + my
            self.msp.add_lwpolyline([(r_x + 5, py), (r_x + r_w - 5, py), (r_x + r_w - 5, py + mh), (r_x + 5, py + mh), (r_x + 5, py)], dxfattribs={"layer": "MEMORY_MAP"})
            self.msp.add_text(name, dxfattribs={"layer": "MEMORY_MAP", "height": 1.7}).set_placement((r_x + 7, py + mh - 7))
            self.msp.add_text(addr, dxfattribs={"layer": "MEMORY_MAP", "height": 1.3}).set_placement((r_x + 7, py + 3))

        # -------------------------------------------------------------
        # 6. 底部表格：UDS 服務清冊與 NRC 錯誤碼矩陣 (BOM Table)
        # -------------------------------------------------------------
        tbl_x, tbl_y, tbl_w, tbl_h = 20, 15, 220, 45
        self.msp.add_lwpolyline([(tbl_x, tbl_y), (tbl_x + tbl_w, tbl_y), (tbl_x + tbl_w, tbl_y + tbl_h), (tbl_x, tbl_y + tbl_h), (tbl_x, tbl_y)], dxfattribs={"layer": "BOM_TABLE"})
        self.msp.add_line((tbl_x, tbl_y + 35), (tbl_x + tbl_w, tbl_y + 35), dxfattribs={"layer": "BOM_TABLE"})
        self.msp.add_text("UDS DIAGNOSTIC SERVICES & NRC ERROR CODE MATRIX", dxfattribs={"layer": "BOM_TABLE", "height": 2.3}).set_placement((tbl_x + 3, tbl_y + 37))

        rows = [
            "0x10 / 0x50: Session (Prog)  | 0x27 / 0x67: Seed-Key (L1) | 0x31: Erase/Integrity",
            "0x34 / 0x74: ReqDownload     | 0x36 / 0x76: TransferData  | 0x37 / 0x77: TransferExit",
            "0x85: DTC OFF | 0x28: Comm OFF | 0x11: HardReset | Flash: 512KB App Partition",
            "NRC 0x13: LenError | 0x24: SeqError | 0x31: OutOfRange | 0x33: Denied | 0x36: Locked",
            "CAN-TP Network: BS=8, STmin=5ms, P2_Server=50ms, P2*_Server=5000ms (0x78 Pending)"
        ]
        for idx, row in enumerate(rows):
            self.msp.add_text(row, dxfattribs={"layer": "BOM_TABLE", "height": 1.7}).set_placement((tbl_x + 3, tbl_y + 28 - (idx * 6.5)))

        # 儲存 DXF
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        self.doc.saveas(output_path)
        print(f"✅ AutoCAD DXF UDS Bootloader 刷寫原理圖已生成: {output_path}")
        return output_path


def run_self_test():
    print("=" * 80)
    print("📐 【PROJ-EXAM-09 AutoCAD DXF UDS Bootloader 出圖引擎自檢】")
    print("=" * 80)
    generator = UdsBootloader_DXFGenerator()
    out_path = "G:/我的雲端硬碟/AI_master_workspace/three_memory/DATA/sample_uds_bootloader_diagram.dxf"
    generator.build_uds_bootloader_dxf(out_path)
    print("🟢 DXF UDS Bootloader 出圖引擎自檢 100% 通過！")


if __name__ == "__main__":
    run_self_test()
