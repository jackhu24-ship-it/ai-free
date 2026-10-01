#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
PHANTOM GRID - Dynamic Path Resolver & Drive Locator
跨電腦災難復原、動態磁碟代號尋標與三層路徑解耦核心模組

憲法鐵律：
1. G 槽為唯一真理來源 (Single Source of Truth)，所有產出第一時間寫入 G 槽。
2. C 槽為高速戰鬥鏡像 (Combat Mirror)，僅作為讀取與快顯投影，可隨時抹除還原。
3. 絕不寫死 C:\Users\{username}，根目錄定錨 C:\260728-code\ 或調用 Path.home()。
"""

import os
import sys
import string
import shutil
from pathlib import Path

# 1. 戰鬥鏡像絕對定錨根目錄 (與使用者名稱 100% 解耦)
COMBAT_ROOT = Path(r"C:\260728-code")

# 2. 家目錄動態解析 (若必須存取 AppData / .config)
USER_HOME = Path.home()
USER_APPDATA = Path(os.environ.get("APPDATA", USER_HOME / "AppData" / "Roaming"))

def find_g_drive_truth() -> Path:
    """自動探測 Google 雲端硬碟真身根目錄，無視硬碟代號 (G:/H:/D:) 飄移"""
    custom_truth = os.environ.get("PHANTOM_TRUTH_DIR")
    if custom_truth and Path(custom_truth).exists():
        return Path(custom_truth)

    default_target = Path(r"G:\我的雲端硬碟\260803_opencode")
    if (default_target / "AGENTS.md").exists():
        return default_target

    possible_subdirs = [
        "我的雲端硬碟/260803_opencode",
        "My Drive/260803_opencode",
        "260803_opencode"
    ]
    
    for letter in string.ascii_uppercase:
        for sub in possible_subdirs:
            candidate = Path(f"{letter}:/{sub}")
            if (candidate / "AGENTS.md").exists():
                return candidate

    return default_target

# 3. 解析當前環境中的真身與鏡像指針
TRUTH_ROOT = find_g_drive_truth()

# 4. 標準子目錄對照表 (真身在 G，鏡像在 C)
G_SAMPLES = TRUTH_ROOT / "samples"
G_INBOX = TRUTH_ROOT / "inbox" / "bob_drafts"
G_KNOWLEDGE_TYPO = TRUTH_ROOT / "02_Knowledge" / "Typography"
G_INSTALLER_TPL = TRUTH_ROOT / "工具安裝包" / "template"
G_HANDOFF = TRUTH_ROOT / "handoff.md"
G_AGENTS = TRUTH_ROOT / "AGENTS.md"

C_SAMPLES = COMBAT_ROOT / "samples"
C_INBOX = COMBAT_ROOT / "inbox" / "bob_drafts"
C_KNOWLEDGE_TYPO = COMBAT_ROOT / "02_Knowledge" / "Typography"
C_INSTALLER_TPL = COMBAT_ROOT / "工具安裝包" / "template"
C_HANDOFF = COMBAT_ROOT / "handoff.md"
C_AGENTS = COMBAT_ROOT / "AGENTS.md"

def ensure_all_dirs():
    """保證真身與鏡像目錄雙向存在"""
    for p in [G_SAMPLES, G_INBOX, G_KNOWLEDGE_TYPO, G_INSTALLER_TPL,
              C_SAMPLES, C_INBOX, C_KNOWLEDGE_TYPO, C_INSTALLER_TPL]:
        try:
            p.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

def save_truth_then_mirror(rel_path: str, data_bytes: bytes) -> tuple:
    """
    資料流動核心規範：
    1. 真身落地：寫入 G 槽真身金庫
    2. 戰鬥鏡像：單向投影回 C 槽極速鏡像
    """
    ensure_all_dirs()
    g_file = TRUTH_ROOT / rel_path
    c_file = COMBAT_ROOT / rel_path

    g_file.parent.mkdir(parents=True, exist_ok=True)
    c_file.parent.mkdir(parents=True, exist_ok=True)

    with open(g_file, "wb") as f:
        f.write(data_bytes)

    shutil.copy2(g_file, c_file)

    return g_file, c_file

if __name__ == "__main__":
    ensure_all_dirs()
    print("=" * 60)
    print("🛡️  PHANTOM GRID 動態路徑解耦與尋標檢驗報告")
    print("=" * 60)
    print(f"• 戰鬥鏡像根目錄 (Combat Mirror) : {COMBAT_ROOT} (解耦 Username: OK)")
    print(f"• 真身金庫根目錄 (Truth Root)    : {TRUTH_ROOT}")
    print(f"• 當前使用者家目錄 (User Home)  : {USER_HOME}")
    print(f"• 當前 AppData 目錄 (User AppData): {USER_APPDATA}")
    print(f"• 真身 AGENTS.md 存在性         : {G_AGENTS.exists()}")
    print(f"• 鏡像 AGENTS.md 存在性         : {C_AGENTS.exists()}")
    print("=" * 60)
