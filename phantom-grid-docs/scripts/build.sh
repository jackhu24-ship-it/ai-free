#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )"
cd "$DIR"

DIST_DIR="dist"
mkdir -p "$DIST_DIR"

echo "=================================================="
echo "  PHANTOM GRID - Production Build Pipeline        "
echo "=================================================="

# 1. 靜態規範審查 (Quality Gate)
echo "--> [1/3] 正在執行靜態排版品質門禁審查 (Quality Gate)..."
python3 scripts/verify_spec.py || python scripts/verify_spec.py

# 2. 自動產出向量圖表
echo "--> [2/3] 正在生成 PG-SPEC 規範向量 SVG 圖表..."
python3 scripts/generate_charts.py || python scripts/generate_charts.py

# 3. 編譯標準 PDF (開啟 PDF/A-2b 標準與長青歸檔標籤)
echo "--> [3/3] 正在編譯符合 PDF/A-2b 與 Tagged PDF 規格文檔..."
if command -v typst &> /dev/null; then
    typst compile \
      --font-path ./assets/fonts \
      --root . \
      --pdf-standard a-2b \
      docs/main.typ \
      "$DIST_DIR/PHANTOM_GRID_SPEC.pdf" || \
    typst compile \
      --font-path ./assets/fonts \
      --root . \
      docs/main.typ \
      "$DIST_DIR/PHANTOM_GRID_SPEC.pdf"
else
    echo "ℹ️ 調用 Python Typst 內核引擎進行 PDF/A-2b 編譯..."
    python3 scripts/compile_typst.py || python scripts/compile_typst.py
fi

echo "--------------------------------------------------"
echo "✅ [SUCCESS] 世界第一規格書已產出至: $DIST_DIR/PHANTOM_GRID_SPEC.pdf"
echo "=================================================="
