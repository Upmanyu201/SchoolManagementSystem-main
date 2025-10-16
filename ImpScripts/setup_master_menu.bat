@echo off
setlocal enabledelayedexpansion
title School Management System - Master Setup Menu
color 0A

REM Change to project root directory (parent of ImpScripts)
cd /d "%~dp0.."

REM Verify we're in the correct directory
if not exist "manage.py" (
    echo ERROR: Cannot find manage.py - wrong directory!
    echo Current directory: %CD%
    echo.
    echo Please run this script from the project root or ImpScripts folder.
    pause
    exit /b 1
)

REM Set Python executable (prefer venv, fallback to system)
set PYTHON_EXE=python
if exist "venv\Scripts\python.exe" (
    set PYTHON_EXE=venv\Scripts\python.exe
    echo Using virtual environment Python: venv\Scripts\python.exe
) else (
    echo Virtual environment not found - using system Python
    echo Run option 2 to create virtual environment
)
echo.

:MAIN_MENU
cls
echo.
echo ===============================================================================
echo                    SCHOOL MANAGEMENT SYSTEM - MASTER SETUP
echo ===============================================================================
echo.
echo [1] System Check and Requirements Validation
echo [2] Python Installation and Environment Setup  
echo [3] Database Setup and Migration
echo [4] Dependencies Installation
echo [5] System Health Check and Testing
echo [6] Start Development Server
echo [7] Reset Demo Mode
echo [8] Complete Fresh Installation - All Steps
echo [0] Exit
echo.
echo ===============================================================================
set /p choice="Select option (0-8): "

if "%choice%"=="1" goto SYSTEM_CHECK
if "%choice%"=="2" goto PYTHON_SETUP
if "%choice%"=="3" goto DATABASE_SETUP
if "%choice%"=="4" goto DEPENDENCIES
if "%choice%"=="5" goto HEALTH_CHECK
if "%choice%"=="6" goto START_SERVER
if "%choice%"=="7" goto RESET_DEMO
if "%choice%"=="8" goto COMPLETE_SETUP
if "%choice%"=="0" goto EXIT
goto INVALID_CHOICE

:SYSTEM_CHECK
cls
echo.
echo ===============================================================================
echo                           SYSTEM REQUIREMENTS CHECK
echo ===============================================================================
echo.
if not exist ImpScripts\check_system.py (
    echo ERROR: check_system.py not found!
    pause
    goto MAIN_MENU
)
echo Checking system requirements...
%PYTHON_EXE% ImpScripts\check_system.py
if errorlevel 1 (
    echo.
    echo ERROR: System check failed! See details above.
    pause
    goto MAIN_MENU
)
echo.
echo System check completed successfully!
pause
goto MAIN_MENU

:PYTHON_SETUP
cls
echo.
echo ===============================================================================
echo                        PYTHON INSTALLATION ^& SETUP
echo ===============================================================================
echo.
if not exist ImpScripts\install_python.py (
    echo ERROR: install_python.py not found!
    pause
    goto MAIN_MENU
)
if not exist ImpScripts\setup_environment.py (
    echo ERROR: setup_environment.py not found!
    pause
    goto MAIN_MENU
)
echo Upgrading pip and installing tools...
%PYTHON_EXE% ImpScripts\install_python.py
if errorlevel 1 (
    echo.
    echo ERROR: Python installation failed! See details above.
    pause
    goto MAIN_MENU
)
echo.
echo Setting up virtual environment...
%PYTHON_EXE% ImpScripts\setup_environment.py
REM Update PYTHON_EXE after venv creation
if exist "venv\Scripts\python.exe" set PYTHON_EXE=venv\Scripts\python.exe
if errorlevel 1 (
    echo.
    echo ERROR: Environment setup failed! See details above.
    pause
    goto MAIN_MENU
)
echo.
echo Python setup completed successfully!
pause
goto MAIN_MENU

:DATABASE_SETUP
cls
echo.
echo ===============================================================================
echo                          DATABASE SETUP ^& MIGRATION
echo ===============================================================================
echo.
if not exist ImpScripts\database_setup.py (
    echo ERROR: database_setup.py not found!
    pause
    goto MAIN_MENU
)
echo Setting up database and running migrations...
%PYTHON_EXE% ImpScripts\database_setup.py
if errorlevel 1 (
    echo.
    echo ERROR: Database setup failed! See details above.
    pause
    goto MAIN_MENU
)
echo.
echo Database setup completed successfully!
pause
goto MAIN_MENU

:DEPENDENCIES
cls
echo.
echo ===============================================================================
echo                         DEPENDENCIES INSTALLATION
echo ===============================================================================
echo.
echo Installing required dependencies...
if exist venv\Scripts\python.exe (
    if exist requirements.txt (
        venv\Scripts\python.exe -m pip install -r requirements.txt
        if errorlevel 1 (
            echo.
            echo ERROR: Dependencies installation failed!
            echo Check the error messages above for details.
            pause
            goto MAIN_MENU
        )
    ) else (
        echo ERROR: requirements.txt not found!
        pause
        goto MAIN_MENU
    )
) else (
    echo ERROR: Virtual environment not found! Please run Python Setup first.
    pause
    goto MAIN_MENU
)
echo.
echo Dependencies installed successfully!
pause
goto MAIN_MENU

:HEALTH_CHECK
cls
echo.
echo ===============================================================================
echo                           SYSTEM HEALTH CHECK
echo ===============================================================================
echo.
echo Running comprehensive system health check...
if exist ImpScripts\comprehensive_health_check.py (
    %PYTHON_EXE% ImpScripts\comprehensive_health_check.py
) else (
    %PYTHON_EXE% comprehensive_health_check.py
)
if errorlevel 1 (
    echo.
    echo WARNING: Some health checks failed!
)
echo.
echo Running system tests...
if exist ImpScripts\run_tests.py (
    %PYTHON_EXE% ImpScripts\run_tests.py
) else (
    %PYTHON_EXE% run_tests.py
)
echo.
echo Health check completed!
pause
goto MAIN_MENU

