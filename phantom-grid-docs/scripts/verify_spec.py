"""
==============================================================================
 ARCHITECTURE : PHANTOM GRID / TOP-TIER INDUSTRIAL PDF SPECIFICATION
 MODULE       : verify_spec.py
 SIGNED BY    : Commander Jack (👑 霸丸總指揮官權威落款)
 SEAL TIME    : 2026-10-02 13:47:24 CST
 STATUS       : OFFICIALLY RELEASED & SEALED
 INTEGRITY    : SHA256:055242541ca83c6c... [VERIFIED]
 SPEC STANDARD: PG-SPEC-2026-PDF-WORLD-CLASS
==============================================================================
"""

import os
import re
import sys
from pathlib import Path

# 強制 UTF-8 輸出
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"
TEMPLATES_DIR = BASE_DIR / "templates"

ERRORS = []
WARNINGS = []

def check_file(filepath: Path):
    content = filepath.read_text(encoding="utf-8", errors="replace")
    filename = filepath.name

    # 1. 檢查數字等寬特性宣告 (Tabular Figures)
    if "phantom_theme.typ" in filename:
        if "tnum" not in content:
            ERRORS.append(f"[{filename}] 違規: 遺漏 OpenType +tnum (Tabular Figures) 強制宣告！")

    # 2. 檢查是否有非法硬編碼直邊框 (嚴禁井字形粗黑框)
    if "table(" in content and "stroke: 1pt + black" in content:
        ERRORS.append(f"[{filename}] 違規: 檢測到未經授權的黑色粗邊框，違反極簡工業風標準！")

    # 3. 檢查字體依賴是否吻合標準三件套 (Inter, Noto Sans TC, JetBrains Mono)
    if "set text(" in content:
        for font in ["Inter", "Noto Sans TC"]:
            if font not in content:
                ERRORS.append(f"[{filename}] 警告: 主文字字型組中未發現 {font}")

    # 4. 檢查頁面規格是否符合 A4 與 8pt Grid
    if "phantom_theme.typ" in filename:
        if 'paper: "a4"' not in content and "paper: 'a4'" not in content:
            ERRORS.append(f"[{filename}] 違規: 頁面紙張規格未設定為標準 A4！")
        if "margin:" not in content:
            ERRORS.append(f"[{filename}] 違規: 缺少 8pt Baseline Grid 頁面邊距定義！")

    # 5. 檢查是否具備無障礙深色標題與主題色
    if "phantom_theme.typ" in filename:
        if "#0066FF" not in content and "#0F172A" not in content:
            WARNINGS.append(f"[{filename}] 提示: 建議採用標準 PHANTOM 藍 (#0066FF) 與深藍夜黑 (#0F172A)")

def main():
    print("=" * 70)
    print("🛡️  [PHANTOM GRID] 正在執行排版規格與幾何靜態檢查 (Quality Gate)...")
    print("=" * 70)

    checked_count = 0
    for root_dir in [DOCS_DIR, TEMPLATES_DIR]:
        if not root_dir.exists():
            continue
        for p in root_dir.rglob("*.typ"):
            check_file(p)
            checked_count += 1

    print(f"🔍 已完成掃描 {checked_count} 個 Typst 規格模組檔案")

    if WARNINGS:
        for w in WARNINGS:
            print(f"  ⚠️  {w}")

    if ERRORS:
        print("\n❌ [Quality Gate REJECTED] 發現以下規範違規項目:")
        for err in ERRORS:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("\n✅ [Quality Gate PASSED] 100% 通過 PHANTOM GRID 排版規範檢驗！")
        print("=" * 70)

if __name__ == "__main__":
    main()
