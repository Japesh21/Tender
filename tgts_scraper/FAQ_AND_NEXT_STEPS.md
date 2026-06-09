# TGTS Tender Scraper - Important Notes & FAQ

## 🔍 Current Status

### ✅ What's Ready
- Project structure and architecture
- Database schema (SQLite)
- Notification system (Email & WhatsApp infrastructure)
- Output generators (CSV, Excel, HTML)
- Configuration management
- Logging system
- Error handling

### ⏳ What Needs API Discovery
The following components have **stubs** that need actual implementation once the API endpoint is discovered:

1. **`scraper/fetch_tenders.py`** - `fetch_tenders()` method
2. **`scraper/parser.py`** - `parse_json_response()` and `parse_html_response()` methods

---

## 🔐 Next Critical Step: API Discovery

### How to Find the API Endpoint:

1. **Open DevTools** (F12)
2. Navigate to: https://tender.telangana.gov.in/TenderDetailsHome.html
3. Go to **Network** tab (or XHR/Fetch sub-tab)
4. **Clear** all requests (circle icon)
5. **Perform a search** on the website for tenders (use IT/TGTS department)
6. Look for the request that returns tender data:
   - Look for requests labeled like: `search`, `api`, `tender`, `list`
   - Check the response tab
   - Note:
     - **Request URL** (endpoint)
     - **Request Method** (GET/POST)
     - **Request Payload** (if POST)
     - **Response Format** (JSON or HTML)

### Example Findings:

**If JSON API (Best Case):**
```
Request: GET /api/tenders?department=IT&page=1
Response: {
  "tenders": [
    {
      "id": "TEN-2024-001",
      "name": "Network Infrastructure",
      "dept": "IT",
      "publishedDate": "2024-01-15",
      "closingDate": "2024-02-15",
      ...
    }
  ]
}
```

**If HTML (Moderate Case):**
```
Request: GET /TenderSearch.html?dept=IT
Response: <html>
  <table class="tender-list">
    <tr class="tender-row">
      <td class="tender-id">TEN-2024-001</td>
      <td class="title">Network...</td>
      ...
    </tr>
  </table>
</html>
```

---

## 💡 How to Update the Scraper

Once you have the API details, update these files:

### 1. **Update `scraper/fetch_tenders.py`:**

```python
def search_tenders(self, search_params: Dict) -> Optional[List[Dict]]:
    """Search for tenders"""
    try:
        # REPLACE THIS STUB:
        endpoint = f"{self.base_url}/api/tenders"  # Your endpoint
        
        response = self.session.post(endpoint, json=search_params, timeout=self.timeout)
        response.raise_for_status()
        
        data = response.json()
        return TenderParser.parse_json_response(data)
        
    except Exception as e:
        logger.error(f"Error searching tenders: {e}")
        return None
```

### 2. **Update `scraper/parser.py`:**

```python
@staticmethod
def _map_json_fields(item: Dict) -> Optional[Dict]:
    """Map your API response fields to standard format"""
    # UPDATE FIELD MAPPING based on actual API response:
    tender = {
        'tender_id': item.get('id'),  # YOUR FIELD NAME
        'title': item.get('name'),    # YOUR FIELD NAME
        'department': item.get('dept'),  # YOUR FIELD NAME
        'published_date': item.get('publishedDate'),  # YOUR FIELD NAME
        'closing_date': item.get('closingDate'),  # YOUR FIELD NAME
        ...
    }
    return tender if TenderParser._is_valid_tender(tender) else None
```

---

## 🚀 Setting Up Locally

### 1. Install Dependencies

```bash
# Activate virtual environment
.\tharun\Scripts\Activate.ps1

# Install packages
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example to actual
cp .env.example .env

# Edit .env with your settings
# At minimum, test with dummy email/WhatsApp disabled
```

### 3. Test Run (No API yet)

```bash
python main.py
```

Expected output:
```
INFO - === TGTS Tender Scraper Started ===
WARNING - Tender fetching not yet implemented - awaiting API discovery
INFO - === TGTS Tender Scraper Completed Successfully ===
```

---

## 📧 Email Configuration

### Gmail Setup (Recommended):

1. **Enable 2-Factor Authentication**
   - Google Account → Security
   - Enable 2-Step Verification

2. **Generate App Password**
   - https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer"
   - Copy the 16-character password

3. **Update `.env`:**
   ```
   EMAIL_FROM=your-email@gmail.com
   EMAIL_PASSWORD=xxxx xxxx xxxx xxxx
   ```

