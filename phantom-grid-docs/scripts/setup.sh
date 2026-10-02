#!/usr/bin/env bash
set -e

FONTS_DIR="assets/fonts"
mkdir -p "$FONTS_DIR"
mkdir -p "assets/images"
mkdir -p "dist"

echo "==> [PHANTOM GRID] 開始佈署字型資產與工作環境..."

# 1. 下載 Inter 字體 (UI / 英文主標)
if [ ! -f "$FONTS_DIR/Inter-Regular.ttf" ]; then
    echo "--> 正在下載 Inter 向量字體..."
    curl -sL "https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Regular.woff2" -o "$FONTS_DIR/Inter-Regular.woff2" || true
fi

# 2. 下載 JetBrains Mono (等寬代碼 / 暫存器數據 / tnum)
if [ ! -f "$FONTS_DIR/JetBrainsMono-Regular.ttf" ]; then
    echo "--> 正在下載 JetBrains Mono 等寬字體..."
    curl -sL "https://raw.githubusercontent.com/JetBrains/JetBrainsMono/master/fonts/ttf/JetBrainsMono-Regular.ttf" -o "$FONTS_DIR/JetBrainsMono-Regular.ttf"
    curl -sL "https://raw.githubusercontent.com/JetBrains/JetBrainsMono/master/fonts/ttf/JetBrainsMono-Bold.ttf" -o "$FONTS_DIR/JetBrainsMono-Bold.ttf"
fi

# 3. 檢查 Python 依賴
echo "--> 檢查 Python 繪圖庫依賴..."
python3 -m pip install -q matplotlib numpy || python -m pip install -q matplotlib numpy || true

# 4. 驗證 Typst CLI
if ! command -v typst &> /dev/null; then
    echo "⚠️ 警告: 尚未檢測到 typst CLI。請手動執行: brew install typst 或 cargo install --locked typst-cli"
else
    echo "✅ Typst CLI 版本: $(typst --version)"
fi

echo "✅ [PHANTOM GRID] 環境與核心資產已就緒！"
