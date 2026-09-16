#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 【PROJ-20 MCU 遙測與調參儀表板】：mcu_telemetry_dashboard.py
========================================================================================
角色協同：
  - 👁️ 小Ｏ (Agent_Vision)  : 牽頭暗黑工業風介面 (Dark Industrial UI)、Matplotlib 示波器動態繪圖
  - 🛠️ 小開 (Agent_Coder)   : 驅動綁定、EventBus 通訊、波形產生器 (階梯/正弦/方波/過壓脈衝)
  - 🐎 小馬 (Agent_Reviewer): 邊界安全過濾 (0~6.0V)、十進制優先 HUD 審查、CWE-1236 CSV 匯出防護
  - 👑 小幫手 (Agent_PM)    : 全系統作戰調度與狀態總控

技術亮點：
  1. 【暗黑工業風配色】：深灰底 #121212 / 碳黑 #1E1E1E / 示波器綠 #00FF66 / 警戒紅 #FF3333
  2. 【Matplotlib 動態示波器】：5.5V 紅色熔斷警戒線、動態波形繪製、FUSE BLOWN 警示 Overlay
  3. 【十進制優先 HUD】：ADC: 512 (十進制) | 2.50V | 原始碼: 0x0200 (0b001000000000)
  4. 【訊號產生器】：內建 階梯波、正弦波、方波、過壓脈衝 (5.8V 熔斷測試)
  5. 【硬體安全保護】：>5.5V 虛擬保險絲熔斷斷路、一鍵復位、CWE-1236 CSV 報表匯出
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

import time
import math
import json
import asyncio
import collections
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText

# Matplotlib Tkinter Canvas
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# 引入核心橋接引擎
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from event_bus_mcu_bridge import MCUEventBusBridge, ADCTelemetryFrame, sanitize_cell


# ============================================================================
# 視覺調色盤常數 (👁️ 小Ｏ 暗黑工業風)
# ============================================================================
THEME = {
    "bg_main": "#121212",
    "bg_panel": "#1E1E1E",
    "bg_card": "#252526",
    "bg_input": "#2D2D30",
    "fg_text": "#E0E0E0",
    "fg_muted": "#888888",
    "border": "#3E3E42",
    "accent_green": "#00FF66",     # 示波器波形綠
    "accent_red": "#FF3333",       # 熔斷警戒紅
    "accent_cyan": "#00E5FF",      # 科技青 (HUD 強調)
    "accent_amber": "#FFB74D",     # 琥珀黃 (警示)
    "grid_color": "#2A2A2A"
}


# ============================================================================
# 主儀表板應用程式類別 (MCUTelemetryDashboard)
# ============================================================================

