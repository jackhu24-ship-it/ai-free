#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 工規 CAD 實戰模組：標準 A3 橫式工程圖紙配置版面 (cad_layout_template.py)
作者：🛠️ 小開 (Agent_Coder)
審查：🐎 小馬 (Agent_Reviewer)
統籌：👑 小幫手 (Agent_PM)

核心功能：
1. 建立標準「圖紙空間 (Paper Space / Layout1 配置)」版面 (A3 橫式: 420mm x 297mm)
2. 繪製工規外圖框、內圖框與標準右下角「工程標題欄 (Title Block)」
3. 建立動態視埠 (Viewport)，自動將模型空間 (Model Space) 的輪胎圖面縮放映照至 A3 圖紙中央
4. 當 AutoCAD 開啟此檔案時，預設直接進入「標準圖紙版面」，一秒看見完整工規出圖排版！
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

LAYOUT_DXF_PATH = DATA_DIR / "tire_r16_a3_layout.dxf"
PREVIEW_LAYOUT_PNG = DATA_DIR / "tire_r16_a3_layout_preview.png"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [CADLayout] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("CADLayout")


class A3EngineeringLayoutBuilder:
    """A3 橫式標準工程圖框與配置版面建置器"""

    def __init__(self) -> None:
        # 使用 R2018 DXF 支援現代完整 Layout 與 Viewport
        self.doc = ezdxf.new("R2018", setup=True)
        self.msp = self.doc.modelspace()
        self._init_standard_layers()

    def _init_standard_layers(self) -> None:
        """建立標準圖層"""
        layers_config = [
            ("BORDER", 7, "Continuous"),      # 圖框線 (白/黑)
            ("TITLE_BLOCK", 4, "Continuous"), # 標題欄 (青色 Cyan)
            ("VIEWPORT", 6, "Continuous"),    # 視埠框 (洋紅)
            ("OUTLINE", 7, "Continuous"),     # 模型輪廓 (白)
            ("CENTER", 1, "CENTER"),          # 中心線 (紅)
            ("HIDDEN", 2, "HIDDEN"),          # 隱藏線 (黃)
            ("DIMENSION", 3, "Continuous"),   # 尺寸 (綠)
            ("TEXT", 2, "Continuous"),        # 文字 (黃)
            ("TABLE", 6, "Continuous")        # 表格 (洋紅)
        ]
        for name, color, linetype in layers_config:
            if name not in self.doc.layers:
                self.doc.layers.add(name=name, color=color, linetype=linetype)

    def build_layout_drawing(self, output_path: Optional[Path | str] = None) -> Path:
        """建構包含模型實體與 A3 標準配置版面的圖紙"""
        target_path = Path(output_path) if output_path else LAYOUT_DXF_PATH

        # 1. 在模型空間 (Model Space) 繪製輪胎雙視圖與規格表
        self._draw_model_entities()

        # 2. 在圖紙空間 (Layout1 配置) 建立 A3 橫式典型版面
        self._setup_a3_paper_layout()

        # 3. 儲存 DXF
        self.doc.saveas(target_path, encoding="utf-8")
        logger.info(f"📐 標準 A3 配置版面圖紙成功產出: {target_path.name}")
        return target_path

    def _draw_model_entities(self) -> None:
        """在模型空間繪製 1:1 輪胎圖元"""
        # 輪胎正面中心 (400, 450)
        cx, cy = 400.0, 450.0
        r_outer = 631.9 / 2.0  # 316.0 mm
        r_rim = 406.4 / 2.0    # 203.2 mm

        # 外圓與輪圈
        self.msp.add_circle((cx, cy), radius=r_outer, dxfattribs={"layer": "OUTLINE", "color": 7})
        self.msp.add_circle((cx, cy), radius=r_outer - 10.0, dxfattribs={"layer": "OUTLINE", "color": 7})
        self.msp.add_circle((cx, cy), radius=r_rim + 12.0, dxfattribs={"layer": "OUTLINE", "color": 7})
        self.msp.add_circle((cx, cy), radius=r_rim, dxfattribs={"layer": "OUTLINE", "color": 7})
        self.msp.add_circle((cx, cy), radius=50.0, dxfattribs={"layer": "OUTLINE", "color": 7})
        self.msp.add_circle((cx, cy), radius=30.0, dxfattribs={"layer": "OUTLINE", "color": 7})

        # 36 導水花紋
        for i in range(36):
            rad = math.radians(i * 10)
            x1 = cx + (r_outer - 10.0) * math.cos(rad)
            y1 = cy + (r_outer - 10.0) * math.sin(rad)
            x2 = cx + r_outer * math.cos(rad + 0.05)
            y2 = cy + r_outer * math.sin(rad + 0.05)
            self.msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": "OUTLINE", "color": 7})

        # 五輻輪輻
        for i in range(5):
            deg = i * 72 + 90
            rad = math.radians(deg)
            p_hub = (cx + 50.0 * math.cos(rad), cy + 50.0 * math.sin(rad))
            p_rim = (cx + (r_rim - 10.0) * math.cos(rad), cy + (r_rim - 10.0) * math.sin(rad))
            self.msp.add_line(p_hub, p_rim, dxfattribs={"layer": "OUTLINE", "color": 7})

        # PCD 螺栓圓
        pcd_r = 114.3 / 2.0
        self.msp.add_circle((cx, cy), radius=pcd_r, dxfattribs={"layer": "CENTER", "color": 1, "linetype": "CENTER"})
        for i in range(5):
            deg = i * 72 + 90
            bx = cx + pcd_r * math.cos(math.radians(deg))
            by = cy + pcd_r * math.sin(math.radians(deg))
            self.msp.add_circle((bx, by), radius=7.0, dxfattribs={"layer": "OUTLINE", "color": 7})

        # 十字中心線
        self.msp.add_line((cx - r_outer - 30, cy), (cx + r_outer + 30, cy), dxfattribs={"layer": "CENTER", "color": 1, "linetype": "CENTER"})
        self.msp.add_line((cx, cy - r_outer - 30), (cx, cy + r_outer + 30), dxfattribs={"layer": "CENTER", "color": 1, "linetype": "CENTER"})

        # 斷面剖面圖 (850, 450)
        sx, sy = 850.0, 450.0
        hw = 205.0 / 2.0
        # 繪製剖面框
        self.msp.add_lwpolyline(
            [(sx - hw, sy + r_outer), (sx + hw, sy + r_outer), (sx + hw + 10, sy + r_rim), (sx - hw - 10, sy + r_rim)],
            close=True,
            dxfattribs={"layer": "OUTLINE", "color": 7}
        )
        self.msp.add_lwpolyline(
            [(sx - hw, sy - r_outer), (sx + hw, sy - r_outer), (sx + hw + 10, sy - r_rim), (sx - hw - 10, sy - r_rim)],
            close=True,
            dxfattribs={"layer": "OUTLINE", "color": 7}
        )
        self.msp.add_line((sx, sy - r_outer - 30), (sx, sy + r_outer + 30), dxfattribs={"layer": "CENTER", "color": 1, "linetype": "CENTER"})

        # 右側工規規格表 (1080, 750)
        tx, ty = 1080.0, 750.0
        tw, th = 260.0, 320.0
        self.msp.add_lwpolyline([(tx, ty), (tx + tw, ty), (tx + tw, ty - th), (tx, ty - th)], close=True, dxfattribs={"layer": "TABLE", "color": 6})
        self.msp.add_line((tx + 130.0, ty), (tx + 130.0, ty - th), dxfattribs={"layer": "TABLE", "color": 6})

        rows = [
            ("SPECIFICATION", "205/55 R16 91V"),
            ("SECTION WIDTH", "205 mm"),
            ("ASPECT RATIO", "55 %"),
            ("RIM DIAMETER", "16 inch (406.4 mm)"),
            ("OVERALL DIA", "631.9 mm"),
            ("BOLT PATTERN", "5 x 114.3 mm"),
            ("STANDARD PSI", "32 - 35 PSI")
        ]
        for idx, (c1, c2) in enumerate(rows):
            ly = ty - (idx + 1) * 40.0
            self.msp.add_line((tx, ly), (tx + tw, ly), dxfattribs={"layer": "TABLE", "color": 6})
            self.msp.add_text(c1, dxfattribs={"layer": "TEXT", "height": 8.0, "color": 2}).set_placement((tx + 8.0, ly + 14.0))
            self.msp.add_text(c2, dxfattribs={"layer": "TEXT", "height": 8.0, "color": 7}).set_placement((tx + 138.0, ly + 14.0))

    def _setup_a3_paper_layout(self) -> None:
        """建立 A3 橫式 (420 x 297 mm) 標準圖紙空間版面"""
        layout_name = "A3_標準工程版面"
        if layout_name in self.doc.layouts:
            layout = self.doc.layouts.get(layout_name)
        else:
            layout = self.doc.layouts.new(layout_name)

        # 1. 繪製 A3 紙張外邊界 (420 x 297 mm)
        layout.add_lwpolyline([(0, 0), (420, 0), (420, 297), (0, 297)], close=True, dxfattribs={"layer": "BORDER", "color": 7})

        # 2. 繪製 A3 工規內圖框 (留邊界: 左 20mm 裝訂邊，上右下各 10mm ➔ 400 x 277 mm)
        p_bl = (20.0, 10.0)
        p_br = (410.0, 10.0)
        p_tr = (410.0, 287.0)
        p_tl = (20.0, 287.0)
        layout.add_lwpolyline([p_bl, p_br, p_tr, p_tl], close=True, dxfattribs={"layer": "BORDER", "color": 7})

        # 3. 繪製右下角標準工程標題欄 (Title Block: 150mm x 45mm)
        tb_x = 260.0
        tb_y = 10.0
        tb_w = 150.0
        tb_h = 45.0

        layout.add_lwpolyline(
            [(tb_x, tb_y), (tb_x + tb_w, tb_y), (tb_x + tb_w, tb_y + tb_h), (tb_x, tb_y + tb_h)],
            close=True,
            dxfattribs={"layer": "TITLE_BLOCK", "color": 4}
        )

        # 標題欄內部網格與文字
        layout.add_line((tb_x, tb_y + 30.0), (tb_x + tb_w, tb_y + 30.0), dxfattribs={"layer": "TITLE_BLOCK", "color": 4})
        layout.add_line((tb_x, tb_y + 15.0), (tb_x + tb_w, tb_y + 15.0), dxfattribs={"layer": "TITLE_BLOCK", "color": 4})
        layout.add_line((tb_x + 75.0, tb_y), (tb_x + 75.0, tb_y + 30.0), dxfattribs={"layer": "TITLE_BLOCK", "color": 4})

        # 標題欄文字 (Text)
        layout.add_text("專案: Five-Agent AI OS 機械工程", dxfattribs={"layer": "TEXT", "height": 3.0, "color": 7}).set_placement((tb_x + 5.0, tb_y + 36.0))
        layout.add_text("圖名: 16吋標準輪胎與鋁圈組", dxfattribs={"layer": "TEXT", "height": 3.5, "color": 2}).set_placement((tb_x + 5.0, tb_y + 20.0))
        layout.add_text("圖號: DWG-TIRE-2026-R16", dxfattribs={"layer": "TEXT", "height": 2.8, "color": 7}).set_placement((tb_x + 80.0, tb_y + 20.0))
        layout.add_text("比例: 1:4  |  單位: mm", dxfattribs={"layer": "TEXT", "height": 2.8, "color": 7}).set_placement((tb_x + 5.0, tb_y + 5.0))
        layout.add_text("繪圖: Agent_Coder (小開)", dxfattribs={"layer": "TEXT", "height": 2.8, "color": 7}).set_placement((tb_x + 80.0, tb_y + 5.0))

        # 4. 建立圖紙空間動態視埠 (Viewport)
        # 視埠放置於圖紙主要區域 (X: 25~405, Y: 60~282 ➔ 中心 215, 171, 寬 380, 高 210)
        vp = layout.add_viewport(
            center=(215.0, 171.0),
            size=(380.0, 210.0),
            view_center_point=(700.0, 450.0),  # 模型空間中點 (輪胎與規格表中點)
            view_height=850.0,                 # 模型空間可視高度 (自動縮放填滿)
            status=2,                          # 啟用視埠
            dxfattribs={"layer": "VIEWPORT", "color": 6}
        )

        # 將此 Layout 設為開檔預設顯示版面
        self.doc.layouts.set_active_layout("A3_標準工程版面")


