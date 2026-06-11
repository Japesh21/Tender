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

# Legacy single-agency config (kept for fallback compatibility)
TARGET_DEPARTMENTS = ["IT", "TGTS", "Telangana Government Technology Services"]
TARGET_DEPARTMENT_IDS = ["1996"]

# Full agencies — show ALL tenders (no keyword filter)
FULL_AGENCIES = {'TGTS', 'TSMSIDC'}

# Multi-agency config — built from ALL_DEPARTMENTS below
# Will be populated after ALL_DEPARTMENTS definition
AGENCIES = {}  # populated below

# Full portal department ID map (from tender.telangana.gov.in dropdown)
ALL_DEPARTMENTS = {
    '600': 'AAROGYASRI HEALTH CARE TRUST',
    '3086': 'AG audit',
    '1252': 'AGRICULTURAL MARKETING DEPARTMENT - TELANGANA',
    '597': 'Agriculture & Cooperative Department',
    '473': 'ARCHAEOLOGY AND MUSEUMS - TELANGANA',
    '588': 'AYUSH',
    '2287': 'BACKWARD CLASSES WELFARE DEPARTMENT',
    '390': 'BOARD OF INTERMEDIATE EDUCATION',
    '2261': 'CENTRE FOR GOOD GOVERNANCE',
    '3117': 'COMMERCIAL TAXES DEPARTMENT',
    '3072': 'Commissioner of Labour',
    '396': 'COMMISSIONERATE OF COLLEGE EDUCATION',
    '2401': 'cooperative electric supply society ltd',
    '14': 'COT - TELANGANA',
    '3077': 'COUNCIL FOR SOCIAL DEVELOPMENT',
    '3407': 'cyberabad municipal corporation',
    '1801': 'DEPARTMENT OF EDUCATION-TELANGANA',
    '68': 'DEPARTMENT OF AGRICULTURE',
    '2267': 'Department of Employment and Training',
    '2573': 'Department Of Mines & Geology',
    '1821': 'DEPARTMENT OF TECHNICAL EDUCATION-TELANGANA',
    '286': 'DEPARTMENT OF TOURISM - TELANGANA',
    '579': 'DIRECTOR OF MEDICAL EDUCATION',
    '1874': 'DIRECTORATE OF ANIMAL HUSBANDRY-TELANGANA',
    '541': 'DIRECTORATE OF INTERMEDIATE EDUCATION',
    '538': 'DIRECTORATE OF TREASURIES AND ACCOUNTS',
    '3351': 'Disaster Management Department',
    '3318': 'DISTRICT ADMINISTRATION',
    '2223': 'Dr. MCR HRD INSTITUTE',
    '567': 'Dr.B.R.Ambedkar Open University',
    '1710': 'ENDOWMENTS DEPARTMENT MARKETING - TELANGANA',
    '791': 'ENDOWMENTS DEPARTMENT - TELANGANA',
    '2616': 'ENERGY DEPARTMENT',
    '3100': 'Environment Forest Science And Technology',
    '2249': 'ENVIRONMENT PROTECTION TRAINING & RESEARCH INST',
    '2998': 'Eprocadmin',
    '2185': 'FISHERIES DEPARTMENT',
    '3360': 'FUTURE CITY DEVELOPMENT AUTHORITY',
    '2536': 'General Administration Department',
    '3192': 'GHMC- MA & UD',
    '181': 'GREATER HYDERABAD MUNICIPAL CORPORATION',
    '293': 'GREATER WARANGAL MUNICIPAL CORPORATION',
    '616': 'Health Medical and Family Welfare Department',
    '2358': 'HIGHER EDUCATION',
    '140': 'HMDA',
    '116': 'HMWSSB',
    '549': 'HYDERABAD GROWTH CORRIDOR LIMITED',
    '521': 'HYDERABAD METRO RAIL LIMITED',
    '2308': 'HYDERABAD ROAD DEVELOPMENT CORPORATION LIMITED',
    '1423': 'I & CAD - Telangana',
    '2047': 'I&CAD - MISSION KAKATIYA',
    '2583': 'INDUSTRIES COMMERCE DEPARTMENT GOVT OF TELANGANA',
    '2010': 'Information and Public Relations Department',
    '30': 'Information Technology and Communications',
    '78': 'INSURANCE MEDICAL SERVICES',
    '1879': 'JAWAHARLAL NEHRU TECHNOLOGICAL UNIVERSITY-TELANG',
    '585': 'JAWAHARLAL NEHRU ARCHITECTURE&FINE ARTS UNIVERSITY',
    '2226': 'JUDICIARY',
    '558': 'KAKATIYA UNIVERSITY',
    '416': 'Kakatiya Urban Development Authority',
    '2164': 'MAHATMA GANDHI UNIVERSITY',
    '3447': 'Malkajgiri Municipal Corporation',
    '2281': 'MEDICAL AND HEALTH DEPARTMENT',
    '2274': 'MEDICAL EDUCATION DEPARTMENT',
    '3197': 'MISSION BAGIRATHA',
    '2476': 'Mission Bhagiratha Department.',
    '2174': 'MJPTBCWREI Society',
    '613': 'MNJ Institute of Oncology & Regional Cancer Centre',
    '689': 'MUNICIPAL ADMINISTRATION DEPARTMENT - TELANGANA',
    '725': 'MUNICIPALITIES - TELANGANA',
    '510': 'Nalgonda-Ranga Reddy Co-operation Milk Producers',
    '606': 'NALSAR UNIVERSITY',
    '2252': 'National Academy of Construction',
    '517': 'National Institute of Technology',
    '2235': 'NITHM',
    '274': 'NIZAMABAD MUNICIPAL CORPORATION',
    '2255': 'Nizambad Dist Co.Operative Central Bank Ltd',
    '2041': 'NIZAMS INSTITUTE OF MEDICAL SCIENCES',
    '437': 'Northern Power Distribution company of TS LTD',
    '2152': 'NOTIFIED AREA COMMITTE, RGIA HYD',
    '430': 'OSMANIA UNIVERSITY',
    '2293': 'P.V.NARSIMHA RAO TELANGANA VETERINARY UNIVERSITY',
    '2241': 'PANCHAYATH RAJ and RURAL DEVELOPMENT',
    '1584': 'PHMED - TELANGANA',
    '425': 'PLANNING DEPARTMENT',
    '307': 'POLICE DEPARTMENT',
    '2038': 'POLICE DEPARTMENT-GREY HOUNDS-TS',
    '2101': 'POLICE DEPARTMENT-OCTOPUS TELANGANA',
    '26': 'POTTI SREERAMULU TELUGU UNIVERSITY',
    '1600': 'PRED - TELANGANA',
    '74': 'Printing, Stationery & Stores Purchase Department',
    '2110': 'PRISONS DEPARTMENT - TELANGANA',
    '2104': 'PROF JAYASHANKAR TS AGRICULTURAL UNIVERSITY',
    '422': 'PROHIBITION AND EXCISE DEPARTMENT',
    '576': 'Quli Qutub Shah Urban Development Authority',
    '1260': 'R&B - Telangana',
    '623': 'Rajiv Gandhi University of Knowledge Technologies',
    '2264': 'RCUES',
    '555': 'REGISTRATION AND STAMPS',
    '2284': 'Resident Commissioner, Telangana Bhavan',
    '657': 'REVENUE DEPARTMENT - TS',
    '1882': 'RURAL DEVELOPMENT-TELANGANA',
    '603': 'Satavahana University',
    '2178': 'SCHEDULED CASTE DEVLOPMENT DEPT',
    '2238': 'SKLTS HORTICULTURAL UNIVERSITY',
    '443': 'SOUTHERN POWER DISTRIBUTION COMPANY OF TELANGANA L',
    '2171': 'SPORTS AUTHORITY OF TELANGANA',
    '64': 'STATE AUDIT DEPARTMENT',
    '340': 'T.G.S.W.R.E.I Society',
    '3291': 'TELANGANA ANTI-NACROTICS BUREAU(TGANB),HYDERABAD',
    '320': 'TELANGANA BEVERAGES CORPORATION LIMITED',
    '479': 'Telangana Dairy Development Co-operative Federatio',
    '3053': 'Telangana District Tribal Development',
    '2044': 'TELANGANA FOODS',
    '399': 'TELANGANA FOREST DEVELOPMENT CORPORATION LTD',
    '3182': 'Telangana Handicrafts Development Corporation Limited',
    '1772': 'TELANGANA HOUSING BOARD',
    '328': 'TELANGANA LIVESTOCK DEVELOPMENT AGENCY',
    '1952': 'Telangana Police Housing, Infratech and Consultancy Services Corp Limited',
    '1968': 'TELANGANA POWER GENERATION CORPORATION LIMITED',
    '513': 'Telangana RAJIV SWAGRUHA CORPORATION LTD',
    '2565': 'Telangana Scheduled Castes Co-operative Development Corporation Ltd',
    '573': 'Telangana State Agro Industries Development Corpor',
    '2872': 'Telangana State Aids Control Society',
    '2340': 'TELANGANA STATE ARCHIVES & RESEARCH INSTITUTE',
    '2322': 'Telangana State Aviation Corporation Ltd',
    '331': 'Telangana State Civil Supplies Corporation Limited',
    '545': 'TELANGANA STATE COOP. OILSEEDS GROWERS FEDERATION',
    '2522': 'Telangana State Cooperative Apex Bank Ltd',
    '627': 'Telangana STATE COOPERATIVE RURAL IRRIGATION CORPO',
    '3065': 'Telangana State Cyber Security Bureau, Hyderabad',
    '3094': 'Telangana State Election Commission',
    '496': 'TELANGANA STATE FINANCIAL CORPORATION',
    '2430': 'Telangana state Girijan Co-Operative Corporation Limited',
    '3129': 'Telangana State Hajj Committee',
    '2155': 'TELANGANA STATE MINERAL DEVEP CORP LTD',
    '654': 'Telangana State Minorities Finance Corporation',
    '2495': 'Telangana State Minorities Welfare Department',
    '2107': 'TELANGANA STATE POLLUTION CONTROL BOARD',
    '2278': 'Telangana State Renewable Energy Development corporation Limited',
    '2016': 'TELANGANA STATE ROAD TRANSPORT CORPORATION - TSRTC',
    '3164': 'Telangana State Seed and Organic Certification Authority',
    '387': 'TELANGANA STATE SEED CERTIFICATION AGENCY',
    '506': 'TELANGANA STATE SEEDS DEVELOPMENT CORPORATION LIMI',
    '2006': 'TELANGANA STATE TOURISM DEVELOPMENT CORPORATION',
    '2220': 'TELANGANA STATE WAQF BOARD',
    '561': 'TELANGANA STATE WAREHOUSING CORPORATION',
    '570': 'TELANGANA TRIBAL POWER COMPANY LTD',
    '2433': 'TELANGANA TRIBAL WELFARE RESIDENTIAL EDUCATIONAL INSTITUTIONS SOCIETY',
    '500': 'TELANGANA UNIVERSITY',
    '283': 'TELANGANA URBAN SERVICES FOR THE POOR',
    '83': 'TELANGANA VAIDYA VIDHANA PARISHAD',
    '2345': 'Telangana Welfare of Disabled & Senior Citizens',
    '643': 'Telangana WOMENS CO-OPERATIVE FINANCE CORPORATION',
    '1913': 'TG FOREST DEPARTMENT',
    '1405': 'TG STATE HOUSING CORPORATION LIMITED',
    '1902': 'TG STATE IRRIGATION DEVELOPMENT CORPORATION LTD',
    '1886': 'TGEWIDC',
    '412': 'TGGenco',
    '22': 'TGSRTC',
    '1333': 'TGTRANSCO - PRODUCTS',
    '1354': 'TGTRANSCO - WORKS',
    '1996': 'TGTS',
    '349': 'THE SINGARENI COLLIERIES COMPANY LIMITED',
    '3364': 'THE TELANGANA STATE HANDLOOM WEAVERS CO-OPERATIVE SOCIETY LTD',
    '503': 'TRANSPORT DEPARTMENT',
    '2290': 'TS COOP HOUSING SOCIETIES FEDERATION LTD',
    '2158': 'TS COOPERATIVE MARKETING FEDERATION LTD',
    '303': 'TS DISASTER RESPONSE AND FIRE SERVICES DEPT',
    '2271': 'TS ENGINEERING RESEARCH LABS',
    '1395': 'TS INDUSTRIAL INFRASTRUCTURE CORPORATION',
    '2376': 'TS SHEEP & GOAT DEVELOPMENT COOPERATIVE FEDERATION LIMITED',
    '1778': 'TSMSIDC',
    '674': 'TWED - TELANGANA',
    '3410': 'Urban Biodiversity wing MMC',
    '2116': 'WOMEN DEVELOPMET AND CHILD WELFARE DEPARTMENT',
    '2229': 'Yadagirigutta Temple Development Authority',
    '552': 'YOUTH ADVANCEMENT,TOURISM &CULTURE (PMU) DEPARTMEN',
}

# Build AGENCIES from ALL_DEPARTMENTS — each dept gets its own entry
# FULL_AGENCIES show all tenders; others show only Steps AI keyword matches
for _dept_id, _dept_name in ALL_DEPARTMENTS.items():
    # Use dept name as key (cleaned), map to dept ID
    _key = _dept_name.upper().strip()
    AGENCIES[_key] = {
        'department_ids': [_dept_id],
        'label': _dept_name,
        'full': _dept_id in ('1996', '1778'),  # TGTS and TSMSIDC get all tenders
    }

# Steps AI keyword filter — tenders matching any of these keywords are flagged
STEPS_AI_KEYWORDS = [
    'artificial intelligence', 'chatbot', 'chat bot', 'agentic',
    'large language model', 'LLM', 'machine learning', 'natural language',
    'NLP', 'generative AI', 'GenAI', 'automation', 'intelligent system',
    'digital assistant', 'virtual assistant', 'data analytics',
    'predictive analytics', 'computer vision', 'deep learning',
    'neural network', 'AI-based', 'AI based', 'smart system',
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
