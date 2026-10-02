@echo off
rem ==============================================================
rem   PHANTOM GRID - World-Class PDF Build Pipeline (Windows)
rem ==============================================================
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

cd /d "%~dp0\.."

if not exist dist mkdir dist

echo ==================================================
echo   PHANTOM GRID - Production Build Pipeline (Win)  
echo ==================================================

echo [1/4] Environment and asset check...
python scripts\setup.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Setup failed!
    exit /b %ERRORLEVEL%
)

echo [2/4] Static spec verification (Quality Gate)...
python scripts\verify_spec.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Spec verification failed!
    exit /b %ERRORLEVEL%
)

echo [3/4] Generating PG-SPEC vector charts...
python scripts\generate_charts.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Chart generation failed!
    exit /b %ERRORLEVEL%
)

echo [4/4] Compiling high-precision Typst vector PDF (PDF/A-2b)...
python scripts\compile_typst.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Typst compilation failed!
    exit /b %ERRORLEVEL%
)

echo.
echo ==============================================================
echo [SUCCESS] PDF/A-2b Build Complete: dist\PHANTOM_GRID_SPEC.pdf
echo ==============================================================
