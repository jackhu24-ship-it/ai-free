#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 桌面 CAD 即時檢視器 (cad_viewer_gui.py)
作者：🛠️ 小開 (Agent_Coder)
審查：🐎 小馬 (Agent_Reviewer)
統籌：👑 小幫手 (Agent_PM)

功能：
1. 直接在桌面開啟獨立 CAD 圖紙檢視器視窗 (免開 AutoCAD 也能直接看圖)
2. 顯示 M12 六角螺帽俯視圖、正視圖、尺寸標註與右側工規規格表
3. 支援滑鼠滾輪縮放、拖曳平移與一鍵全圖置中
"""

from __future__ import annotations

import sys
import os
import math
from pathlib import Path

# 強制 Windows 標準輸出為 UTF-8
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = WORKSPACE_ROOT / "DATA"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PREVIEW_PNG = DATA_DIR / "hex_nut_m12_preview.png"
DXF_FILE = DATA_DIR / "hex_nut_m12.dxf"


def ensure_preview_exists() -> None:
    """確保渲染預覽圖存在"""
    if not PREVIEW_PNG.exists() or PREVIEW_PNG.stat().st_size == 0:
        import ezdxf
        from ezdxf.addons.drawing import Frontend, RenderContext
        from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
        import matplotlib.pyplot as plt

        doc = ezdxf.readfile(str(DXF_FILE))
        msp = doc.modelspace()
        fig = plt.figure(figsize=(14, 8), facecolor='#1e1e1e')
        ax = fig.add_axes([0.05, 0.05, 0.9, 0.9], facecolor='#1e1e1e')
        ctx = RenderContext(doc)
        out = MatplotlibBackend(ax)
        Frontend(ctx, out).draw_layout(msp, finalize=True)
        ax.set_title('AutoCAD M12 Hex Nut Drawing Preview', color='white', fontsize=16)
        fig.savefig(str(PREVIEW_PNG), dpi=250, facecolor='#1e1e1e')
        plt.close(fig)


class CADViewerGUI:
    """AutoCAD 圖紙桌面即時檢視視窗"""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("📐 AutoCAD M12 標準六角螺帽工規圖紙即時檢視器 (Five-Agent AI OS)")
        self.root.geometry("1100x720")
        self.root.minsize(800, 500)
        self.root.configure(bg="#1E1E1E")

        self.zoom_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.orig_image: Image.Image | None = None
        self.tk_image: ImageTk.PhotoImage | None = None

        self._build_ui()
        ensure_preview_exists()
        self._load_cad_preview()

        # 延遲 150ms 待視窗大小確定後執行首次全圖置中
        self.root.after(150, self.reset_view)

    def _build_ui(self) -> None:
        # 1. 頂部控制列
        top_bar = tk.Frame(self.root, bg="#2D3748", padx=15, pady=10)
        top_bar.pack(fill="x")

        title_lbl = tk.Label(
            top_bar,
            text="🔩 M12 標準六角螺帽 (ISO 4032 / CNS) 工規圖面",
            font=("微軟正黑體", 14, "bold"),
            fg="#63B3ED",
            bg="#2D3748"
        )
        title_lbl.pack(side="left")

        # 縮放與重置按鈕
        btn_reset = tk.Button(
            top_bar,
            text="🎯 全圖置中 (Zoom Extents)",
            font=("微軟正黑體", 10, "bold"),
            bg="#3182CE",
            fg="white",
            padx=10,
            command=self.reset_view
        )
        btn_reset.pack(side="right", padx=6)

        btn_zoom_in = tk.Button(
            top_bar,
            text="🔍 放大 (+)",
            font=("微軟正黑體", 10),
            bg="#4A5568",
            fg="white",
            padx=8,
            command=lambda: self.adjust_zoom(1.2)
        )
        btn_zoom_in.pack(side="right", padx=4)

        btn_zoom_out = tk.Button(
            top_bar,
            text="🔍 縮小 (-)",
            font=("微軟正黑體", 10),
            bg="#4A5568",
            fg="white",
            padx=8,
            command=lambda: self.adjust_zoom(0.8)
        )
        btn_zoom_out.pack(side="right", padx=4)

        # 2. 中央 CAD 畫布 (暗色背景)
        canvas_frame = tk.Frame(self.root, bg="#1E1E1E")
        canvas_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg="#1E1E1E", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # 綁定滑鼠滾輪與拖曳事件
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_motion)
        self.root.bind("<Configure>", self._on_window_resize)

        # 3. 底部狀態列
        bottom_bar = tk.Frame(self.root, bg="#2D3748", padx=15, pady=6)
        bottom_bar.pack(fill="x")

        status_lbl = tk.Label(
            bottom_bar,
            text="💡 操作提示：滑鼠滾輪可直接放大/縮小，按住滑鼠左鍵可拖曳移動 ｜ 實體檔案：DATA/hex_nut_m12.dxf",
            font=("微軟正黑體", 9),
            fg="#E2E8F0",
            bg="#2D3748"
        )
        status_lbl.pack(side="left")

    def _load_cad_preview(self) -> None:
        """載入渲染預覽圖"""
        if PREVIEW_PNG.exists():
            self.orig_image = Image.open(PREVIEW_PNG)
        else:
            messagebox.showerror("錯誤", "找不到圖紙預覽圖！")

    def reset_view(self) -> None:
        """全圖置中重置"""
        if not self.orig_image:
            return
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw <= 10:
            cw = 1050
        if ch <= 10:
            ch = 620

        iw, ih = self.orig_image.size
        scale_w = cw / iw
        scale_h = ch / ih
        self.zoom_factor = min(scale_w, scale_h) * 0.95
        self.pan_x = (cw - iw * self.zoom_factor) / 2
        self.pan_y = (ch - ih * self.zoom_factor) / 2
        self._render_image()

    def adjust_zoom(self, factor: float) -> None:
        """調整縮放"""
        self.zoom_factor *= factor
        self._render_image()

    def _render_image(self) -> None:
        """重繪影像至畫布"""
        if not self.orig_image:
            return
        iw, ih = self.orig_image.size
        new_w = max(10, int(iw * self.zoom_factor))
        new_h = max(10, int(ih * self.zoom_factor))

        resized = self.orig_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized)

        self.canvas.delete("all")
        self.canvas.create_image(self.pan_x, self.pan_y, anchor="nw", image=self.tk_image)

    def _on_mousewheel(self, event: tk.Event) -> None:
        """滑鼠滾輪縮放"""
        if event.delta > 0:
            self.adjust_zoom(1.15)
        else:
            self.adjust_zoom(0.85)

    def _on_drag_start(self, event: tk.Event) -> None:
        """開始拖曳"""
        self._drag_data_x = event.x
        self._drag_data_y = event.y

    def _on_drag_motion(self, event: tk.Event) -> None:
        """拖曳平移"""
        dx = event.x - self._drag_data_x
        dy = event.y - self._drag_data_y
        self.pan_x += dx
        self.pan_y += dy
        self._drag_data_x = event.x
        self._drag_data_y = event.y
        self._render_image()

    def _on_window_resize(self, event: tk.Event) -> None:
        pass


def launch_viewer() -> None:
    root = tk.Tk()
    app = CADViewerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch_viewer()
