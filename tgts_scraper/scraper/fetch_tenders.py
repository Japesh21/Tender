"""
Tender fetcher module
Handles HTTP requests to Telangana eProcurement portal
"""

import logging
import requests
import json
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from scraper.parser import TenderParser

logger = logging.getLogger(__name__)


class TenderFetcher:
    """Handles fetching tender data from the website"""

    def __init__(self, base_url: str, timeout: int = 30, max_retries: int = 3,
                 session: requests.Session = None):
        """
        Initialize fetcher.
        Pass an authenticated session from browser_session.get_authenticated_session()
        to use portal cookies; otherwise falls back to a plain unauthenticated session.
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = session if session is not None else self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a plain (unauthenticated) requests session as fallback."""
        session = requests.Session()

        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        return session

    def get_rsa_key(self, endpoint: str) -> Optional[Dict]:
        """
        Fetch RSA public key from the server
        Required for encrypting search parameters
        """
        try:
            logger.info("Fetching RSA key...")
            response = self.session.get(endpoint, timeout=self.timeout)
            response.raise_for_status()

            key_data = response.json()
            logger.info("RSA key fetched successfully")
            return key_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch RSA key: {e}")
            return None

    def search_tenders(self, search_params: Dict) -> Optional[List[Dict]]:
        """
        Search for tenders with given parameters
        Uses TenderDetailsHome.json.html endpoint
        """
        try:
            logger.info(f"Searching tenders with params: {search_params}")

            # Establish a valid session by loading the login page first
            login_url = urljoin(self.base_url, "/login.html")
            logger.debug(f"Loading login page: {login_url}")
            self.session.get(login_url, timeout=self.timeout)

            endpoint = urljoin(self.base_url, "/TenderDetailsHomeJson.html")

            # Query parameters observed from the working browser request
            display_length = search_params.get('iDisplayLength', '100')
            try:
                display_length_int = int(display_length)
            except (ValueError, TypeError):
                display_length_int = 100

            params = {
                'nTenderID': search_params.get('nTenderID', ''),
                'nDepartmentID': search_params.get('nDepartmentID', ''),
                'subDeptId': search_params.get('subDeptId', ''),
                'ddlDistrict': search_params.get('ddlDistrict', ''),
                'ddlMandal': search_params.get('ddlMandal', ''),
                'biddingType': search_params.get('biddingType', ''),
                'sProcurementType': search_params.get('sProcurementType', ''),
                'mECVValue1': search_params.get('mECVValue1', ''),
                'mECVValue2': search_params.get('mECVValue2', ''),
                'dtBidClosingselect': search_params.get('dtBidClosingselect', ''),
                'dtBidClosing1': search_params.get('dtBidClosing1', ''),
                'dtBidClosing2': search_params.get('dtBidClosing2', ''),
                'dtTenderOpening1': search_params.get('dtTenderOpening1', ''),
                'dtTenderOpening2': search_params.get('dtTenderOpening2', ''),
                'hdnSearch4': search_params.get('hdnSearch4', ''),
                'hdnSearch': search_params.get('hdnSearch', ''),
                'hdncorrigendumsDetails': search_params.get('hdncorrigendumsDetails', ''),
                'hdncorrigendumsDetails1': search_params.get('hdncorrigendumsDetails1', ''),
                'hdnnoSearch': search_params.get('hdnnoSearch', '1'),
                'hdncorrigendumsDetails2': search_params.get('hdncorrigendumsDetails2', ''),
                'hdnPreviousPage': search_params.get('hdnPreviousPage', ''),
                'hdnIndentID': search_params.get('hdnIndentID', ''),
                'hdnTenderCategory': search_params.get('hdnTenderCategory', ''),
                'hdnProcurementID': search_params.get('hdnProcurementID', ''),
                'hdnType': search_params.get('hdnType', 'current'),
                'hdnPreviousPge': search_params.get('hdnPreviousPge', 'TenderDetailsHome.html'),
                'hdnadvsearch': search_params.get('hdnadvsearch', ''),
                'hdnFromStatus': search_params.get('hdnFromStatus', ''),
                'typeOfWorkFromConsolidation': search_params.get('typeOfWorkFromConsolidation', ''),
                'popUPRequestParameter': search_params.get('popUPRequestParameter', ''),
                'selectedCircleDivison': search_params.get('selectedCircleDivison', ''),
                'selectedDepartmentID': search_params.get('selectedDepartmentID', ''),
                'selectedProcurementType': search_params.get('selectedProcurementType', ''),
                'selectedTypeofWork': search_params.get('selectedTypeofWork', ''),
                'aid': search_params.get('aid', ''),
                'hdnEncryptNames': 'hdnEncryptNames',
                'hdnEncryptValues': 'hdnEncryptValues',
                'sEcho': search_params.get('sEcho', '1'),
                'iColumns': search_params.get('iColumns', '10'),
                'sColumns': search_params.get('sColumns', ',,,,,,,,,') ,
                'iDisplayStart': search_params.get('iDisplayStart', '0'),
                'iDisplayLength': str(display_length_int),
                'mDataProp_0': search_params.get('mDataProp_0', '0'),
                'bSortable_0': search_params.get('bSortable_0', 'true'),
                'mDataProp_1': search_params.get('mDataProp_1', '1'),
                'bSortable_1': search_params.get('bSortable_1', 'true'),
                'mDataProp_2': search_params.get('mDataProp_2', '2'),
                'bSortable_2': search_params.get('bSortable_2', 'true'),
                'mDataProp_3': search_params.get('mDataProp_3', '3'),
                'bSortable_3': search_params.get('bSortable_3', 'true'),
                'mDataProp_4': search_params.get('mDataProp_4', '4'),
                'bSortable_4': search_params.get('bSortable_4', 'true'),
                'mDataProp_5': search_params.get('mDataProp_5', '5'),
                'bSortable_5': search_params.get('bSortable_5', 'true'),
                'mDataProp_6': search_params.get('mDataProp_6', '6'),
                'bSortable_6': search_params.get('bSortable_6', 'true'),
                'mDataProp_7': search_params.get('mDataProp_7', '7'),
                'bSortable_7': search_params.get('bSortable_7', 'true'),
                'mDataProp_8': search_params.get('mDataProp_8', '8'),
                'bSortable_8': search_params.get('bSortable_8', 'true'),
                'mDataProp_9': search_params.get('mDataProp_9', '9'),
                'bSortable_9': search_params.get('bSortable_9', 'false'),
                'iSortCol_0': search_params.get('iSortCol_0', '5'),
                'sSortDir_0': search_params.get('sSortDir_0', 'desc'),
                'iSortingCols': search_params.get('iSortingCols', '1'),
                '_': str(int(time.time() * 1000))
            }

            self.session.headers.update({
                'Referer': login_url,
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'en-US,en;q=0.9',
                'X-Requested-With': 'XMLHttpRequest'
            })

            response = self.session.get(endpoint, params=params, timeout=self.timeout)
            logger.debug(f"Search endpoint returned {response.status_code} -> {response.url}")
            response.raise_for_status()

            if 'login.html' in response.url or 'SessionTimeOut.html' in response.url:
                logger.error("Search request redirected to login/session-timeout page. The site may require a handshake or valid browser session")
                return None

            # Try to parse as JSON first
            try:
                data = response.json()
                logger.info("Response is JSON format")

                if isinstance(data, dict):
                    total_records = int(data.get('iTotalRecords') or data.get('iTotalDisplayRecords') or data.get('recordsTotal') or 0)
                    items = data.get('aaData') if isinstance(data.get('aaData'), list) else (
                        data.get('rows') if isinstance(data.get('rows'), list) else None
                    )
                    if total_records and items is not None and len(items) < total_records:
                        logger.info(f"Detected {total_records} records, refetching with full page size")
                        params['iDisplayLength'] = str(total_records)
                        response = self.session.get(endpoint, params=params, timeout=self.timeout)
                        response.raise_for_status()
                        data = response.json()

                return TenderParser.parse_json_response(data)
            except ValueError:
                # If not JSON, parse as HTML
                logger.info("Response is HTML format - parsing with BeautifulSoup")
                return TenderParser.parse_html_response(response.text)

        except Exception as e:
            logger.error(f"Error searching tenders: {e}")
            return None

    def fetch_tender_details(self, tender_id: str) -> Optional[Dict]:
        """
        Fetch detailed information for a specific tender
        STUB - Implementation depends on API endpoint discovery
        """
        try:
            logger.info(f"Fetching details for tender: {tender_id}")

            # TODO: Implement actual detail fetching
            # Endpoint could be: /tender/{tender_id} or /TenderDetails?id={tender_id}

            logger.warning("Tender detail endpoint not yet implemented")
            return None

        except Exception as e:
            logger.error(f"Error fetching tender details: {e}")
            return None

    def close(self):
        """Close the session"""
        self.session.close()
        logger.info("Session closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