### Test Email:
```python
from notifications.email_notifier import EmailNotifier

notifier = EmailNotifier(
    smtp_server='smtp.gmail.com',
    smtp_port=587,
    sender_email='your-email@gmail.com',
    sender_password='your-app-password'
)

notifier.send_error_alert(['test@example.com'], "Test error")
```

---

## 📱 WhatsApp Configuration

### Twilio Setup:

1. **Create Account**
   - https://www.twilio.com/console

2. **Activate WhatsApp Sandbox**
   - Messaging → Try it out → WhatsApp
   - Send test message to sandbox number

3. **Get Credentials**
   - Account SID (from dashboard)
   - Auth Token (from dashboard)
   - Sandbox sender number

4. **Update `.env`:**
   ```
   WHATSAPP_ENABLED=True
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_FROM=+1234567890
   WHATSAPP_TO=+91-9876543210
   ```

5. **Install Twilio (optional):**
   ```bash
   pip install twilio
   ```

---

## 🗄️ Database Usage

### Inspect Database:

```bash
# Option 1: SQLite CLI
sqlite3 database/tenders.db
sqlite> SELECT COUNT(*) FROM tenders;
sqlite> SELECT * FROM tenders LIMIT 5;

# Option 2: Python
from database.db_manager import TenderDatabase
db = TenderDatabase('database/tenders.db')
tenders = db.get_all_tenders()
stats = db.get_database_stats()
print(stats)
```

### Check Change Log:

```sql
SELECT tender_id, change_type, field_name, old_value, new_value, changed_at 
FROM tender_changelog 
WHERE changed_at >= datetime('now', '-1 day')
ORDER BY changed_at DESC;
```

---

## 📊 Output Files

After running the scraper (once API is connected):

```
output/
├── tgts_tenders.csv        # All tenders
├── tgts_tenders.xlsx       # Multi-sheet Excel
└── tgts_report.html        # Email-friendly HTML
```

### Example CSV Output:
```csv
tender_id,title,department,published_date,closing_date,emd,tender_value,status,document_link,pdf_link
TEN-2024-001,Network Infrastructure,IT,2024-01-15,2024-02-15,50000.0,5000000.0,Active,http://...,http://...
```

---

## 🐛 Debugging Tips

### Enable Verbose Logging:

```python
# In main.py, change:
LOG_LEVEL = logging.DEBUG

# Or in config.py:
LOG_LEVEL = "DEBUG"
```

### Inspect HTTP Requests:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
urllib3_log = logging.getLogger('urllib3')
urllib3_log.setLevel(logging.DEBUG)
```

### Test Fetcher Directly:

```python
from scraper.fetch_tenders import TenderFetcher

with TenderFetcher('https://tender.telangana.gov.in') as fetcher:
    # Test RSA key fetch
    key = fetcher.get_rsa_key('https://tender.telangana.gov.in/tender/encrypt?generateKeyPair=true')
    print(key)
```

---

## 📋 Checklist for Full Setup

- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Copy `.env.example` to `.env`
- [ ] Configure Gmail (SMTP)
- [ ] Configure Twilio (WhatsApp) - optional
- [ ] Discover API endpoint (network inspection)
- [ ] Update `fetch_tenders.py` with API logic
- [ ] Update `parser.py` with field mapping
- [ ] Test locally: `python main.py`
- [ ] Verify database: `sqlite3 database/tenders.db`
- [ ] Check output files: `ls output/`
- [ ] Test email notification
- [ ] Deploy to Render (optional)

---

## 🆘 Common Issues

| Issue | Solution |
|-------|----------|
| `AttributeError: 'NoneType' object has no attribute` | API endpoint not implemented - update parser |
| `sqlite3.OperationalError: database is locked` | Close other connections to database |
| `SMTPAuthenticationError` | Wrong email/password - verify Gmail app password |
| `ConnectionError: HTTPSConnectionPool` | Network issue - check internet |
| `Empty results` | API endpoint may have changed - re-inspect network tab |

---

## 🎓 Learning Resources

- **BeautifulSoup:** https://www.crummy.com/software/BeautifulSoup/bs4/doc/
- **Pandas:** https://pandas.pydata.org/docs/
- **Requests:** https://requests.readthedocs.io/
- **SQLite:** https://www.sqlite.org/lang.html
- **Twilio WhatsApp:** https://www.twilio.com/docs/sms/whatsapp/api

---

## 📞 Need Help?

1. **Check logs:** `tail -f logs/scraper.log`
2. **Inspect database:** `sqlite3 database/tenders.db`
3. **Review README.md** for full documentation
4. **Test components independently** (email, database, etc.)
5. **Use DevTools** to verify API endpoint

---

**Good luck! 🚀**

Once you complete the API discovery, the scraper will be fully operational.
