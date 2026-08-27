@echo off
chcp 65001 >nul
title 🚀 MCU 即時遙測示波器與調參儀表板
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

python "G:\我的雲端硬碟\AI_master_workspace\three_memory\SRC\mcu_telemetry_dashboard.py"
