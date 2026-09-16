#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 新電腦初始化與乾淨出廠部署腳本 (init_fresh_workspace.py)
作者：🛠️ 小開 (Agent_Coder)
審查：🐎 小馬 (Agent_Reviewer)
統籌：👑 小幫手 (Agent_PM)

核心功能：
1. 自動建立/修復完整目錄結構 (00_System, 01_Memory, 02_Knowledge, DATA, SRC, TEST)
2. 自動生成全新空白且符合規格之 01_Memory/Memory_Log.md (Day-0 乾淨狀態)
3. 自動初始化全新 DATA/master_ledger.json 主帳本
4. 執行核心調度引擎 (core_dispatcher.py) 與 MCP 健康體檢，確保新機 100% 隨插即用
"""

from __future__ import annotations

import sys
import os
import json
import argparse
import datetime
from pathlib import Path
from typing import Dict, Any, List

# 強制 Windows 標準輸出為 UTF-8
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
SYSTEM_DIR = WORKSPACE_ROOT / "00_System"
MEMORY_DIR = WORKSPACE_ROOT / "01_Memory"
KNOWLEDGE_DIR = WORKSPACE_ROOT / "02_Knowledge"
DATA_DIR = WORKSPACE_ROOT / "DATA"
SRC_DIR = WORKSPACE_ROOT / "SRC"
TEST_DIR = WORKSPACE_ROOT / "TEST"

MEMORY_LOG_FILE = MEMORY_DIR / "Memory_Log.md"
MASTER_LEDGER_FILE = DATA_DIR / "master_ledger.json"


def init_directories() -> None:
    """建立所有必備目錄"""
    dirs = [
        SYSTEM_DIR / "Agents",
        MEMORY_DIR,
        KNOWLEDGE_DIR / "Specs",
        KNOWLEDGE_DIR / "Manuals",
        KNOWLEDGE_DIR / "Skills_Index",
        DATA_DIR,
        SRC_DIR,
        TEST_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    print("📁 [1/4] 核心目錄結構檢查與建立完成。")


def init_fresh_memory_log(force_overwrite: bool = False) -> None:
    """初始化全新乾淨的 Memory_Log.md"""
    if MEMORY_LOG_FILE.exists() and not force_overwrite:
        print(f"ℹ️ [2/4] Memory_Log.md 已存在，略過生成 (若需重設請使用 --force 參數)。")
        return

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    template = f"""# 01_Memory / Memory_Log.md（跨 Agent 共享動態記憶日誌）

> 本文件為所有 Agent 共享的動態決策與偏好日誌。  
> 格式規範：`- [YYYY-MM-DD] [Agent_Role] 決策/進度/偏好內容`

---

## 📅 {datetime.date.today().year} 年決策與進度時間軸

### 🚀 系統出廠初始化 (Day-0)
- [{today_str}] [PM] 系統於新工作環境執行 Clean Deployment 出廠初始化完成，四大 Agent（小幫手、小開、小馬、小Ｏ）就緒。

---
*(後續由各 Agent 透過 save_memory 自動追加最新決策)*
"""
    with open(MEMORY_LOG_FILE, "w", encoding="utf-8", errors="replace") as f:
        f.write(template)
    print(f"✨ [2/4] 已生成全新乾淨之 Memory_Log.md (Day-0 出廠狀態)。")


def init_fresh_master_ledger(force_overwrite: bool = False) -> None:
    """初始化全新乾淨的 master_ledger.json"""
    if MASTER_LEDGER_FILE.exists() and not force_overwrite:
        print(f"ℹ️ [3/4] master_ledger.json 已存在，略過重設。")
        return

    init_ledger = {
        "system_name": "Five-Agent AI OS Master Ledger",
        "version": "1.0.0",
        "initialized_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_records": 0,
        "records": []
    }
    with open(MASTER_LEDGER_FILE, "w", encoding="utf-8", errors="replace") as f:
        json.dump(init_ledger, f, ensure_ascii=False, indent=2)
    print(f"✨ [3/4] 已初始化全新 DATA/master_ledger.json 主帳本。")


def run_system_health_check() -> bool:
    """執行全系統健康檢查，確認 core_dispatcher 具備就緒調度能力"""
    print("🔍 [4/4] 正在進行新機核心調度引擎 (core_dispatcher) 健康檢查...")
    try:
        import asyncio
        from core_dispatcher import CoreDispatcher, TaskRequest

        dispatcher = CoreDispatcher()
        req = TaskRequest(
            task_id="HEALTH-CHECK-INIT",
            task_type="PURE_CODE",
            raw_prompt="執行新機初始化健康檢查"
        )
        res = asyncio.run(dispatcher.dispatch_task(req))
        if res.final_status == "SUCCESS":
            print(f"   -> ✅ 核心調度主幹 (CoreDispatcher) 測試通過 (耗時: {res.execution_time_sec}s)")
            return True
        else:
            print(f"   -> ❌ 健康檢查未通過: {res.error_message}")
            return False
    except Exception as e:
        print(f"   -> ⚠️ 健康檢查遭遇異常 (請確認相依套件): {e}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Five-Agent AI OS 新電腦出廠初始化工具")
    parser.add_argument("--force", action="store_true", help="強制重設 Memory_Log.md 與 master_ledger.json")
    parser.add_argument("--check-only", action="store_true", help="僅執行系統健康檢查")
    args = parser.parse_args()

    print("\n" + "="*70)
    print("🌟 [Clean-Deployment] Five-Agent AI OS 新電腦出廠部署工具")
    print("="*70 + "\n")

    if args.check_only:
        run_system_health_check()
        return

    init_directories()
    init_fresh_memory_log(force_overwrite=args.force)
    init_fresh_master_ledger(force_overwrite=args.force)
    all_ok = run_system_health_check()

    print("\n" + "="*70)
    if all_ok:
        print("🎉 [部署成功] 新電腦環境初始化 100% 完成！系統隨插即用！")
    else:
        print("⚠️ [部分完成] 目錄與檔案已建立，請確認 Python 環境與相依模組。")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
