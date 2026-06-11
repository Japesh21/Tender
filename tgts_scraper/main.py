"""
Main entry point for TGTS Tender Scraper
Orchestrates fetching, parsing, storing, and exporting tender data
"""

import logging
import sys
import os
from datetime import datetime
from typing import List, Dict, Optional

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Import local modules
from config import (
    TENDER_WEBSITE_URL,
    TARGET_DEPARTMENTS,
    TARGET_DEPARTMENT_IDS,
    OUTPUT_DIR,
    DATABASE_FILE,
    SCHEDULE_TIME,
    EMAIL_ENABLED,
    WHATSAPP_ENABLED,
    EMAIL_FROM,
    EMAIL_PASSWORD,
    EMAIL_TO_LIST,
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_PHONE_FROM,
    WHATSAPP_PHONE_TO_LIST,
    PORTAL_USERNAME,
    PORTAL_PASSWORD,
)

from scraper.fetch_tenders import TenderFetcher
from scraper.parser import TenderParser
from scraper.filters import TenderFilter
from scraper.browser_session import get_authenticated_session, invalidate_cookies
from database.db_manager import TenderDatabase
from output.generator import OutputGenerator
from notifications.email_notifier import EmailNotifier
from notifications.whatsapp_notifier import WhatsAppNotifier


