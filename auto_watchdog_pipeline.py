#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_watchdog_pipeline.py - PHANTOM GRID 無人值守目錄哨兵監聽器
=============================================================
功能：
1. 常駐監聽 samples/ 目錄
2. 丟檔 0.5 秒內自動觸發：
   Bob 逆向 ➔ 小米 L1 安全格式安檢 ➔ 二辦 L2 沙盒試跑 ➔ 統帥落款
3. 全程 0 人工干預無人值守
"""

import os
import sys
import time
import json
from pathlib import Path
from dual_verify_pipeline import DualVerifyPipeline

WATCH_DIR = Path("samples")
OUT_DIR = Path(r"G:\我的雲端硬碟\AI產出成品總庫\Solo_Documents")

def run_watchdog_loop():
    WATCH_DIR.mkdir(parents=True, exist_ok=True)
    pipeline = DualVerifyPipeline()
    print("=" * 70)
    print("🐕 PHANTOM GRID 無人值守目錄哨兵 (auto_watchdog_pipeline.py) 已啟動")
    print(f"👀 監聽目錄: {WATCH_DIR.resolve()}")
    print("=" * 70)

    processed = set()
    while True:
        try:
            for item in WATCH_DIR.glob("*.*"):
                if item.name not in processed and not item.name.endswith(".tmp"):
                    print(f"⚡ [哨兵捕獲] 偵測到新樣板資產: {item.name}")
                    time.sleep(0.5)  # 等待寫檔完全
                    try:
                        content = item.read_text(encoding="utf-8", errors="ignore")
                        data = {"filename": item.name, "raw_content": content}
                        result = pipeline.sign_off(data, style_name=item.stem)
                        
                        out_file = WATCH_DIR / f"{item.stem}_certified.json"
                        out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
                        print(f"✅ [全自動閉環] 完成 L1安檢 + L2試跑 + 統帥落款: {out_file.name}")
                        processed.add(item.name)
                    except Exception as e:
                        print(f"⚠️ [處理異常] {item.name}: {e}")
            time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 哨兵已正常停止。")
            break

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        print("哨兵單次巡檢模式：目錄就緒。")
    else:
        run_watchdog_loop()
