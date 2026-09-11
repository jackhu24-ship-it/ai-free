@echo off
chcp 65001 >nul
title AutoCopilot Voice Diagnostic Gateway
echo ========================================================
echo   AutoCopilot - 即時聲控車載診斷副駕 (AssemblyAI Voice Agent)
echo ========================================================
echo.
echo [1/2] 正在啟動 FastAPI 非同步網關與 WebSocket 伺服器...
echo [2/2] 正在開啟暗黑工規即時診斷儀表板: http://127.0.0.1:8000
echo.
start http://127.0.0.1:8000
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
python -m uvicorn auto_copilot.server:app --host 0.0.0.0 --port 8000 --reload
pause
