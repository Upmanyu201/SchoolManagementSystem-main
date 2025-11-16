@echo off
title School Management System - Quick Actions
color 0E

cd /d "%~dp0"

if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe tools\quick_actions.py
) else (
    python tools\quick_actions.py
)

pause
