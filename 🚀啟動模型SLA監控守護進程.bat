@echo off
chcp 65001 >nul
title 🚀 Four-Agent AI OS: 模型端點 SLA 監控守護進程 (PROJ-25)
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

python "G:\我的雲端硬碟\AI_master_workspace\three_memory\SRC\model_endpoint_monitor.py" --daemon --interval 30
