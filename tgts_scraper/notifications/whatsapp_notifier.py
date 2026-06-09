"""
WhatsApp notification module (Twilio)
Sends WhatsApp alerts for new tenders and errors
"""

import logging
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class WhatsAppNotifier:
    """Handles WhatsApp notifications via Twilio"""

    def __init__(self, account_sid: str, auth_token: str, from_phone: str):
        """
        Initialize WhatsApp notifier
        Note: Requires twilio package - install with: pip install twilio
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_phone = from_phone

        # Lazy import - only load if actually used
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Twilio client"""
        try:
            from twilio.rest import Client
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("Twilio client initialized")
        except ImportError:
            logger.warning("Twilio not installed. WhatsApp notifications disabled. Install with: pip install twilio")
        except Exception as e:
            logger.error(f"Error initializing Twilio: {e}")

    def send_new_tender_alert(self, phone_numbers: List[str], new_tenders: List[dict]) -> bool:
        """Send WhatsApp alert about new tenders"""
        try:
            if not self.client:
                logger.error("Twilio client not available")
                return False

            if not phone_numbers or not new_tenders:
                logger.warning("No recipients or tenders to notify")
                return False

            message = self._build_tender_message(new_tenders, "NEW")

            return self._send_message(phone_numbers, message)

        except Exception as e:
            logger.error(f"Error sending new tender alert: {e}")
            return False

    def send_daily_report(self, phone_numbers: List[str], all_tenders: List[dict]) -> bool:
        """Send full daily report when no new tenders detected"""
        try:
            if not self.client:
                logger.error("Twilio client not available")
                return False
            message = self._build_tender_message(all_tenders, "DAILY")
            return self._send_message(phone_numbers, message)
        except Exception as e:
            logger.error(f"Error sending daily report: {e}")
            return False

    def send_closing_soon_alert(self, phone_numbers: List[str], closing_tenders: List[dict]) -> bool:
        """Send WhatsApp alert about tenders closing soon"""
        try:
            if not self.client:
                logger.error("Twilio client not available")
                return False

            if not phone_numbers or not closing_tenders:
                logger.warning("No recipients or tenders to notify")
                return False

            message = self._build_tender_message(closing_tenders, "CLOSING SOON")

            return self._send_message(phone_numbers, message)

        except Exception as e:
            logger.error(f"Error sending closing soon alert: {e}")
            return False

    def send_error_alert(self, phone_numbers: List[str], error_message: str) -> bool:
        """Send WhatsApp alert about errors"""
        try:
            if not self.client:
                logger.error("Twilio client not available")
                return False

            message = f"""
❌ TGTS Tender Scraper Error
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Error: {error_message}

Please check the system logs.
"""

            return self._send_message(phone_numbers, message)

        except Exception as e:
            logger.error(f"Error sending error alert: {e}")
            return False

    def send_daily_summary(self, phone_numbers: List[str], stats: dict) -> bool:
        """Send daily summary via WhatsApp"""
        try:
            if not self.client:
                logger.error("Twilio client not available")
                return False

            message = f"""
📊 TGTS Daily Summary
Date: {datetime.now().strftime('%Y-%m-%d')}

Total Tenders: {stats.get('total_tenders', 0)}
New Tenders: {stats.get('new_tenders', 0)}
Updated: {stats.get('updated_tenders', 0)}
Closing Soon: {stats.get('closing_soon', 0)}

Reports: CSV & Excel formats available
"""

            return self._send_message(phone_numbers, message)

        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
            return False

    def _send_message(self, phone_numbers: List[str], message: str) -> bool:
        """Send WhatsApp message (split into chunks if exceeds 1600 chars)"""
        try:
            if not self.client:
                logger.error("Twilio client not available")
                return False

            # Split message into chunks if exceeds Twilio's 1600 char limit
            messages = self._split_message(message)

            success_count = 0
            for phone in phone_numbers:
                try:
                    formatted_phone = self._format_phone(phone)
                    all_sent = True

                    for i, msg_chunk in enumerate(messages, 1):
                        try:
                            msg = self.client.messages.create(
                                from_=f"whatsapp:{self.from_phone}",
                                to=f"whatsapp:{formatted_phone}",
                                body=msg_chunk
                            )
                            logger.info(f"WhatsApp message {i}/{len(messages)} sent to {formatted_phone}: {msg.sid}")
                        except Exception as e:
                            logger.error(f"Error sending message {i} to {phone}: {e}")
                            all_sent = False

                    if all_sent:
                        success_count += 1

                except Exception as e:
                    logger.error(f"Error processing phone {phone}: {e}")

            return success_count == len(phone_numbers)

        except Exception as e:
            logger.error(f"Error in send message: {e}")
            return False

    @staticmethod
    def _format_phone(phone: str) -> str:
        """Format phone number to E.164 format"""
        # Remove common separators
        phone = phone.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')

        # Ensure + prefix
        if not phone.startswith('+'):
            # Assume India (+91) if no country code
            if not phone.startswith('91') and len(phone) == 10:
                phone = '+91' + phone
            elif len(phone) == 10:
                phone = '+91' + phone
            else:
                phone = '+' + phone

        return phone

    @staticmethod
    def _build_tender_message(tenders: List[dict], alert_type: str) -> str:
        """Build compact WhatsApp message with all tender info (split into chunks if too long)"""
        if alert_type == "NEW":
            header = f"🆕 NEW Tenders Alert - {len(tenders)} new tender(s)!\n{'='*40}\n\n"
        else:
            header = f"📊 TGTS Daily Report - {len(tenders)} Tenders\n{'='*40}\n\n"

        tender_lines = []
        for i, tender in enumerate(tenders, 1):
            tender_id = tender.get('tender_id', 'N/A')
            title = tender.get('title', 'N/A').replace('\r\n', ' ').replace('\n', ' ').strip()[:40]
            closing = tender.get('closing_date', 'N/A')

            tender_lines.append(f"{i}. [{tender_id}] {title}")
            tender_lines.append(f"   Closes: {closing}\n")

        footer = f"{'='*40}\n🌐 tender.telangana.gov.in"

        return header + "\n".join(tender_lines) + footer

    @staticmethod
    def _split_message(message: str, max_length: int = 1500) -> List[str]:
        """Split message into chunks respecting 1600 char Twilio limit"""
        if len(message) <= max_length:
            return [message]

        chunks = []
        lines = message.split('\n')
        current_chunk = ""

        for line in lines:
            test_chunk = current_chunk + line + "\n" if current_chunk else line + "\n"
            if len(test_chunk) > max_length:
                if current_chunk:
                    chunks.append(current_chunk.rstrip())
                    current_chunk = line + "\n"
                else:
                    chunks.append(line)
                    current_chunk = ""
            else:
                current_chunk = test_chunk

        if current_chunk:
            chunks.append(current_chunk.rstrip())

        # Add part numbers to help user understand multi-message splits
        if len(chunks) > 1:
            chunks = [f"[Part {i+1}/{len(chunks)}]\n{chunk}" for i, chunk in enumerate(chunks)]

        return chunks
