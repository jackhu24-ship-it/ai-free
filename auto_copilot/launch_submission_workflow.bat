@echo off
chcp 65001 >nul
title AutoCopilot 黑客松官方報名送件工作流中樞

echo ==============================================================================
echo    🚀 AutoCopilot ✕ AssemblyAI 黑客松官方報名送件工作流
echo ==============================================================================
echo.
echo [1/4] 正在為您打開包含展示影片與 4K 封面的雲端成品資料夾...
start explorer.exe "G:\我的雲端硬碟\AI產出成品總庫\04_多媒體與教學素材"

echo [2/4] 正在打開 YouTube Studio 影片上傳頁面...
start https://studio.youtube.com

echo [3/4] 正在打開 lablab.ai 官方賽事提交頁面...
start https://lablab.ai/event/assemblyai-hackathon

echo [4/4] 正在開啟完整英文送件文案 (SUBMISSION.md)...
start notepad.exe "%~dp0SUBMISSION.md"

echo.
echo ==============================================================================
echo   ✅ 工作流入口已全數開啟！
echo.
echo   【操作流程說明】
echo   1. 在 YouTube 拖入影片與 4K 封面，設為「不公開 (Unlisted)」或「公開」，並複製影片網址。
echo   2. 在 lablab.ai 點擊「Submit Project」或「Create Project」。
echo   3. 對照剛開啟的 SUBMISSION.md，將專案名稱、Tagline、GitHub 網址、YouTube 連結依序貼上。
echo.
echo   小幫手隨時在 Antigravity 視窗待命為您提供支援！
echo ==============================================================================
pause
