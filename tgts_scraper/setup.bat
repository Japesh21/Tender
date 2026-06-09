@echo off
REM TGTS Tender Scraper - Quick Setup Script (Windows)
REM This script sets up the project and installs dependencies

setlocal enabledelayedexpansion

echo.
echo ====================================
echo TGTS Tender Scraper - Setup
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to PATH
    pause
    exit /b 1
)

echo [1/5] Python found: 
python --version

REM Check if virtual environment exists
if not exist "tharun\Scripts\activate.bat" (
    echo [2/5] Creating virtual environment...
    python -m venv tharun
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
) else (
    echo [2/5] Virtual environment already exists
)

REM Activate virtual environment
echo [3/5] Activating virtual environment...
call tharun\Scripts\activate.bat

REM Install dependencies
echo [4/5] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Create .env file if not exists
if not exist ".env" (
    echo [5/5] Creating .env file...
    copy .env.example .env
    echo.
    echo WARNING: .env file created from .env.example
    echo IMPORTANT: Edit .env with your email and WhatsApp settings
    echo.
) else (
    echo [5/5] .env file already exists
)

echo.
echo ====================================
echo ✓ Setup Complete!
echo ====================================
echo.
echo Next steps:
echo 1. Edit .env file with your settings:
echo    - Email (Gmail SMTP)
echo    - WhatsApp (Twilio) - optional
echo.
echo 2. Run the scraper:
echo    python main.py
echo.
echo 3. Check logs:
echo    tail -f logs/scraper.log
echo.
echo 4. View outputs:
echo    - CSV: output/tgts_tenders.csv
echo    - Excel: output/tgts_tenders.xlsx
echo    - Database: database/tenders.db
echo.
echo For more info, see README.md or FAQ_AND_NEXT_STEPS.md
echo.
pause
