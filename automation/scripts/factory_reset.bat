@echo off
title School Management System - Factory Reset
color 0C

echo.
echo ========================================
echo   WARNING: Factory Reset
echo ========================================
echo.
echo This will reset the application to
echo a fresh installation state.
echo.
echo Press Ctrl+C to cancel now!
echo.
pause

cd /d "%~dp0\..\..\"

if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe automation\setup\factory_reset.py
) else (
    python automation\setup\factory_reset.py
)

pause
