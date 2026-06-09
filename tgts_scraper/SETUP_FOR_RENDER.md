# Setup for Render Deployment

## What's Been Implemented

✅ **HTML Report Enhancements**
- 🆕 **New Tender Highlighting** — Tenders added today (IST) are shown with green background and "NEW" badge
- 📧 **Email Button** — One click opens your email client with tender pre-filled (`mailto:`)
- 💬 **WhatsApp Button** — One click opens WhatsApp with tender details ready to send (`wa.me`)

✅ **Daily Auto-Email at 9 AM IST**
- Sends an email every day at 9:00 AM (India Standard Time)
- Email includes a summary table of top 20 tenders
- **Excel file is attached** (`tgts_tenders.xlsx`) with all 23 tenders and full details
- Shows count of new tenders added that day

✅ **Portal Login (Playwright)**
- Browser-based login to `tender.telangana.gov.in`
- Session cookies saved automatically
- Reuses cookies for 1 hour before re-login

---

## Prerequisites for Render

1. **Gmail Account with App Password**
   - Enable 2-Factor Authentication on your Gmail account
   - Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
   - Select "Mail" and "Windows Computer"
   - Copy the 16-character app password

2. **Portal Account**
   - Username and password for `tender.telangana.gov.in`
   - (Available in 2 days)

3. **Recipient Email(s)**
   - Email address where the daily report should be sent

---

## Before Deploying to Render

### Step 1: Create a `.env` file

```bash
# Portal Login (add in 2 days)
PORTAL_USERNAME=your_portal_username
PORTAL_PASSWORD=your_portal_password

# Email Configuration
EMAIL_ENABLED=True
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_FROM=your-gmail@gmail.com
EMAIL_PASSWORD=your-16-char-app-password
EMAIL_TO=recipient@example.com

# WhatsApp (optional, leave blank for now)
WHATSAPP_ENABLED=False
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_FROM=
WHATSAPP_TO=
```

### Step 2: Test Locally

Run once to verify everything works:

```bash
python main.py
```

You should see:
- ✅ HTML report generated with new-tender highlighting
- ✅ Excel file generated with all tenders
- ✅ Daily email sent with Excel attachment
- ✅ Email received in your inbox

### Step 3: Deploy to Render

1. Push code to GitHub (with `.env` in `.gitignore`)
2. Add environment variables in Render dashboard (copy from `.env`)
3. Set up a **Background Worker**:
   - Build command: `pip install -r requirements.txt`
   - Start command: `python scheduler.py`
4. The scheduler will run `python main.py` every day at 9:00 AM IST

---

## How It Works

### Daily Flow (9 AM IST)
```
1. Scheduler triggers → Calls main.py
2. main.py runs:
   - Logs into portal (if credentials are set)
   - Fetches live tenders
   - Filters for TGTS only
   - Detects new/updated tenders
   - Generates Excel, CSV, HTML reports
   - Sends daily email with Excel attached
   - Logs new tender alerts (email + WhatsApp if enabled)
3. Reports saved to /output/
4. HTML report available at tgts_report.html (refresh to see latest)
```

### HTML Report Features
- **Click "📧 Email"** → Opens your email with tender details pre-filled
- **Click "💬 WhatsApp"** → Opens WhatsApp Web with tender text ready
- **Green rows** = Tenders added today

### Daily Email
- **Subject:** `📊 TGTS Daily Tender Report - YYYY-MM-DD (23 tenders, 1 new)`
- **Body:** Summary table (top 20 tenders shown)
- **Attachment:** Full Excel file with all tenders, 4 sheets (All, by Status, by Department, Metadata)

---

## FAQ

**Q: Why does the portal login need Playwright?**  
A: The portal uses RSA-encrypted client-side password submission + session cookies. Only a real browser can handle the encryption. Playwright automates this.

**Q: What if I don't have portal credentials yet?**  
A: The scraper will error, but the HTML report will still regenerate from existing DB tenders (23 currently). Once you add credentials, it fetches live data.

**Q: Can I manually send Email/WhatsApp without the scheduler?**  
A: Yes. Click the 📧 Email or 💬 WhatsApp buttons in the HTML report—they open your client directly, no server needed.

**Q: How often does the report update if I'm not in Render?**  
A: Every time you run `python main.py` locally. Scheduler only runs in Render at 9 AM IST.

**Q: Where does the Excel file come from?**  
A: Generated fresh each run by `generate_excel()` from all tenders in the database. Sorted by closing date, includes 4 sheets with stats.

---

## Files Changed

- `output/generator.py` — HTML report with highlighting + share buttons
- `notifications/email_notifier.py` — New `send_daily_report()` method with Excel attachment
- `main.py` — Calls `send_daily_report()` after generating reports
- `requirements.txt` — Added `playwright>=1.40.0`
- `config.py` — Added `PORTAL_USERNAME`, `PORTAL_PASSWORD` env vars
- `.env.example` — Updated with Gmail setup instructions

---

## Next Steps

1. **Wait for portal credentials** (2 days)
2. **Add them to `.env`**: `PORTAL_USERNAME`, `PORTAL_PASSWORD`
3. **Set up Gmail App Password** and add to `.env`: `EMAIL_PASSWORD`
4. **Set up email recipients** in `.env`: `EMAIL_TO`
5. **Test locally**: `python main.py`
6. **Deploy to Render** as Background Worker
7. **Verify** — Check email inbox at 9 AM IST next day