class MCUTelemetryDashboard:
    """
    PROJ-20 MCU 即時遙測與調參儀表板
    """

    def __init__(self, root: Optional[tk.Tk] = None):
        self.root = root or tk.Tk()
        self.bridge = MCUEventBusBridge()

        # 波形數據緩衝區 (保存最新 60 點)
        self.buffer_len = 60
        self.time_history = collections.deque(maxlen=self.buffer_len)
        self.volt_history = collections.deque(maxlen=self.buffer_len)
        self.adc_history = collections.deque(maxlen=self.buffer_len)

        for i in range(self.buffer_len):
            self.time_history.append(- (self.buffer_len - i) * 0.05)
            self.volt_history.append(0.0)
            self.adc_history.append(0)

        # 訊號產生器狀態
        self.gen_mode = "manual"  # manual | step | sine | square | pulse
        self.gen_step_index = 0
        self.gen_time = 0.0
        self.timer_running = True
        self.current_channel = 0
        self.current_input_voltage = 2.50

        if root is not None:
            self._setup_window()
            self._setup_styles()
            self._build_ui()
            self._init_plot()
            self._start_update_loop()

    def _setup_window(self):
        """配置主視窗屬性"""
        self.root.title("🚀 Five-Agent AI OS: MCU 數位分身 10-bit ADC 遙測與調參儀表板 (PROJ-20)")
        self.root.geometry("1180x760")
        self.root.minsize(1020, 680)
        self.root.configure(bg=THEME["bg_main"])

    def _setup_styles(self):
        """配置 ttk 暗黑樣式"""
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure("Dark.TFrame", background=THEME["bg_panel"])
        style.configure("Card.TFrame", background=THEME["bg_card"], relief="flat")
        style.configure("Dark.TLabel", background=THEME["bg_panel"], foreground=THEME["fg_text"], font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=THEME["bg_panel"], foreground=THEME["accent_cyan"], font=("Segoe UI", 13, "bold"))
        style.configure("SubTitle.TLabel", background=THEME["bg_card"], foreground=THEME["accent_amber"], font=("Segoe UI", 11, "bold"))

        style.configure("Dark.TButton", background=THEME["bg_input"], foreground=THEME["fg_text"], font=("Segoe UI", 9, "bold"), borderwidth=1)
        style.map("Dark.TButton", background=[("active", "#3E3E42")])

        style.configure("Green.TButton", background="#007A33", foreground="#FFFFFF", font=("Segoe UI", 9, "bold"))
        style.map("Green.TButton", background=[("active", "#009940")])

        style.configure("Red.TButton", background="#991111", foreground="#FFFFFF", font=("Segoe UI", 9, "bold"))
        style.map("Red.TButton", background=[("active", "#CC2222")])

    def _build_ui(self):
        """構建整體 UI 佈局 (左側控制 + 中央示波器 + 右側/下方 HUD)"""
        main_frame = ttk.Frame(self.root, style="Dark.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # 頂部標題列
        header = ttk.Frame(main_frame, style="Dark.TFrame")
        header.pack(fill=tk.X, pady=(0, 10))

        title_lbl = ttk.Label(
            header,
            text="⚡ MCU 數位分身 10-bit ADC 即時遙測示波器與訊號調參系統",
            style="Title.TLabel"
        )
        title_lbl.pack(side=tk.LEFT)

        sub_info = ttk.Label(
            header,
            text="Five-Agent AI OS | 👁️ 小Ｏ 介面 ✕ 🛠️ 小開 驅動 ✕ 🐎 小馬 審查",
            style="Dark.TLabel",
            foreground=THEME["fg_muted"]
        )
        sub_info.pack(side=tk.RIGHT, padx=5)

        # 中間內容區 (左: 控制欄, 右: 示波器與 HUD)
        content_pane = ttk.Frame(main_frame, style="Dark.TFrame")
        content_pane.pack(fill=tk.BOTH, expand=True)

        # ====================================================================
        # 左側控制欄 (340px 寬)
        # ====================================================================
        ctrl_panel = ttk.Frame(content_pane, style="Card.TFrame", width=340)
        ctrl_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        ctrl_panel.pack_propagate(False)

        # 1. 採樣通道設定
        ch_frame = ttk.Frame(ctrl_panel, style="Card.TFrame")
        ch_frame.pack(fill=tk.X, padx=12, pady=(12, 6))
        ttk.Label(ch_frame, text="🎛️ 採樣通道選擇", style="SubTitle.TLabel").pack(anchor=tk.W, pady=(0, 4))
        self.ch_var = tk.StringVar(value="CH0 (AN0 / RA0)")
        ch_combo = ttk.Combobox(
            ch_frame, textvariable=self.ch_var,
            values=["CH0 (AN0 / RA0)", "CH1 (AN1 / RA1)", "CH2 (AN2 / RA2)", "CH3 (AN3 / RA4)"],
            state="readonly"
        )
        ch_combo.pack(fill=tk.X)
        ch_combo.bind("<<ComboboxSelected>>", self._on_channel_change)

        # 2. 模擬輸入電壓滑桿
        slider_frame = ttk.Frame(ctrl_panel, style="Card.TFrame")
        slider_frame.pack(fill=tk.X, padx=12, pady=8)
        
        v_title_box = ttk.Frame(slider_frame, style="Card.TFrame")
        v_title_box.pack(fill=tk.X)
        ttk.Label(v_title_box, text="⚡ 模擬輸入電壓 (Vin)", style="SubTitle.TLabel").pack(side=tk.LEFT)
        self.v_disp_lbl = ttk.Label(v_title_box, text="2.50 V", font=("Consolas", 12, "bold"), foreground=THEME["accent_cyan"], background=THEME["bg_card"])
        self.v_disp_lbl.pack(side=tk.RIGHT)

        self.v_slider = tk.Scale(
            slider_frame, from_=0.0, to=6.0, resolution=0.01, orient=tk.HORIZONTAL,
            showvalue=False, bg=THEME["bg_input"], fg=THEME["fg_text"],
            troughcolor=THEME["bg_main"], activebackground=THEME["accent_cyan"],
            highlightthickness=0, command=self._on_slider_change
        )
        self.v_slider.set(2.50)
        self.v_slider.pack(fill=tk.X, pady=(4, 2))

        # 刻度安全提示標籤
        scale_legend = ttk.Frame(slider_frame, style="Card.TFrame")
        scale_legend.pack(fill=tk.X)
        ttk.Label(scale_legend, text="🟢 0.0V (安全區間 0~5.0V)", font=("Segoe UI", 8), foreground=THEME["accent_green"], background=THEME["bg_card"]).pack(side=tk.LEFT)
        ttk.Label(scale_legend, text="🔴 5.5V 熔斷 | 6.0V", font=("Segoe UI", 8), foreground=THEME["accent_red"], background=THEME["bg_card"]).pack(side=tk.RIGHT)

        # 3. 訊號波形產生器 (Waveform Generator)
        gen_frame = ttk.Frame(ctrl_panel, style="Card.TFrame")
        gen_frame.pack(fill=tk.X, padx=12, pady=8)
        ttk.Label(gen_frame, text="🌊 訊號波形產生器 (小開驅動)", style="SubTitle.TLabel").pack(anchor=tk.W, pady=(0, 6))

        btn_grid = ttk.Frame(gen_frame, style="Card.TFrame")
        btn_grid.pack(fill=tk.X)

        ttk.Button(btn_grid, text="🪜 階梯波 (Step)", style="Dark.TButton", command=lambda: self.set_gen_mode("step")).grid(row=0, column=0, padx=2, pady=3, sticky="ew")
        ttk.Button(btn_grid, text="〰️ 正弦波 (Sine)", style="Dark.TButton", command=lambda: self.set_gen_mode("sine")).grid(row=0, column=1, padx=2, pady=3, sticky="ew")
        ttk.Button(btn_grid, text="⏹️ 方波 (Square)", style="Dark.TButton", command=lambda: self.set_gen_mode("square")).grid(row=1, column=0, padx=2, pady=3, sticky="ew")
        ttk.Button(btn_grid, text="🚨 過壓脈衝 (Pulse)", style="Red.TButton", command=lambda: self.set_gen_mode("pulse")).grid(row=1, column=1, padx=2, pady=3, sticky="ew")
        btn_grid.columnconfigure(0, weight=1)
        btn_grid.columnconfigure(1, weight=1)

        ttk.Button(gen_frame, text="✋ 停止波形 / 恢復手動滑桿", style="Dark.TButton", command=lambda: self.set_gen_mode("manual")).pack(fill=tk.X, pady=(4, 0))

        # 4. 安全與操作按鈕
        act_frame = ttk.Frame(ctrl_panel, style="Card.TFrame")
        act_frame.pack(fill=tk.X, padx=12, pady=10)
        ttk.Label(act_frame, text="🛡️ 硬體防護與報表", style="SubTitle.TLabel").pack(anchor=tk.W, pady=(0, 6))

        self.btn_reset_fuse = ttk.Button(
            act_frame, text="🔄 一鍵復位保險絲 (Reset Fuse)", style="Green.TButton", command=self.reset_fuse
        )
        self.btn_reset_fuse.pack(fill=tk.X, pady=3)

        ttk.Button(
            act_frame, text="💾 匯出 CSV 遙測報表 (CWE防護)", style="Dark.TButton", command=self.export_csv
        ).pack(fill=tk.X, pady=3)

        # ====================================================================
        # 右側區域 (上: Matplotlib 示波器, 下: HUD 儀表板與日誌)
        # ====================================================================
        right_panel = ttk.Frame(content_pane, style="Dark.TFrame")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 示波器畫布卡片
        scope_card = ttk.Frame(right_panel, style="Card.TFrame")
        scope_card.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self.fig = Figure(figsize=(7, 3.8), dpi=100, facecolor=THEME["bg_main"])
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=scope_card)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # 下方 HUD 狀態與自然語言日誌 (水平分割)
        bottom_box = ttk.Frame(right_panel, style="Dark.TFrame", height=200)
        bottom_box.pack(fill=tk.X)

        # HUD 十進制讀數卡片 (寬度 48%)
        hud_card = ttk.Frame(bottom_box, style="Card.TFrame")
        hud_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        ttk.Label(hud_card, text="💡 10-bit ADC 數位分身遙測 (十進制優先)", style="SubTitle.TLabel").pack(anchor=tk.W, padx=10, pady=(8, 4))

        hud_grid = ttk.Frame(hud_card, style="Card.TFrame")
        hud_grid.pack(fill=tk.X, padx=10, pady=2)

        # LED 狀態燈
        ttk.Label(hud_grid, text="硬體狀態:", style="Dark.TLabel", background=THEME["bg_card"]).grid(row=0, column=0, sticky="w", pady=2)
        led_box = ttk.Frame(hud_grid, style="Card.TFrame")
        led_box.grid(row=0, column=1, sticky="w", pady=2)
        self.led_canvas = tk.Canvas(led_box, width=16, height=16, bg=THEME["bg_card"], highlightthickness=0)
        self.led_canvas.pack(side=tk.LEFT, padx=(0, 6))
        self.led_circle = self.led_canvas.create_oval(2, 2, 14, 14, fill=THEME["accent_green"], outline="")
        self.lbl_fuse_text = ttk.Label(led_box, text="🟢 導通正常 (SAFE)", font=("Segoe UI", 9, "bold"), foreground=THEME["accent_green"], background=THEME["bg_card"])
        self.lbl_fuse_text.pack(side=tk.LEFT)

        # 十進制 ADC 讀數
        ttk.Label(hud_grid, text="ADC 採樣:", style="Dark.TLabel", background=THEME["bg_card"]).grid(row=1, column=0, sticky="w", pady=2)
        self.lbl_adc_dec = ttk.Label(
            hud_grid, text="512 (十進制)", font=("Consolas", 12, "bold"), foreground=THEME["accent_cyan"], background=THEME["bg_card"]
        )
        self.lbl_adc_dec.grid(row=1, column=1, sticky="w", pady=2)

        # 物理電壓與量化
        ttk.Label(hud_grid, text="測得物理電壓:", style="Dark.TLabel", background=THEME["bg_card"]).grid(row=2, column=0, sticky="w", pady=2)
        self.lbl_volt_val = ttk.Label(
            hud_grid, text="2.500 V", font=("Consolas", 10, "bold"), foreground=THEME["fg_text"], background=THEME["bg_card"]
        )
        self.lbl_volt_val.grid(row=2, column=1, sticky="w", pady=2)

        # 暫存器源碼
        ttk.Label(hud_grid, text="暫存器源碼:", style="Dark.TLabel", background=THEME["bg_card"]).grid(row=3, column=0, sticky="w", pady=2)
        self.lbl_raw_code = ttk.Label(
            hud_grid, text="0x0200 (0b001000000000)", font=("Consolas", 9), foreground=THEME["fg_muted"], background=THEME["bg_card"]
        )
        self.lbl_raw_code.grid(row=3, column=1, sticky="w", pady=2)

        # 自然語言診斷日誌框 (寬度 52%)
        log_card = ttk.Frame(bottom_box, style="Card.TFrame")
        log_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(6, 0))

        ttk.Label(log_card, text="🩺 系統即時診斷與事件日誌 (繁體中文)", style="SubTitle.TLabel").pack(anchor=tk.W, padx=10, pady=(8, 4))
        self.txt_log = ScrolledText(
            log_card, height=5, bg=THEME["bg_input"], fg=THEME["fg_text"],
            insertbackground="white", font=("Consolas", 8), relief="flat", highlightthickness=0
        )
        self.txt_log.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self._log_message("系統啟動完成：MCU 數位分身 10-bit ADC 遙測示波器就緒。")

    def _init_plot(self):
        """初始化 Matplotlib 示波器圖表樣式"""
        self.ax.set_facecolor(THEME["bg_panel"])
        self.fig.patch.set_facecolor(THEME["bg_main"])
        self.ax.tick_params(colors=THEME["fg_muted"], labelsize=8)
        for spine in self.ax.spines.values():
            spine.set_color(THEME["border"])

        self.ax.set_ylim(0.0, 6.5)
        self.ax.set_xlim(-3.0, 0.0)
        self.ax.grid(True, linestyle="--", alpha=0.3, color=THEME["grid_color"])

        # 5.5V 紅色過壓熔斷警戒線
        self.ax.axhline(5.50, color=THEME["accent_red"], linestyle="--", linewidth=1.5, label="5.5V 熔斷警戒線")
        # 5.0V 基準參考線
        self.ax.axhline(5.00, color=THEME["accent_amber"], linestyle=":", linewidth=1.0, label="5.0V Vref")

        # 安全區域半透明遮罩
        self.ax.axhspan(0.0, 5.0, facecolor=THEME["accent_green"], alpha=0.04)
        # 危險過壓區域半透明遮罩
        self.ax.axhspan(5.5, 6.5, facecolor=THEME["accent_red"], alpha=0.08)

        # 初始化動態波形曲線
        self.line_plot, = self.ax.plot(
            list(self.time_history), list(self.volt_history),
            color=THEME["accent_green"], linewidth=2.0
        )

        self.overlay_text = self.ax.text(
            -1.5, 3.25, "", color=THEME["accent_red"],
            fontsize=13, fontweight="bold", ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#330000", edgecolor=THEME["accent_red"], alpha=0.85)
        )
        self.overlay_text.set_visible(False)
        self.canvas.draw()

    def _log_message(self, msg: str):
        """將訊息輸出至診斷日誌框"""
        now_str = time.strftime("%H:%M:%S")
        if hasattr(self, "txt_log") and self.txt_log is not None:
            self.txt_log.insert(tk.END, f"[{now_str}] {msg}\n")
            self.txt_log.see(tk.END)
        else:
            print(f"[{now_str}] [Dashboard Log] {msg}")

    def _on_channel_change(self, event=None):
        raw = self.ch_var.get()
        if "CH0" in raw: self.current_channel = 0
        elif "CH1" in raw: self.current_channel = 1
        elif "CH2" in raw: self.current_channel = 2
        elif "CH3" in raw: self.current_channel = 3
        self._log_message(f"切換至採樣通道: CH{self.current_channel}")

    def _on_slider_change(self, val):
        self.current_input_voltage = float(val)
        if hasattr(self, "v_disp_lbl") and self.v_disp_lbl is not None:
            self.v_disp_lbl.config(text=f"{self.current_input_voltage:.2f} V")
        if self.gen_mode != "manual":
            self.gen_mode = "manual"
            self._log_message("已切換為手動滑桿調參模式。")

    def set_gen_mode(self, mode: str):
        """設定訊號產生器模式"""
        self.gen_mode = mode
        self.gen_time = 0.0
        self.gen_step_index = 0
        names = {
            "step": "階梯波 (0.5V~5.0V 步階)",
            "sine": "正弦波 (2.5V ± 2.0V)",
            "square": "方波 (0V / 5.0V 躍變)",
            "pulse": "🚨 過壓脈衝 (注入 5.80V 測試熔斷)",
            "manual": "手動滑桿控制"
        }
        self._log_message(f"訊號產生器已設定為: {names.get(mode, mode)}")

    def reset_fuse(self):
        """一鍵復位虛擬硬體保險絲"""
        self.bridge.reset_hardware_fuse()
        if hasattr(self, "overlay_text") and self.overlay_text is not None:
            self.overlay_text.set_visible(False)
        if hasattr(self, "led_canvas") and self.led_canvas is not None:
            self.led_canvas.itemconfig(self.led_circle, fill=THEME["accent_green"])
        if hasattr(self, "lbl_fuse_text") and self.lbl_fuse_text is not None:
            self.lbl_fuse_text.config(text="🟢 導通正常 (SAFE)", foreground=THEME["accent_green"])
        if hasattr(self, "v_slider") and self.v_slider is not None:
            self.v_slider.set(2.50)
        self.current_input_voltage = 2.50
        self.gen_mode = "manual"
        self._log_message("🔄 虛擬硬體保險絲已重設，系統恢復正常採樣！")

    def export_csv(self):
        """匯出遙測歷史 CSV (CWE-1236 防護)"""
        if not self.bridge.sample_history:
            messagebox.showinfo("提示", "目前尚無遙測採樣歷史可供匯出。")
            return

        out_file = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV 試算表", "*.csv"), ("所有檔案", "*.*")],
            title="儲存遙測報表"
        )
        if out_file:
            try:
                saved_path = self.bridge.export_telemetry_csv(out_file)
                self._log_message(f"💾 遙測報表已成功匯出至: {saved_path}")
                messagebox.showinfo("成功", f"遙測報表已匯出！\n路徑: {saved_path}\n(已落實 CWE-1236 公式注入防護)")
            except Exception as e:
                messagebox.showerror("錯誤", f"匯出失敗: {str(e)}")

    def step_simulation(self, delta_sec: float = 0.05) -> ADCTelemetryFrame:
        """
        執行單步模擬更新 (供 UI 定時器或測試調用)
        """
        self.gen_time += delta_sec

        # 訊號產生器計算
        if self.gen_mode == "step":
            steps = [0.5, 1.5, 2.5, 3.5, 4.5, 5.0]
            step_idx = int(self.gen_time / 0.6) % len(steps)
            input_v = steps[step_idx]
            self.current_input_voltage = input_v
        elif self.gen_mode == "sine":
            # 2.5V 偏壓, 2.0V 振幅, 0.5Hz 頻率
            input_v = 2.5 + 2.0 * math.sin(2 * math.pi * 0.5 * self.gen_time)
            self.current_input_voltage = round(max(0.0, min(input_v, 6.0)), 2)
        elif self.gen_mode == "square":
            # 0V 與 5.0V 每 0.5 秒交替
            input_v = 5.0 if int(self.gen_time / 0.5) % 2 == 0 else 0.0
            self.current_input_voltage = input_v
        elif self.gen_mode == "pulse":
            # 瞬態脈衝：第 0.3 秒注入 5.8V 過壓
            input_v = 5.80 if self.gen_time > 0.3 else 2.50
            self.current_input_voltage = input_v
            if self.gen_time > 1.0:
                self.gen_mode = "manual"
        else:  # manual
            input_v = self.current_input_voltage

        # 呼叫底層驅動採樣
        frame = self.bridge.sample_adc(channel=self.current_channel, input_voltage=input_v)

        # 更新歷史隊列
        self.volt_history.append(frame.measured_voltage)
        self.adc_history.append(frame.adc_raw_dec)

        return frame

    def _start_update_loop(self):
        """啟動 UI 毫秒級更新主迴圈 (50ms)"""
        if not self.timer_running:
            return

        frame = self.step_simulation(delta_sec=0.05)

        # 1. 更新 HUD 讀數 (十進制優先)
        self.v_disp_lbl.config(text=f"{self.current_input_voltage:.2f} V")
        self.lbl_adc_dec.config(text=f"{frame.adc_raw_dec} (十進制)")
        self.lbl_volt_val.config(
            text=f"{frame.measured_voltage:.3f} V (輸入: {frame.simulated_input_voltage:.2f}V)"
        )
        self.lbl_raw_code.config(text=f"{frame.hex_code} ({frame.bin_code})")

        # 2. 狀態燈與熔斷反應
        if frame.is_overvoltage_tripped:
            self.led_canvas.itemconfig(self.led_circle, fill=THEME["accent_red"])
            self.lbl_fuse_text.config(text="🔴 熔斷斷開 (FUSE BLOWN)", foreground=THEME["accent_red"])
            self.line_plot.set_color(THEME["accent_red"])
            self.overlay_text.set_text("🔴 [FUSE BLOWN - 保險絲已熔斷]\n輸入電壓 > 5.50V，系統強制斷路保護！")
            self.overlay_text.set_visible(True)
        else:
            self.led_canvas.itemconfig(self.led_circle, fill=THEME["accent_green"])
            self.lbl_fuse_text.config(text="🟢 導通正常 (SAFE)", foreground=THEME["accent_green"])
            self.line_plot.set_color(THEME["accent_green"])
            self.overlay_text.set_visible(False)

        # 3. 刷新示波器畫布
        self.line_plot.set_ydata(list(self.volt_history))
        self.canvas.draw_idle()

        # 4. 註冊下一次定時器
        self.root.after(50, self._start_update_loop)


def launch_dashboard():
    """啟動 GUI 儀表板入口"""
    root = tk.Tk()
    app = MCUTelemetryDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    launch_dashboard()
