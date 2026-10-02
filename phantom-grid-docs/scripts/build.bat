@echo off
rem ==============================================================
rem   PHANTOM GRID - Doc-as-Code Build Pipeline (Windows)
rem ==============================================================
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

cd /d "%~dp0\.."

if not exist dist mkdir dist

echo ==================================================
echo   PHANTOM GRID - Doc-as-Code Build Pipeline (Win) 
echo ==================================================

echo [1/5] Environment and asset check...
python scripts\setup.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Setup failed!
    exit /b %ERRORLEVEL%
)

echo [2/5] Data-driven calculation (CAN timing and register code)...
python scripts\compile_matrix.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Compile matrix failed!
    exit /b %ERRORLEVEL%
)

echo [3/5] Generating PG-SPEC vector charts (Line Chart + Safety FSM)...
python scripts\generate_charts.py
python scripts\generate_fsm.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Chart generation failed!
    exit /b %ERRORLEVEL%
)

echo [4/5] Static spec verification (Quality Gate)...
python scripts\verify_spec.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Spec verification failed!
    exit /b %ERRORLEVEL%
)

echo [5/5] Compiling high-precision Typst vector PDF (PDF/A-2b)...
python scripts\compile_typst.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Typst compilation failed!
    exit /b %ERRORLEVEL%
)

echo.
echo ==============================================================
echo [SUCCESS] PDF/A-2b Build Complete: dist\PHANTOM_GRID_SPEC.pdf
echo ==============================================================
