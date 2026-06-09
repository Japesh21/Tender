# TGTS Tender Scraper

> Automated tender monitoring for Telangana Government Technology Services (TGTS)

## Quick Start

**Windows:**
```bash
.\setup.bat
```

**macOS/Linux:**
```bash
bash setup.sh
source venv/bin/activate
```

## Run Scraper

```bash
python main.py
```

## Configuration

1. Copy `.env.example` → `.env`
2. Add your email & WhatsApp settings
3. Run scraper

## Outputs

- **CSV:** `output/tgts_tenders.csv`
- **Excel:** `output/tgts_tenders.xlsx`
- **Database:** `database/tenders.db`
- **Logs:** `logs/scraper.log`

## Next Steps

👉 See **[FAQ_AND_NEXT_STEPS.md](FAQ_AND_NEXT_STEPS.md)** for:
- API discovery instructions
- Configuration guide
- Troubleshooting

👉 See **[README.md](README.md)** for:
- Full documentation
- Database schema
- Deployment guide

## Features

✅ Daily scraping  
✅ Duplicate detection  
✅ CSV/Excel export  
✅ Email alerts  
✅ WhatsApp notifications  
✅ SQLite database  
✅ Render deployment ready  

---

**Version:** 1.0.0  
**Status:** Ready for API integration
