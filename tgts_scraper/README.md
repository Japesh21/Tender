# TGTS Tender Scraper

Automated tender monitoring system for Telangana Government Technology Services (TGTS) tenders from the Telangana eProcurement portal.

**Website:** https://tender.telangana.gov.in/TenderDetailsHome.html

---

## 📋 Features

✅ **Automated Scraping** - Daily tender data collection  
✅ **Duplicate Detection** - Identifies new vs existing tenders  
✅ **Change Tracking** - SQLite database with historical changelog  
✅ **Multiple Export Formats** - CSV, Excel (.xlsx), HTML  
✅ **Email Notifications** - Alerts for new tenders and errors  
✅ **WhatsApp Alerts** - Real-time updates via Twilio  
✅ **Department Filtering** - Focus on specific departments (IT/TGTS)  
✅ **Render Deployment Ready** - Cloud-native design  

---

## 📦 Installation

### 1. **Clone or Extract Project**
```bash
cd tgts_scraper
```

### 2. **Activate Python Virtual Environment**
```bash
# Windows
.\tharun\Scripts\Activate.ps1

# macOS/Linux
source tharun/bin/activate
```

### 3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 4. **Configure Environment Variables**

Copy `.env.example` to `.env` and fill in your settings:

```bash
cp .env.example .env
```

**Edit `.env`:**

```ini
# Email Configuration (Gmail)
EMAIL_ENABLED=True
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_FROM=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_TO=recipient1@example.com,recipient2@example.com

# WhatsApp Configuration (Twilio)
WHATSAPP_ENABLED=True
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_FROM=+1234567890
WHATSAPP_TO=+91-recipient1,+91-recipient2
```

**For Gmail App Password:**
1. Enable 2-Factor Authentication on Google Account
2. Go to https://myaccount.google.com/apppasswords
3. Generate app-specific password for "Mail"
4. Use this password in `EMAIL_PASSWORD`

**For Twilio WhatsApp:**
1. Create account: https://www.twilio.com
2. Set up WhatsApp sandbox
3. Get Account SID & Auth Token from dashboard
4. Get phone number from Twilio WhatsApp Sandbox

---

## 🚀 Quick Start

### Run Once
```bash
python main.py
```

### Run with Logging
```bash
python main.py 2>&1 | tee logs/run.log
```

---

## 📁 Project Structure

```
tgts_scraper/
├── scraper/
│   ├── fetch_tenders.py      # HTTP requests & API calls
│   ├── parser.py              # JSON/HTML parsing (stub)
│   └── filters.py             # Filtering & selection logic
│
├── output/
│   └── generator.py           # CSV, Excel, HTML export
│
├── database/
│   └── db_manager.py          # SQLite operations
│
├── notifications/
│   ├── email_notifier.py      # Email alerts
│   └── whatsapp_notifier.py   # WhatsApp alerts (Twilio)
│
├── logs/                       # Log files
│
├── output/                     # Generated reports (CSV, Excel)
│   ├── tgts_tenders.csv
│   └── tgts_tenders.xlsx
│
├── database/
│   └── tenders.db            # SQLite database
│
├── config.py                  # Configuration
├── main.py                    # Entry point
├── requirements.txt           # Dependencies
├── .env.example               # Environment template
└── README.md                  # This file
```

---

## ⚙️ Configuration (`config.py`)

Key settings:

```python
# Target Department
TARGET_DEPARTMENTS = ["IT", "TGTS", "Telangana Government Technology Services"]

# Schedule
SCHEDULE_TIME = "09:00"  # Daily at 9 AM
SCHEDULE_TIMEZONE = "Asia/Kolkata"

# Notifications
ALERT_ON_ERROR = True
ALERT_ON_NEW_TENDER = True
```

---

## 🗄️ Database Schema

