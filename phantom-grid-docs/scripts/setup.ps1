# PHANTOM GRID :: 一鍵環境與字體佈署腳本 (PowerShell)
$ErrorActionPreference = "SilentlyContinue"

$FONTS_DIR = "assets/fonts"
if (!(Test-Path $FONTS_DIR)) { New-Item -ItemType Directory -Path $FONTS_DIR -Force | Out-Null }
if (!(Test-Path "assets/images")) { New-Item -ItemType Directory -Path "assets/images" -Force | Out-Null }
if (!(Test-Path "dist")) { New-Item -ItemType Directory -Path "dist" -Force | Out-Null }

Write-Host "==> [PHANTOM GRID] 開始佈署字型資產與工作環境..." -ForegroundColor Cyan

# 1. 下載 Inter 字體
if (!(Test-Path "$FONTS_DIR/Inter-Regular.woff2")) {
    Write-Host "--> 正在下載 Inter 向量字體..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri "https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Regular.woff2" -OutFile "$FONTS_DIR/Inter-Regular.woff2"
}

# 2. 下載 JetBrains Mono
if (!(Test-Path "$FONTS_DIR/JetBrainsMono-Regular.ttf")) {
    Write-Host "--> 正在下載 JetBrains Mono Regular..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/JetBrains/JetBrainsMono/master/fonts/ttf/JetBrainsMono-Regular.ttf" -OutFile "$FONTS_DIR/JetBrainsMono-Regular.ttf"
}
if (!(Test-Path "$FONTS_DIR/JetBrainsMono-Bold.ttf")) {
    Write-Host "--> 正在下載 JetBrains Mono Bold..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/JetBrains/JetBrainsMono/master/fonts/ttf/JetBrainsMono-Bold.ttf" -OutFile "$FONTS_DIR/JetBrainsMono-Bold.ttf"
}

# 3. 檢查 Python 依賴
Write-Host "--> 檢查 Python 繪圖庫依賴..." -ForegroundColor Yellow
python -m pip install -q matplotlib numpy

# 4. 驗證 Typst CLI
$typstCmd = Get-Command typst -ErrorAction SilentlyContinue
if ($null -eq $typstCmd) {
    Write-Host "⚠️ 警告: 尚未檢測到 typst CLI。若需編譯，可透過 winget/cargo 或下載專屬免安裝二進位檔。" -ForegroundColor Red
} else {
    $ver = & typst --version
    Write-Host "✅ Typst CLI 版本: $ver" -ForegroundColor Green
}

Write-Host "✅ [PHANTOM GRID] 環境與核心資產已就緒！" -ForegroundColor Green
