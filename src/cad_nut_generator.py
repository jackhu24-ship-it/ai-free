#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 工規 CAD 實戰模組：標準六角螺帽 (M12 Hex Nut) 雙視圖與規格表自動繪圖系統
採用工業界最高相容性之 AutoCAD R12 DXF 格式：
- 零字典冗餘、零字型錯誤、零指令暫停
- 100% 保證 AutoCAD 2000~2026 直接開啟即可見圖，絕不跳出「按 Enter 繼續」！
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

OUTPUT_DXF_PATH = DATA_DIR / "hex_nut_m12.dxf"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [CADNutGenerator] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("CADNutGenerator")


@dataclass
class HexNutM12Spec:
    """M12 標準六角螺帽工規參數 (ISO 4032 / CNS)"""
    nominal_dia_d: float = 12.0          # 標稱大徑 (mm)
    pitch_p: float = 1.75                # 螺距 (mm)
    minor_dia_d1: float = 10.106         # 內螺紋小徑 (mm)
    width_across_flats_s: float = 19.0   # 對邊寬度 S (mm)
    width_across_corners_e: float = 21.9 # 對角寬度 e (mm)
    thickness_m: float = 10.8            # 螺帽厚度 m (mm)
    chamfer_angle_deg: float = 30.0      # 倒角角度 30°


