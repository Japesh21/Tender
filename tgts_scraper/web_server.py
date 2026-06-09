"""
Simple Flask web server for sending emails and WhatsApp from HTML report buttons.
Run alongside main.py to enable one-click send functionality.
"""

import logging
import os
from typing import List, Dict
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from datetime import datetime

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


def get_email_notifier():
    """Lazy-load email notifier with credentials from env"""
    from config import EMAIL_FROM, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT
    from notifications.email_notifier import EmailNotifier

    if not EMAIL_FROM or not EMAIL_PASSWORD:
        return None

    try:
        return EmailNotifier(
            smtp_server=SMTP_SERVER,
            smtp_port=SMTP_PORT,
            sender_email=EMAIL_FROM,
            sender_password=EMAIL_PASSWORD
        )
    except Exception as e:
        logger.error(f"Failed to initialize email notifier: {e}")
        return None


def get_whatsapp_notifier():
    """Lazy-load WhatsApp notifier with credentials from env"""
    from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_FROM

    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        return None

    try:
        from notifications.whatsapp_notifier import WhatsAppNotifier
        return WhatsAppNotifier(
            account_sid=TWILIO_ACCOUNT_SID,
            auth_token=TWILIO_AUTH_TOKEN,
            from_phone=TWILIO_PHONE_FROM
        )
    except Exception as e:
        logger.error(f"Failed to initialize WhatsApp notifier: {e}")
        return None


@app.route('/api/send-email', methods=['POST', 'OPTIONS'])
def send_email():
    """Send email with all tenders"""
    if request.method == 'OPTIONS':
        return '', 200

    try:
        data = request.json
        tenders = data.get('tenders', [])
        recipient_emails = data.get('recipients', [])

        logger.info(f"send_email called: {len(tenders)} tenders, {len(recipient_emails)} recipients")

        if not tenders or not recipient_emails:
            return jsonify({'success': False, 'error': 'Missing tenders or recipients'}), 400

        notifier = get_email_notifier()
        if not notifier:
            logger.error("Email notifier not initialized")
            return jsonify({'success': False, 'error': 'Email not configured. Set EMAIL_FROM and EMAIL_PASSWORD in .env'}), 500

        # Build email content - clean titles (remove \r\n)
        subject = f"TGTS Tenders Report - {len(tenders)} tenders - {datetime.now().strftime('%d %b %Y')}"
        body_lines = [
            "<h2 style='color:#333;'>TGTS Tenders Report</h2>",
            f"<p><strong>Total Tenders: {len(tenders)}</strong> | Generated: {datetime.now().strftime('%d %b %Y %H:%M')}</p>",
            "<table style='border-collapse:collapse;width:100%;font-family:Arial,sans-serif;font-size:13px;'>",
            "<tr style='background:#4CAF50;color:white;'>",
            "<th style='border:1px solid #ddd;padding:8px;text-align:left;'>#</th>",
            "<th style='border:1px solid #ddd;padding:8px;text-align:left;'>Tender ID</th>",
            "<th style='border:1px solid #ddd;padding:8px;text-align:left;'>Title</th>",
            "<th style='border:1px solid #ddd;padding:8px;text-align:left;'>Closing Date</th>",
            "<th style='border:1px solid #ddd;padding:8px;text-align:left;'>Status</th>",
            "<th style='border:1px solid #ddd;padding:8px;text-align:left;'>Document</th>",
            "</tr>"
        ]

        for i, tender in enumerate(tenders, 1):
            title = tender.get('title', '').replace('\r\n', ' ').replace('\n', ' ').strip()
            doc_link = tender.get('document_link', '')
            doc_cell = f"<a href='{doc_link}' style='color:#0066cc;'>View</a>" if doc_link else "N/A"
            row_bg = "#f9f9f9" if i % 2 == 0 else "#ffffff"
            body_lines.append(
                f"<tr style='background:{row_bg};'>"
                f"<td style='border:1px solid #ddd;padding:8px;'>{i}</td>"
                f"<td style='border:1px solid #ddd;padding:8px;'>{tender.get('tender_id', '')}</td>"
                f"<td style='border:1px solid #ddd;padding:8px;'>{title}</td>"
                f"<td style='border:1px solid #ddd;padding:8px;'>{tender.get('closing_date', '')}</td>"
                f"<td style='border:1px solid #ddd;padding:8px;'>{tender.get('status', '')}</td>"
                f"<td style='border:1px solid #ddd;padding:8px;'>{doc_cell}</td>"
                f"</tr>"
            )

        body_lines.append("</table>")
        body_lines.append("<p style='color:#666;font-size:12px;margin-top:20px;'>Automated report from TGTS Tender Scraper</p>")
        body = "".join(body_lines)

        logger.info(f"Attempting to send email to {recipient_emails}")
        success = notifier.send_with_attachments(recipient_emails, subject, body, [])

        if success:
            logger.info(f"Email sent successfully to {recipient_emails}")
            return jsonify({'success': True, 'message': f'Email sent to {len(recipient_emails)} recipient(s)'}), 200
        else:
            logger.error("send_with_attachments returned False")
            return jsonify({'success': False, 'error': 'Failed to send email'}), 500

    except Exception as e:
        logger.error(f"Error in send_email: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/send-whatsapp', methods=['POST'])
def send_whatsapp():
    """Send WhatsApp message with all tenders"""
    try:
        data = request.json
        tenders = data.get('tenders', [])
        phone_numbers = data.get('phone_numbers', [])

        if not tenders or not phone_numbers:
            return jsonify({'success': False, 'error': 'Missing tenders or phone numbers'}), 400

        notifier = get_whatsapp_notifier()
        if not notifier:
            return jsonify({'success': False, 'error': 'WhatsApp not configured. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env'}), 500

        # Build WhatsApp message
        msg_lines = [f"📊 TGTS Tenders Report - {len(tenders)} tenders\n"]
        for i, tender in enumerate(tenders[:10], 1):
            msg_lines.append(f"{i}. {tender.get('tender_id')} - {tender.get('title')[:40]}")
            msg_lines.append(f"   Closes: {tender.get('closing_date')}\n")

        if len(tenders) > 10:
            msg_lines.append(f"... and {len(tenders) - 10} more tenders\n")

        msg_lines.append("Check email for full list with Excel attachment.")
        message = "".join(msg_lines)

        # Build the message (WhatsApp notifier expects a list of tenders)
        success = notifier.send_new_tender_alert(phone_numbers, tenders)

        if success:
            return jsonify({'success': True, 'message': f'WhatsApp sent to {len(phone_numbers)} number(s)'}), 200
        else:
            return jsonify({'success': False, 'error': 'Failed to send WhatsApp'}), 500

    except Exception as e:
        logger.error(f"Error in send_whatsapp: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/download-excel', methods=['GET'])
def download_excel():
    """Download the latest Excel report"""
    excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'tgts_tenders.xlsx')
    if os.path.exists(excel_path):
        return send_file(excel_path, as_attachment=True, download_name='tgts_tenders.xlsx')
    return jsonify({'error': 'Excel file not found. Run main.py first to generate it.'}), 404


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()}), 200


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting TGTS Web Server on http://localhost:5000")
    logger.info("HTML buttons will POST to /api/send-email and /api/send-whatsapp")
    app.run(debug=False, host='127.0.0.1', port=5000)
