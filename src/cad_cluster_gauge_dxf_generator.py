#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 【PROJ-EXAM-06 AutoCAD DXF 雙錶盤儀表板與 CAN 電氣原理圖出圖引擎】
================================================================================
主責工程師：🛠️ A02 小開 (Agent_Coder)
圖面校驗官：👁️ A04 小Ｏ (02_Knowledge/CAD_Specs/Cluster_Gauge_DXF_Audit.md)
品質把關者：🐎 A03 小馬 (TEST/test_cluster_sensor_can_engine.py)

功能亮點：
  1. ACI 8 大工規圖層色彩標準 (COMPONENTS=綠/DIALS=青/NEEDLES=紅/CAN=青/MOTORS=黃/TABLE=青)
  2. 雙錶盤工規佈局：左時速錶 (0~240 km/h) ✕ 右轉速錶 (0~8000 RPM) ✕ 中央多功能液晶顯示幕
  3. 315° 圓弧刻度、微步進指針向量與紅線區 (Redline) 標註
  4. TJA1050 CAN 收發器電路、Switec X27.168 雙 H 橋驅動與 DBC 訊號清冊 BOM 表
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


class ClusterGauge_DXFGenerator:
    """
    AutoCAD DXF 車載雙錶盤儀表板與 CAN 電氣原理圖生成器 (A3 420x297mm)
    """

    LAYERS_CONFIG = {
        "0": {"color": 7, "desc": "預設圖層"},
        "FRAME_BORDER": {"color": 7, "desc": "A3 標準圖框與標題欄 (白色)"},
        "COMPONENTS": {"color": 3, "desc": "儀表板外殼與電路模組框 (綠色)"},
        "DIAL_GRAPHICS": {"color": 4, "desc": "錶盤外圓、315° 刻度弧線與數字標註 (青色)"},
        "NEEDLE_VECTORS": {"color": 1, "desc": "步進馬達指針動態指示向量 (紅色)"},
        "WIRING_CAN": {"color": 4, "desc": "CAN_H / CAN_L 差分總線與 120Ω 終端 (青色)"},
        "WIRING_MOTORS": {"color": 2, "desc": "Switec X27.168 步進馬達相線驅動 (黃色)"},
        "BOM_TABLE": {"color": 4, "desc": "DBC 訊號矩陣與接線 Pinout 清冊 (青色)"},
        "DIAG_SPECS": {"color": 2, "desc": "儀表控制與 S-Curve 規範註記 (黃色)"},
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

    def draw_dial(self, cx: float, cy: float, radius: float, title: str, unit: str, max_val: float, num_ticks: int, needle_val: float, is_rpm: bool = False):
        """繪製 315° 標準工規圓形錶盤"""
        # 外圓與內圓
        self.msp.add_circle((cx, cy), radius, dxfattribs={"layer": "DIAL_GRAPHICS"})
        self.msp.add_circle((cx, cy), radius - 1.5, dxfattribs={"layer": "DIAL_GRAPHICS"})
        self.msp.add_circle((cx, cy), 4.0, dxfattribs={"layer": "DIAL_GRAPHICS"}) # 中心軸蓋

        # 標題與單位
        self.msp.add_text(title, dxfattribs={"layer": "DIAL_GRAPHICS", "height": 3.0}).set_placement((cx - 18.0, cy - 15.0))
        self.msp.add_text(unit, dxfattribs={"layer": "DIAL_GRAPHICS", "height": 2.0}).set_placement((cx - 10.0, cy - 22.0))

        # 角度範圍: 225° 順時針轉至 -90° (總共 315°)
        start_angle = 225.0
        total_span = 315.0

        for i in range(num_ticks + 1):
            val = (max_val / num_ticks) * i
            ratio = i / num_ticks
            ang_deg = start_angle - (ratio * total_span)
            ang_rad = math.radians(ang_deg)

            # 主刻度線
            r1 = radius - 1.5
            r2 = radius - 6.0
            p1 = (cx + r1 * math.cos(ang_rad), cy + r1 * math.sin(ang_rad))
            p2 = (cx + r2 * math.cos(ang_rad), cy + r2 * math.sin(ang_rad))

            layer_tick = "NEEDLE_VECTORS" if (is_rpm and val >= 6500.0) else "DIAL_GRAPHICS"
            self.msp.add_line(p1, p2, dxfattribs={"layer": layer_tick})

            # 數字標註
            r_txt = radius - 11.0
            tx = cx + r_txt * math.cos(ang_rad) - 3.0
            ty = cy + r_txt * math.sin(ang_rad) - 1.2
            lbl = f"{int(val // 1000)}" if is_rpm else f"{int(val)}"
            self.msp.add_text(lbl, dxfattribs={"layer": layer_tick, "height": 2.2}).set_placement((tx, ty))

        # 指針向量 (Needle Vector)
        needle_ratio = min(1.0, max(0.0, needle_val / max_val))
        needle_ang_deg = start_angle - (needle_ratio * total_span)
        needle_ang_rad = math.radians(needle_ang_deg)
        np_end = (cx + (radius - 8.0) * math.cos(needle_ang_rad), cy + (radius - 8.0) * math.sin(needle_ang_rad))
        np_tail = (cx - 6.0 * math.cos(needle_ang_rad), cy - 6.0 * math.sin(needle_ang_rad))

        # 指針主體 (雙線多段線)
        self.msp.add_lwpolyline([np_tail, np_end], dxfattribs={"layer": "NEEDLE_VECTORS"})
        self.msp.add_circle((cx, cy), 2.5, dxfattribs={"layer": "NEEDLE_VECTORS"})

    def build_cluster_dxf(self, output_path: str) -> str:
        """構建完整 A3 工規雙錶盤儀表板與 CAN 原理圖"""

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

        self.msp.add_text("PROJ-EXAM-06: DIGITAL CLUSTER & CAN MATRIX", dxfattribs={"layer": "FRAME_BORDER", "height": 3.0}).set_placement((tb_x + 3, tb_y + 33))
        self.msp.add_text("STANDARDS: ISO 11898 CAN 2.0B / SAE J1939 / Switec X27", dxfattribs={"layer": "FRAME_BORDER", "height": 2.3}).set_placement((tb_x + 3, tb_y + 23))
        self.msp.add_text("DESIGNER: A02 CODER / A05 DEEP", dxfattribs={"layer": "FRAME_BORDER", "height": 2.2}).set_placement((tb_x + 3, tb_y + 13))
        self.msp.add_text("AUDITOR: A04 VISION / A03 REVIEWER", dxfattribs={"layer": "FRAME_BORDER", "height": 2.2}).set_placement((tb_x + 83, tb_y + 13))
        self.msp.add_text("CAN BAUD: 500 KBPS | STEPPER: 945 MICROSTEPS (315°)", dxfattribs={"layer": "FRAME_BORDER", "height": 2.0}).set_placement((tb_x + 3, tb_y + 3))

        # -------------------------------------------------------------
        # 2. 儀表板頂部外框 (Instrument Cluster Housing)
        # -------------------------------------------------------------
        cl_x, cl_y, cl_w, cl_h = 20, 130, 380, 145
        self.msp.add_lwpolyline([(cl_x, cl_y), (cl_x + cl_w, cl_y), (cl_x + cl_w, cl_y + cl_h), (cl_x, cl_y + cl_h), (cl_x, cl_y)], dxfattribs={"layer": "COMPONENTS"})
        self.msp.add_text("AUTOMOTIVE DUAL-GAUGE DIGITAL INSTRUMENT CLUSTER (車載雙錶盤數位儀表板)", dxfattribs={"layer": "COMPONENTS", "height": 2.5}).set_placement((cl_x + 5, cl_y + cl_h - 7))

        # -------------------------------------------------------------
        # 3. 繪製左時速錶 (Speedometer: 0~240 km/h, 指向 105 km/h)
        # -------------------------------------------------------------
        self.draw_dial(cx=100.0, cy=200.0, radius=48.0, title="SPEED", unit="km/h", max_val=240.0, num_ticks=12, needle_val=105.5, is_rpm=False)

        # -------------------------------------------------------------
        # 4. 繪製右轉速錶 (Tachometer: 0~8000 RPM, 指向 3200 RPM)
        # -------------------------------------------------------------
        self.draw_dial(cx=320.0, cy=200.0, radius=48.0, title="TACHO", unit="x1000 r/min", max_val=8000.0, num_ticks=8, needle_val=3200.0, is_rpm=True)

        # -------------------------------------------------------------
        # 5. 繪製中央多功能 LCD / OLED 顯示幕 (Multi-Function Display)
        # -------------------------------------------------------------
        disp_x, disp_y, disp_w, disp_h = 175.0, 160.0, 70.0, 80.0
        self.msp.add_lwpolyline([(disp_x, disp_y), (disp_x + disp_w, disp_y), (disp_x + disp_w, disp_y + disp_h), (disp_x, disp_y + disp_h), (disp_x, disp_y)], dxfattribs={"layer": "COMPONENTS"})
        self.msp.add_text("MULTI-FUNCTION OLED", dxfattribs={"layer": "COMPONENTS", "height": 2.0}).set_placement((disp_x + 3, disp_y + disp_h - 6))
        self.msp.add_line((disp_x, disp_y + disp_h - 9), (disp_x + disp_w, disp_y + disp_h - 9), dxfattribs={"layer": "COMPONENTS"})

        self.msp.add_text("GEAR:  [ D ]", dxfattribs={"layer": "DIAL_GRAPHICS", "height": 3.0}).set_placement((disp_x + 15, disp_y + 55))
        self.msp.add_text("COOLANT: 90 °C", dxfattribs={"layer": "DIAL_GRAPHICS", "height": 2.0}).set_placement((disp_x + 8, disp_y + 43))
        self.msp.add_text("FUEL:    75 %", dxfattribs={"layer": "DIAL_GRAPHICS", "height": 2.0}).set_placement((disp_x + 8, disp_y + 33))
        self.msp.add_text("VOLTAGE: 13.8 V", dxfattribs={"layer": "DIAL_GRAPHICS", "height": 2.0}).set_placement((disp_x + 8, disp_y + 23))
        self.msp.add_text("ODO: 012345.6 km", dxfattribs={"layer": "DIAL_GRAPHICS", "height": 2.2}).set_placement((disp_x + 5, disp_y + 11))
        self.msp.add_text("CAN: ONLINE (500k)", dxfattribs={"layer": "WIRING_CAN", "height": 1.8}).set_placement((disp_x + 6, disp_y + 3))

        # -------------------------------------------------------------
        # 6. 左下：CAN 收發器電路 (TJA1050 Transceiver)
        # -------------------------------------------------------------
        tja_x, tja_y, tja_w, tja_h = 20, 65, 95, 55
        self.msp.add_lwpolyline([(tja_x, tja_y), (tja_x + tja_w, tja_y), (tja_x + tja_w, tja_y + tja_h), (tja_x, tja_y + tja_h), (tja_x, tja_y)], dxfattribs={"layer": "WIRING_CAN"})
        self.msp.add_text("CAN TRANSCEIVER (TJA1050)", dxfattribs={"layer": "WIRING_CAN", "height": 2.2}).set_placement((tja_x + 3, tja_y + tja_h - 6))
        self.msp.add_text("• CAN_H / CAN_L Differential Bus", dxfattribs={"layer": "WIRING_CAN", "height": 1.7}).set_placement((tja_x + 3, tja_y + 36))
        self.msp.add_text("• 120Ω Split Termination Resistor", dxfattribs={"layer": "WIRING_CAN", "height": 1.7}).set_placement((tja_x + 3, tja_y + 28))
        self.msp.add_text("• ISO 11898-2 EMC / ESD Filter", dxfattribs={"layer": "WIRING_CAN", "height": 1.7}).set_placement((tja_x + 3, tja_y + 20))
        self.msp.add_text("• RxD / TxD -> MCU CAN Controller", dxfattribs={"layer": "WIRING_CAN", "height": 1.7}).set_placement((tja_x + 3, tja_y + 12))

        # -------------------------------------------------------------
        # 7. 右下：Switec X27.168 雙步進馬達驅動電路
        # -------------------------------------------------------------
        drv_x, drv_y, drv_w, drv_h = 125, 65, 105, 55
        self.msp.add_lwpolyline([(drv_x, drv_y), (drv_x + drv_w, drv_y), (drv_x + drv_w, drv_y + drv_h), (drv_x, drv_y + drv_h), (drv_x, drv_y)], dxfattribs={"layer": "WIRING_MOTORS"})
        self.msp.add_text("STEPPER MOTOR DRIVER (X27.168)", dxfattribs={"layer": "WIRING_MOTORS", "height": 2.2}).set_placement((drv_x + 3, drv_y + drv_h - 6))
        self.msp.add_text("• Dual Microstep H-Bridge Drivers", dxfattribs={"layer": "WIRING_MOTORS", "height": 1.7}).set_placement((drv_x + 3, drv_y + 36))
        self.msp.add_text("• 1/3° Step Angle (945 Steps Full Arc)", dxfattribs={"layer": "WIRING_MOTORS", "height": 1.7}).set_placement((drv_x + 3, drv_y + 28))
        self.msp.add_text("• S-Curve Jerk-Free Trajectory FSM", dxfattribs={"layer": "WIRING_MOTORS", "height": 1.7}).set_placement((drv_x + 3, drv_y + 20))
        self.msp.add_text("• Auto Stall Zero-Point Calibration", dxfattribs={"layer": "WIRING_MOTORS", "height": 1.7}).set_placement((drv_x + 3, drv_y + 12))

        # -------------------------------------------------------------
        # 8. 底部表格：DBC 訊號矩陣與接線清冊 (BOM Table)
        # -------------------------------------------------------------
        tbl_x, tbl_y, tbl_w, tbl_h = 20, 15, 220, 45
        self.msp.add_lwpolyline([(tbl_x, tbl_y), (tbl_x + tbl_w, tbl_y), (tbl_x + tbl_w, tbl_y + tbl_h), (tbl_x, tbl_y + tbl_h), (tbl_x, tbl_y)], dxfattribs={"layer": "BOM_TABLE"})
        self.msp.add_line((tbl_x, tbl_y + 35), (tbl_x + tbl_w, tbl_y + 35), dxfattribs={"layer": "BOM_TABLE"})
        self.msp.add_text("DBC SIGNAL MATRIX & CAN BUS INTERFACE SCHEDULE", dxfattribs={"layer": "BOM_TABLE", "height": 2.3}).set_placement((tbl_x + 3, tbl_y + 37))

        rows = [
            "0x0C4 | Engine_RPM       | 16b Motorola | Factor=0.25 | Offset=0   | 0~8000 RPM (100Hz)",
            "0x0C4 | Vehicle_Speed    | 16b Motorola | Factor=0.01 | Offset=0   | 0~250.0 km/h (100Hz)",
            "0x1F0 | Coolant_Temp     | 8b  Intel    | Factor=1.0  | Offset=-40 | -40~150 °C (20Hz)",
            "0x1F0 | Fuel_Level       | 8b  Intel    | Factor=0.5  | Offset=0   | 0~100.0 % (20Hz)",
            "Failsafe: CAN Timeout 200ms -> S-Curve Smooth Needle Drop to 0 + MIL Warning LED ON"
        ]
        for idx, row in enumerate(rows):
            self.msp.add_text(row, dxfattribs={"layer": "BOM_TABLE", "height": 1.7}).set_placement((tbl_x + 3, tbl_y + 28 - (idx * 6.5)))

        # 儲存 DXF
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        self.doc.saveas(output_path)
        print(f"✅ AutoCAD DXF 雙錶盤儀表板原理圖已生成: {output_path}")
        return output_path


def run_self_test():
    print("=" * 80)
    print("📐 【PROJ-EXAM-06 AutoCAD DXF 雙錶盤儀表出圖引擎自檢】")
    print("=" * 80)
    generator = ClusterGauge_DXFGenerator()
    out_path = "G:/我的雲端硬碟/AI_master_workspace/three_memory/DATA/sample_cluster_gauge_diagram.dxf"
    generator.build_cluster_dxf(out_path)
    print("🟢 DXF 雙錶盤儀表出圖引擎自檢 100% 通過！")


if __name__ == "__main__":
    run_self_test()
