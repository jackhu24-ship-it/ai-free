#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )"
cd "$DIR"

DIST_DIR="dist"
mkdir -p "$DIST_DIR"

echo "=================================================="
echo "  PHANTOM GRID - Doc-as-Code Build Pipeline       "
echo "=================================================="

# 1. 數據驅動計算 (CAN 矩陣與硬體時序暫存器換算)
echo "--> [1/4] 正在執行數據驅動計算與暫存器代碼生成..."
python3 scripts/compile_matrix.py || python scripts/compile_matrix.py

# 2. 自動產出向量圖表 (折線圖 + ISO 26262 狀態機)
echo "--> [2/4] 正在生成 PG-SPEC 規範向量圖表 (SVG)..."
python3 scripts/generate_charts.py || python scripts/generate_charts.py
python3 scripts/generate_fsm.py || python scripts/generate_fsm.py

# 3. 靜態規範審查 (Quality Gate)
echo "--> [3/4] 正在執行靜態排版品質門禁審查 (Quality Gate)..."
python3 scripts/verify_spec.py || python scripts/verify_spec.py

# 4. 編譯標準 PDF (開啟 PDF/A-2b 標準與長青歸檔標籤)
echo "--> [4/4] 正在編譯符合 PDF/A-2b 與 Tagged PDF 規格文檔..."
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
