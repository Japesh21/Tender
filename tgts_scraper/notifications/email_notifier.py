"""
Email notification module
Sends email alerts for new tenders and errors
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Handles email notifications"""

    def __init__(self, smtp_server: str, smtp_port: int, sender_email: str, sender_password: str):
        """Initialize email notifier"""
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password

    def send_new_tender_alert(self, recipient_emails: List[str], new_tenders: List[dict]) -> bool:
        """Send email alert about new tenders"""
        try:
            if not recipient_emails or not new_tenders:
                logger.warning("No recipients or tenders to notify")
                return False

            subject = f"🔔 New TGTS Tenders Alert - {len(new_tenders)} new tender(s)"

            # Build email body
            body = self._build_tender_email_body(new_tenders)

            return self._send_email(recipient_emails, subject, body)

        except Exception as e:
            logger.error(f"Error sending new tender alert: {e}")
            return False

    def send_closing_soon_alert(self, recipient_emails: List[str], closing_tenders: List[dict]) -> bool:
        """Send email alert about tenders closing soon"""
        try:
            if not recipient_emails or not closing_tenders:
                logger.warning("No recipients or tenders to notify")
                return False

            subject = f"⏰ Closing Soon - {len(closing_tenders)} tender(s) closing in 7 days"

            body = self._build_tender_email_body(closing_tenders, "CLOSING SOON")

            return self._send_email(recipient_emails, subject, body)

        except Exception as e:
            logger.error(f"Error sending closing soon alert: {e}")
            return False

    def send_error_alert(self, recipient_emails: List[str], error_message: str, error_details: str = "") -> bool:
        """Send email alert about errors"""
        try:
            subject = "❌ TGTS Tender Scraper - Error Alert"

            body = f"""
            <h2>Error in TGTS Tender Scraper</h2>
            <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Error:</strong> {error_message}</p>
            
            {f'<h3>Details:</h3><pre>{error_details}</pre>' if error_details else ''}
            
            <p>Please check the logs for more information.</p>
            """

            return self._send_email(recipient_emails, subject, body)

        except Exception as e:
            logger.error(f"Error sending error alert: {e}")
            return False

    def send_daily_summary(self, recipient_emails: List[str], stats: dict) -> bool:
        """Send daily summary email"""
        try:
            subject = f"📊 TGTS Daily Summary - {datetime.now().strftime('%Y-%m-%d')}"

            body = f"""
            <h2>TGTS Tender Daily Summary</h2>
            <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h3>Statistics</h3>
            <ul>
                <li><strong>Total Tenders:</strong> {stats.get('total_tenders', 0)}</li>
                <li><strong>New Tenders:</strong> {stats.get('new_tenders', 0)}</li>
                <li><strong>Updated Tenders:</strong> {stats.get('updated_tenders', 0)}</li>
                <li><strong>Closing Soon (7 days):</strong> {stats.get('closing_soon', 0)}</li>
                <li><strong>By Status:</strong> {self._format_status_stats(stats.get('by_status', {}))}</li>
            </ul>
            
            <p>Reports are available in CSV and Excel formats.</p>
            """

            return self._send_email(recipient_emails, subject, body)

        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
            return False

    def send_daily_report(self, recipient_emails: List[str], tenders: List[dict], excel_path: str, new_count: int = 0) -> bool:
        """Send daily tender report with Excel attachment"""
        try:
            total = len(tenders)
            subject = f"📊 TGTS Daily Tender Report - {datetime.now().strftime('%Y-%m-%d')} ({total} tenders, {new_count} new)"

            # Build compact HTML table (top 20 rows)
            table_html = "<table style='border-collapse:collapse;width:100%;'>"
            table_html += "<thead><tr style='background-color:#4CAF50;color:white;'>"
            table_html += "<th style='padding:10px;border:1px solid #ddd;'>Tender ID</th>"
            table_html += "<th style='padding:10px;border:1px solid #ddd;'>Title</th>"
            table_html += "<th style='padding:10px;border:1px solid #ddd;'>Closing Date</th>"
            table_html += "<th style='padding:10px;border:1px solid #ddd;'>Department</th>"
            table_html += "</tr></thead><tbody>"

            for tender in tenders[:20]:
                table_html += f"<tr style='border-bottom:1px solid #ddd;'>"
                table_html += f"<td style='padding:10px;border:1px solid #ddd;'>{tender.get('tender_id', '')}</td>"
                table_html += f"<td style='padding:10px;border:1px solid #ddd;'>{tender.get('title', '')[:60]}...</td>"
                table_html += f"<td style='padding:10px;border:1px solid #ddd;'>{tender.get('closing_date', '')}</td>"
                table_html += f"<td style='padding:10px;border:1px solid #ddd;'>{tender.get('department', '')}</td>"
                table_html += "</tr>"

            table_html += "</tbody></table>"
            if total > 20:
                table_html += f"<p style='color:#666;font-size:12px;'>Showing top 20 of {total} tenders. See attached Excel for complete list.</p>"

            body = f"""
            <h2>📊 TGTS Daily Tender Report</h2>
            <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST</p>
            <p><strong>Total Tenders:</strong> {total}</p>
            <p><strong>🆕 New Today:</strong> {new_count}</p>

            <h3>Recent Tenders</h3>
            {table_html}

            <p style='margin-top:20px;padding:10px;background:#E3F2FD;border-left:4px solid #2196F3;'>
            <strong>📎 Attachment:</strong> Full tender list with all details is in the attached Excel file (tgts_tenders.xlsx).
            </p>
            """

            return self.send_with_attachments(recipient_emails, subject, body, [excel_path])

        except Exception as e:
            logger.error(f"Error sending daily report: {e}")
            return False

    def send_with_attachments(
        self,
        recipient_emails: List[str],
        subject: str,
        body: str,
        attachments: List[str]
    ) -> bool:
        """Send email with file attachments"""
        try:
            message = MIMEMultipart()
            message['From'] = self.sender_email
            message['To'] = ', '.join(recipient_emails)
            message['Subject'] = subject

            # Add body
            message.attach(MIMEText(body, 'html'))

            # Add attachments
            for file_path in attachments:
                try:
                    with open(file_path, 'rb') as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f'attachment; filename= {file_path.split("/")[-1]}')
                        message.attach(part)
                except Exception as e:
                    logger.error(f"Could not attach file {file_path}: {e}")

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)

            logger.info(f"Email sent to {len(recipient_emails)} recipient(s)")
            return True

        except Exception as e:
            logger.error(f"Error sending email with attachments: {e}")
            return False

    def _send_email(self, recipient_emails: List[str], subject: str, body: str) -> bool:
        """Send email internally"""
        try:
            message = MIMEMultipart('alternative')
            message['From'] = self.sender_email
            message['To'] = ', '.join(recipient_emails)
            message['Subject'] = subject

            # Attach HTML body
            message.attach(MIMEText(body, 'html'))

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)

            logger.info(f"Email sent to {len(recipient_emails)} recipient(s): {subject}")
            return True

        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    @staticmethod
    def _build_tender_email_body(tenders: List[dict], alert_type: str = "NEW") -> str:
        """Build HTML email body with tender information"""
        rows = ""
        for tender in tenders[:10]:  # Limit to 10 tenders per email
            rows += f"""
            <tr>
                <td><strong>{tender.get('tender_id', 'N/A')}</strong></td>
                <td>{tender.get('title', 'N/A')}</td>
                <td>{tender.get('department', 'N/A')}</td>
                <td>{tender.get('closing_date', 'N/A')}</td>
                <td>{tender.get('tender_value', 'N/A')}</td>
                <td><a href="{tender.get('pdf_link', '#')}">Link</a></td>
            </tr>
            """

        body = f"""
        <h2>{alert_type} TGTS Tenders</h2>
        <p><strong>Count:</strong> {len(tenders)}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <table border="1" cellpadding="10" cellspacing="0" style="border-collapse: collapse; width: 100%;">
            <thead>
                <tr style="background-color: #4CAF50; color: white;">
                    <th>Tender ID</th>
                    <th>Title</th>
                    <th>Department</th>
                    <th>Closing Date</th>
                    <th>Value</th>
                    <th>Link</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        
        {f'<p><em>Showing first 10 of {len(tenders)} tenders</em></p>' if len(tenders) > 10 else ''}
        """

        return body

    @staticmethod
    def _format_status_stats(status_dict: dict) -> str:
        """Format status statistics for email"""
        return ', '.join([f"{status}: {count}" for status, count in status_dict.items()]) or "No data"
