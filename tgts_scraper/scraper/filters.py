"""
Filter module for tender filtering and selection
"""

import logging
import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TenderFilter:
    """Filters tenders based on various criteria"""

    @staticmethod
    def filter_by_department(tenders: List[Dict], target_departments: List[str]) -> List[Dict]:
        """Filter tenders by department"""
        filtered = []
        for tender in tenders:
            dept = tender.get('department', '')
            if not dept:
                continue

            lower_dept = dept.lower()
            for target in target_departments:
                if not target:
                    continue

                target = target.strip()
                if not target:
                    continue

                lower_target = target.lower()
                if lower_target == lower_dept:
                    filtered.append(tender)
                    break

                # Match whole words for short keywords like IT/TGTS,
                # and exact phrase match for longer department names.
                if re.search(rf"\b{re.escape(target)}\b", dept, flags=re.IGNORECASE):
                    filtered.append(tender)
                    break

        if not filtered:
            unique_depts = {}
            for tender in tenders:
                dept = tender.get('department')
                unique_depts[dept] = unique_depts.get(dept, 0) + 1
            sample = list(unique_depts.items())[:20]
            logger.info(f"No department matches. Sample departments: {sample}")

        logger.info(f"Filtered {len(filtered)}/{len(tenders)} tenders by department")
        return filtered

    @staticmethod
    def filter_by_status(tenders: List[Dict], statuses: List[str]) -> List[Dict]:
        """Filter tenders by status"""
        filtered = [t for t in tenders if t.get('status') in statuses]
        logger.info(f"Filtered {len(filtered)}/{len(tenders)} tenders by status")
        return filtered

    @staticmethod
    def filter_by_closing_date_range(
        tenders: List[Dict],
        min_days: int = 0,
        max_days: int = 30
    ) -> List[Dict]:
        """
        Filter tenders by closing date range
        min_days: days from now (minimum)
        max_days: days from now (maximum)
        """
        try:
            filtered = []
            now = datetime.now()

            for tender in tenders:
                closing_date_str = tender.get('closing_date')
                if not closing_date_str:
                    continue

                try:
                    # Try multiple date formats
                    closing_date = TenderFilter._parse_date(closing_date_str)
                    if closing_date:
                        days_until = (closing_date - now).days
                        if min_days <= days_until <= max_days:
                            filtered.append(tender)
                except Exception:
                    logger.warning(f"Could not parse closing date: {closing_date_str}")

            logger.info(f"Filtered {len(filtered)}/{len(tenders)} tenders by closing date")
            return filtered

        except Exception as e:
            logger.error(f"Error filtering by closing date: {e}")
            return tenders

    @staticmethod
    def filter_by_minimum_value(tenders: List[Dict], min_value: float) -> List[Dict]:
        """Filter tenders with minimum tender value"""
        filtered = []
        for tender in tenders:
            try:
                value = float(tender.get('tender_value', 0))
                if value >= min_value:
                    filtered.append(tender)
            except (ValueError, TypeError):
                filtered.append(tender)  # Include if value is unparseable

        logger.info(f"Filtered {len(filtered)}/{len(tenders)} tenders by minimum value")
        return filtered

    @staticmethod
    def filter_by_keywords(tenders: List[Dict], keywords: List[str]) -> List[Dict]:
        """Return tenders whose title matches any keyword (case-insensitive)."""
        patterns = [re.compile(re.escape(kw), re.IGNORECASE) for kw in keywords]
        filtered = [t for t in tenders if any(p.search(t.get('title', '')) for p in patterns)]
        logger.info(f"Keyword filter: {len(filtered)}/{len(tenders)} tenders matched")
        return filtered

    @staticmethod
    def remove_duplicates(tenders: List[Dict], key: str = 'tender_id') -> List[Dict]:
        """Remove duplicate tenders based on key field"""
        seen = set()
        unique = []

        for tender in tenders:
            tender_key = tender.get(key)
            if tender_key and tender_key not in seen:
                seen.add(tender_key)
                unique.append(tender)

        logger.info(f"Removed {len(tenders) - len(unique)} duplicates")
        return unique

    @staticmethod
    def _parse_date(date_string: str) -> Optional[datetime]:
        """Parse date string in multiple formats"""
        formats = [
            '%Y-%m-%d',
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%Y/%m/%d',
            '%d %b %Y',
            '%d %B %Y',
            '%Y-%m-%d %H:%M:%S',
            '%d-%m-%Y %H:%M:%S'
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_string.strip(), fmt)
            except ValueError:
                continue

        return None

    @staticmethod
    def apply_filters(
        tenders: List[Dict],
        departments: Optional[List[str]] = None,
        statuses: Optional[List[str]] = None,
        closing_days_range: Optional[tuple] = None,
        min_tender_value: Optional[float] = None
    ) -> List[Dict]:
        """Apply multiple filters in sequence"""
        result = tenders

        if departments:
            result = TenderFilter.filter_by_department(result, departments)

        if statuses:
            result = TenderFilter.filter_by_status(result, statuses)

        if closing_days_range:
            min_days, max_days = closing_days_range
            result = TenderFilter.filter_by_closing_date_range(result, min_days, max_days)

        if min_tender_value is not None:
            result = TenderFilter.filter_by_minimum_value(result, min_tender_value)

        result = TenderFilter.remove_duplicates(result)

        logger.info(f"Applied filters: {len(result)}/{len(tenders)} tenders remain")
        return result