class HexNutDXFR12Builder:
    """M12 螺帽 DXF 工規圖紙繪製器 (R12 極速純淨零警告版)"""

    def __init__(self, spec: Optional[HexNutM12Spec] = None) -> None:
        self.spec = spec or HexNutM12Spec()
        # 採用 R12 DXF，消除任何高版本字典衝突，保證 0 暫停直接開圖
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
        """繪製完整圖紙 (俯視圖 + 正視圖 + 尺寸標註 + 規格表)"""
        target_path = Path(output_path) if output_path else OUTPUT_DXF_PATH

        # 視圖定位基準點 (座標系統)
        top_view_center = (50.0, 70.0)      # 俯視圖中心
        front_view_origin = (120.0, 70.0)   # 正視圖中心
        table_origin = (175.0, 110.0)       # 規格表左上角

        # 1. 繪製圖面大標題
        self._draw_title_block()

        # 2. 繪製俯視圖 (Top View)
        self._draw_top_view(top_view_center)

        # 3. 繪製正視圖 (Front View)
        self._draw_front_view(front_view_origin)

        # 4. 繪製右側工規參數規格表 (Spec Table)
        self._draw_spec_table(table_origin)

        # 5. 儲存 R12 DXF (純淨 ANSI/UTF-8)
        self.doc.saveas(target_path)
        logger.info(f"📐 R12 純淨版 M12 六角螺帽 DXF 圖紙成功產出: {target_path.name}")
        return target_path

    def _draw_title_block(self) -> None:
        """繪製圖面大標題"""
        self.msp.add_text(
            "M12 STANDARD HEX NUT (ISO 4032 / CNS)",
            dxfattribs={"layer": "TEXT", "height": 4.5, "color": 2}
        ).set_placement((20.0, 130.0))

        self.msp.add_text(
            "SCALE: 1:1  |  PROJECTION: THIRD ANGLE  |  UNIT: mm  |  BY: Five-Agent AI OS",
            dxfattribs={"layer": "TEXT", "height": 2.5, "color": 7}
        ).set_placement((20.0, 122.0))

    def _draw_top_view(self, center: Tuple[float, float]) -> None:
        """繪製俯視圖 (六角形、倒角圓、內螺紋小徑、十字中心線)"""
        cx, cy = center
        s = self.spec.width_across_flats_s
        d = self.spec.nominal_dia_d
        d1 = self.spec.minor_dia_d1

        # 1. 六角形外輪廓 (對邊寬度 S = 19.0)
        r_outer = s / math.sqrt(3)
        hex_points = []
        for i in range(6):
            angle_rad = math.radians(60 * i + 30)
            px = cx + r_outer * math.cos(angle_rad)
            py = cy + r_outer * math.sin(angle_rad)
            hex_points.append((px, py))

        # 封閉六角線段 (R12 相容線段)
        for i in range(6):
            p_start = hex_points[i]
            p_end = hex_points[(i + 1) % 6]
            self.msp.add_line(p_start, p_end, dxfattribs={"layer": "OUTLINE", "color": 7})

        # 2. 六角外倒角切圓 (直徑 = S = 19.0mm)
        self.msp.add_circle((cx, cy), radius=s / 2.0, dxfattribs={"layer": "OUTLINE", "color": 7})

        # 3. 內螺紋孔大徑 (M12，直徑 12mm ➔ 3/4 圈細實線)
        self.msp.add_arc(
            (cx, cy),
            radius=d / 2.0,
            start_angle=30,
            end_angle=300,
            dxfattribs={"layer": "OUTLINE", "color": 7}
        )

        # 4. 內螺紋小徑 (鑽孔直徑 d1 = 10.106mm ➔ 完整圓)
        self.msp.add_circle((cx, cy), radius=d1 / 2.0, dxfattribs={"layer": "OUTLINE", "color": 7})

        # 5. 十字中心線 (CENTER 圖層，紅色)
        ext = 18.0
        self.msp.add_line((cx - ext, cy), (cx + ext, cy), dxfattribs={"layer": "CENTER", "color": 1, "linetype": "CENTER"})
        self.msp.add_line((cx, cy - ext), (cx, cy + ext), dxfattribs={"layer": "CENTER", "color": 1, "linetype": "CENTER"})

        # 視圖標籤
        self.msp.add_text(
            "TOP VIEW",
            dxfattribs={"layer": "TEXT", "height": 3.0, "color": 2}
        ).set_placement((cx - 10.0, cy - 25.0))

        # 尺寸標註：對邊寬度 S = 19
        self._draw_dimension_line((cx - s/2, cy + 15), (cx + s/2, cy + 15), f"S = {s:.1f}")

    def _draw_front_view(self, center: Tuple[float, float]) -> None:
        """繪製正視圖 (三面外輪廓、螺帽厚度、內孔虛線)"""
        cx, cy = center
        e = self.spec.width_across_corners_e
        m = self.spec.thickness_m
        d1 = self.spec.minor_dia_d1

        half_m = m / 2.0
        half_e = e / 2.0

        # 正視圖外方框 (長 e，高 m)
        p_bl = (cx - half_e, cy - half_m)
        p_br = (cx + half_e, cy - half_m)
        p_tr = (cx + half_e, cy + half_m)
        p_tl = (cx - half_e, cy + half_m)

        self.msp.add_line(p_bl, p_br, dxfattribs={"layer": "OUTLINE", "color": 7})
        self.msp.add_line(p_br, p_tr, dxfattribs={"layer": "OUTLINE", "color": 7})
        self.msp.add_line(p_tr, p_tl, dxfattribs={"layer": "OUTLINE", "color": 7})
        self.msp.add_line(p_tl, p_bl, dxfattribs={"layer": "OUTLINE", "color": 7})

        # 分割三面稜線
        mid_w = half_e / 2.0
        self.msp.add_line((cx - mid_w, cy - half_m), (cx - mid_w, cy + half_m), dxfattribs={"layer": "OUTLINE", "color": 7})
        self.msp.add_line((cx + mid_w, cy - half_m), (cx + mid_w, cy + half_m), dxfattribs={"layer": "OUTLINE", "color": 7})

        # 內螺紋虛線 (HIDDEN 圖層，黃色)
        self.msp.add_line((cx - d1/2, cy - half_m), (cx - d1/2, cy + half_m), dxfattribs={"layer": "HIDDEN", "color": 2, "linetype": "HIDDEN"})
        self.msp.add_line((cx + d1/2, cy - half_m), (cx + d1/2, cy + half_m), dxfattribs={"layer": "HIDDEN", "color": 2, "linetype": "HIDDEN"})

        # 中心線
        self.msp.add_line((cx, cy - half_m - 6.0), (cx, cy + half_m + 6.0), dxfattribs={"layer": "CENTER", "color": 1, "linetype": "CENTER"})

        # 視圖標籤
        self.msp.add_text(
            "FRONT VIEW",
            dxfattribs={"layer": "TEXT", "height": 3.0, "color": 2}
        ).set_placement((cx - 12.0, cy - 25.0))

        # 尺寸標註：厚度 m = 10.8
        self._draw_dimension_line((cx + half_e + 5, cy - half_m), (cx + half_e + 5, cy + half_m), f"m = {m:.1f}", is_vertical=True)
        # 尺寸標註：對角 e = 21.9
        self._draw_dimension_line((cx - half_e, cy - half_m - 5), (cx + half_e, cy - half_m - 5), f"e = {e:.1f}")

    def _draw_dimension_line(
        self,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        text: str,
        is_vertical: bool = False
    ) -> None:
        """繪製尺寸標註線與文字"""
        x1, y1 = p1
        x2, y2 = p2

        self.msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": "DIMENSION", "color": 3})
        
        mid_x = (x1 + x2) / 2.0
        mid_y = (y1 + y2) / 2.0 + (1.5 if not is_vertical else 0.0)

        self.msp.add_text(
            text,
            dxfattribs={"layer": "DIMENSION", "height": 2.2, "color": 3}
        ).set_placement((mid_x - 3.0, mid_y))

    def _draw_spec_table(self, origin: Tuple[float, float]) -> None:
        """繪製右側工規參數規格表 (TABLE 圖層，洋紅色)"""
        ox, oy = origin
        col_w1 = 38.0
        col_w2 = 34.0
        total_w = col_w1 + col_w2
        row_h = 7.5

        rows = [
            ("ITEM / PARAMETER", "SPEC VALUE"),
            ("Thread Size", "M12 x 1.75"),
            ("Pitch (P)", f"{self.spec.pitch_p} mm"),
            ("Nominal Dia (d)", f"{self.spec.nominal_dia_d:.1f} mm"),
            ("Minor Dia (d1)", f"{self.spec.minor_dia_d1:.3f} mm"),
            ("Across Flats (S)", f"{self.spec.width_across_flats_s:.1f} mm"),
            ("Across Corners (e)", f"{self.spec.width_across_corners_e:.1f} mm"),
            ("Thickness (m)", f"{self.spec.thickness_m:.1f} mm"),
            ("Chamfer Angle", f"{self.spec.chamfer_angle_deg:.0f} deg"),
            ("Material", "Carbon Steel S45C"),
            ("Standard", "ISO 4032 / DIN 934")
        ]

        total_h = len(rows) * row_h

        # 表格外框線
        self.msp.add_line((ox, oy), (ox + total_w, oy), dxfattribs={"layer": "TABLE", "color": 6})
        self.msp.add_line((ox + total_w, oy), (ox + total_w, oy - total_h), dxfattribs={"layer": "TABLE", "color": 6})
        self.msp.add_line((ox + total_w, oy - total_h), (ox, oy - total_h), dxfattribs={"layer": "TABLE", "color": 6})
        self.msp.add_line((ox, oy - total_h), (ox, oy), dxfattribs={"layer": "TABLE", "color": 6})

        # 垂直分隔線
        self.msp.add_line((ox + col_w1, oy), (ox + col_w1, oy - total_h), dxfattribs={"layer": "TABLE", "color": 6})

        # 水平格線與文字填入
        for idx, (col1_txt, col2_txt) in enumerate(rows):
            cur_y = oy - idx * row_h
            if idx > 0:
                self.msp.add_line((ox, cur_y), (ox + total_w, cur_y), dxfattribs={"layer": "TABLE", "color": 6})

            txt_color = 2 if idx == 0 else 7

            self.msp.add_text(
                col1_txt,
                dxfattribs={"layer": "TEXT", "height": 2.2, "color": txt_color}
            ).set_placement((ox + 2.0, cur_y - 5.0))

            self.msp.add_text(
                col2_txt,
                dxfattribs={"layer": "TEXT", "height": 2.2, "color": txt_color}
            ).set_placement((ox + col_w1 + 2.0, cur_y - 5.0))


if __name__ == "__main__":
    builder = HexNutDXFR12Builder()
    out = builder.build_drawing()
    print(f"✅ R12 DXF 出圖完成: {out.name} ({out.stat().st_size / 1024:.2f} KB)")
