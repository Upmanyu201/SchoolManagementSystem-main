@echo off
title School Management System
color 0B

:MENU
cls
echo.
echo ========================================
echo   School Management System
echo ========================================
echo.
echo   1. Quick Start (Launch Server)
echo   2. Setup Wizard (First Time)
echo   3. Quick Actions Menu
echo   4. System Diagnostics
echo   5. Check for Updates
echo   6. Network Manager
echo   7. Factory Reset
echo   8. Exit
echo.
echo ========================================
echo.

set /p choice="Enter your choice (1-8): "

if "%choice%"=="1" goto START_SERVER
if "%choice%"=="2" goto SETUP
if "%choice%"=="3" goto QUICK_ACTIONS
if "%choice%"=="4" goto DIAGNOSTICS
if "%choice%"=="5" goto UPDATES
if "%choice%"=="6" goto NETWORK
if "%choice%"=="7" goto RESET
if "%choice%"=="8" goto EXIT

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto MENU

:START_SERVER
cls
echo.
echo Starting Server...
echo.
cd /d "%~dp0\..\..\"
call automation\scripts\launch_server.bat
goto MENU

:SETUP
cls
echo.
echo Running Setup Wizard...
echo.
cd /d "%~dp0\..\..\"
call automation\scripts\setup_wizard.bat
goto MENU

:QUICK_ACTIONS
cls
cd /d "%~dp0\..\..\"
call automation\scripts\quick_actions.bat
goto MENU

:DIAGNOSTICS
cls
cd /d "%~dp0\..\..\"
call automation\scripts\diagnostics.bat
goto MENU

:UPDATES
cls
cd /d "%~dp0\..\..\"
call automation\scripts\check_updates.bat
goto MENU

:NETWORK
cls
echo.
echo Opening Network Manager...
echo.
cd /d "%~dp0\..\..\"
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe automation\server\network_manager.py
) else (
    python automation\server\network_manager.py
)
pause
goto MENU

:RESET
cls
cd /d "%~dp0\..\..\"
call automation\scripts\factory_reset.bat
goto MENU

:EXIT
cls
echo.
echo Thank you for using School Management System!
echo.
timeout /t 2 >nul
exit
