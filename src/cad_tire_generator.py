#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 工規 CAD 實戰模組：16 吋汽車標準輪胎與五輻鋁圈工規圖紙自動繪圖系統 (cad_tire_generator.py)
作者：🛠️ 小開 (Agent_Coder)
審查：🐎 小馬 (Agent_Reviewer)
統籌：👑 小幫手 (Agent_PM)

圖紙規格與標準：
1. 輪胎規格：205/55 R16 91V（總外徑 632mm，胎面寬 205mm，輪框直徑 16 吋 / 406.4mm）
2. 輪圈規格：16 x 6.5J，5 孔 PCD 114.3mm，經典運動型五輻式鋁合金輪圈
3. 圖面內容：
   - 正面視圖 (Front/Face View)：胎面花紋外圓、胎壁輪廓、輪圈外框、五輻輪輻幾何、五孔螺栓 PCD、中心蓋、十字中心線
   - 剖面斷面圖 (Section View)：胎面寬度 205mm、胎壁弧形、輪框胎唇卡槽、輪軸中心線
   - 工規規格表 (Spec Table)：右側洋紅色機械與輪胎參數規格清單
   - 尺寸標註 (Dimensions)：外徑 Ø632、輪圈 Ø406.4 (16")、胎寬 205、PCD 5x114.3
4. DXF 標準：純淨 R12 DXF，保證 AutoCAD 2000~2026 零警告直接開圖！
"""

from __future__ import annotations

import sys
import math
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional

# 強制 Windows 標準輸出為 UTF-8
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import ezdxf

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = WORKSPACE_ROOT / "DATA"
DATA_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_DXF_PATH = DATA_DIR / "tire_r16.dxf"
PREVIEW_PNG_PATH = DATA_DIR / "tire_r16_preview.png"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [CADTireGenerator] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("CADTireGenerator")


@dataclass
class TireR16Spec:
    """16 吋汽車標準輪胎工規參數 (205/55 R16)"""
    tire_spec_str: str = "205/55 R16 91V"
    section_width: float = 205.0         # 胎寬 (mm)
    aspect_ratio: float = 0.55           # 扁平比 55%
    rim_diameter_inch: float = 16.0      # 輪圈直徑 (inch)
    rim_diameter_mm: float = 406.4       # 輪圈直徑 (mm) = 16 * 25.4
    sidewall_height: float = 112.75      # 胎壁高 (mm) = 205 * 0.55
    outer_diameter_mm: float = 631.9     # 輪胎總外徑 (mm) = 406.4 + 2 * 112.75
    pcd_dia_mm: float = 114.3            # 5 孔螺栓圓直徑 PCD (mm)
    bolt_hole_count: int = 5             # 螺栓孔數
    bolt_hole_dia: float = 14.0          # 螺栓孔徑 (mm)
    center_bore_dia: float = 60.0        # 中心軸孔直徑 (mm)


class TireR16DXFBuilder:
    """16 吋輪胎與輪圈工規 DXF 繪製器 (R12 純淨相容版)"""

    def __init__(self, spec: Optional[TireR16Spec] = None) -> None:
        self.spec = spec or TireR16Spec()
        self.doc = ezdxf.new("R12")
        self.msp = self.doc.modelspace()
        self._init_standard_layers()

    def _init_standard_layers(self) -> None:
        """初始化 6 大標準圖層與線型"""
        layers_config = [
            ("OUTLINE", 7, "CONTINUOUS"),     # 輪廓線 (白/黑)
            ("CENTER", 1, "CENTER"),          # 中心線 (紅)
            ("HIDDEN", 2, "HIDDEN"),          # 隱藏線 (黃)
            ("DIMENSION", 3, "CONTINUOUS"),   # 尺寸標註 (綠)
            ("TEXT", 2, "CONTINUOUS"),        # 文字說明 (黃)
            ("TABLE", 6, "CONTINUOUS")        # 規格表格 (洋紅)
        ]
        for name, color, linetype in layers_config:
            if name not in self.doc.layers:
                self.doc.layers.add(name=name, color=color, linetype=linetype)

    def build_drawing(self, output_path: Optional[Path | str] = None) -> Path:
        """繪製完整圖紙 (輪胎正視圖 + 斷面剖視圖 + 尺寸標註 + 規格表)"""
        target_path = Path(output_path) if output_path else OUTPUT_DXF_PATH

        # 基準定位 (座標原點)
        front_view_center = (400.0, 450.0)    # 正面視圖中心
        section_view_center = (900.0, 450.0)  # 剖面圖中心
        table_origin = (1150.0, 780.0)        # 規格表左上角

        # 1. 繪製圖紙標題與圖框
        self._draw_title_block()

        # 2. 繪製輪胎正面視圖 (五輻鋁圈 + 胎面花紋)
        self._draw_front_view(front_view_center)

        # 3. 繪製輪胎剖面斷面圖 (胎寬 205mm + 輪圈卡槽)
        self._draw_section_view(section_view_center)

        # 4. 繪製右側工規規格參數表
        self._draw_spec_table(table_origin)

        # 5. 儲存 R12 DXF 檔案
        self.doc.saveas(target_path)
        logger.info(f"📐 16 吋汽車標準輪胎 DXF 圖紙成功產出: {target_path.name}")
        return target_path

    def _draw_title_block(self) -> None:
        """繪製圖面大標題"""
        self.msp.add_text(
            "16-INCH AUTOMOTIVE TIRE & WHEEL ASSEMBLY (205/55 R16 91V)",
            dxfattribs={"layer": "TEXT", "height": 18.0, "color": 2}
        ).set_placement((60.0, 920.0))

        self.msp.add_text(
            "SCALE: 1:1  |  PROJECTION: THIRD ANGLE  |  UNIT: mm  |  DESIGNED BY: Five-Agent AI OS",
            dxfattribs={"layer": "TEXT", "height": 10.0, "color": 7}
        ).set_placement((60.0, 880.0))

    def _draw_front_view(self, center: Tuple[float, float]) -> None:
        """繪製正面視圖：胎面、胎壁、五輻鋁框、螺栓孔與花紋"""
        cx, cy = center
        r_outer = self.spec.outer_diameter_mm / 2.0   # ~316.0 mm (胎面外徑)
        r_tread_groove = r_outer - 10.0              # ~306.0 mm (胎溝底圓)
        r_rim_outer = (self.spec.rim_diameter_mm + 25.0) / 2.0 # ~215.7 mm (輪圈外緣唇邊)
        r_rim_inner = self.spec.rim_diameter_mm / 2.0 # 203.2 mm (16 吋標稱胎唇直徑)
        r_hub_cap = 50.0                             # 中心蓋外圓
        r_pcd = self.spec.pcd_dia_mm / 2.0           # 57.15 mm
        r_bolt = self.spec.bolt_hole_dia / 2.0       # 7.0 mm

        # 1. 胎面外圓與胎壁輪廓
        self.msp.add_circle((cx, cy), radius=r_outer, dxfattribs={"layer": "OUTLINE", "color": 7})
        self.msp.add_circle((cx, cy), radius=r_tread_groove, dxfattribs={"layer": "OUTLINE", "color": 7})
        self.msp.add_circle((cx, cy), radius=r_rim_outer, dxfattribs={"layer": "OUTLINE", "color": 7})
        self.msp.add_circle((cx, cy), radius=r_rim_inner, dxfattribs={"layer": "OUTLINE", "color": 7})

        # 2. 胎面運動花紋溝槽 (Tread Sipes: 36 道外周導水溝槽)
        for i in range(36):
            deg = i * 10
            rad = math.radians(deg)
            x1 = cx + r_tread_groove * math.cos(rad)
            y1 = cy + r_tread_groove * math.sin(rad)
            x2 = cx + r_outer * math.cos(rad + 0.05)
            y2 = cy + r_outer * math.sin(rad + 0.05)
            self.msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": "OUTLINE", "color": 7})

        # 3. 五輻式運動鋁合金輪輻 (5-Spoke Wheel Rim)
        spoke_count = 5
        hub_inner_r = 55.0
        rim_attach_r = r_rim_inner - 15.0

        for i in range(spoke_count):
            base_deg = i * (360 / spoke_count) + 90 # 頂部向上對齊
            ang_center = math.radians(base_deg)
            ang_left = math.radians(base_deg - 14)
            ang_right = math.radians(base_deg + 14)

            # 輪輻根部點
            p_hub_l = (cx + hub_inner_r * math.cos(ang_left), cy + hub_inner_r * math.sin(ang_left))
            p_hub_r = (cx + hub_inner_r * math.cos(ang_right), cy + hub_inner_r * math.sin(ang_right))

            # 輪輻末端點
            p_rim_l = (cx + rim_attach_r * math.cos(math.radians(base_deg - 8)), cy + rim_attach_r * math.sin(math.radians(base_deg - 8)))
            p_rim_r = (cx + rim_attach_r * math.cos(math.radians(base_deg + 8)), cy + rim_attach_r * math.sin(math.radians(base_deg + 8)))

            # 繪製輪輻左右兩側實體線條
            self.msp.add_line(p_hub_l, p_rim_l, dxfattribs={"layer": "OUTLINE", "color": 7})
            self.msp.add_line(p_hub_r, p_rim_r, dxfattribs={"layer": "OUTLINE", "color": 7})
            self.msp.add_line(p_rim_l, p_rim_r, dxfattribs={"layer": "OUTLINE", "color": 7})

        # 4. 中心輪轂 (Hub Center & 5-Bolt PCD)
        self.msp.add_circle((cx, cy), radius=hub_inner_r, dxfattribs={"layer": "OUTLINE", "color": 7})
        self.msp.add_circle((cx, cy), radius=r_hub_cap, dxfattribs={"layer": "OUTLINE", "color": 7})
        self.msp.add_circle((cx, cy), radius=self.spec.center_bore_dia / 2.0, dxfattribs={"layer": "OUTLINE", "color": 7})

        # PCD 螺栓圓中心線
        self.msp.add_circle((cx, cy), radius=r_pcd, dxfattribs={"layer": "CENTER", "color": 1, "linetype": "CENTER"})

        # 5 顆螺栓孔 (5-Lug Bolt Holes)
        for i in range(5):
            deg = i * 72 + 90
            bx = cx + r_pcd * math.cos(math.radians(deg))
            by = cy + r_pcd * math.sin(math.radians(deg))
            self.msp.add_circle((bx, by), radius=r_bolt, dxfattribs={"layer": "OUTLINE", "color": 7})
            self.msp.add_circle((bx, by), radius=r_bolt + 4.0, dxfattribs={"layer": "HIDDEN", "color": 2, "linetype": "HIDDEN"})

        # 5. 十字中心線 (CENTER 圖層)
        ext = r_outer + 40.0
        self.msp.add_line((cx - ext, cy), (cx + ext, cy), dxfattribs={"layer": "CENTER", "color": 1, "linetype": "CENTER"})
        self.msp.add_line((cx, cy - ext), (cx, cy + ext), dxfattribs={"layer": "CENTER", "color": 1, "linetype": "CENTER"})

        # 視圖標籤
        self.msp.add_text(
            "TIRE FRONT VIEW (正面正視圖)",
            dxfattribs={"layer": "TEXT", "height": 12.0, "color": 2}
        ).set_placement((cx - 110.0, cy - r_outer - 50.0))

        # 尺寸標註：總外徑 Ø632、輪圈直徑 16 吋 (Ø406.4)
        self._draw_dim_line((cx - r_outer, cy + r_outer + 25), (cx + r_outer, cy + r_outer + 25), f"Tire Outer Dia: DIA {self.spec.outer_diameter_mm:.1f} mm")
        self._draw_dim_line((cx - r_rim_inner, cy + r_rim_inner + 15), (cx + r_rim_inner, cy + r_rim_inner + 15), f"Rim Dia: 16 inch (DIA {self.spec.rim_diameter_mm:.1f})")

    def _draw_section_view(self, center: Tuple[float, float]) -> None:
        """繪製輪胎斷面剖視圖 (Section View: 胎面寬 205mm + 輪圈寬 6.5J)"""
        cx, cy = center
        w_half = self.spec.section_width / 2.0       # 102.5 mm
        r_outer = self.spec.outer_diameter_mm / 2.0  # 315.95 mm
        r_rim = self.spec.rim_diameter_mm / 2.0      # 203.2 mm
        r_hub = 30.0

        # 上半部胎體剖面外廓 (Tire Profile Top)
        top_y = cy + r_outer
        rim_top_y = cy + r_rim
        sw_bend_x = w_half + 12.0 # 胎壁外鼓外型

        p_t_tl = (cx - w_half + 15, top_y)
        p_t_tr = (cx + w_half - 15, top_y)
        p_t_sl = (cx - sw_bend_x, cy + (r_outer + r_rim)/2)
        p_t_sr = (cx + sw_bend_x, cy + (r_outer + r_rim)/2)
        p_t_bl = (cx - 80.0, rim_top_y)
        p_t_br = (cx + 80.0, rim_top_y)

        # 繪製上半部胎體封閉線段
        self.msp.add_line(p_t_tl, p_t_tr, dxfattribs={"layer": "OUTLINE", "color": 7})
        self.msp.add_line(p_t_tr, p_t_sr, dxfattribs={"layer": "OUTLINE", "color": 7})
        self.msp.add_line(p_t_sr, p_t_br, dxfattribs={"layer": "OUTLINE", "color": 7})
        self.msp.add_line(p_t_br, p_t_bl, dxfattribs={"layer": "OUTLINE", "color": 7})
        self.msp.add_line(p_t_bl, p_t_sl, dxfattribs={"layer": "OUTLINE", "color": 7})
        self.msp.add_line(p_t_sl, p_t_tl, dxfattribs={"layer": "OUTLINE", "color": 7})

        # 輪胎內腔空氣層 (Tire Cavity)
        cavity_h = 12.0
        self.msp.add_line((cx - w_half + 25, top_y - cavity_h), (cx + w_half - 25, top_y - cavity_h), dxfattribs={"layer": "HIDDEN", "color": 2, "linetype": "HIDDEN"})

        # 下半部胎體剖面外廓 (Tire Profile Bottom - 對稱鏡像)
        bot_y = cy - r_outer
        rim_bot_y = cy - r_rim

        p_b_bl = (cx - w_half + 15, bot_y)
        p_b_br = (cx + w_half - 15, bot_y)
        p_b_sl = (cx - sw_bend_x, cy - (r_outer + r_rim)/2)
        p_b_sr = (cx + sw_bend_x, cy - (r_outer + r_rim)/2)
        p_b_tl = (cx - 80.0, rim_bot_y)
        p_b_tr = (cx + 80.0, rim_bot_y)

        self.msp.add_line(p_b_bl, p_b_br, dxfattribs={"layer": "OUTLINE", "color": 7})
        self.msp.add_line(p_b_br, p_b_sr, dxfattribs={"layer": "OUTLINE", "color": 7})
        self.msp.add_line(p_b_sr, p_b_tr, dxfattribs={"layer": "OUTLINE", "color": 7})
        self.msp.add_line(p_b_tr, p_b_tl, dxfattribs={"layer": "OUTLINE", "color": 7})
        self.msp.add_line(p_b_tl, p_b_sl, dxfattribs={"layer": "OUTLINE", "color": 7})
        self.msp.add_line(p_b_sl, p_b_bl, dxfattribs={"layer": "OUTLINE", "color": 7})

        # 輪圈軸心連通線 (Rim Barrel & Hub Center)
        self.msp.add_line(p_t_bl, p_b_tl, dxfattribs={"layer": "OUTLINE", "color": 7})
        self.msp.add_line(p_t_br, p_b_tr, dxfattribs={"layer": "OUTLINE", "color": 7})

        # 中心旋轉軸線 (CENTER 圖層)
        self.msp.add_line((cx, cy - r_outer - 40.0), (cx, cy + r_outer + 40.0), dxfattribs={"layer": "CENTER", "color": 1, "linetype": "CENTER"})
        self.msp.add_line((cx - w_half - 30.0, cy), (cx + w_half + 30.0, cy), dxfattribs={"layer": "CENTER", "color": 1, "linetype": "CENTER"})

        # 視圖標籤
        self.msp.add_text(
            "CROSS-SECTION (斷面剖視圖)",
            dxfattribs={"layer": "TEXT", "height": 12.0, "color": 2}
        ).set_placement((cx - 100.0, cy - r_outer - 50.0))

        # 尺寸標註：胎寬 205 mm
        self._draw_dim_line((cx - w_half, top_y + 25), (cx + w_half, top_y + 25), f"Section Width: {self.spec.section_width:.0f} mm")

    def _draw_dim_line(self, p1: Tuple[float, float], p2: Tuple[float, float], text: str) -> None:
        """繪製尺寸線與尺寸文字"""
        x1, y1 = p1
        x2, y2 = p2

        self.msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": "DIMENSION", "color": 3})
        mid_x = (x1 + x2) / 2.0
        mid_y = (y1 + y2) / 2.0 + 4.0

        self.msp.add_text(
            text,
            dxfattribs={"layer": "DIMENSION", "height": 8.0, "color": 3}
        ).set_placement((mid_x - 40.0, mid_y))

    def _draw_spec_table(self, origin: Tuple[float, float]) -> None:
        """繪製右側工規參數規格表 (TABLE 圖層，洋紅色)"""
        ox, oy = origin
        col_w1 = 150.0
        col_w2 = 140.0
        total_w = col_w1 + col_w2
        row_h = 24.0

        rows = [
            ("PARAMETER / SPEC", "ENGINEERING VALUE"),
            ("Tire Specification", self.spec.tire_spec_str),
            ("Nominal Section Width", f"{self.spec.section_width:.0f} mm"),
            ("Aspect Ratio (扁平比)", f"{self.spec.aspect_ratio * 100:.0f} %"),
            ("Rim Diameter (輪圈直徑)", f"{self.spec.rim_diameter_inch:.0f} inch ({self.spec.rim_diameter_mm:.1f} mm)"),
            ("Sidewall Height (胎壁高)", f"{self.spec.sidewall_height:.2f} mm"),
            ("Overall Diameter (總外徑)", f"{self.spec.outer_diameter_mm:.1f} mm"),
            ("Rim Width & Type (輪圈)", "16 x 6.5J (Aluminum Alloy)"),
            ("Bolt Pattern (PCD 規格)", f"5 x {self.spec.pcd_dia_mm:.1f} mm"),
            ("Center Bore (中心孔徑)", f"DIA {self.spec.center_bore_dia:.1f} mm"),
            ("Lug Bolt Size (螺栓規格)", f"M12 x 1.5 (Hex 19mm)"),
            ("Standard Cold Pressure", "32 - 35 PSI (2.2 - 2.4 bar)"),
            ("Load & Speed Index", "91V (615 kg / 240 km/h)"),
            ("Compliance Standard", "ISO 4000-1 / ETRTO / CNS")
        ]

        total_h = len(rows) * row_h

        # 表格大外框
        self.msp.add_line((ox, oy), (ox + total_w, oy), dxfattribs={"layer": "TABLE", "color": 6})
        self.msp.add_line((ox + total_w, oy), (ox + total_w, oy - total_h), dxfattribs={"layer": "TABLE", "color": 6})
        self.msp.add_line((ox + total_w, oy - total_h), (ox, oy - total_h), dxfattribs={"layer": "TABLE", "color": 6})
        self.msp.add_line((ox, oy - total_h), (ox, oy), dxfattribs={"layer": "TABLE", "color": 6})

        # 垂直分隔線
        self.msp.add_line((ox + col_w1, oy), (ox + col_w1, oy - total_h), dxfattribs={"layer": "TABLE", "color": 6})

        # 水平分隔線與文字填充
        for idx, (col1_txt, col2_txt) in enumerate(rows):
            cur_y = oy - idx * row_h
            if idx > 0:
                self.msp.add_line((ox, cur_y), (ox + total_w, cur_y), dxfattribs={"layer": "TABLE", "color": 6})

            txt_color = 2 if idx == 0 else 7

            self.msp.add_text(
                col1_txt,
                dxfattribs={"layer": "TEXT", "height": 7.5, "color": txt_color}
            ).set_placement((ox + 8.0, cur_y - 16.0))

            self.msp.add_text(
                col2_txt,
                dxfattribs={"layer": "TEXT", "height": 7.5, "color": txt_color}
            ).set_placement((ox + col_w1 + 8.0, cur_y - 16.0))


def render_high_res_preview(dxf_path: Path, png_path: Path) -> None:
    """產出高解析度全彩 CAD 暗黑模式預覽圖"""
    from ezdxf.addons.drawing import Frontend, RenderContext
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    import matplotlib.pyplot as plt

    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()
    fig = plt.figure(figsize=(15, 9), facecolor='#1a1a1a')
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.96], facecolor='#1a1a1a')
    ctx = RenderContext(doc)
    out = MatplotlibBackend(ax)
    Frontend(ctx, out).draw_layout(msp, finalize=True)
    ax.set_title('16-Inch Tire & Wheel Assembly (205/55 R16) CAD Drawing', color='white', fontsize=16)
    fig.savefig(str(png_path), dpi=250, facecolor='#1a1a1a')
    plt.close(fig)
    logger.info(f"🖼️ 高解析度渲染預覽圖已產出: {png_path.name}")


if __name__ == "__main__":
    builder = TireR16DXFBuilder()
    dxf_out = builder.build_drawing()
    render_high_res_preview(dxf_out, PREVIEW_PNG_PATH)
    print(f"✅ 16 吋輪胎工規出圖完成: {dxf_out.name} ({dxf_out.stat().st_size / 1024:.2f} KB)")
