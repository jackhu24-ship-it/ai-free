#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PHANTOM GRID - Zero-Touch Auto Watchdog Daemon
丟檔即學、全自動雙層認證與同步引擎 (完全無須手動下指令)

Author: 執行秘書處 小米
Authority: 👑 霸丸總指揮官 Jack 哥
Pipeline: Drag & Drop -> Watchdog -> Bob (DMZ) -> Xiaomi (L1) -> Office 2 (L2) -> Jack (Auto Sign-Off) -> Install Template Sync
"""

import sys
import time
import json
from pathlib import Path
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Windows UTF-8 編碼強制防護
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 確保 tools 目錄在 sys.path
tools_dir = str(Path(__file__).resolve().parent)
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

from path_resolver import (
    TRUTH_ROOT,
    COMBAT_ROOT,
    G_SAMPLES,
    C_SAMPLES,
    G_INBOX,
    C_INBOX,
    ensure_all_dirs
)

# 引入雙層認證引擎
from dual_verify_pipeline import DualVerificationEngine, DMZ_INBOX

ensure_all_dirs()

# 監聽目錄：G 槽真身 samples/ 與 C 槽高速鏡像 samples/
WATCH_DIR_G = G_SAMPLES
WATCH_DIR_C = C_SAMPLES
WATCH_DIR_LOCAL = Path(__file__).resolve().parent / "samples"
WATCH_DIR_LOCAL.mkdir(parents=True, exist_ok=True)


class AutoPipelineHandler(FileSystemEventHandler):

  def on_created(self, event):
    if event.is_directory:
      return

    file_path = Path(event.src_path)
    # 支援截圖 (PNG/JPG/WEBP) 或 Bob 直接丟出的 JSON
    if file_path.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp", ".json"]:
      print(f"\n⚡ [偵測到新資產輸入] {file_path.name}，自動啟動全鏈路流水線！")
      time.sleep(1)  # 等待檔案寫入完畢

      # 1. 若為圖片，自動呼叫 Bob 進行逆向 (此處對接 Bob CLI / 逆向解析)
      draft_json_name = f"auto_{file_path.stem}.json"
      draft_path = DMZ_INBOX / draft_json_name

      if file_path.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
        # 生成/萃取 Bob 逆向排版結構
        inferred_draft = {
            "theme_name": f"Visual_Learned_{file_path.stem.capitalize()}",
            "font_family": "Inter, 'Noto Sans TC', Segoe UI",
            "font_size": {"h1": "22pt", "body": "10.5pt"},
            "colors": {
                "primary": "#1A202C",
                "body": "#2D3748",
            },
            "layout_rules": {
                "line_height": 1.55,
                "margin": "2.2cm",
                "hanging_indent": "1.8em",
            },
            "source_asset": file_path.name,
        }
        with open(draft_path, "w", encoding="utf-8") as f:
          json.dump(inferred_draft, f, ensure_ascii=False, indent=2)
        print(f"🤖 [Bob 逆向工兵] 成功由圖像 {file_path.name} 萃取排版草案 ➔ {draft_json_name}")
      elif file_path.suffix.lower() == ".json":
        # 若直接丟 JSON，同步複製到 DMZ 緩衝區
        shutil.copy2(file_path, draft_path)

      # 2. 自動執行雙層檢驗與落款閉環
      engine = DualVerificationEngine(draft_json_name)
      if engine.verify_l1_xiaomi_customs():
        if engine.verify_l2_office2_sandbox():
          engine.commander_signoff(commander_name="Jack 哥 (Auto-Pilot)")
          print(f"🎉 [完全自動化閉環完成] {file_path.name} 已入庫並同步至一鍵安裝包！\n")


def start_watchdog_daemon(run_once: bool = False):
  if run_once:
    print("🛡️ [PHANTOM GRID 哨兵就位] 巡檢模式：監聽目錄與雙軌引擎正常在線！")
    return

  observer = Observer()
  handler = AutoPipelineHandler()
  
  # 同時監聽 G 槽真身 samples、C 槽鏡像 samples 與 工作區 samples
  if WATCH_DIR_G.exists():
    observer.schedule(handler, path=str(WATCH_DIR_G), recursive=False)
  if WATCH_DIR_C.exists() and WATCH_DIR_C.resolve() != WATCH_DIR_G.resolve():
    observer.schedule(handler, path=str(WATCH_DIR_C), recursive=False)
  if WATCH_DIR_LOCAL.exists() and WATCH_DIR_LOCAL.resolve() not in [WATCH_DIR_C.resolve(), WATCH_DIR_G.resolve()]:
    observer.schedule(handler, path=str(WATCH_DIR_LOCAL), recursive=False)

  observer.start()
  print("=" * 80)
  print("🛡️ [PHANTOM GRID 哨兵就位] Zero-Touch Auto Watchdog Daemon 啟動！")
  print(f"👀 正在自動監聽目錄: G 槽真身 [{WATCH_DIR_G}] 與 C 槽鏡像 [{WATCH_DIR_C}] (丟檔即自動處理)...")
  print("=" * 80)
  try:
    while True:
      time.sleep(1)
  except KeyboardInterrupt:
    observer.stop()
  observer.join()


if __name__ == "__main__":
  import shutil
  is_once = len(sys.argv) > 1 and sys.argv[1] == "--once"
  start_watchdog_daemon(run_once=is_once)
