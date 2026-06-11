"""
Scrapes all departments from the portal using browser session cookies.
- TGTS (1996) and TSMSIDC (1778): inserts ALL tenders
- All other departments: inserts only Steps AI keyword-matched tenders

Usage:
    1. Log into tender.telangana.gov.in with your DSC
    2. F12 -> Network -> click any TenderDetailsHomeJson request
    3. Copy the full cookie: header value
    4. Paste it as COOKIE below
    5. Run: python scrape_with_cookies.py
"""

import sys, os, re, requests, logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ─── PASTE YOUR FRESH COOKIE HERE ────────────────────────────────────────────
COOKIE = "_ga_X968Z7MRCZ=GS2.1.s1779284790$o1$g0$t1779284790$j60$l0$h0; _ga=GA1.1.366867877.1779284790; ApplicationGatewayAffinityCORS=3a47e806014a4c80710bb7f765456535; ApplicationGatewayAffinity=3a47e806014a4c80710bb7f765456535; SRVID=cee9960eca599e33affdfbed3aa12c29; JSESSIONID=2460B7064EFE86C745566DFA2307416C.inst3tms"
# ─────────────────────────────────────────────────────────────────────────────

# Full agencies — insert ALL tenders (not just AI-matched)
FULL_DEPT_IDS = {'1996', '1778'}  # TGTS, TSMSIDC

BASE_URL = "https://tender.telangana.gov.in"
JSON_URL = f"{BASE_URL}/TenderDetailsHomeJson.html"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"{BASE_URL}/TenderDetailsHome.html",
    "cookie": COOKIE,
}


def build_params(dept_id):
    p = {
        'nTenderID': '', 'nDepartmentID': dept_id, 'subDeptId': '', 'ddlDistrict': '',
        'ddlMandal': '', 'biddingType': '', 'sProcurementType': '', 'mECVValue1': '',
        'mECVValue2': '', 'dtBidClosingselect': '', 'dtBidClosing1': '', 'dtBidClosing2': '',
        'dtTenderOpening1': '', 'dtTenderOpening2': '', 'hdnSearch4': '', 'hdnSearch': '',
        'hdncorrigendumsDetails': '', 'hdncorrigendumsDetails1': '', 'hdnnoSearch': '1',
        'hdncorrigendumsDetails2': '', 'hdnPreviousPage': '', 'hdnIndentID': '',
        'hdnTenderCategory': '', 'hdnProcurementID': '', 'hdnType': 'current',
        'hdnPreviousPge': 'TenderDetailsHome.html', 'hdnadvsearch': '', 'hdnFromStatus': '',
        'typeOfWorkFromConsolidation': '', 'popUPRequestParameter': '',
        'selectedCircleDivison': '', 'selectedDepartmentID': dept_id,
        'selectedProcurementType': '', 'selectedTypeofWork': '', 'aid': '',
        'hdnEncryptNames': 'hdnEncryptNames', 'hdnEncryptValues': 'hdnEncryptValues',
        'sEcho': '1', 'iColumns': '10', 'sColumns': '',
        'iDisplayStart': '0', 'iDisplayLength': '1000',
        'iSortCol_0': '5', 'sSortDir_0': 'desc', 'iSortingCols': '1',
    }
    for i in range(10):
        p[f'mDataProp_{i}'] = str(i)
        p[f'bSortable_{i}'] = 'true'
    p['bSortable_9'] = 'false'
    return p


def main():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tgts_scraper'))
    from scraper.parser import TenderParser
    from scraper.filters import TenderFilter
    from database.db_manager import TenderDatabase
    from output.generator import OutputGenerator
    from config import DATABASE_FILE, OUTPUT_DIR, ALL_DEPARTMENTS, STEPS_AI_KEYWORDS

    db = TenderDatabase(DATABASE_FILE)
    gen = OutputGenerator(OUTPUT_DIR)

    # Build AI keyword patterns
    ai_patterns = [re.compile(re.escape(kw), re.IGNORECASE) for kw in STEPS_AI_KEYWORDS]
    def is_ai(title):
        return any(p.search(title or '') for p in ai_patterns)

    total_new = 0
    total_found = 0
    dept_results = {}  # dept_name -> count inserted

    depts = list(ALL_DEPARTMENTS.items())
    logger.info(f"Scraping {len(depts)} departments...")

    for dept_id, dept_name in depts:
        is_full = dept_id in FULL_DEPT_IDS
        try:
            r = requests.get(JSON_URL, params=build_params(dept_id), headers=HEADERS, timeout=20)
            if r.status_code != 200 or len(r.text) < 100:
                continue

            data = r.json()
            tenders = TenderParser.parse_json_response(data)
            if not tenders:
                continue

            total_found += len(tenders)

            # For non-full depts, keep only AI-matched tenders
            if not is_full:
                tenders = [t for t in tenders if is_ai(t.get('title', ''))]

            if not tenders:
                continue

            new_count = 0
            for t in tenders:
                t['source_agency'] = dept_name  # use full dept name as agency key
                if db.insert_tender(t):
                    new_count += 1

            if new_count > 0:
                dept_results[dept_name] = new_count
                total_new += new_count
                logger.info(f"  [{dept_id}] {dept_name}: {new_count} new inserted")

        except Exception as e:
            logger.error(f"  [{dept_id}] {dept_name}: error — {e}")

    logger.info(f"\nDone. Scanned {len(depts)} depts, found {total_found} tenders total, {total_new} new inserted.")
    if dept_results:
        logger.info("New tenders by dept:")
        for name, cnt in sorted(dept_results.items()):
            logger.info(f"  {name}: {cnt}")

    # Regenerate HTML
    all_tenders = db.get_all_tenders()
    html_path = gen.generate_html_report(all_tenders)
    logger.info(f"HTML updated: {html_path} ({len(all_tenders)} total tenders)")


if __name__ == "__main__":
    main()