:START_SERVER
cls
echo.
echo ===============================================================================
echo                         START DEVELOPMENT SERVER
echo ===============================================================================
echo.
echo Starting Django development server...
if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe ImpScripts\enhanced_start_server.py
) else (
    echo ERROR: Virtual environment not found! Please run Complete Setup first.
    pause
    goto MAIN_MENU
)
pause
goto MAIN_MENU

:RESET_DEMO
cls
echo.
echo ===============================================================================
echo                              RESET DEMO MODE
echo ===============================================================================
echo.
echo Resetting system to demo mode...
if exist dev_tools\scripts\reset_demo_mode.py (
    %PYTHON_EXE% dev_tools\scripts\reset_demo_mode.py
) else (
    echo WARNING: reset_demo_mode.py not found - skipping
)
echo.
echo Demo mode reset completed!
pause
goto MAIN_MENU

:COMPLETE_SETUP
cls
echo.
echo ===============================================================================
echo                        COMPLETE FRESH INSTALLATION
echo ===============================================================================
echo.
echo This will perform a complete setup of the School Management System.
echo The following steps will be executed:
echo.
echo 1. System Requirements Check
echo 2. Python Installation & Environment Setup
echo 3. Dependencies Installation
echo 4. Database Setup & Migration
echo 5. System Health Check
echo 6. Demo Mode Reset
echo.
set /p confirm="Continue with complete setup? (Y/N): "
if /i not "%confirm%"=="Y" goto MAIN_MENU

echo.
echo ===============================================================================
echo Step 1/6: System Requirements Check (Progress: 0%%)
echo ===============================================================================
if not exist ImpScripts\check_system.py (
    echo ERROR: check_system.py not found! Aborting setup.
    pause
    goto MAIN_MENU
)
%PYTHON_EXE% ImpScripts\check_system.py
if errorlevel 1 (
    echo ERROR: System check failed! Aborting setup.
    pause
    goto MAIN_MENU
)

echo.
echo ===============================================================================
echo Step 2/6: Python Installation ^& Environment Setup (Progress: 17%%)
echo ===============================================================================
%PYTHON_EXE% ImpScripts\install_python.py
if errorlevel 1 (
    echo ERROR: Python installation failed! Aborting setup.
    pause
    goto MAIN_MENU
)

%PYTHON_EXE% ImpScripts\setup_environment.py
if errorlevel 1 (
    echo ERROR: Environment setup failed! Aborting setup.
    pause
    goto MAIN_MENU
)
REM Update PYTHON_EXE after venv creation
if exist "venv\Scripts\python.exe" set PYTHON_EXE=venv\Scripts\python.exe

echo.
echo ===============================================================================
echo Step 3/6: Dependencies Installation (Progress: 33%% - May take 5-10 min)
echo ===============================================================================
if exist venv\Scripts\python.exe (
    if exist requirements.txt (
        echo Installing Python packages (this may take several minutes)...
        venv\Scripts\python.exe -m pip install -r requirements.txt
        if errorlevel 1 (
            echo ERROR: Dependencies installation failed! Aborting setup.
            echo Check the error messages above for details.
            pause
            goto MAIN_MENU
        )
    ) else (
        echo ERROR: requirements.txt not found! Aborting setup.
        pause
        goto MAIN_MENU
    )
) else (
    echo ERROR: Virtual environment not found! Aborting setup.
    pause
    goto MAIN_MENU
)

echo.
echo ===============================================================================
echo Step 4/6: Database Setup ^& Migration (Progress: 67%%)
echo ===============================================================================
%PYTHON_EXE% ImpScripts\database_setup.py
if errorlevel 1 (
    echo ERROR: Database setup failed! Aborting setup.
    pause
    goto MAIN_MENU
)

echo.
echo ===============================================================================
echo Step 5/6: System Health Check (Progress: 83%%)
echo ===============================================================================
%PYTHON_EXE% ImpScripts\comprehensive_health_check.py
%PYTHON_EXE% ImpScripts\run_tests.py

echo.
echo ===============================================================================
echo Step 6/6: Demo Mode Reset (Progress: 95%%)
echo ===============================================================================
if exist dev_tools\scripts\reset_demo_mode.py (
    %PYTHON_EXE% dev_tools\scripts\reset_demo_mode.py
) else (
    echo WARNING: reset_demo_mode.py not found - skipping
)

echo.
echo ===============================================================================
echo                        SETUP COMPLETED SUCCESSFULLY!
echo ===============================================================================
echo.
echo Your School Management System is now ready to use!
echo.
echo Next steps:
echo 1. Start the development server (Option 6)
echo 2. Access the system at: http://127.0.0.1:8000/
echo 3. Use the 7-day demo period or contact for licensing
echo.
echo For support: Upmanyu201@gmail.com
echo Phone: +91-9955590919
echo.
pause
goto MAIN_MENU

:INVALID_CHOICE
cls
echo.
echo ===============================================================================
echo                              INVALID CHOICE
echo ===============================================================================
echo.
echo Please select a valid option (0-8).
echo.
pause
goto MAIN_MENU

:EXIT
cls
echo.
echo ===============================================================================
echo                    THANK YOU FOR USING SETUP MASTER
echo ===============================================================================
echo.
echo School Management System Setup Complete!
echo.
echo For technical support:
echo Email: Upmanyu201@gmail.com
echo Phone: +91-9955590919, +91-9473089919
echo.
echo Press any key to exit...
pause >nul
exit /b 0