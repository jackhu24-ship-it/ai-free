@echo off
chcp 65001 >nul
title 🚀 MCU 數位分身 10-bit ADC 遙測與調參儀表板 (PROJ-20)
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo ===============================================================================
echo 🚀 正在啟動 Four-Agent AI OS: MCU 10-bit ADC 即時遙測示波器與調參儀表板...
echo 👁️ 小Ｏ 介面 ✕ 🛠️ 小開 驅動 ✕ 🐎 小馬 審查 ✕ 👑 小幫手 調度
echo ===============================================================================

python "G:\我的雲端硬碟\AI_master_workspace\three_memory\SRC\mcu_telemetry_dashboard.py"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ⚠️ 執行過程中發生異常，請檢查 Python 3.12 環境與相依性。
    pause
)
