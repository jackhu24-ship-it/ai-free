#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
作者：小幫手（A03）
用途：學生座號抽籤 + 課堂倒數計時器
功能說明：
1. 抽籤區域會隨機顯示 1~35 的座號，點擊「抽籤」按鈕時會以動畫方式快速跳動 1 秒後停在一個座號。
2. 倒數計時區域可以自行輸入秒數，並提供「開始/暫停」與「重置」按鈕。
3. 介面使用 Tkinter，佈局以簡潔為主，所有文字均使用繁體中文。
4. 內部註解完整說明每個函式、變數用途，方便日後維護。
"""

from __future__ import annotations

import tkinter as tk
import random
import time
from typing import Optional

# ---------------------------------------------------------------------------
# 全域設定
# ---------------------------------------------------------------------------
# 抽籤座號範圍
MIN_SEAT = 1
MAX_SEAT = 35
# 抽籤動畫持續時間（秒）
ANIMATION_DURATION = 1.0
# 抽籤動畫更新頻率（毫秒）
ANIMATION_DELAY = 50
# ---------------------------------------------------------------------------

class SeatPicker(tk.Frame):
    """座號抽籤小工具"""

    def __init__(self, master: tk.Widget):
        super().__init__(master)
        self.pack(padx=10, pady=10, fill="x")

        # 顯示座號的 Label
        self.result_var = tk.StringVar(value="尚未抽籤")
        self.result_label = tk.Label(
            self,
            textvariable=self.result_var,
            font=("微軟正黑體", 24),
            width=12,
            relief="groove",
            bd=2,
        )
        self.result_label.pack(pady=(0, 10))

        # 抽籤按鈕
        self.pick_button = tk.Button(
            self,
            text="抽籤",
            command=self.start_animation,
            width=8,
            font=("微軟正黑體", 14),
        )
        self.pick_button.pack()

        self.is_animating = False
        self.animation_start_time: float = 0.0

    def start_animation(self) -> None:
        """啟動抽籤動畫"""
        if self.is_animating:
            # 如果還在動畫中，先忽略
            return
        self.is_animating = True
        self.animation_start_time = time.time()
        self.update_animation()

    def update_animation(self) -> None:
        """抽籤動畫每個步驟，直到時間結束"""
        elapsed = time.time() - self.animation_start_time
        if elapsed < ANIMATION_DURATION:
            # 仍在動畫中，隨機產生座號顯示
            seat = random.randint(MIN_SEAT, MAX_SEAT)
            self.result_var.set(str(seat))
            # 下一個更新
            self.after(ANIMATION_DELAY, self.update_animation)
            return
        # 動畫結束，隨機選一個座號放入
        final_seat = random.randint(MIN_SEAT, MAX_SEAT)
        self.result_var.set(str(final_seat))
        self.is_animating = False

# ---------------------------------------------------------------------------

class CountdownTimer(tk.Frame):
    """課堂倒數計時器"""

    def __init__(self, master: tk.Widget):
        super().__init__(master)
        self.pack(padx=10, pady=10, fill="x")

        # 輸入秒數的 Entry
        input_frame = tk.Frame(self)
        input_frame.pack(fill="x", pady=(0, 10))
        tk.Label(
            input_frame,
            text="請輸入秒數：",
            font=("微軟正黑體", 12),
        ).pack(side="left")
        self.seconds_var = tk.StringVar(value="60")
        self.seconds_entry = tk.Entry(
            input_frame,
            textvariable=self.seconds_var,
            width=8,
            font=("微軟正黑體", 12),
        )
        self.seconds_entry.pack(side="left", padx=(5, 10))

        # 顯示剩餘時間
        self.time_var = tk.StringVar(value="00:00")
        self.time_label = tk.Label(
            self,
            textvariable=self.time_var,
            font=("微軟正黑體", 36),
        )
        self.time_label.pack(pady=(0, 10))

        # 控制按鈕
        button_frame = tk.Frame(self)
        button_frame.pack()
        self.start_button = tk.Button(
            button_frame,
            text="開始",
            command=self.start_timer,
            width=6,
            font=("微軟正黑體", 12),
        )
        self.start_button.pack(side="left", padx=5)
        self.pause_button = tk.Button(
            button_frame,
            text="暫停",
            command=self.pause_timer,
            width=6,
            font=("微軟正黑體", 12),
            state="disabled",
        )
        self.pause_button.pack(side="left", padx=5)
        self.reset_button = tk.Button(
            button_frame,
            text="重置",
            command=self.reset_timer,
            width=6,
            font=("微軟正黑體", 12),
        )
        self.reset_button.pack(side="left", padx=5)

        # 內部狀態
        self.total_seconds: int = 60
        self.remaining_seconds: int = 60
        self._timer_job: Optional[str] = None

    def parse_seconds(self) -> int:
        """將使用者輸入轉成秒數，預設 60 秒"""
        try:
            val = int(self.seconds_var.get())
            if val < 0:
                raise ValueError
            return val
        except Exception:
            return 60

    def update_display(self) -> None:
        """更新剩餘時間顯示"""
        minutes, seconds = divmod(self.remaining_seconds, 60)
        self.time_var.set(f"{minutes:02d}:{seconds:02d}")

    def tick(self) -> None:
        """一秒倒數"""
        if self.remaining_seconds <= 0:
            # 時間結束，停用 timer
            self._timer_job = None
            self.pause_button.config(state="disabled")
            self.start_button.config(state="normal")
            return
        self.remaining_seconds -= 1
        self.update_display()
        # 排程下一秒
        self._timer_job = self.after(1000, self.tick)

    def start_timer(self) -> None:
        """開始倒數"""
        if self._timer_job is not None:
            # 已在倒數中
            return
        # 重新取秒數
        self.total_seconds = self.parse_seconds()
        self.remaining_seconds = self.total_seconds
        self.update_display()
        self._timer_job = self.after(1000, self.tick)
        self.start_button.config(state="disabled")
        self.pause_button.config(state="normal")

    def pause_timer(self) -> None:
        """暫停倒數"""
        if self._timer_job is not None:
            self.after_cancel(self._timer_job)
            self._timer_job = None
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled")

    def reset_timer(self) -> None:
        """重置倒數"""
        if self._timer_job is not None:
            self.after_cancel(self._timer_job)
            self._timer_job = None
        self.total_seconds = self.parse_seconds()
        self.remaining_seconds = self.total_seconds
        self.update_display()
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled")

# ---------------------------------------------------------------------------

class App(tk.Tk):
    """主程式，整合抽籤與倒數計時器"""

    def __init__(self):
        super().__init__()
        self.title("座號抽籤 & 倒數計時器")
        self.geometry("400x400")
        self.resizable(False, False)

        # 抽籤模組
        SeatPicker(self)
        # 倒數計時器模組
        CountdownTimer(self)

if __name__ == "__main__":
    app = App()
    app.mainloop()
""