### `tenders` Table
```sql
CREATE TABLE tenders(
    tender_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    department TEXT,
    published_date TEXT,
    closing_date TEXT,
    emd REAL,
    tender_value REAL,
    document_link TEXT,
    pdf_link TEXT,
    status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `tender_changelog` Table
```sql
CREATE TABLE tender_changelog(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tender_id TEXT NOT NULL,
    change_type TEXT,
    field_name TEXT,
    old_value TEXT,
    new_value TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔍 Data Collection Fields

For each tender:

| Field | Type | Description |
|-------|------|-------------|
| `tender_id` | Text | Unique tender identifier |
| `title` | Text | Tender title/description |
| `department` | Text | Issuing department |
| `published_date` | Date | Publication date |
| `closing_date` | Date | Bid submission deadline |
| `emd` | Float | Earnest Money Deposit |
| `tender_value` | Float | Estimated tender value |
| `document_link` | URL | Link to tender documents |
| `pdf_link` | URL | Direct PDF link |
| `status` | Text | Active/Closed/Cancelled |

---

## 📊 Output Formats

### CSV Export
```
tender_id,title,department,published_date,closing_date,emd,tender_value,status,document_link,pdf_link
TEN-2024-001,Network Infrastructure,IT,2024-01-15,2024-02-15,50000,5000000,Active,...
```

### Excel Export
- **Sheet 1:** All Tenders (with sorting/filtering)
- **Sheet 2:** Summary by Status
- **Sheet 3:** Summary by Department
- **Sheet 4:** Export Metadata

### HTML Report
- Email-friendly table format
- Hyperlinked tender documents

---

## 🔄 Workflow

### Daily Execution:

```
1. Fetch tenders from website
   ↓
2. Parse JSON/HTML response
   ↓
3. Filter by department (IT/TGTS)
   ↓
4. Check database for new/updated
   ↓
5. Insert/update in SQLite
   ↓
6. Generate CSV, Excel, HTML
   ↓
7. Send email & WhatsApp alerts
   ↓
8. Log summary statistics
```

---

## 🚨 Error Handling

- **Fail-fast strategy:** Script stops on critical errors
- **Alert on error:** Email & WhatsApp notifications sent
- **Retry with exponential backoff:** Network requests retry 3× automatically
- **Logging:** All errors logged to `logs/scraper.log`

---

## 📧 Email Notifications

Sent automatically for:

✉️ **New Tenders** - Summary of newly discovered tenders  
✉️ **Closing Soon** - Reminders for tenders closing in 7 days  
✉️ **Error Alerts** - When scraper encounters errors  
✉️ **Daily Summary** - Statistics and report links  

Includes attachments with CSV/Excel files.

---

## 📱 WhatsApp Alerts

Sent via Twilio for:

- 🆕 New tenders (first 3 shown)
- ⏰ Tenders closing soon
- ❌ Error alerts

Character-limited for WhatsApp format.

---

## 🐍 Python Requirements

- Python 3.8+
- requests (HTTP library)
- beautifulsoup4 (HTML parsing)
- pandas (Data processing)
- openpyxl (Excel generation)
- python-dotenv (Environment management)

**Optional:**
- twilio (WhatsApp notifications)
- schedule (Task scheduling)

---

## 🔐 Security Notes

- **Never commit `.env` file** to version control
- **API credentials** stored in environment variables only
- **Email passwords:** Use app-specific passwords, not main account password
- **Twilio tokens:** Keep private, rotate regularly

---

## 🚀 Deployment on Render

### Prerequisites:
- Render account (free tier available)
- GitHub repository with project

### Setup Steps:

1. **Push code to GitHub**
```bash
git init
git add .
git commit -m "Initial commit"
git push origin main
```

2. **Create Render Service**
   - Dashboard → New → Web Service
   - Connect GitHub repo
   - Build command: `pip install -r requirements.txt`
   - Start command: `python main.py`

3. **Set Environment Variables**
   - In Render dashboard → Environment
   - Add all variables from `.env`

4. **Configure Cron Job**
   - Render → New → Background Job
   - Schedule: `0 9 * * *` (Daily at 9 AM UTC)
   - Command: `python main.py`

---

## 📋 FAQ

### Q: How do I know if the scraper is working?

**A:** Check:
- `logs/scraper.log` for execution logs
- `output/` folder for CSV/Excel files
- Database: `database/tenders.db`
- Email inbox for notifications

### Q: The website structure changed - how do I update the parser?

**A:** 
1. Open DevTools (F12) → Network tab
2. Perform a tender search
3. Find the API request (XHR/Fetch)
4. Note the endpoint URL, request method, response format
5. Update `fetch_tenders.py` and `parser.py` with new logic

### Q: Can I run the scraper on a schedule?

**A:** Yes! Options:

**Windows Task Scheduler:**
```batch
python C:\path\to\main.py >> C:\path\to\logs\schedule.log 2>&1
```

**Linux Cron:**
```bash
0 9 * * * cd /path/to/scraper && python main.py >> logs/schedule.log 2>&1
```

**Render Cron Job:**
Use built-in scheduler (see Deployment section)

### Q: How do I filter by different departments?

**A:** Edit `config.py`:
```python
TARGET_DEPARTMENTS = [
    "Finance",
    "Health",
    "Public Works"
]
```

### Q: Emails are not sending - what's wrong?

**A:** Check:
1. `.env` file exists with correct email/password
2. Gmail app password (not main account password)
3. SMTP server is `smtp.gmail.com` and port is `587`
4. 2FA is enabled on Google account
5. Check logs for SMTP errors

### Q: How do I add more notification channels?

**A:** Create new notifier module:
1. Copy `notifications/email_notifier.py`
2. Implement your notification service (Slack, Telegram, etc.)
3. Import in `main.py`
4. Add to `send_notifications()` method

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `No module named 'twilio'` | Install: `pip install twilio` (optional) |
| `.env file not found` | Copy `.env.example` to `.env` and configure |
| Database locked | Close other database connections |
| Network timeout | Check internet, increase `REQUEST_TIMEOUT` in config |
| Email not sent | Verify credentials, check logs for SMTP errors |
| Empty tender list | Website structure may have changed (check parser) |

---

## 📝 Logging

Logs are stored in `logs/scraper.log` with format:

```
2024-01-15 09:00:00 - tgts_scraper.main - INFO - === TGTS Tender Scraper Started ===
2024-01-15 09:00:01 - tgts_scraper.scraper - INFO - Fetching tenders...
2024-01-15 09:00:05 - tgts_scraper.database - INFO - Inserted tender: TEN-2024-001
```

View live logs:
```bash
tail -f logs/scraper.log
```

---

## 🤝 Contributing

To improve this project:

1. Test changes locally
2. Document any API changes
3. Update parser logic based on website changes
4. Add new notification channels as needed

---

## 📄 License

This project is provided as-is for research and personal use.

---

## ⚠️ Disclaimer

- This scraper is for educational purposes
- Comply with Telangana portal's Terms of Service
- Respect rate limits and robots.txt
- Do not use for commercial purposes without permission
- Author is not liable for misuse

---

## 🎯 Next Steps

After deploying:

1. **Test the scraper:** Run `python main.py` manually
2. **Verify database:** Check `database/tenders.db` for records
3. **Check exports:** Review CSV/Excel in `output/` folder
4. **Test notifications:** Verify email & WhatsApp delivery
5. **Monitor logs:** Watch `logs/scraper.log` for issues
6. **Schedule it:** Set up daily execution via Render/Cron

---

## 📞 Support

- **Documentation:** See this README
- **Logs:** Check `logs/scraper.log`
- **Errors:** Review error messages in logs
- **Database:** Use SQLite browser to inspect `tenders.db`

---

**Last Updated:** 2024-01-15  
**Version:** 1.0.0
