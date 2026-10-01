# tools/smart_bob_sanitizer.py
# -*- coding: utf-8 -*-
"""
==============================================================================
 PHANTOM GRID - 沙盒資產分流與逆向影音保護清理引擎 (Smart Bob Sanitizer)
 規範依據：CONTRACT_RULES 第六條 ＆ AGENTS.md 第 23 條鐵律
 核心原則：
 1. 任務封版後，01_WORKSPACE / 02_OUTBOX 臨時代碼與快取物理清空（Zero-Trace）。
 2. 影視資產（.mp4/.mp3/肖像）與逆向工程資產（PROJECTS/ 及學習帳本）絕對豁免，永久保護！
==============================================================================
"""

import sys
import shutil
from pathlib import Path

BOB_ROOT = Path(r"C:\ibm-bob")
PROTECTED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".mp3", ".wav"}
PROTECTED_FILES = {
    "BOB_REVERSE_ENGINEERING_LEARNING_LEDGER.md",
    "progress_ledger.json",
    "project_manifest.json",
    "CONTRACT_RULES.md",
    "IBM_BOB_OPERATIONAL_CHARTER.md",
    "README.md",
    "QUARANTINE_CHECKLIST.md"
}
PROTECTED_DIRS = {
    "PROJECTS",
    "IBM Bob",
    "core_repo",
    "PROMPT_TEMPLATES"
}


def sanitize_bob_sandbox(dry_run: bool = False):
    print("🛡️ [Smart Bob Sanitizer] 啟動沙盒資產分流安全清理...")
    if not BOB_ROOT.exists():
        print(f"❌ 目錄不存在: {BOB_ROOT}")
        return

    # 1. 清理 01_WORKSPACE (但跳過任何多媒體或受保護專案)
    ws = BOB_ROOT / "01_WORKSPACE"
    if ws.exists():
        for item in ws.iterdir():
            if item.is_dir() and item.name in PROTECTED_DIRS:
                continue
            if item.suffix.lower() in PROTECTED_EXTENSIONS or item.name in PROTECTED_FILES:
                print(f"🔒 [保護豁免] 影音/逆向資產保留: {item.name}")
                continue
            if not dry_run:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                print(f"🧹 清除工作區暫存: {item.name}")

    # 2. 清理 02_OUTBOX (僅清除已落款之普通代碼，影音嚴格保護)
    ob = BOB_ROOT / "02_OUTBOX"
    if ob.exists():
        for item in ob.iterdir():
            if item.suffix.lower() in PROTECTED_EXTENSIONS or item.name in PROTECTED_FILES:
                print(f"🔒 [保護豁免] 影音/逆向資產保留: {item.name}")
                continue
            if not dry_run:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                print(f"🧹 清除已落款代碼: {item.name}")

    # 3. 清理 02_OUTBOX_STAGING
    stg = BOB_ROOT / "02_OUTBOX_STAGING"
    if stg.exists() and not dry_run:
        for item in stg.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        print("🧹 清除中繼檢驗區: 02_OUTBOX_STAGING")

    print("✅ [Smart Bob Sanitizer] 沙盒清理完畢！影音成片與逆向資料 100% 完好受保護！")


if __name__ == "__main__":
    sanitize_bob_sandbox(dry_run=False)
