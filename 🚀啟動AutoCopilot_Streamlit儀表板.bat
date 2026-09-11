@echo off
chcp 65001 >nul
title AutoCopilot - Streamlit Voice AI Diagnostic Dashboard
color 0B

echo =======================================================================
echo          AutoCopilot : Streamlit 即時語音診斷儀表板
echo          AssemblyAI Universal-3 Pro + lablab.ai 黑客松展示
echo =======================================================================
echo.
echo [1/2] 檢查 Python 與 Streamlit 環境...
python -m streamlit --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 正在安裝 Streamlit 與 Pandas 依賴...
    pip install streamlit pandas
)

echo [2/2] 啟動 Streamlit 儀表板 (http://localhost:8501)...
echo.
python -m streamlit run streamlit_app.py --server.headless=false

pause