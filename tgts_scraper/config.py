"""
Configuration module for TGTS Tender Scraper
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ===== SCRAPER SETTINGS =====
TENDER_WEBSITE_URL = "https://tender.telangana.gov.in"
TENDER_API_BASE = "https://tender.telangana.gov.in"  # Update after API discovery
RSA_KEY_ENDPOINT = f"{TENDER_API_BASE}/tender/encrypt?generateKeyPair=true"

# Target departments to monitor
TARGET_DEPARTMENTS = [
    "IT",
    "TGTS",
    "Telangana Government Technology Services"
]

# Target department IDs as used by the Telangana tender search page
# The TGTS option value discovered from the search page is 1996.
TARGET_DEPARTMENT_IDS = [
    "1996"
]

# ===== OUTPUT SETTINGS =====
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
CSV_FILENAME = "tgts_tenders.csv"
EXCEL_FILENAME = "tgts_tenders.xlsx"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ===== DATABASE SETTINGS =====
DATABASE_DIR = os.path.join(os.path.dirname(__file__), "database")
DATABASE_FILE = os.path.join(DATABASE_DIR, "tenders.db")

os.makedirs(DATABASE_DIR, exist_ok=True)

# ===== LOGGING SETTINGS =====
LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE = os.path.join(LOGS_DIR, "scraper.log")

os.makedirs(LOGS_DIR, exist_ok=True)

LOG_LEVEL = "INFO"

# ===== PORTAL LOGIN =====
PORTAL_USERNAME = os.getenv("PORTAL_USERNAME", "")
PORTAL_PASSWORD = os.getenv("PORTAL_PASSWORD", "")

# ===== NOTIFICATION SETTINGS =====

# Email Configuration
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "True").lower() == "true"
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_TO_LIST = os.getenv("EMAIL_TO", "").split(",") if os.getenv("EMAIL_TO") else []

# WhatsApp Configuration (Twilio)
WHATSAPP_ENABLED = os.getenv("WHATSAPP_ENABLED", "True").lower() == "true"
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_FROM = os.getenv("TWILIO_PHONE_FROM", "")  # e.g., "+1234567890"
WHATSAPP_PHONE_TO_LIST = os.getenv("WHATSAPP_TO", "").split(",") if os.getenv("WHATSAPP_TO") else []

# ===== SCRAPER BEHAVIOR =====
REQUEST_TIMEOUT = 30  # seconds
RETRY_ATTEMPTS = 3
RETRY_DELAY = 5  # seconds
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# ===== SCHEDULE SETTINGS =====
SCHEDULE_TIME = "09:00"  # Daily at 9 AM
SCHEDULE_TIMEZONE = "Asia/Kolkata"

# ===== ALERT SETTINGS =====
ALERT_ON_ERROR = True
ALERT_ON_NEW_TENDER = True
