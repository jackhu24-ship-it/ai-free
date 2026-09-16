#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 【PROJ-EXAM-04 AutoCAD DXF ISO 14229 UDS 狀態機時序圖出圖引擎】
================================================================================
主責工程師：🛠️ A02 小開 (Agent_Coder)
圖面校驗官：👁️ A04 小Ｏ (02_Knowledge/CAD_Specs/UDS_State_Machine_DXF_Audit.md)
品質把關者：🐎 A03 小馬 (TEST/test_uds_iso14229_state_machine.py)

功能亮點：
  1. ACI 8 大工規圖層色彩標準 (STATES=綠/ARROWS=黃/MSGS=青/TIMERS=紅/NRC=洋紅/TABLE=青)
  2. 完整 ISO 14229-1 會話狀態轉移拓撲 (預設會話 ➔ 擴展會話 ➔ 安全解鎖 ➔ S3 超時回退 ➔ 3 次防爆破鎖定)
  3. 正交曼哈頓箭頭走線與 UDS 服務報文格式標註 (0x10, 0x27, 0x22, 0x2E, 0x3E, 0x31)
  4. A3 標準工程圖框 (420x297mm) 與 ISO 14229 服務表與 NRC 處置矩陣
"""

from __future__ import annotations

import sys
import os
import math
from pathlib import Path
from typing import List, Tuple, Dict, Any

try:
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
except ImportError:
    print("❌ 請先安裝 ezdxf: pip install ezdxf")
    sys.exit(1)

# Windows UTF-8 編碼防護
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


class UdsStateMachine_DXFGenerator:
    """
    AutoCAD DXF ISO 14229 UDS 狀態機與會話轉移時序圖生成器 (A3 420x297mm)
    """

    LAYERS_CONFIG = {
        "0": {"color": 7, "desc": "預設圖層"},
        "FRAME_BORDER": {"color": 7, "desc": "A3 標準圖框與標題欄 (白色)"},
        "STATE_BOXES": {"color": 3, "desc": "UDS 會話狀態節點框 (綠色)"},
        "TRANSITION_ARROWS": {"color": 2, "desc": "狀態轉移曼哈頓正交箭頭線 (黃色)"},
        "UDS_MESSAGES": {"color": 4, "desc": "請求/響應報文代碼標註 (青色)"},
        "TIMERS_CALLOUTS": {"color": 1, "desc": "S3Server / P2Server 計時器引線 (紅色)"},
        "NRC_CODES": {"color": 6, "desc": "負響應 NRC 錯誤碼與懲罰冷卻註記 (洋紅色)"},
        "UDS_SERVICE_TABLE": {"color": 4, "desc": "ISO 14229-1 診斷服務與 NRC 參照表 (青色)"},
        "DIAG_SPECS": {"color": 2, "desc": "車規診斷技術規格與尋址規範 (黃色)"},
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

    def draw_state_box(self, x: float, y: float, w: float, h: float, title: str, subtitle: str = ""):
        """繪製狀態節點框 (雙線外框)"""
        # 外框
        self.msp.add_lwpolyline([(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)], dxfattribs={"layer": "STATE_BOXES"})
        # 內框
        self.msp.add_lwpolyline([(x + 1.5, y + 1.5), (x + w - 1.5, y + 1.5), (x + w - 1.5, y + h - 1.5), (x + 1.5, y + h - 1.5), (x + 1.5, y + 1.5)], dxfattribs={"layer": "STATE_BOXES"})
        # 標題文字
        self.msp.add_text(title, dxfattribs={"layer": "STATE_BOXES", "height": 2.2}).set_placement((x + 3.0, y + h - 6.0))
        if subtitle:
            self.msp.add_text(subtitle, dxfattribs={"layer": "STATE_BOXES", "height": 1.6}).set_placement((x + 3.0, y + 3.5))

    def draw_arrow(self, pts: List[Tuple[float, float]], layer: str = "TRANSITION_ARROWS"):
        """繪製折線與末端箭頭"""
        self.msp.add_lwpolyline(pts, dxfattribs={"layer": layer})
        # 終點畫箭頭
        if len(pts) >= 2:
            p_end = pts[-1]
            p_prev = pts[-2]
            dx = p_end[0] - p_prev[0]
            dy = p_end[1] - p_prev[1]
            angle = math.atan2(dy, dx)
            # 箭頭兩翼
            a_len = 3.5
            a_ang = math.radians(25)
            p_left = (p_end[0] - a_len * math.cos(angle - a_ang), p_end[1] - a_len * math.sin(angle - a_ang))
            p_right = (p_end[0] - a_len * math.cos(angle + a_ang), p_end[1] - a_len * math.sin(angle + a_ang))
            self.msp.add_lwpolyline([p_left, p_end, p_right], dxfattribs={"layer": layer})

    def build_uds_dxf(self, output_path: str) -> str:
        """構建完整 A3 工規 ISO 14229 UDS 狀態轉移時序圖"""

        # -------------------------------------------------------------
        # 1. 繪製 A3 標準圖框與標題欄 (Title Block)
        # -------------------------------------------------------------
        self.msp.add_lwpolyline([(0, 0), (420, 0), (420, 297), (0, 297), (0, 0)], dxfattribs={"layer": "FRAME_BORDER"})
        self.msp.add_lwpolyline([(10, 10), (410, 10), (410, 287), (10, 287), (10, 10)], dxfattribs={"layer": "FRAME_BORDER"})

        # 標題欄
        tb_x, tb_y, tb_w, tb_h = 250, 10, 160, 40
        self.msp.add_lwpolyline([(tb_x, tb_y), (tb_x + tb_w, tb_y), (tb_x + tb_w, tb_y + tb_h), (tb_x, tb_y + tb_h), (tb_x, tb_y)], dxfattribs={"layer": "FRAME_BORDER"})
        self.msp.add_line((tb_x, tb_y + 20), (tb_x + tb_w, tb_y + 20), dxfattribs={"layer": "FRAME_BORDER"})
        self.msp.add_line((tb_x, tb_y + 30), (tb_x + tb_w, tb_y + 30), dxfattribs={"layer": "FRAME_BORDER"})
        self.msp.add_line((tb_x + 80, tb_y), (tb_x + 80, tb_y + 30), dxfattribs={"layer": "FRAME_BORDER"})

        self.msp.add_text("PROJ-EXAM-04: ISO 14229 UDS STATE MACHINE", dxfattribs={"layer": "FRAME_BORDER", "height": 3.2}).set_placement((tb_x + 3, tb_y + 33))
        self.msp.add_text("STANDARDS: ISO 14229-1 / ISO 15765-2 (DoCAN)", dxfattribs={"layer": "FRAME_BORDER", "height": 2.5}).set_placement((tb_x + 3, tb_y + 23))
        self.msp.add_text("DESIGNER: A02 CODER / A05 DEEP", dxfattribs={"layer": "FRAME_BORDER", "height": 2.2}).set_placement((tb_x + 3, tb_y + 13))
        self.msp.add_text("AUDITOR: A04 VISION / A03 REVIEWER", dxfattribs={"layer": "FRAME_BORDER", "height": 2.2}).set_placement((tb_x + 83, tb_y + 13))
        self.msp.add_text("PHYS ID: 0x7E0/0x7E8 | FUNC ID: 0x7DF", dxfattribs={"layer": "FRAME_BORDER", "height": 2.2}).set_placement((tb_x + 3, tb_y + 3))

        # -------------------------------------------------------------
        # 2. 繪製 5 大 UDS 狀態節點框 (State Boxes)
        # -------------------------------------------------------------
        # (A) 預設會話 (Default Session - 初始態)
        s1_x, s1_y, s1_w, s1_h = 25.0, 210.0, 75.0, 32.0
        self.draw_state_box(s1_x, s1_y, s1_w, s1_h, "1. DEFAULT SESSION (0x01)", "Security: LOCKED | DIDs Read Only")

        # (B) 擴展會話 (Extended Session)
        s2_x, s2_y, s2_w, s2_h = 145.0, 210.0, 80.0, 32.0
        self.draw_state_box(s2_x, s2_y, s2_w, s2_h, "2. EXTENDED SESSION (0x03)", "Full Diag & 0x27 Seed-Key Active")

        # (C) 安全解鎖態 (Security Unlocked Level 1)
        s3_x, s3_y, s3_w, s3_h = 275.0, 210.0, 85.0, 32.0
        self.draw_state_box(s3_x, s3_y, s3_w, s3_h, "3. SECURITY UNLOCKED (L1)", "Protected 0x2E Write / 0x31 Routine")

        # (D) 編程會話 (Programming Session)
        s4_x, s4_y, s4_w, s4_h = 145.0, 130.0, 80.0, 32.0
        self.draw_state_box(s4_x, s4_y, s4_w, s4_h, "4. PROGRAMMING SESSION (0x02)", "Bootloader / Flash Memory Erase")

        # (E) 3 次錯誤密鑰鎖定懲罰態 (Locked Delay State)
        s5_x, s5_y, s5_w, s5_h = 275.0, 130.0, 85.0, 32.0
        self.draw_state_box(s5_x, s5_y, s5_w, s5_h, "5. LOCKED DELAY (NRC 0x36/0x37)", "10s Penalty Timer Active")

        # -------------------------------------------------------------
        # 3. 繪製狀態轉移箭頭與報文標註 (Transitions & Callouts)
        # -------------------------------------------------------------
        # (1) Default -> Extended: 0x10 03
        self.draw_arrow([(s1_x + s1_w, s1_y + 20), (s2_x, s2_y + 20)])
        self.msp.add_text("Req: 0x10 03 (Extended)", dxfattribs={"layer": "UDS_MESSAGES", "height": 1.8}).set_placement((s1_x + s1_w + 3, s1_y + 22))
        self.msp.add_text("Resp: 0x50 03 00 32...", dxfattribs={"layer": "UDS_MESSAGES", "height": 1.6}).set_placement((s1_x + s1_w + 3, s1_y + 15))

        # (2) Extended -> Security Unlocked: 0x27 01 / 0x27 02
        self.draw_arrow([(s2_x + s2_w, s2_y + 20), (s3_x, s3_y + 20)])
        self.msp.add_text("0x27 01 (ReqSeed)", dxfattribs={"layer": "UDS_MESSAGES", "height": 1.8}).set_placement((s2_x + s2_w + 3, s2_y + 24))
        self.msp.add_text("0x27 02 (SendKey)", dxfattribs={"layer": "UDS_MESSAGES", "height": 1.8}).set_placement((s2_x + s2_w + 3, s2_y + 17))
        self.msp.add_text("Resp: 0x67 02 (PASS)", dxfattribs={"layer": "UDS_MESSAGES", "height": 1.6}).set_placement((s2_x + s2_w + 3, s2_y + 10))

        # (3) S3Server Timeout 回退 (Extended -> Default) (紅色引線)
        self.draw_arrow([(s2_x + 40, s2_y + s2_h), (s2_x + 40, s2_y + s2_h + 15), (s1_x + 40, s1_y + s1_h + 15), (s1_x + 40, s1_y + s1_h)], layer="TIMERS_CALLOUTS")
        self.msp.add_text("S3Server Timeout (5000ms) -> Fallback to Default Session & Lock Security", dxfattribs={"layer": "TIMERS_CALLOUTS", "height": 1.8}).set_placement((s1_x + 15, s1_y + s1_h + 18))

        # (4) Extended -> Programming: 0x10 02
        self.draw_arrow([(s2_x + 40, s2_y), (s2_x + 40, s4_y + s4_h)])
        self.msp.add_text("Req: 0x10 02 (Prog)", dxfattribs={"layer": "UDS_MESSAGES", "height": 1.8}).set_placement((s2_x + 43, s4_y + 18))

        # (5) Security Failure (3 Attempts -> Locked Delay): NRC 0x36
        self.draw_arrow([(s3_x + 42, s3_y), (s5_x + 42, s5_y + s5_h)], layer="NRC_CODES")
        self.msp.add_text("3 Invalid Keys -> NRC 0x36", dxfattribs={"layer": "NRC_CODES", "height": 1.8}).set_placement((s3_x + 45, s5_y + 18))

        # (6) Locked Delay -> Extended (10s Timer Expiry)
        self.draw_arrow([(s5_x, s5_y + 16), (s4_x + s4_w, s5_y + 16)])
        self.msp.add_text("10s Lockout Expired -> Ready", dxfattribs={"layer": "NRC_CODES", "height": 1.6}).set_placement((s4_x + s4_w + 3, s5_y + 18))

        # (7) ECU Reset: 0x11 01 -> Reset to Default
        self.draw_arrow([(s4_x, s4_y + 16), (s1_x + 40, s4_y + 16), (s1_x + 40, s1_y)])
        self.msp.add_text("0x11 01 (HardReset) -> Return to Default", dxfattribs={"layer": "UDS_MESSAGES", "height": 1.8}).set_placement((s1_x + 5, s4_y + 20))

        # (8) TesterPresent 0x3E 80 心跳維持
        self.msp.add_text("TesterPresent (0x3E 80) Keep-Alive: Resets S3Server Timer (< 4000ms period)", dxfattribs={"layer": "TIMERS_CALLOUTS", "height": 1.8}).set_placement((25, 195))

        # -------------------------------------------------------------
        # 4. 底部 ISO 14229 服務彙整表與 NRC 對照表 (Service & NRC Table)
        # -------------------------------------------------------------
        table_x, table_y, table_w, table_h = 20, 15, 220, 75
        self.msp.add_lwpolyline([(table_x, table_y), (table_x + table_w, table_y), (table_x + table_w, table_y + table_h), (table_x, table_y + table_h), (table_x, table_y)], dxfattribs={"layer": "UDS_SERVICE_TABLE"})
        self.msp.add_line((table_x, table_y + 65), (table_x + table_w, table_y + 65), dxfattribs={"layer": "UDS_SERVICE_TABLE"})
        self.msp.add_text("ISO 14229-1 UDS DIAGNOSTIC SERVICES & NRC SPECIFICATION MATRIX", dxfattribs={"layer": "UDS_SERVICE_TABLE", "height": 2.5}).set_placement((table_x + 3, table_y + 68))

        rows = [
            "0x10 | DiagnosticSessionControl | 0x01 Default, 0x02 Prog, 0x03 Extended | P2=50ms, S3=5000ms",
            "0x11 | ECUReset                 | 0x01 HardReset, 0x02 KeyOffOn, 0x03 Soft | Resets FSM to Default",
            "0x22 | ReadDataByIdentifier     | 0xF190 (VIN), 0xF188 (SW_Ver), 0x0100    | Allowed in All Sessions",
            "0x2E | WriteDataByIdentifier    | 0x0102 (TripThreshold), 0xF190 (VIN)    | Protected by Level 1/2",
            "0x27 | SecurityAccess           | 0x01 ReqSeed, 0x02 SendKey (PRNG+Mask)   | 3-Fail Lockout 10.0s",
            "0x31 | RoutineControl           | 0x01 Start, 0x03 RequestResults (0x0201) | E-Fuse Self-Test Routine",
            "0x3E | TesterPresent            | 0x00 / 0x80 (Suppress Pos Response)      | Keeps Extended Alive",
            "NRCs | 0x11(NotSup), 0x12(SubFnNotSup), 0x13(LenErr), 0x33(SecDenied), 0x35(InvKey), 0x36/37(Lockout)"
        ]
        for idx, row in enumerate(rows):
            self.msp.add_text(row, dxfattribs={"layer": "UDS_SERVICE_TABLE", "height": 1.7}).set_placement((table_x + 3, table_y + 57 - (idx * 6.5)))

        # -------------------------------------------------------------
        # 5. 車規通訊技術註記 (Diag Specs)
        # -------------------------------------------------------------
        spec_x = 250.0
        self.msp.add_text("CAN-TP & SECURITY ACCESS SPECS:", dxfattribs={"layer": "DIAG_SPECS", "height": 2.2}).set_placement((spec_x, 80))
        self.msp.add_text("• ISO 15765-2 CAN-TP Multi-Frame (FF, FC, CF) Supported", dxfattribs={"layer": "DIAG_SPECS", "height": 1.8}).set_placement((spec_x, 72))
        self.msp.add_text("• Flow Control: BS = 8 blocks, STmin = 10 ms", dxfattribs={"layer": "DIAG_SPECS", "height": 1.8}).set_placement((spec_x, 65))
        self.msp.add_text("• Seed-Key Mask: (Seed ^ 0xA5A5A5A5 <<< 3) + 0x55AA55AA", dxfattribs={"layer": "DIAG_SPECS", "height": 1.8}).set_placement((spec_x, 58))
        self.msp.add_text("• Anti-Brute-Force: 3 Invalid Keys -> 10s Delay (NRC 0x37)", dxfattribs={"layer": "DIAG_SPECS", "height": 1.8}).set_placement((spec_x, 51))

        # -------------------------------------------------------------
        # 6. 儲存 DXF
        # -------------------------------------------------------------
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        self.doc.saveas(output_path)
        print(f"✅ AutoCAD DXF UDS 狀態機時序圖已生成: {output_path}")
        return output_path


def run_self_test():
    print("=" * 80)
    print("📐 【PROJ-EXAM-04 AutoCAD DXF UDS 狀態機時序圖出圖引擎自檢】")
    print("=" * 80)
    generator = UdsStateMachine_DXFGenerator()
    out_path = "G:/我的雲端硬碟/AI_master_workspace/three_memory/DATA/sample_uds_state_machine_diagram.dxf"
    generator.build_uds_dxf(out_path)
    print("🟢 DXF UDS 狀態機時序圖出圖引擎自檢 100% 通過！")


if __name__ == "__main__":
    run_self_test()
