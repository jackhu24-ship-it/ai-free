#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 【PROJ-22 資料驅動通用動態 UI 渲染引擎 v2.0】：dynamic_schema_dashboard.py
========================================================================================
角色分工：
  - 👁️ 小Ｏ (Agent_Vision)  : 牽頭暗黑工業風通用組件庫、黑底綠字 CAN 報文監聽終端、示波器整合
  - 🛠️ 小開 (Agent_Coder)   : 專案 JSON 配置標準、PIC18F25K80 ECAN 暫存器雙向映射、CAN 報文產生器
  - 🐎 小馬 (Agent_Reviewer): Schema 語法邊界檢查 (min < max)、CWE-1236 防禦、十進位優先審查
  - 👑 小幫手 (Agent_PM)    : 多專案下拉熱抽換 (Hot-Reload) 與狀態總控

新增戰略旗艦功能：
  1. 【即時 CAN 報文監聽器 (CAN Raw Frame Sniffer)】：
     - 黑底矩陣綠字 (#0A0E14 / #00FF66) 終端滾動視窗
     - 格式化十進位優先解析：[RX] TIMESTAMP | ID: 0x7E0 (2016) | DLC: 8 | DATA: ... (語意)
     - 支援一鍵手動注入 0x7E0 診斷心跳與自動滾動控制
  2. 【PIC18F25K80 ECAN 暫存器雙向映射 (Baud Calculator)】：
     - 滑動鮑率 (125/250/500/1000 kbps) 實時動態計算 BRGCON1, BRGCON2, BRGCON3
     - 嚴格落實「十進位優先 (Decimal-First)」與 Hex/Bin 雙向對照
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

import math
import time
import json
import random
import asyncio
import collections
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable, Union

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from can_sniffer_ecan_calculator import (
    ECANBaudCalculator,
    ECANRegisterConfig,
    CANFrameGenerator,
    CANRawFrame,
    sanitize_cell
)


# ============================================================================
# 視覺調色盤常數 (👁️ 小Ｏ 暗黑工業風 & 黑底綠字終端)
# ============================================================================

THEME = {
    "bg_main": "#121212",
    "bg_panel": "#1E1E1E",
    "bg_card": "#252526",
    "bg_input": "#2D2D30",
    "bg_terminal": "#0A0E14",     # 終端純黑底色
    "fg_terminal": "#00FF66",     # 終端矩陣螢光綠
    "fg_text": "#E0E0E0",
    "fg_muted": "#888888",
    "border": "#3E3E42",
    "accent_green": "#00FF66",     # 正常 / 導通
    "accent_red": "#FF3333",       # 警戒 / 熔斷
    "accent_cyan": "#00E5FF",      # 科技青 (HUD 主色)
    "accent_amber": "#FFB74D",     # 琥珀黃 (警告)
    "accent_blue": "#3399FF",      # 訊號藍
    "grid_color": "#2A2A2A"
}


# ============================================================================
# 核心模組一：Schema 安全校驗與解析器 (SchemaValidator - 🐎 小馬守門)
# ============================================================================

class SchemaValidationError(Exception):
    """Schema 格式或邊界錯誤例外"""
    pass


class SchemaValidator:
    """
    專案設定檔語法、邊界與安全檢查器
    """

    @classmethod
    def validate_and_sanitize(cls, schema: Dict[str, Any]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        校驗 Schema 邊界並執行 CWE-1236 安全過濾
        回傳: (is_valid, error_msg, sanitized_schema)
        """
        try:
            if not isinstance(schema, dict):
                raise SchemaValidationError("Schema 必須為 JSON 物件 (Dictionary)。")

            # 1. 檢查必要欄位
            if "project_name" not in schema:
                raise SchemaValidationError("缺少必要欄位 'project_name'。")

            sanitized: Dict[str, Any] = {
                "project_id": schema.get("project_id", "custom_project"),
                "project_name": sanitize_cell(schema["project_name"]),
                "version": str(schema.get("version", "1.0.0")),
                "target_hardware": sanitize_cell(schema.get("target_hardware", "Generic MCU")),
                "description": sanitize_cell(schema.get("description", "")),
                "inputs": [],
                "parameters": [],
                "outputs": []
            }

            seen_ids = set()

            # 2. 檢驗輸入項 (inputs)
            for inp in schema.get("inputs", []):
                i_id = inp.get("id")
                if not i_id or i_id in seen_ids:
                    raise SchemaValidationError(f"輸入項 ID '{i_id}' 無效或重複。")
                seen_ids.add(i_id)
                i_type = inp.get("type", "button")
                if i_type not in ("toggle", "button", "pulse"):
                    raise SchemaValidationError(f"不支援的輸入組件類型: '{i_type}'。")
                sanitized["inputs"].append({
                    "id": i_id,
                    "label": sanitize_cell(inp.get("label", i_id)),
                    "type": i_type,
                    "default": bool(inp.get("default", False)),
                    "description": sanitize_cell(inp.get("description", ""))
                })

            # 3. 檢驗參數項 (parameters)
            for param in schema.get("parameters", []):
                p_id = param.get("id")
                if not p_id or p_id in seen_ids:
                    raise SchemaValidationError(f"參數項 ID '{p_id}' 無效或重複。")
                seen_ids.add(p_id)
                p_min = float(param.get("min", 0.0))
                p_max = float(param.get("max", 100.0))
                if p_min >= p_max:
                    raise SchemaValidationError(f"參數 '{p_id}' 之 min ({p_min}) 必須小於 max ({p_max})。")
                p_def = float(param.get("default", p_min))
                if not (p_min <= p_def <= p_max):
                    p_def = p_min
                p_step = float(param.get("step", 1.0))
                if p_step <= 0:
                    p_step = 1.0

                danger_th = param.get("danger_threshold")
                danger_val = float(danger_th) if danger_th is not None else None

                sanitized["parameters"].append({
                    "id": p_id,
                    "label": sanitize_cell(param.get("label", p_id)),
                    "type": param.get("type", "slider"),
                    "min": p_min,
                    "max": p_max,
                    "default": p_def,
                    "step": p_step,
                    "unit": sanitize_cell(param.get("unit", "")),
                    "danger_threshold": danger_val,
                    "description": sanitize_cell(param.get("description", ""))
                })

            # 4. 檢驗輸出項 (outputs)
            for out in schema.get("outputs", []):
                o_id = out.get("id")
                if not o_id or o_id in seen_ids:
                    raise SchemaValidationError(f"輸出項 ID '{o_id}' 無效或重複。")
                seen_ids.add(o_id)
                o_type = out.get("type", "numeric_gauge")
                sanitized["outputs"].append({
                    "id": o_id,
                    "label": sanitize_cell(out.get("label", o_id)),
                    "type": o_type,
                    "unit": sanitize_cell(out.get("unit", "")),
                    "scope_channel": bool(out.get("scope_channel", False)),
                    "description": sanitize_cell(out.get("description", ""))
                })

            return True, None, sanitized

        except Exception as e:
            return False, str(e), {}


# ============================================================================
# 核心模組二：反應式雙向狀態中心 (ReactiveStateStore)
# ============================================================================

class ReactiveStateStore:
    """
    全域雙向反應式數據中心
    """

    def __init__(self):
        self.state: Dict[str, Any] = {}
        self.listeners: Dict[str, List[Callable[[str, Any], None]]] = collections.defaultdict(list)

    def set(self, key: str, value: Any):
        """更新狀態並觸發監聽回呼"""
        self.state[key] = value
        for cb in self.listeners.get(key, []):
            try:
                cb(key, value)
            except Exception as e:
                print(f"⚠️ 狀態回呼異常 ({key}): {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)

    def subscribe(self, key: str, callback: Callable[[str, Any], None]):
        """註冊變更監聽器"""
        self.listeners[key].append(callback)

    def clear(self):
        self.state.clear()
        self.listeners.clear()


# ============================================================================
# 主程式類別：DynamicSchemaDashboard (👁️ 小Ｏ 牽頭動態渲染引擎 v2.0)
# ============================================================================

class DynamicSchemaDashboard:
    """
    PROJ-22 資料驅動動態 UI 儀表板
    """

    def __init__(self, root: Optional[tk.Tk] = None, configs_dir: Optional[Union[str, Path]] = None):
        self.root = root or tk.Tk()
        self.configs_dir = Path(configs_dir or Path(r"G:\我的雲端硬碟\AI_master_workspace\three_memory\CONFIGS")).resolve()
        self.state_store = ReactiveStateStore()
        self.current_schema: Dict[str, Any] = {}

        # 示波器波形隊列 (60點)
        self.buffer_len = 60
        self.time_history = collections.deque(maxlen=self.buffer_len)
        self.scope_history = collections.deque(maxlen=self.buffer_len)
        for i in range(self.buffer_len):
            self.time_history.append(- (self.buffer_len - i) * 0.05)
            self.scope_history.append(0.0)

        # 動態組件控制項容器
        self.dynamic_widgets = {}
        self.ecan_labels = {}
        self.timer_running = True
        self.sim_time = 0.0
        self.last_can_rx_time = 0.0
        self.auto_scroll_var = tk.BooleanVar(value=True)

        if root is not None:
            self._setup_window()
            self._setup_styles()
            self._build_static_layout()
            self._init_plot()
            self._load_default_preset()
            self._start_main_loop()

    def _setup_window(self):
        self.root.title("🚀 Five-Agent AI OS: 通用資料驅動動態 UI 渲染引擎 (PROJ-22 v2.0)")
        self.root.geometry("1280x820")
        self.root.minsize(1050, 720)
        self.root.configure(bg=THEME["bg_main"])

    def _setup_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Dark.TFrame", background=THEME["bg_panel"])
        style.configure("Card.TFrame", background=THEME["bg_card"])
        style.configure("Dark.TLabel", background=THEME["bg_panel"], foreground=THEME["fg_text"], font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=THEME["bg_panel"], foreground=THEME["accent_cyan"], font=("Segoe UI", 13, "bold"))
        style.configure("CardTitle.TLabel", background=THEME["bg_card"], foreground=THEME["accent_amber"], font=("Segoe UI", 11, "bold"))
        style.configure("TerminalTitle.TLabel", background=THEME["bg_card"], foreground=THEME["accent_green"], font=("Consolas", 10, "bold"))
        style.configure("Dark.TButton", background=THEME["bg_input"], foreground=THEME["fg_text"], font=("Segoe UI", 9, "bold"))
        style.map("Dark.TButton", background=[("active", "#3E3E42")])

    def _build_static_layout(self):
        """構建外層固定框架 (頂部專案選單 + 左右分割區)"""
        main_box = ttk.Frame(self.root, style="Dark.TFrame")
        main_box.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # 頂部導航與專案切換列
        nav_bar = ttk.Frame(main_box, style="Dark.TFrame")
        nav_bar.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(nav_bar, text="📁 專案切換 (Hot-Reload):", style="Title.TLabel").pack(side=tk.LEFT, padx=(0, 8))

        # 掃描 CONFIGS/ 目錄下所有 JSON 設定檔
        preset_files = list(self.configs_dir.glob("*.json"))
        preset_names = [f.name for f in preset_files] if preset_files else ["(尚無預設配置)"]

        self.project_combo_var = tk.StringVar(value=preset_names[0] if preset_names else "")
        self.project_combo = ttk.Combobox(
            nav_bar, textvariable=self.project_combo_var, values=preset_names,
            state="readonly", width=42
        )
        self.project_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.project_combo.bind("<<ComboboxSelected>>", self._on_preset_selected)

        ttk.Button(nav_bar, text="📂 載入外部 JSON", style="Dark.TButton", command=self.load_external_json).pack(side=tk.LEFT, padx=4)
        ttk.Button(nav_bar, text="💾 匯出目前遙測報表", style="Dark.TButton", command=self.export_telemetry_csv).pack(side=tk.LEFT, padx=4)

        self.lbl_target_hw = ttk.Label(nav_bar, text="目標硬體: PIC18F25K80", style="Dark.TLabel", foreground=THEME["accent_cyan"])
        self.lbl_target_hw.pack(side=tk.RIGHT, padx=5)

        # 內容分割區 (左: 動態控制面板 400px, 右: 示波器與終端 HUD)
        content_box = ttk.Frame(main_box, style="Dark.TFrame")
        content_box.pack(fill=tk.BOTH, expand=True)

        # 左側動態生成面板 (可滾動)
        self.left_panel = ttk.Frame(content_box, style="Card.TFrame", width=400)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        self.left_panel.pack_propagate(False)

        # 右側示波器與終端 Sniffer
        self.right_panel = ttk.Frame(content_box, style="Dark.TFrame")
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 右上: Matplotlib 示波器
        scope_card = ttk.Frame(self.right_panel, style="Card.TFrame")
        scope_card.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self.fig = Figure(figsize=(7, 3.2), dpi=100, facecolor=THEME["bg_main"])
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=scope_card)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # 右下: 動態輸出 HUD 與 CAN Sniffer 終端
        bottom_box = ttk.Frame(self.right_panel, style="Dark.TFrame", height=240)
        bottom_box.pack(fill=tk.X)

        self.hud_container = ttk.Frame(bottom_box, style="Card.TFrame", width=300)
        self.hud_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 6))

        # CAN 報文監聽器 / 診斷終端 (黑底綠字)
        terminal_card = ttk.Frame(bottom_box, style="Card.TFrame")
        terminal_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(6, 0))

        top_term_bar = ttk.Frame(terminal_card, style="Card.TFrame")
        top_term_bar.pack(fill=tk.X, padx=8, pady=(4, 2))

        ttk.Label(top_term_bar, text="📡 CAN Raw Frame Sniffer [黑底綠字 / 十進位優先]", style="TerminalTitle.TLabel").pack(side=tk.LEFT)
        
        ttk.Button(top_term_bar, text="⚡ 注入 0x7E0 心跳", style="Dark.TButton", command=self.inject_heartbeat_from_ui).pack(side=tk.RIGHT, padx=4)
        ttk.Button(top_term_bar, text="🧹 清空", style="Dark.TButton", command=self.clear_sniffer_terminal).pack(side=tk.RIGHT, padx=4)

        self.txt_log = ScrolledText(
            terminal_card, height=7, bg=THEME["bg_terminal"], fg=THEME["fg_terminal"],
            insertbackground="#00FF66", font=("Consolas", 8, "bold"), relief="flat"
        )
        self.txt_log.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 6))

    def _init_plot(self):
        """初始化示波器樣式"""
        self.ax.set_facecolor(THEME["bg_panel"])
        self.fig.patch.set_facecolor(THEME["bg_main"])
        self.ax.tick_params(colors=THEME["fg_muted"], labelsize=8)
        for spine in self.ax.spines.values():
            spine.set_color(THEME["border"])

        self.ax.set_ylim(0.0, 20.0)
        self.ax.set_xlim(-3.0, 0.0)
        self.ax.grid(True, linestyle="--", alpha=0.3, color=THEME["grid_color"])

        self.danger_line = self.ax.axhline(15.0, color=THEME["accent_red"], linestyle="--", linewidth=1.5)
        self.danger_line.set_visible(False)

        self.line_plot, = self.ax.plot(
            list(self.time_history), list(self.scope_history),
            color=THEME["accent_green"], linewidth=2.0
        )
        self.canvas.draw()

    def _log_msg(self, msg: str):
        now_str = time.strftime("%H:%M:%S")
        if hasattr(self, "txt_log") and self.txt_log is not None:
            self.txt_log.insert(tk.END, f"[{now_str}] {msg}\n")
            if self.auto_scroll_var.get():
                self.txt_log.see(tk.END)
        else:
            print(f"[{now_str}] [Schema Log] {msg}")

    def log_can_frame(self, frame: CANRawFrame):
        """向黑底綠字終端輸出標準 CAN 報文"""
        line = frame.format_log_line()
        if hasattr(self, "txt_log") and self.txt_log is not None:
            self.txt_log.insert(tk.END, f"{line}\n")
            if self.auto_scroll_var.get():
                self.txt_log.see(tk.END)
        else:
            print(line)

    def clear_sniffer_terminal(self):
        if hasattr(self, "txt_log") and self.txt_log is not None:
            self.txt_log.delete("1.0", tk.END)

    def inject_heartbeat_from_ui(self):
        frame = CANFrameGenerator.generate_heartbeat_pulse()
        self.log_can_frame(frame)
        self.state_store.set("send_heartbeat", time.time())

    # ========================================================================
    # 核心功能：動態 Schema 載入與 0.05 秒介面重建 (Dynamic Rebuild)
    # ========================================================================

    def load_schema(self, schema_dict: Dict[str, Any]) -> bool:
        """
        解析 Schema 並動態重構所有 UI 組件
        """
        # 1. 🐎 小馬 執行安全檢查與邊界防護
        ok, err_msg, clean_schema = SchemaValidator.validate_and_sanitize(schema_dict)
        if not ok:
            self._log_msg(f"❌ Schema 校驗失敗: {err_msg}")
            if hasattr(self, "root") and self.root:
                messagebox.showerror("Schema 錯誤", f"無法載入專案設定檔:\n{err_msg}")
            return False

        self.current_schema = clean_schema
        self.state_store.clear()

        # 2. 清理左側控制欄與右側 HUD 所有舊組件
        if hasattr(self, "left_panel"):
            for child in self.left_panel.winfo_children():
                child.destroy()
        if hasattr(self, "hud_container"):
            for child in self.hud_container.winfo_children():
                child.destroy()

        self.dynamic_widgets.clear()
        self.ecan_labels.clear()

        # 3. 更新標題與硬體標籤
        p_name = clean_schema["project_name"]
        hw_target = clean_schema["target_hardware"]
        if hasattr(self, "lbl_target_hw"):
            self.lbl_target_hw.config(text=f"目標硬體: {hw_target}")

        self._log_msg(f"🔄 正在為專案 [{p_name}] 動態生成控制介面...")

        # 4. 動態生成【輸入控制項】(Inputs)
        if hasattr(self, "left_panel"):
            self._build_dynamic_inputs(clean_schema.get("inputs", []))
            self._build_dynamic_parameters(clean_schema.get("parameters", []))

        # 5. 動態生成【輸出監控項】(Outputs)
        if hasattr(self, "hud_container"):
            self._build_dynamic_outputs(clean_schema.get("outputs", []))

        # 6. 動態配置示波器範圍
        self._reconfigure_scope_for_schema(clean_schema)

        self._log_msg(f"✅ 專案 [{p_name}] 動態介面長出完成 (零改動程式碼)！")
        return True

    def _build_dynamic_inputs(self, inputs: List[Dict[str, Any]]):
        """動態生成輸入開關與伴隨發光指示燈 (Input Accompanying LED)"""
        sec = ttk.Frame(self.left_panel, style="Card.TFrame")
        sec.pack(fill=tk.X, padx=10, pady=(8, 4))
        ttk.Label(sec, text="🎛️ 輸入控制訊號 (Inputs ✕ 伴隨指示燈)", style="CardTitle.TLabel").pack(anchor=tk.W, pady=(0, 4))

        for inp in inputs:
            i_id = inp["id"]
            i_lbl = inp["label"]
            i_type = inp["type"]
            i_def = inp["default"]

            self.state_store.set(i_id, i_def)

            row = ttk.Frame(sec, style="Card.TFrame")
            row.pack(fill=tk.X, pady=2)

            # 伴隨圓形指示燈 (LED)
            canv = tk.Canvas(row, width=16, height=16, bg=THEME["bg_card"], highlightthickness=0)
            canv.pack(side=tk.LEFT, padx=(0, 6))
            circle = canv.create_oval(2, 2, 14, 14, fill=THEME["accent_green"] if i_def else "#333333", outline="#555555")

            if i_type == "toggle":
                btn = tk.Button(
                    row, text=f"{i_lbl}: {'ON' if i_def else 'OFF'}",
                    bg="#007A33" if i_def else THEME["bg_input"],
                    fg="#FFFFFF" if i_def else THEME["fg_text"],
                    font=("Segoe UI", 9, "bold"), relief="flat", padx=8, pady=3
                )
                btn.config(command=lambda bid=i_id, bbtn=btn, blbl=i_lbl, ccanv=canv, ccirc=circle: self._toggle_button_click(bid, bbtn, blbl, ccanv, ccirc))
                btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.dynamic_widgets[i_id] = (btn, canv, circle)

            elif i_type in ("button", "pulse"):
                is_pulse = (i_type == "pulse")
                btn = tk.Button(
                    row, text=f"⚡ {i_lbl}",
                    bg="#991111" if is_pulse else THEME["bg_input"],
                    fg="#FFFFFF" if is_pulse else THEME["fg_text"],
                    font=("Segoe UI", 9, "bold"), relief="flat", padx=8, pady=3
                )
                btn.config(command=lambda bid=i_id, bpulse=is_pulse, ccanv=canv, ccirc=circle: self._trigger_button_click(bid, bpulse, ccanv, ccirc))
                btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.dynamic_widgets[i_id] = (btn, canv, circle)

    def _build_dynamic_parameters(self, params: List[Dict[str, Any]]):
        """動態生成調參滑桿 ＆ PIC18F25K80 ECAN 暫存器計算卡"""
        sec = ttk.Frame(self.left_panel, style="Card.TFrame")
        sec.pack(fill=tk.X, padx=10, pady=(6, 8))
        ttk.Label(sec, text="⚙️ 參數調節滑桿 (Parameters)", style="CardTitle.TLabel").pack(anchor=tk.W, pady=(0, 4))

        has_baud_slider = False

        for p in params:
            p_id = p["id"]
            p_lbl = p["label"]
            p_min = p["min"]
            p_max = p["max"]
            p_def = p["default"]
            p_step = p["step"]
            p_unit = p["unit"]
            danger_th = p["danger_threshold"]

            self.state_store.set(p_id, p_def)

            p_box = ttk.Frame(sec, style="Card.TFrame")
            p_box.pack(fill=tk.X, pady=2)

            title_row = ttk.Frame(p_box, style="Card.TFrame")
            title_row.pack(fill=tk.X)
            ttk.Label(title_row, text=p_lbl, style="Dark.TLabel", background=THEME["bg_card"], font=("Segoe UI", 9)).pack(side=tk.LEFT)
            
            disp_lbl = ttk.Label(
                title_row, text=f"{p_def:.2f} {p_unit}",
                font=("Consolas", 9, "bold"), foreground=THEME["accent_cyan"], background=THEME["bg_card"]
            )
            disp_lbl.pack(side=tk.RIGHT)

            slider = tk.Scale(
                p_box, from_=p_min, to=p_max, resolution=p_step, orient=tk.HORIZONTAL,
                showvalue=False, bg=THEME["bg_input"], fg=THEME["fg_text"],
                troughcolor=THEME["bg_main"], activebackground=THEME["accent_cyan"],
                highlightthickness=0
            )
            slider.set(p_def)
            slider.config(
                command=lambda val, pid=p_id, dlbl=disp_lbl, unit=p_unit, dth=danger_th: self._on_slider_move(val, pid, dlbl, unit, dth)
            )
            slider.pack(fill=tk.X, pady=(1, 2))
            self.dynamic_widgets[p_id] = (slider, disp_lbl)

            if "baud" in p_id.lower():
                has_baud_slider = True

        # 若專案包含鮑率設定，動態長出 PIC18F25K80 ECAN 暫存器雙向映射卡
        if has_baud_slider:
            self._build_ecan_register_card(sec)

    def _build_ecan_register_card(self, parent_frame: ttk.Frame):
        """動態生成 PIC18F25K80 ECAN 暫存器十進位優先對照卡"""
        ecan_card = ttk.Frame(parent_frame, style="Card.TFrame")
        ecan_card.pack(fill=tk.X, pady=(6, 2))

        ttk.Label(ecan_card, text="📟 PIC18F25K80 ECAN 暫存器對照 (十進位優先):", font=("Segoe UI", 9, "bold"), foreground=THEME["accent_amber"], background=THEME["bg_card"]).pack(anchor=tk.W, pady=(2, 2))

        init_baud = self.state_store.get("baud_rate_kbps", self.state_store.get("param_baudrate", 500.0))
        reg_cfg = ECANBaudCalculator.calculate(init_baud)
        fmt_dict = reg_cfg.format_decimal_first()

        for reg_name in ("BRGCON1", "BRGCON2", "BRGCON3"):
            lbl = ttk.Label(
                ecan_card, text=fmt_dict[reg_name],
                font=("Consolas", 8), foreground=THEME["accent_cyan"], background=THEME["bg_input"], padding=(4, 2)
            )
            lbl.pack(fill=tk.X, pady=1)
            self.ecan_labels[reg_name] = lbl

    def _update_ecan_registers(self, baud_kbps: float):
        """滑動鮑率時即時更新 ECAN 暫存器卡"""
        reg_cfg = ECANBaudCalculator.calculate(baud_kbps)
        fmt_dict = reg_cfg.format_decimal_first()
        for reg_name, lbl in self.ecan_labels.items():
            if reg_name in fmt_dict:
                lbl.config(text=fmt_dict[reg_name])

    def _build_dynamic_outputs(self, outputs: List[Dict[str, Any]]):
        """動態生成輸出 HUD (大顆發光 LED 指示燈 + 十進制大字儀表)"""
        ttk.Label(self.hud_container, text="💡 輸出監控 ✕ 狀態指示燈 (Outputs)", style="CardTitle.TLabel").pack(anchor=tk.W, padx=8, pady=(4, 2))

        grid_box = ttk.Frame(self.hud_container, style="Card.TFrame")
        grid_box.pack(fill=tk.BOTH, expand=True, padx=8, pady=2)

        for idx, out in enumerate(outputs):
            o_id = out["id"]
            o_lbl = out["label"]
            o_type = out["type"]
            o_unit = out["unit"]

            self.state_store.set(o_id, 0.0)

            row_frame = ttk.Frame(grid_box, style="Card.TFrame")
            row_frame.pack(fill=tk.X, pady=2)

            ttk.Label(row_frame, text=f"{o_lbl}:", style="Dark.TLabel", background=THEME["bg_card"], width=20, anchor="w", font=("Segoe UI", 9)).pack(side=tk.LEFT)

            if o_type == "led":
                # 大顆發光 LED 指示燈 (18x18 Canvas)
                canv = tk.Canvas(row_frame, width=18, height=18, bg=THEME["bg_card"], highlightthickness=0)
                canv.pack(side=tk.LEFT, padx=(0, 6))
                circle = canv.create_oval(2, 2, 16, 16, fill=THEME["accent_green"], outline="#FFFFFF", width=1)
                txt = ttk.Label(row_frame, text="🟢 NORMAL", foreground=THEME["accent_green"], background=THEME["bg_card"], font=("Segoe UI", 9, "bold"))
                txt.pack(side=tk.LEFT)
                self.dynamic_widgets[o_id] = (canv, circle, txt)
            else:  # numeric_gauge
                g_lbl = ttk.Label(
                    row_frame, text=f"0.00 {o_unit}",
                    font=("Consolas", 10, "bold"), foreground=THEME["accent_cyan"], background=THEME["bg_card"]
                )
                g_lbl.pack(side=tk.LEFT)
                self.dynamic_widgets[o_id] = g_lbl

    def _reconfigure_scope_for_schema(self, schema: Dict[str, Any]):
        """依據專案參數動態調整示波器 Y 軸上限與危險線"""
        if not hasattr(self, "ax"):
            return

        max_val = 10.0
        danger_th = None

        for p in schema.get("parameters", []):
            if p["max"] > max_val:
                max_val = p["max"]
            if p.get("danger_threshold") is not None:
                danger_th = p["danger_threshold"]

        self.ax.set_ylim(0.0, max_val * 1.25)
        if danger_th is not None:
            self.danger_line.set_ydata([danger_th, danger_th])
            self.danger_line.set_visible(True)
        else:
            self.danger_line.set_visible(False)

        self.canvas.draw_idle()

    # ========================================================================
    # 互動事件處理 (動態發光指示燈聯動)
    # ========================================================================

    def _toggle_button_click(self, b_id: str, btn: tk.Button, label: str, canv: Optional[tk.Canvas] = None, circle: Optional[int] = None):
        curr = self.state_store.get(b_id, False)
        new_val = not curr
        self.state_store.set(b_id, new_val)
        btn.config(
            text=f"{label}: {'ON' if new_val else 'OFF'}",
            bg="#007A33" if new_val else THEME["bg_input"],
            fg="#FFFFFF" if new_val else THEME["fg_text"]
        )
        if canv is not None and circle is not None:
            canv.itemconfig(circle, fill=THEME["accent_green"] if new_val else "#333333")

        self._log_msg(f"開關切換: {label} ➔ {'ON' if new_val else 'OFF'}")

    def _trigger_button_click(self, b_id: str, is_pulse: bool, canv: Optional[tk.Canvas] = None, circle: Optional[int] = None):
        self.state_store.set(b_id, time.time())
        tag = "🚨 脈衝注入" if is_pulse else "按鈕觸發"
        self._log_msg(f"{tag}: ID [{b_id}] 已發送觸發事件")
        
        if canv is not None and circle is not None:
            canv.itemconfig(circle, fill="#FF3333" if is_pulse else "#FFB74D")
            if hasattr(self, "root") and self.root:
                self.root.after(200, lambda: canv.itemconfig(circle, fill="#333333"))

        if "heartbeat" in b_id.lower() or "send" in b_id.lower():
            self.inject_heartbeat_from_ui()

    def _on_slider_move(self, val_str: str, p_id: str, disp_lbl: ttk.Label, unit: str, danger_th: Optional[float]):
        val = float(val_str)
        self.state_store.set(p_id, val)
        disp_lbl.config(text=f"{val:.2f} {unit}")
        if danger_th is not None and val >= danger_th:
            disp_lbl.config(foreground=THEME["accent_red"])
        else:
            disp_lbl.config(foreground=THEME["accent_cyan"])

        # 若為鮑率滑桿，連帶更新 ECAN 暫存器卡
        if "baud" in p_id.lower():
            self._update_ecan_registers(val)

    def _on_preset_selected(self, event=None):
        filename = self.project_combo_var.get()
        target_path = self.configs_dir / filename
        if target_path.exists():
            self.load_schema_from_file(target_path)

    def load_external_json(self):
        """開啟檔案選擇視窗載入自訂 JSON"""
        fp = filedialog.askopenfilename(
            filetypes=[("JSON 專案設定檔", "*.json"), ("所有檔案", "*.*")],
            title="選擇專案設定檔"
        )
        if fp:
            self.load_schema_from_file(fp)

    def load_schema_from_file(self, file_path: Union[str, Path]) -> bool:
        """從檔案載入 JSON Schema"""
        path = Path(file_path).resolve()
        if not path.exists():
            self._log_msg(f"檔案不存在: {path}")
            return False
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
            return self.load_schema(data)
        except Exception as e:
            self._log_msg(f"JSON 解析失敗: {str(e)}")
            return False

    def _load_default_preset(self):
        """預設載入第一個專案設定檔"""
        presets = list(self.configs_dir.glob("*.json"))
        if presets:
            self.load_schema_from_file(presets[0])

    def export_telemetry_csv(self):
        """匯出目前狀態為 CSV (落實 CWE-1236 防護)"""
        out_file = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV 試算表", "*.csv")],
            title="匯出專案遙測報表"
        )
        if out_file:
            try:
                headers = ["key", "value", "sanitized_value"]
                rows = []
                for k, v in self.state_store.state.items():
                    rows.append(f"{sanitize_cell(k)},{sanitize_cell(v)},{sanitize_cell(str(v))}")
                content = "\n".join([",".join(headers)] + rows)
                with open(out_file, "w", encoding="utf-8", newline="\n") as f:
                    f.write(content)
                self._log_msg(f"💾 報表已匯出至: {out_file}")
                messagebox.showinfo("成功", f"報表已安全匯出 (CWE-1236 防護)！\n路徑: {out_file}")
            except Exception as e:
                messagebox.showerror("錯誤", f"匯出失敗: {str(e)}")

    def _update_output_led(self, o_id: str, color: str, text: str):
        """更新特定輸出 LED 指示燈顏色與文字"""
        widget_entry = self.dynamic_widgets.get(o_id)
        if isinstance(widget_entry, tuple) and len(widget_entry) == 3:
            canv, circle, txt = widget_entry
            try:
                canv.itemconfig(circle, fill=color)
                txt.config(text=text, foreground=color)
            except Exception:
                pass

    def step_simulation(self, delta_sec: float = 0.05):
        """單步動態模擬更新、指示燈動態閃爍與 CAN 報文串流"""
        self.sim_time += delta_sec

        # 1. 模擬示波器數據採集
        first_param_id = None
        for p in self.current_schema.get("parameters", []):
            first_param_id = p["id"]
            break

        base_val = self.state_store.get(first_param_id, 2.0) if first_param_id else 2.0
        noise = 0.15 * math.sin(self.sim_time * 6.0)
        curr_val = max(0.0, base_val + noise)

        self.scope_history.append(curr_val)

        # 2. 動態更新輸出監控 gauge
        for out in self.current_schema.get("outputs", []):
            o_id = out["id"]
            if out.get("scope_channel"):
                self.state_store.set(o_id, round(curr_val, 2))
                widget_entry = self.dynamic_widgets.get(o_id)
                if isinstance(widget_entry, ttk.Label):
                    widget_entry.config(text=f"{curr_val:.2f} {out.get('unit', '')}")

        # 3. 實時動態更新所有 LED 指示燈狀態 (依各專案真實業務邏輯)
        p_id_str = self.current_schema.get("project_id", "").lower()
        p_name_str = self.current_schema.get("project_name", "").lower()

        # A. 方向燈專案 (proj_turn_signal): 開啟時以 1.5Hz 頻率亮滅閃爍
        if "turn" in p_id_str or "方向燈" in p_name_str:
            turn_active = self.state_store.get("in_left_turn", False) or self.state_store.get("in_hazard", False)
            blink_phase = (math.sin(self.sim_time * 2.0 * math.pi * 1.5) > 0)
            
            if turn_active:
                lamp_color = "#00FF66" if blink_phase else "#1A1A1A"
                lamp_txt = "🟢 閃爍中 (BLINK)" if blink_phase else "⚫ 熄滅 (OFF)"
                self._update_output_led("out_lamp_left", lamp_color, lamp_txt)
            else:
                self._update_output_led("out_lamp_left", "#333333", "⚫ 待命 (IDLE)")

            volt_val = self.state_store.get("param_voltage", 12.0)
            if volt_val >= 15.0:
                self._update_output_led("out_fault_warn", "#FF3333", "🔴 異常 (ECE R48 FAULT)")
            else:
                self._update_output_led("out_fault_warn", "#333333", "⚫ 正常 (NO FAULT)")

        # B. CAN 節點專案 (PROJ-CAN-745): 通訊正常閃綠燈，過載黃燈，過壓紅燈
        elif "can" in p_id_str or "can" in p_name_str:
            is_can_en = self.state_store.get("can_enable", self.state_store.get("in_can_ack", True))
            v_diff = self.state_store.get("v_diff_voltage", 2.0)
            bus_load = self.state_store.get("bus_load_target", 35.0)

            if not is_can_en:
                self._update_output_led("bus_status_led", "#333333", "⚫ 匯流排關閉")
            elif v_diff >= 3.5:
                self._update_output_led("bus_status_led", "#FF3333", "🔴 差分過壓 (FAULT)")
            elif bus_load >= 80.0:
                self._update_output_led("bus_status_led", "#FFB74D", "🟡 負載壅塞 (WARN)")
            else:
                flicker = (math.sin(self.sim_time * 20.0) > 0)
                self._update_output_led("bus_status_led", "#00FF66" if flicker else "#009933", "🟢 傳輸正常 (ACTIVE)")

            if is_can_en and (self.sim_time - self.last_can_rx_time) >= 0.35:
                self.last_can_rx_time = self.sim_time
                can_frame = CANFrameGenerator.generate_random_frame()
                self.log_can_frame(can_frame)

        # C. ADC 智慧電源專案 (proj_adc_power_guard): 過壓自動觸發保險絲熔斷
        elif "adc" in p_id_str or "power" in p_name_str:
            in_v = self.state_store.get("param_input_voltage", 2.5)
            if in_v > 5.5:
                self._update_output_led("out_fuse_status", "#FF3333", "🔴 保險絲熔斷 (FUSE BLOWN)")
            else:
                self._update_output_led("out_fuse_status", "#00FF66", "🟢 導通正常 (SAFE)")

        # D. 雙 ECU 專案 (proj_dual_ecu_chronos)
        elif "dual" in p_id_str or "ecu" in p_name_str:
            gw_v = self.state_store.get("param_gateway_voltage", 5.0)
            self._update_output_led("out_bcm_status", "#00FF66", "🟢 BCM 正常")
            if gw_v > 5.5:
                self._update_output_led("out_gateway_status", "#FF3333", "🔴 GATEWAY 熔斷斷路")
            else:
                self._update_output_led("out_gateway_status", "#00FF66", "🟢 GATEWAY 正常")

    def _start_main_loop(self):
        """定時更新迴圈"""
        if not self.timer_running:
            return

        self.step_simulation(delta_sec=0.05)

        if hasattr(self, "line_plot") and hasattr(self, "canvas"):
            self.line_plot.set_ydata(list(self.scope_history))
            self.canvas.draw_idle()

        self.root.after(50, self._start_main_loop)


def launch_dashboard():
    root = tk.Tk()
    app = DynamicSchemaDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    launch_dashboard()
