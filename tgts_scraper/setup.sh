#!/bin/bash
# TGTS Tender Scraper - Quick Setup Script (macOS/Linux)
# This script sets up the project and installs dependencies

echo ""
echo "===================================="
echo "TGTS Tender Scraper - Setup"
echo "===================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ using:"
    echo "  macOS: brew install python3"
    echo "  Ubuntu: sudo apt-get install python3"
    exit 1
fi

echo "[1/5] Python found:"
python3 --version

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[2/5] Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
else
    echo "[2/5] Virtual environment already exists"
fi

# Activate virtual environment
echo "[3/5] Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "[4/5] Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

# Create .env file if not exists
if [ ! -f ".env" ]; then
    echo "[5/5] Creating .env file..."
    cp .env.example .env
    echo ""
    echo "WARNING: .env file created from .env.example"
    echo "IMPORTANT: Edit .env with your email and WhatsApp settings"
    echo ""
else
    echo "[5/5] .env file already exists"
fi

echo ""
echo "===================================="
echo "✓ Setup Complete!"
echo "===================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your settings:"
echo "   - Email (Gmail SMTP)"
echo "   - WhatsApp (Twilio) - optional"
echo ""
echo "2. Run the scraper:"
echo "   python main.py"
echo ""
echo "3. Check logs:"
echo "   tail -f logs/scraper.log"
echo ""
echo "4. View outputs:"
echo "   - CSV: output/tgts_tenders.csv"
echo "   - Excel: output/tgts_tenders.xlsx"
echo "   - Database: database/tenders.db"
echo ""
echo "For more info, see README.md or FAQ_AND_NEXT_STEPS.md"
echo ""
