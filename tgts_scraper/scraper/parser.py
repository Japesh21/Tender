"""
Parser module for extracting tender data
Handles both JSON and HTML parsing
"""

import logging
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import json

logger = logging.getLogger(__name__)


class TenderParser:
    """Parses tender data from various formats"""

    # Required fields for a valid tender
    REQUIRED_FIELDS = [
        'tender_id',
        'title',
        'published_date',
        'closing_date'
    ]

    @staticmethod
    def parse_json_response(response_data: Dict) -> Optional[List[Dict]]:
        """
        Parse JSON API response from TenderDetailsHome.json.html
        """
        try:
            tenders = []

            # The response could be in different formats:
            # 1. Direct array: [...]
            # 2. Wrapped in object: {"data": [...], "aaData": [...], "records": [...]}
            # 3. With metadata: {"tenders": [...], "count": ..., ...}

            items = []

            # Check if response is directly an array
            if isinstance(response_data, list):
                items = response_data
            # Check common wrapper keys
            elif isinstance(response_data, dict):
                # Try common API response patterns
                for key in ['data', 'aaData', 'rows', 'records', 'tenders', 'items', 'results']:
                    if key in response_data and isinstance(response_data[key], list):
                        items = response_data[key]
                        break

                # Some responses wrap the actual rows inside a nested data object
                if not items and isinstance(response_data.get('data'), dict):
                    for key in ['aaData', 'rows', 'records', 'tenders', 'items', 'results']:
                        if key in response_data['data'] and isinstance(response_data['data'][key], list):
                            items = response_data['data'][key]
                            break

            # Parse each item
            for item in items:
                if isinstance(item, dict):
                    tender = TenderParser._map_json_fields(item)
                elif isinstance(item, list):
                    tender = TenderParser._map_json_array(item)
                else:
                    tender = None

                if tender:
                    tenders.append(tender)

            logger.info(f"Parsed {len(tenders)} tenders from JSON response")
            return tenders if tenders else None

        except Exception as e:
            logger.error(f"Error parsing JSON response: {e}")
            return None

    @staticmethod
    def parse_html_response(html_content: str) -> Optional[List[Dict]]:
        """
        Parse HTML response using BeautifulSoup
        Adjust selectors based on actual HTML structure
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            tenders = []

            # TODO: Update selectors based on actual HTML structure
            # Example (to be updated after network inspection):
            # tender_rows = soup.find_all('tr', class_='tender-row')
            # for row in tender_rows:
            #     tender = TenderParser._extract_tender_from_row(row)
            #     if tender:
            #         tenders.append(tender)

            logger.warning("HTML parsing not yet configured - awaiting HTML structure analysis")
            return None

        except Exception as e:
            logger.error(f"Error parsing HTML response: {e}")
            return None

    @staticmethod
    def _map_json_fields(item: Dict) -> Optional[Dict]:
        """
        Map JSON fields to standard tender format
        Handles common field name variations
        """
        try:
            # Try multiple field name variations (common in different API responses)
            def get_field(item, *possible_names):
                for name in possible_names:
                    if name in item:
                        return item.get(name)
                return None

            tender = {
                'tender_id': get_field(item, 'id', 'tender_id', 'tenderID', 'TenderID', 'ref_id'),
                'title': get_field(item, 'title', 'name', 'description', 'tenderTitle', 'TenderTitle'),
                'department': get_field(item, 'department', 'dept', 'departmentName', 'DepartmentName', 'ministry'),
                'published_date': get_field(item, 'published_date', 'publishedDate', 'publishDate', 'posted_date', 'publish_date'),
                'closing_date': get_field(item, 'closing_date', 'closingDate', 'deadline', 'dueDate', 'close_date'),
                'emd': TenderParser._parse_number(get_field(item, 'emd', 'earnest_money', 'earnestMoney', 'EMD')),
                'tender_value': TenderParser._parse_number(get_field(item, 'tender_value', 'value', 'amount', 'tenderValue', 'TenderValue')),
                'document_link': get_field(item, 'document_link', 'document_url', 'doc_link', 'docLink', 'documents'),
                'pdf_link': get_field(item, 'pdf_link', 'pdf_url', 'pdfLink', 'pdf', 'document_pdf'),
                'status': get_field(item, 'status', 'tender_status', 'state') or 'Active'
            }

            # Validate required fields
            if TenderParser._is_valid_tender(tender):
                return tender
            else:
                logger.warning(f"Tender missing required fields: {tender}")
                return None

        except Exception as e:
            logger.error(f"Error mapping JSON fields: {e}")
            return None

    BASE_URL = "https://tender.telangana.gov.in"

    @staticmethod
    def _map_json_array(item: List) -> Optional[Dict]:
        """Map array-style DataTables rows to the standard tender format."""
        try:
            if not isinstance(item, list):
                return None

            action_html = item[9] if len(item) > 9 else None
            document_link, pdf_link, corrigendum_link = TenderParser._extract_links_from_html(action_html)

            tender = {
                'department': item[0] if len(item) > 0 else None,
                'tender_id': item[1] if len(item) > 1 else None,
                'tender_category': str(item[3]).strip() if len(item) > 3 and item[3] else '',
                'title': item[4] if len(item) > 4 and item[4] else (item[2] if len(item) > 2 else None),
                'published_date': item[6] if len(item) > 6 else None,
                'bid_submission_start': item[7] if len(item) > 7 else None,
                'closing_date': item[8] if len(item) > 8 else None,
                'emd': None,
                'tender_value': TenderParser._parse_number(item[5]) if len(item) > 5 else None,
                'document_link': document_link,
                'pdf_link': pdf_link,
                'corrigendum_link': corrigendum_link,
                'status': 'Active'
            }

            return tender if TenderParser._is_valid_tender(tender) else None

        except Exception as e:
            logger.error(f"Error mapping array JSON fields: {e}")
            return None

    @staticmethod
    def _extract_links_from_html(html_content: str):
        """
        Extract document_link and pdf_link URLs from the action cell HTML.

        The action cell contains:
          viewBtn(tenderId, deptType, indentId)       -> public tender detail page
          fnviewTenderDocuments(indentId, tenderId)   -> document download (requires login)

        document_link uses viewBtn to build a public URL (no login redirect loop).
        pdf_link uses fnviewTenderDocuments for the document download page.

        Returns (document_link, pdf_link) as a tuple of strings or Nones.
        """
        try:
            if not html_content:
                return None, None, None

            base = TenderParser.BASE_URL
            document_link = None
            pdf_link = None
            corrigendum_link = None

            # viewBtn(tenderId, deptType, indentId) — public tender detail page
            view_match = re.search(r"viewBtn\s*\(\s*(\d+)\s*,\s*\d+\s*,\s*(\d+)\s*\)", html_content)
            if view_match:
                tender_id = view_match.group(1)
                indent_id = view_match.group(2)
                document_link = (
                    f"{base}/Activity/TenderDetails"
                    f"?nTenderID={tender_id}&nIndentID={indent_id}"
                )
                # NITdownloadPDF is public and requires no login
                pdf_link = f"{base}/Activity/NITdownloadPDF?nIndentID={indent_id}"

            # viewCorrigendum(indentId) — only present on some tenders
            corr_match = re.search(r"viewCorrigendum\s*\(\s*(\d+)\s*\)", html_content)
            if corr_match:
                indent_id = corr_match.group(1)
                corrigendum_link = f"{base}/Activity/CorrigendumDetails?nIndentID={indent_id}"

            return document_link, pdf_link, corrigendum_link

        except Exception as e:
            logger.debug(f"Error extracting links from HTML: {e}")
            return None, None, None

    @staticmethod
    def _extract_link_from_html(html_content: str) -> Optional[str]:
        """Legacy helper — returns document_link only."""
        document_link, _, _ = TenderParser._extract_links_from_html(html_content)
        return document_link

    @staticmethod
    def _parse_number(value) -> Optional[float]:
        """Parse numeric values, handling strings and various formats"""
        if value is None:
            return None
        try:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                # Remove common currency symbols and separators
                clean = value.replace('₹', '').replace(',', '').replace('Rs.', '').strip()
                return float(clean) if clean else None
        except (ValueError, TypeError):
            pass
        return None

    @staticmethod
    def _is_valid_tender(tender: Dict) -> bool:
        """Check if tender has all required fields"""
        for field in TenderParser.REQUIRED_FIELDS:
            if not tender.get(field):
                return False
        return True

    @staticmethod
    def _extract_tender_from_row(row_element) -> Optional[Dict]:
        """
        Extract tender data from HTML table row
        TODO: Update selectors based on actual HTML structure
        """
        try:
            # Example (to be updated):
            # tender = {
            #     'tender_id': row_element.find('td', class_='tender-id').text.strip(),
            #     'title': row_element.find('td', class_='title').text.strip(),
            #     ...
            # }
            pass

        except Exception as e:
            logger.error(f"Error extracting tender from row: {e}")
            return None
