"""
==============================================================================
 ARCHITECTURE : PHANTOM GRID / TOP-TIER INDUSTRIAL PDF SPECIFICATION
 MODULE       : compile_typst.py
 SIGNED BY    : Commander Jack (👑 霸丸總指揮官權威落款)
 SEAL TIME    : 2026-10-02 13:44:48 CST
 STATUS       : OFFICIALLY RELEASED & SEALED
 INTEGRITY    : SHA256:56c514798ce5c703... [VERIFIED]
 SPEC STANDARD: PG-SPEC-2026-PDF-WORLD-CLASS
==============================================================================
"""

# -*- coding: utf-8 -*-
"""
PHANTOM GRID :: 出版級 Typst 向量 PDF 自動編譯引擎 (Cross-Platform)
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DOC_SRC = BASE_DIR / "docs" / "main.typ"
DIST_DIR = BASE_DIR / "dist"
PDF_OUT = DIST_DIR / "PHANTOM_GRID_SPEC.pdf"
FONTS_DIR = BASE_DIR / "assets" / "fonts"

def compile_pdf():
    print("==> [PHANTOM GRID] 正在編譯規格書 PDF (A4 / 8pt Baseline Grid)...")
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    
    # 方案 1: 原生 typst CLI
    typst_cli = shutil.which("typst")
    if typst_cli:
        cmd = [
            typst_cli, "compile",
            "--font-path", str(FONTS_DIR),
            "--root", str(BASE_DIR),
            "--pdf-standard", "a-2b",
            str(DOC_SRC),
            str(PDF_OUT)
        ]
        print(f"--> 調用原生 Typst CLI (PDF/A-2b): {' '.join(cmd)}")
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode == 0:
            print(f"✅ [SUCCESS] 原生 PDF/A-2b 編譯完成: {PDF_OUT} ({PDF_OUT.stat().st_size} bytes)")
            return True
        else:
            print(f"⚠️ 原生編譯反饋: {res.stderr.strip()}，切換為 Python Typst 引擎...")

    # 方案 2: Python typst 內核編譯
    try:
        import typst
        print("--> 調用 Python Typst 官方內核編譯引擎 (PDF/A-2b & 全字型嵌入)...")
        
        # 準備字型路徑
        font_paths = [str(FONTS_DIR)]
        
        typst.compile(
            input=str(DOC_SRC),
            output=str(PDF_OUT),
            font_paths=font_paths,
            root=str(BASE_DIR),
            pdf_standards=["a-2b"]
        )
        print(f"✅ [SUCCESS] Python Typst 內核編譯完成 (PDF/A-2b 歸檔級): {PDF_OUT} ({PDF_OUT.stat().st_size} bytes)")
        return True
    except Exception as e:
        print(f"⚠️ PDF/A-2b 編譯異常: {e}，嘗試標準 PDF 輸出...")
        try:
            typst.compile(
                input=str(DOC_SRC),
                output=str(PDF_OUT),
                font_paths=font_paths,
                root=str(BASE_DIR)
            )
            print(f"✅ [SUCCESS] Python Typst 標準編譯完成: {PDF_OUT} ({PDF_OUT.stat().st_size} bytes)")
            return True
        except Exception as e2:
            print(f"❌ 編譯發生異常: {e2}")
            return False

if __name__ == "__main__":
    success = compile_pdf()
    sys.exit(0 if success else 1)
