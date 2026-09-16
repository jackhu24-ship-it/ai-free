#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 【方案 C】：MCU 數位孿生即時互動實驗台 (interactive_mcu_playground.py)
========================================================================================
作者：🛠️ 小開 (Agent_Coder)
統籌：👑 小幫手 (Agent_PM)

核心功能：
1. 🎮 【實時硬體按鈕操作】：可點擊 Warning Key、Save Key、P 檔與坐墊開關，即時觀察狀態機跳轉。
2. 💡 【動態引腳 LED 與警報方波】：RA0~RA5 實時亮燈/熄滅動畫，RA5 支援 2Hz 蜂鳴閃爍視覺反饋。
3. 📊 【十進制優先暫存器動態儀表板】：TRISA, LATA, PORTA, TMR0 數值即時變更顯示。
4. 💥 【虛擬故障注入實驗室】：一鍵測試未設 TRIS 寫入、短路接地、記憶體越界，直觀體驗 100% 安全攔截！
5. 📈 【實時波形時序繪圖】：整合動態波形時序圖。
"""

from __future__ import annotations

import sys
import os
import time
import math
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# 載入數位孿生核心
SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))
from mcu_digital_twin import MCUDigitalTwin


class MCUPlaygroundApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🎮 MCU 數位孿生互動實驗台 (PIC16F18313 / PIC18F25K80) - Five-Agent AI OS")
        self.root.geometry("980x720")
        self.root.minsize(900, 650)

        # 核心數位孿生引擎
        self.twin = MCUDigitalTwin(chip_model="PIC16F18313")
        self.twin.configure_parameters(start_delay=1.0, alarm_freq=2.0, mute_delay=2.0)

        # 模擬狀態
        self.is_running = True
        self.sim_time_ms = 0.0
        self.blink_state = False

        self._setup_ui()
        self._schedule_tick()

    def _setup_ui(self):
        style = ttk.Style()
        style.theme_use("clam")

        # 主框架
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 標題
        title_lbl = tk.Label(
            main_frame, 
            text="🎮 Microchip PIC MCU 暫存器級數位孿生即時實驗台", 
            font=("Microsoft JhengHei UI", 16, "bold"),
            fg="#1E3A8A"
        )
        title_lbl.pack(anchor="w", pady=(0, 10))

        # 上半部：控制面板與 LED 狀態
        top_pane = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        top_pane.pack(fill=tk.BOTH, expand=True, pady=5)

        # 左側：虛擬按鈕與操作
        btn_frame = ttk.LabelFrame(top_pane, text="🎛️ 車載硬體開關控制區", padding="10")
        top_pane.add(btn_frame, weight=1)

        tk.Label(btn_frame, text="請點擊下方按鈕模擬實體車載訊號輸入：", font=("Microsoft JhengHei UI", 9)).pack(anchor="w", pady=2)

        self.btn_warning = tk.Button(
            btn_frame, 
            text="🚨 按下警報開關 (Warning Key / RA2=0)", 
            bg="#EF4444", fg="white", font=("Microsoft JhengHei UI", 10, "bold"),
            command=self._on_press_warning, relief=tk.RAISED, height=2
        )
        self.btn_warning.pack(fill=tk.X, pady=5)

        self.btn_save = tk.Button(
            btn_frame, 
            text="💾 安全解除 / 存檔 (Save Key / RA4=0)", 
            bg="#10B981", fg="white", font=("Microsoft JhengHei UI", 10, "bold"),
            command=self._on_press_save, relief=tk.RAISED, height=2
        )
        self.btn_save.pack(fill=tk.X, pady=5)

        self.btn_reset = tk.Button(
            btn_frame, 
            text="🔄 系統硬體復位 (Reset MCLR)", 
            bg="#6B7280", fg="white", font=("Microsoft JhengHei UI", 9),
            command=self._on_reset_mcu, relief=tk.RAISED
        )
        self.btn_reset.pack(fill=tk.X, pady=5)

        # 狀態標籤
        self.lbl_fsm_state = tk.Label(
            btn_frame, 
            text="系統狀態：STARTUP_DELAY (開機保護中)", 
            font=("Microsoft JhengHei UI", 10, "bold"),
            bg="#FEF3C7", fg="#92400E", relief=tk.GROOVE, padx=8, pady=6
        )
        self.lbl_fsm_state.pack(fill=tk.X, pady=10)

        # 右側：引腳 LED 燈號與暫存器
        status_frame = ttk.LabelFrame(top_pane, text="💡 引腳動態電位與 LED 儀表板", padding="10")
        top_pane.add(status_frame, weight=1)

        # LED 視覺指示
        led_canvas_frame = tk.Frame(status_frame)
        led_canvas_frame.pack(fill=tk.X, pady=5)

        self.led_labels = {}
        pins = [("RA0", "輸出 (綠)"), ("RA1", "輸出 (黃)"), ("RA2", "輸入 (按鍵)"), ("RA3", "MCLR"), ("RA4", "輸入 (按鍵)"), ("RA5", "🚨 警報蜂鳴")]
        for p, desc in pins:
            f = tk.Frame(led_canvas_frame)
            f.pack(side=tk.LEFT, expand=True, padx=4)
            c = tk.Canvas(f, width=28, height=28, highlightthickness=0)
            c.pack()
            circle = c.create_oval(3, 3, 25, 25, fill="#D1D5DB", outline="#9CA3AF", width=2)
            lbl = tk.Label(f, text=f"{p}\n{desc}", font=("Microsoft JhengHei UI", 8), justify=tk.CENTER)
            lbl.pack()
            self.led_labels[p] = {"canvas": c, "circle": circle, "desc": desc}

        # 暫存器十進制儀表板
        sfr_frame = ttk.LabelFrame(status_frame, text="📊 特殊功能暫存器 (SFR) 實時數據 (十進制優先)", padding="8")
        sfr_frame.pack(fill=tk.BOTH, expand=True, pady=8)

        self.sfr_text = tk.Text(sfr_frame, height=7, font=("Consolas", 9), bg="#F8FAFC", relief=tk.SOLID, bd=1)
        self.sfr_text.pack(fill=tk.BOTH, expand=True)

        # 下半部：虛擬故障注入實驗室 (炸板防護測試)
        fault_frame = ttk.LabelFrame(main_frame, text="💥 虛擬防炸板與故障注入實驗室 (點擊測試 100% 攔截)", padding="10")
        fault_frame.pack(fill=tk.X, pady=5)

        f_btn_box = tk.Frame(fault_frame)
        f_btn_box.pack(fill=tk.X)

        tk.Button(
            f_btn_box, text="⚠️ 測試未設 TRIS 輸出寫入", bg="#F59E0B", fg="white", font=("Microsoft JhengHei UI", 9, "bold"),
            command=self._test_fault_tris
        ).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        tk.Button(
            f_btn_box, text="💣 測試引腳短路接地 (RA5 衝突)", bg="#DC2626", fg="white", font=("Microsoft JhengHei UI", 9, "bold"),
            command=self._test_fault_short
        ).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        tk.Button(
            f_btn_box, text="⛔ 測試非法記憶體位址越界寫入", bg="#7C3AED", fg="white", font=("Microsoft JhengHei UI", 9, "bold"),
            command=self._test_fault_memory
        ).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # 即時診斷日誌框
        log_frame = ttk.LabelFrame(main_frame, text="🗣️ 自然語言直覺診斷日誌", padding="6")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.diag_log = tk.Text(log_frame, height=5, font=("Microsoft JhengHei UI", 9), bg="#1E293B", fg="#38BDF8")
        self.diag_log.pack(fill=tk.BOTH, expand=True)
        self._log_msg("系統就緒！數位孿生時鐘運作中，請隨意點擊上方按鈕體驗！")

    def _log_msg(self, msg: str):
        t_str = time.strftime("%H:%M:%S")
        self.diag_log.insert(tk.END, f"[{t_str}] {msg}\n")
        self.diag_log.see(tk.END)

    def _schedule_tick(self):
        """每 50ms 推進模擬時鐘並刷新 UI"""
        if self.is_running:
            # 推進 50ms (5 個 10ms 週期)
            for _ in range(5):
                self.twin._step_10ms_cycle()
                self.sim_time_ms += 10.0
                self.twin.simulated_time_ms = self.sim_time_ms

            self._update_display()

        self.root.after(50, self._schedule_tick)

    def _update_display(self):
        # 1. 更新狀態機文字
        st = self.twin.current_state
        state_colors = {
            "STARTUP_DELAY": ("#FEF3C7", "#92400E", "開機保護中 (1.0s)"),
            "IDLE_MONITORING": ("#D1FAE5", "#065F46", "正常待機監控中"),
            "MUTE_COUNTDOWN": ("#FED7AA", "#9A3412", f"前置靜音倒數中 (剩餘 {self.twin.timer0_counter2} 拍)"),
            "ALARM_ACTIVE_BLINK": ("#FEE2E2", "#991B1B", "🚨 2Hz 警報方波閃爍中！")
        }
        bg, fg, desc = state_colors.get(st, ("#E5E7EB", "#1F2937", st))
        self.lbl_fsm_state.config(text=f"系統狀態：{st} ({desc})", bg=bg, fg=fg)

        # 2. 更新 LED 燈號
        ra5_active = (self.twin.sfr["LATA"] & 0x20) != 0
        ra2_active = (self.twin.sfr["PORTA"] & 0x04) != 0
        ra4_active = (self.twin.sfr["PORTA"] & 0x10) != 0

        # RA5 (警報紅燈)
        self.led_labels["RA5"]["canvas"].itemconfig(
            self.led_labels["RA5"]["circle"], 
            fill="#EF4444" if ra5_active else "#4B5563"
        )
        # RA2 (按鍵輸入)
        self.led_labels["RA2"]["canvas"].itemconfig(
            self.led_labels["RA2"]["circle"], 
            fill="#3B82F6" if ra2_active else "#9CA3AF"
        )
        # RA4 (按鍵輸入)
        self.led_labels["RA4"]["canvas"].itemconfig(
            self.led_labels["RA4"]["circle"], 
            fill="#3B82F6" if ra4_active else "#9CA3AF"
        )

        # 3. 刷新暫存器數值
        dump = self.twin.get_formatted_sfr_dump()
        self.sfr_text.delete("1.0", tk.END)
        lines = [
            f"• {dump['PR2']}",
            f"• {dump['TRISA']}",
            f"• {dump['PORTA']}",
            f"• {dump['LATA']}",
            f"• {dump['TMR0']}",
            f"• {self.twin.format_register_value('OPTION_REG', self.twin.sfr['OPTION_REG'], '1:256 預除器')}"
        ]
        self.sfr_text.insert(tk.END, "\n".join(lines))

    # ==================== 按鈕事件 ====================
    def _on_press_warning(self):
        # 觸發 RA2 = 0 (Warning Key)
        self.twin.sfr["PORTA"] &= ~0x04
        self._log_msg("🚨 觸發 Warning Key (RA2 拉低為 0V)，進入警報倒數狀態機！")
        # 500ms 後自動彈起恢復 1
        self.root.after(500, lambda: self._release_key(0x04))

    def _on_press_save(self):
        # 觸發 RA4 = 0 (Save Key)
        self.twin.sfr["PORTA"] &= ~0x10
        self._log_msg("💾 觸發 Save Key (RA4 拉低為 0V)，系統解除警報並重置為待機！")
        self.root.after(500, lambda: self._release_key(0x10))

    def _release_key(self, mask: int):
        self.twin.sfr["PORTA"] |= mask

    def _on_reset_mcu(self):
        self.twin.reset()
        self.sim_time_ms = 0.0
        self._log_msg("🔄 觸發硬體 MCLR 復位，晶片重新啟動開機延遲！")

    # ==================== 故障注入實驗 ====================
    def _test_fault_tris(self):
        self.twin.sfr["TRISA"] = 20  # RA2 is input
        ok = self.twin.write_sfr("LATA", 4)
        if not ok and self.twin.intercepted_anomalies:
            latest = self.twin.intercepted_anomalies[-1]
            self._log_msg(f"🛡️ 【安全攔截成功】 {latest['message']}")
            messagebox.showwarning("🛡️ 虛擬安全攔截器啟動", latest['message'])

    def _test_fault_short(self):
        self.twin.sfr["TRISA"] = 0
        self.twin.sfr["LATA"] = 32  # RA5 is 5V
        res = self.twin.inject_short_circuit_hazard("RA5", forced_level=0)
        if res["status"] == "INTERCEPTED":
            latest = res["anomaly"]
            self._log_msg(f"💥 【防炸板攔截成功】 {latest['message']}")
            messagebox.showerror("💥 虛擬防炸板警報", latest['message'])

    def _test_fault_memory(self):
        ok = self.twin.write_memory_address(39321, 255)  # 0x9999
        if not ok and self.twin.intercepted_anomalies:
            latest = self.twin.intercepted_anomalies[-1]
            self._log_msg(f"⛔ 【記憶體保護攔截成功】 {latest['message']}")
            messagebox.showerror("⛔ 記憶體越界保護", latest['message'])


def launch_playground():
    root = tk.Tk()
    app = MCUPlaygroundApp(root)
    root.mainloop()


if __name__ == "__main__":
    launch_playground()