class TenderScraper:
    """Main orchestrator for tender scraping process"""

    def __init__(self):
        """Initialize scraper components"""
        self.db = TenderDatabase(DATABASE_FILE)
        self.output_gen = OutputGenerator(OUTPUT_DIR)

        # Initialize notifiers if enabled
        self.email_notifier = None
        if EMAIL_ENABLED and EMAIL_FROM and EMAIL_PASSWORD:
            try:
                self.email_notifier = EmailNotifier(
                    smtp_server='smtp.gmail.com',
                    smtp_port=587,
                    sender_email=EMAIL_FROM,
                    sender_password=EMAIL_PASSWORD
                )
            except Exception as e:
                logger.warning(f"Email notifier initialization failed: {e}")

        self.whatsapp_notifier = None
        if WHATSAPP_ENABLED and TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
            try:
                self.whatsapp_notifier = WhatsAppNotifier(
                    account_sid=TWILIO_ACCOUNT_SID,
                    auth_token=TWILIO_AUTH_TOKEN,
                    from_phone=TWILIO_PHONE_FROM
                )
            except Exception as e:
                logger.warning(f"WhatsApp notifier initialization failed: {e}")

    def run(self) -> bool:
        """Execute the complete scraping workflow"""
        try:
            logger.info("=== TGTS Tender Scraper Started ===")
            logger.info(f"Target departments: {TARGET_DEPARTMENTS}")

            # Step 1: Fetch tenders from portal (falls back to DB if credentials missing)
            tenders = self.fetch_tenders()
            if not tenders:
                logger.warning("Portal fetch failed or no credentials — falling back to existing DB tenders")
                filtered_tenders = self.db.get_all_tenders()
                if not filtered_tenders:
                    return self.handle_error("No tenders in DB and portal fetch failed")
                logger.info(f"Using {len(filtered_tenders)} tenders from DB")
                # Still generate reports and send notifications from DB data
                self.generate_reports(filtered_tenders)
                excel_path = self.output_gen.get_latest_files().get('excel')
                if self.email_notifier and EMAIL_TO_LIST and excel_path:
                    self.email_notifier.send_daily_report(EMAIL_TO_LIST, filtered_tenders, excel_path, new_count=0)
                self.send_notifications([], [], filtered_tenders)
                logger.info("=== TGTS Tender Scraper Completed (DB fallback) ===")
                return True

            # Step 2: Filter by department
            filtered_tenders = TenderFilter.filter_by_department(tenders, TARGET_DEPARTMENTS)
            if not filtered_tenders:
                logger.warning("No tenders matched filter criteria")

            # Step 3: Detect new and updated tenders
            new_tenders, updated_tenders = self.process_tenders(filtered_tenders)

            # Step 4: Generate reports
            self.generate_reports(filtered_tenders)

            # Step 4b: Send daily report email with Excel attachment
            excel_path = self.output_gen.get_latest_files().get('excel')
            if self.email_notifier and EMAIL_TO_LIST and excel_path:
                logger.info("Sending daily report email with Excel attachment...")
                self.email_notifier.send_daily_report(
                    EMAIL_TO_LIST,
                    filtered_tenders,
                    excel_path,
                    new_count=len(new_tenders)
                )

            # Step 5: Send notifications (WhatsApp always sends all tenders; email sends new/closing alerts)
            self.send_notifications(new_tenders, updated_tenders, filtered_tenders)

            # Step 6: Log summary
            self.log_summary(filtered_tenders, new_tenders, updated_tenders)

            logger.info("=== TGTS Tender Scraper Completed Successfully ===")
            return True

        except Exception as e:
            logger.error(f"Fatal error in scraper: {e}", exc_info=True)
            return self.handle_error(str(e))

    def fetch_tenders(self) -> Optional[List[Dict]]:
        """Fetch tenders from website using an authenticated browser session."""
        try:
            if not PORTAL_USERNAME or not PORTAL_PASSWORD:
                logger.error(
                    "PORTAL_USERNAME and PORTAL_PASSWORD must be set in .env — "
                    "cannot fetch tenders without portal credentials"
                )
                return None

            try:
                auth_session = get_authenticated_session(PORTAL_USERNAME, PORTAL_PASSWORD)
            except RuntimeError as e:
                logger.error(f"Portal login failed: {e}")
                invalidate_cookies()
                return None

            with TenderFetcher(TENDER_WEBSITE_URL, session=auth_session) as fetcher:
                if TARGET_DEPARTMENT_IDS:
                    all_tenders = []
                    for department_id in TARGET_DEPARTMENT_IDS:
                        search_params = {
                            'nDepartmentID': department_id,
                            'selectedDepartmentID': department_id,
                            'iDisplayLength': '1000'
                        }
                        logger.info(f"Searching tenders for department id {department_id}")
                        tenders = fetcher.search_tenders(search_params)
                        if tenders:
                            all_tenders.extend(tenders)

                    if not all_tenders:
                        logger.warning("No tenders returned from department-specific search")
                        return []

                    unique_tenders = TenderFilter.remove_duplicates(all_tenders)
                    logger.info(f"Fetched {len(unique_tenders)} unique tenders from website")
                    return unique_tenders

                # Fallback: search all tenders if no department IDs are configured
                search_params = {'queryString': ''}
                tenders = fetcher.search_tenders(search_params)
                if not tenders:
                    logger.warning("No tenders returned from search")
                    return []

                logger.info(f"Fetched {len(tenders)} tenders from website")
                return tenders

        except Exception as e:
            logger.error(f"Error fetching tenders: {e}")
            return None

    def process_tenders(self, tenders: List[Dict]) -> tuple:
        """Process tenders: detect new and updated"""
        new_tenders = []
        updated_tenders = []

        try:
            for tender in tenders:
                existing = self.db.get_tender(tender['tender_id'])

                if not existing:
                    # New tender
                    if self.db.insert_tender(tender):
                        new_tenders.append(tender)
                        logger.info(f"New tender detected: {tender['tender_id']}")
                else:
                    # Existing tender - check for updates
                    updates = {k: v for k, v in tender.items() if existing.get(k) != v}
                    if updates:
                        self.db.update_tender(tender['tender_id'], updates)
                        updated_tenders.append(tender)
                        logger.info(f"Tender updated: {tender['tender_id']}")
                    else:
                        # Mark as seen
                        self.db.mark_tender_seen(tender['tender_id'])

            # Detect tenders no longer on portal → mark as Removed
            fetched_ids = {t['tender_id'] for t in tenders}
            for db_tender in self.db.get_all_tenders():
                if db_tender['tender_id'] not in fetched_ids and db_tender.get('status') != 'Removed':
                    self.db.update_tender(db_tender['tender_id'], {'status': 'Removed'})
                    logger.info(f"Marked as Removed (no longer on portal): {db_tender['tender_id']}")

        except Exception as e:
            logger.error(f"Error processing tenders: {e}")

        return new_tenders, updated_tenders

    def generate_reports(self, tenders: List[Dict]):
        """Generate CSV, Excel, and HTML reports"""
        try:
            if not tenders:
                logger.warning("No tenders to generate reports")
                return

            logger.info("Generating reports...")

            # CSV
            csv_path = self.output_gen.generate_csv(tenders)
            if csv_path:
                logger.info(f"CSV report: {csv_path}")

            # Excel
            excel_path = self.output_gen.generate_excel(tenders)
            if excel_path:
                logger.info(f"Excel report: {excel_path}")

            # HTML
            html_path = self.output_gen.generate_html_report(tenders)
            if html_path:
                logger.info(f"HTML report: {html_path}")

        except Exception as e:
            logger.error(f"Error generating reports: {e}")

    def send_notifications(self, new_tenders: List[Dict], updated_tenders: List[Dict], all_tenders: List[Dict]):
        """Send notifications — new tender alert on both channels when new tenders found, else full daily report"""
        try:
            if new_tenders:
                # Instant alert with ONLY the new tenders on both email + WhatsApp
                logger.info(f"NEW tenders detected: {len(new_tenders)} — sending alerts")
                if self.email_notifier and EMAIL_TO_LIST:
                    self.email_notifier.send_new_tender_alert(EMAIL_TO_LIST, new_tenders)
                if self.whatsapp_notifier and WHATSAPP_PHONE_TO_LIST:
                    self.whatsapp_notifier.send_new_tender_alert(WHATSAPP_PHONE_TO_LIST, new_tenders)
            else:
                # No new tenders — WhatsApp gets the full daily report so user always gets a morning message
                logger.info("No new tenders — sending full daily report to WhatsApp")
                if self.whatsapp_notifier and WHATSAPP_PHONE_TO_LIST and all_tenders:
                    self.whatsapp_notifier.send_daily_report(WHATSAPP_PHONE_TO_LIST, all_tenders)

            # Closing soon email alert (independent of new tenders)
            if self.email_notifier and EMAIL_TO_LIST:
                closing_soon = self.db.get_closing_soon_tenders(days=7)
                if closing_soon:
                    self.email_notifier.send_closing_soon_alert(EMAIL_TO_LIST, closing_soon)

        except Exception as e:
            logger.error(f"Error sending notifications: {e}")

    def log_summary(self, all_tenders: List[Dict], new_tenders: List[Dict], updated_tenders: List[Dict]):
        """Log execution summary"""
        try:
            stats = self.db.get_database_stats()

            summary = f"""
            ===== EXECUTION SUMMARY =====
            Processed: {len(all_tenders)} tenders
            New: {len(new_tenders)}
            Updated: {len(updated_tenders)}
            Total in DB: {stats.get('total_tenders', 0)}
            By Status: {stats.get('by_status', {})}
            By Department: {stats.get('by_department', {})}
            Recent Changes (24h): {stats.get('changes_last_24h', 0)}
            =============================
            """

            logger.info(summary)

        except Exception as e:
            logger.error(f"Error logging summary: {e}")

    def handle_error(self, error_message: str) -> bool:
        """Handle errors and send alert"""
        try:
            logger.error(f"Scraper error: {error_message}")

            # Send error notification
            if self.email_notifier and EMAIL_TO_LIST:
                self.email_notifier.send_error_alert(
                    EMAIL_TO_LIST,
                    error_message,
                    "Check logs for details"
                )

            if self.whatsapp_notifier and WHATSAPP_PHONE_TO_LIST:
                self.whatsapp_notifier.send_error_alert(
                    WHATSAPP_PHONE_TO_LIST,
                    error_message
                )

            return False

        except Exception as e:
            logger.error(f"Error in error handler: {e}")
            return False


def main():
    """Main entry point"""
    try:
        scraper = TenderScraper()
        success = scraper.run()
        sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
