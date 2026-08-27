@echo off
chcp 65001 >nul
title 🚀 Four-Agent AI OS: 通用資料驅動動態 UI 儀表板 (PROJ-22)
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo ===============================================================================
echo 🚀 正在啟動 Four-Agent AI OS: 通用資料驅動動態 UI 儀表板 (PROJ-22)...
echo 👁️ 小Ｏ 動態渲染 ✕ 🛠️ 小開 JSON Schema ✕ 🐎 小馬 邊界守門 ✕ 👑 小幫手 調度
echo ===============================================================================

python "G:\我的雲端硬碟\AI_master_workspace\three_memory\SRC\dynamic_schema_dashboard.py"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ⚠️ 執行異常，請檢查 Python 環境。
    pause
)
