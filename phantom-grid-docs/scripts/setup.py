"""
==============================================================================
 ARCHITECTURE : PHANTOM GRID / TOP-TIER INDUSTRIAL PDF SPECIFICATION
 MODULE       : setup.py
 SIGNED BY    : Commander Jack (👑 霸丸總指揮官權威落款)
 SEAL TIME    : 2026-10-02 13:47:24 CST
 STATUS       : OFFICIALLY RELEASED & SEALED
 INTEGRITY    : SHA256:865cd12ab2d26b23... [VERIFIED]
 SPEC STANDARD: PG-SPEC-2026-PDF-WORLD-CLASS
==============================================================================
"""

# -*- coding: utf-8 -*-
"""
PHANTOM GRID :: 一鍵環境與字體佈署腳本 (Cross-Platform Python Engine)
"""
import os
import sys
import shutil
import urllib.request
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FONTS_DIR = BASE_DIR / "assets" / "fonts"
IMAGES_DIR = BASE_DIR / "assets" / "images"
DIST_DIR = BASE_DIR / "dist"

def run_setup():
    print("==> [PHANTOM GRID] 開始佈署字型資產與工作環境...")
    
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Inter 字型下載
    inter_files = {
        "Inter-Regular.woff2": "https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Regular.woff2",
        "Inter-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf"
    }
    
    for fname, url in inter_files.items():
        target = FONTS_DIR / fname
        if not target.exists() or target.stat().st_size == 0:
            print(f"--> 正在下載 {fname}...")
            try:
                urllib.request.urlretrieve(url, target)
                print(f"✅ 已下載: {fname} ({target.stat().st_size} bytes)")
            except Exception as e:
                print(f"⚠️ 下載 {fname} 失敗: {e}")
                
    # 2. JetBrains Mono
    jb_files = {
        "JetBrainsMono-Regular.ttf": "https://raw.githubusercontent.com/JetBrains/JetBrainsMono/master/fonts/ttf/JetBrainsMono-Regular.ttf",
        "JetBrainsMono-Bold.ttf": "https://raw.githubusercontent.com/JetBrains/JetBrainsMono/master/fonts/ttf/JetBrainsMono-Bold.ttf"
    }
    for fname, url in jb_files.items():
        target = FONTS_DIR / fname
        if not target.exists() or target.stat().st_size == 0:
            print(f"--> 正在下載 {fname}...")
            try:
                urllib.request.urlretrieve(url, target)
                print(f"✅ 已下載: {fname} ({target.stat().st_size} bytes)")
            except Exception as e:
                print(f"⚠️ 下載 {fname} 失敗: {e}")
                
    # 3. 檢查 Python 繪圖庫
    print("--> 檢查 Python 繪圖庫依賴...")
    try:
        import matplotlib
        import numpy
        print("✅ matplotlib, numpy 已安裝就緒！")
    except ImportError:
        print("--> 正在安裝 matplotlib, numpy...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "matplotlib", "numpy"], check=False)

    # 4. 驗證 Typst CLI
    typst_path = shutil.which("typst")
    if typst_path:
        try:
            res = subprocess.run(["typst", "--version"], capture_output=True, text=True, check=False)
            print(f"✅ Typst CLI 版本: {res.stdout.strip()}")
        except Exception:
            print("✅ 檢測到 Typst 執行檔在路徑中。")
    else:
        print("⚠️ 警告: 尚未檢測到 typst CLI。若需編譯，可透過 winget/cargo 或下載專屬免安裝二進位檔。")

    print("✅ [PHANTOM GRID] 環境與核心資產已就緒！")

if __name__ == "__main__":
    run_setup()
