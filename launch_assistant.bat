@echo off
title AI Assistant Setup
color 0A

echo ================================================
echo         AI ASSISTANT SETUP LAUNCHER
echo ================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed!
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

:: Display Python version
echo Python found:
python --version
echo.

:: Check internet connection
ping -n 1 google.com >nul 2>&1
if errorlevel 1 (
    echo No internet connection detected!
    echo Please connect to internet for first-time setup
    pause
    exit /b 1
)

echo Internet connection OK
echo.

:: Run the setup script
echo Starting AI Assistant Setup...
echo This may take 5-10 minutes for first run
echo.

python ai_assistant.py

if errorlevel 1 (
    echo.
    echo Setup failed!
    echo Please check your internet connection and try again
    pause
) else (
    echo.
    echo AI Assistant closed
)

pause