"""
One-off scraper that uses your browser session cookies to fetch tenders
for all configured departments and insert them into the DB.

Usage:
    1. Log into tender.telangana.gov.in with your DSC
    2. Open DevTools -> Network -> click any TenderDetailsHomeJson request
    3. Copy the full cookie: header value
    4. Paste it as COOKIE below (replace the existing value)
    5. Run: python scrape_with_cookies.py

The cookies expire after a few hours, so paste fresh ones each time you run.
"""

import sys
import os
import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ─── PASTE YOUR FRESH COOKIE HERE ────────────────────────────────────────────
COOKIE = "_ga_X968Z7MRCZ=GS2.1.s1779284790$o1$g0$t1779284790$j60$l0$h0; _ga=GA1.1.366867877.1779284790; ApplicationGatewayAffinityCORS=3a47e806014a4c80710bb7f765456535; ApplicationGatewayAffinity=3a47e806014a4c80710bb7f765456535; SRVID=cee9960eca599e33affdfbed3aa12c29; JSESSIONID=2460B7064EFE86C745566DFA2307416C.inst3tms"
# ─────────────────────────────────────────────────────────────────────────────

# Departments to scrape: (agency_name, dept_id)
# Add more as you discover dept IDs from the portal
DEPARTMENTS = [
    ('TGTS',    '1996'),
    ('TSMSIDC', '1778'),
    ('TSGRTC',  '22'),
    ('TGGENCO', '412'),
]

BASE_URL = "https://tender.telangana.gov.in"
JSON_URL = f"{BASE_URL}/TenderDetailsHomeJson.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"{BASE_URL}/TenderDetailsHome.html",
    "cookie": COOKIE,
}


def build_params(dept_id):
    params = {
        'nTenderID': '', 'nDepartmentID': dept_id, 'subDeptId': '',
        'ddlDistrict': '', 'ddlMandal': '', 'biddingType': '',
        'sProcurementType': '', 'mECVValue1': '', 'mECVValue2': '',
        'dtBidClosingselect': '', 'dtBidClosing1': '', 'dtBidClosing2': '',
        'dtTenderOpening1': '', 'dtTenderOpening2': '',
        'hdnSearch4': '', 'hdnSearch': '', 'hdncorrigendumsDetails': '0',
        'hdncorrigendumsDetails1': '', 'hdnnoSearch': '1',
        'hdncorrigendumsDetails2': '', 'hdnPreviousPage': '',
        'hdnIndentID': '', 'hdnTenderCategory': '', 'hdnProcurementID': '',
        'hdnType': 'current', 'hdnPreviousPge': 'TenderDetailsHome.html',
        'hdnadvsearch': '', 'hdnFromStatus': '',
        'typeOfWorkFromConsolidation': '', 'popUPRequestParameter': '',
        'selectedCircleDivison': '', 'selectedDepartmentID': dept_id,
        'selectedProcurementType': '', 'selectedTypeofWork': '',
        'aid': '', 'hdnEncryptNames': 'hdnEncryptNames',
        'hdnEncryptValues': 'hdnEncryptValues',
        'sEcho': '1', 'iColumns': '10',
        'sColumns': '%2C%2C%2C%2C%2C%2C%2C%2C%2C',
        'iDisplayStart': '0', 'iDisplayLength': '1000',
        'iSortCol_0': '5', 'sSortDir_0': 'desc', 'iSortingCols': '1',
    }
    for i in range(10):
        params[f'mDataProp_{i}'] = str(i)
        params[f'bSortable_{i}'] = 'true'
    params['bSortable_9'] = 'false'
    return params


def main():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tgts_scraper'))
    from scraper.parser import TenderParser
    from database.db_manager import TenderDatabase
    from output.generator import OutputGenerator
    from config import DATABASE_FILE, OUTPUT_DIR

    db = TenderDatabase(DATABASE_FILE)
    gen = OutputGenerator(OUTPUT_DIR)

    total_new = 0
    total_found = 0

    for agency, dept_id in DEPARTMENTS:
        logger.info(f"Fetching {agency} (dept {dept_id})...")
        try:
            r = requests.get(JSON_URL, params=build_params(dept_id), headers=HEADERS, timeout=30)
            if r.status_code != 200:
                logger.error(f"  HTTP {r.status_code} — cookies may be expired")
                continue

            data = r.json()
            if len(r.text) < 100:
                logger.warning(f"  Response too small ({len(r.text)} bytes) — session expired or no tenders")
                continue

            tenders = TenderParser.parse_json_response(data)
            if not tenders:
                logger.info(f"  No tenders found for {agency}")
                continue

            logger.info(f"  Found {len(tenders)} tenders")
            total_found += len(tenders)
            new_count = 0

            for t in tenders:
                t['source_agency'] = agency
                if db.insert_tender(t):
                    new_count += 1

            logger.info(f"  Inserted {new_count} new into DB (skipped {len(tenders) - new_count} duplicates)")
            total_new += new_count

        except Exception as e:
            logger.error(f"  Error scraping {agency}: {e}")

    logger.info(f"\nDone. Found {total_found} tenders total, {total_new} new inserted.")

    # Regenerate HTML report
    all_tenders = db.get_all_tenders()
    html_path = gen.generate_html_report(all_tenders)
    logger.info(f"HTML report updated: {html_path} ({len(all_tenders)} tenders)")
    logger.info("Open tgts_scraper/output/tgts_report.html in browser to see TSMSIDC tab.")


if __name__ == "__main__":
    main()
