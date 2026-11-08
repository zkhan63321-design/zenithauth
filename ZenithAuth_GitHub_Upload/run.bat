@echo off
title Zenith Auth - Enterprise Cloud Sentinel
color 0b
echo ======================================================================
echo              ZENITH AUTH - CLOUD AUTHENTICATION PLATFORM
echo ======================================================================
echo.
echo [*] Checking Python environment...
py -V >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python (py launcher) was not found! Please install Python.
    pause
    exit /b 1
)

echo [*] Initializing Database Schema...
py database.py
if %errorlevel% neq 0 (
    echo [!] Database initialization error.
    pause
    exit /b 1
)

echo.
echo [1] Start Zenith Auth Web Server (http://localhost:5000)
echo [2] Run Python Client SDK Demo
echo [3] Run Discord Bot (requires BOT_TOKEN inside discord_bot.py)
echo [4] Exit
echo.
set /p opt="Select an option (default: 1): "
if "%opt%"=="2" (
    echo [*] Starting Client SDK...
    py client_sdk.py
    pause
    exit /b 0
)
if "%opt%"=="3" (
    echo [*] Starting Discord Bot...
    py discord_bot.py
    pause
    exit /b 0
)

echo [*] Starting Zenith Auth Server on http://localhost:5000 ...
start http://localhost:5000
py app.py
pause