def render_a3_layout_preview(dxf_path: Path, png_path: Path) -> None:
    """渲染 A3 配置版面預覽圖"""
    from ezdxf.addons.drawing import Frontend, RenderContext
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    import matplotlib.pyplot as plt

    doc = ezdxf.readfile(str(dxf_path))
    # 渲染 A3 標準工程版面
    layout = doc.layouts.get("A3_標準工程版面")
    fig = plt.figure(figsize=(14, 10), facecolor='#2b2b2b')
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.96], facecolor='#2b2b2b')
    ctx = RenderContext(doc)
    out = MatplotlibBackend(ax)
    Frontend(ctx, out).draw_layout(layout, finalize=True)
    ax.set_title('A3 Engineering Layout & Title Block Preview', color='white', fontsize=15)
    fig.savefig(str(png_path), dpi=250, facecolor='#2b2b2b')
    plt.close(fig)
    logger.info(f"🖼️ A3 標準圖紙版面預覽圖已產出: {png_path.name}")


if __name__ == "__main__":
    builder = A3EngineeringLayoutBuilder()
    dxf_out = builder.build_layout_drawing()
    render_a3_layout_preview(dxf_out, PREVIEW_LAYOUT_PNG)
    print(f"✅ A3 標準圖紙版面出圖完成: {dxf_out.name} ({dxf_out.stat().st_size / 1024:.2f} KB)")
