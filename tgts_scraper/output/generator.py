"""
Output generator for CSV and Excel formats
"""

import logging
import os
import re
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime, timezone, timedelta
from urllib.parse import quote

logger = logging.getLogger(__name__)


class OutputGenerator:
    """Generates CSV and Excel reports from tender data"""

    def __init__(self, output_dir: str):
        """Initialize output generator"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_csv(self, tenders: List[Dict], filename: str = "tgts_tenders.csv") -> Optional[str]:
        """
        Generate CSV file from tender data
        Returns file path if successful
        """
        try:
            if not tenders:
                logger.warning("No tenders to export to CSV")
                return None

            df = pd.DataFrame(tenders)

            # Reorder columns for better readability
            column_order = [
                'tender_id', 'title', 'department', 'published_date',
                'closing_date', 'emd', 'tender_value', 'status',
                'document_link', 'corrigendum_link', 'pdf_link'
            ]

            # Only include columns that exist
            existing_cols = [col for col in column_order if col in df.columns]
            df = df[existing_cols]

            # Sort by closing date
            if 'closing_date' in df.columns:
                df = df.sort_values('closing_date')

            filepath = os.path.join(self.output_dir, filename)
            df.to_csv(filepath, index=False, encoding='utf-8')

            logger.info(f"CSV exported to {filepath} ({len(tenders)} tenders)")
            return filepath

        except Exception as e:
            logger.error(f"Error generating CSV: {e}")
            return None

    def generate_excel(self, tenders: List[Dict], filename: str = "tgts_tenders.xlsx") -> Optional[str]:
        """
        Generate Excel file from tender data
        Includes formatting and multiple sheets
        """
        try:
            if not tenders:
                logger.warning("No tenders to export to Excel")
                return None

            filepath = os.path.join(self.output_dir, filename)

            # Create Excel writer
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Sheet 1: All tenders
                df_all = pd.DataFrame(tenders)

                column_order = [
                    'tender_id', 'title', 'department', 'published_date',
                    'closing_date', 'emd', 'tender_value', 'status',
                    'document_link', 'corrigendum_link', 'pdf_link'
                ]

                existing_cols = [col for col in column_order if col in df_all.columns]
                df_all = df_all[existing_cols]
                df_all = df_all.sort_values('closing_date')

                df_all.to_excel(writer, sheet_name='All Tenders', index=False)

                # Sheet 2: Summary by status
                if 'status' in df_all.columns:
                    df_status = df_all.groupby('status').size().reset_index(name='Count')
                    df_status.to_excel(writer, sheet_name='Summary by Status', index=False)

                # Sheet 3: Summary by department
                if 'department' in df_all.columns:
                    df_dept = df_all.groupby('department').size().reset_index(name='Count')
                    df_dept.to_excel(writer, sheet_name='Summary by Department', index=False)

                # Sheet 4: Metadata
                metadata = {
                    'Property': [
                        'Export Date',
                        'Total Tenders',
                        'Export Time',
                        'Version'
                    ],
                    'Value': [
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        len(tenders),
                        datetime.now().isoformat(),
                        '1.0'
                    ]
                }
                df_meta = pd.DataFrame(metadata)
                df_meta.to_excel(writer, sheet_name='Metadata', index=False)

                # Format worksheets
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    # Auto-adjust column widths
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width

            logger.info(f"Excel exported to {filepath} ({len(tenders)} tenders)")
            return filepath

        except Exception as e:
            logger.error(f"Error generating Excel: {e}")
            return None

    def generate_html_report(self, tenders: List[Dict], filename: str = "tgts_report.html") -> Optional[str]:
        """
        Generate HTML report with new tender highlighting and share buttons.
        New tenders (created today IST) are marked in green with 🆕 badge.
        Each row has Email and WhatsApp buttons that open mailto: and wa.me links.
        """
        try:
            if not tenders:
                logger.warning("No tenders to export to HTML")
                return None

            IST = timezone(timedelta(hours=5, minutes=30))
            today_ist = datetime.now(IST).date()

            def is_new_tender(published_date_str):
                """A tender is 'new' if its published_date is TODAY in IST strictly."""
                if not published_date_str:
                    return False
                try:
                    # Portal format: "09/06/2026 11:36 AM"
                    dt = datetime.strptime(str(published_date_str).strip(), '%d/%m/%Y %I:%M %p')
                    return dt.date() == today_ist
                except:
                    return False

            # JSON data for buttons to send via API
            import json
            from config import AGENCIES, STEPS_AI_KEYWORDS
            tenders_json = json.dumps(tenders)

            # Steps AI keyword matching
            ai_patterns = [re.compile(re.escape(kw), re.IGNORECASE) for kw in STEPS_AI_KEYWORDS]
            def is_ai_tender(title):
                return any(p.search(title or '') for p in ai_patterns)

            # Count by state
            new_count = sum(1 for t in tenders if is_new_tender(t.get('published_date')))
            removed_count = sum(1 for t in tenders if t.get('status') == 'Removed')
            active_count = len(tenders) - removed_count
            ai_count = sum(1 for t in tenders if is_ai_tender(t.get('title', '')))

            # Per-agency counts for navbar — use source_agency field directly
            agency_counts = {}
            for t in tenders:
                ag = t.get('source_agency', 'TGTS')
                agency_counts[ag] = agency_counts.get(ag, 0) + 1

            # All unique agencies present in data (sorted, TGTS+TSMSIDC first)
            all_agencies_in_data = sorted(agency_counts.keys())
            priority = ['TGTS', 'TSMSIDC']
            ordered_agencies = [a for a in priority if a in agency_counts] + \
                               [a for a in all_agencies_in_data if a not in priority]

            # Build table manually for per-row styling
            th = 'style="padding:10px;border:1px solid #ddd;background:#1565C0;color:white;text-align:left;white-space:nowrap;"'
            table_rows = []
            table_rows.append(f'<thead><tr>'
                f'<th {th}>#</th>'
                f'<th {th}>Tender ID</th>'
                f'<th {th}>Title</th>'
                f'<th {th}>Tender Category</th>'
                f'<th {th}>Published Date & Time</th>'
                f'<th {th}>Bid Submission Start</th>'
                f'<th {th}>Bid Submission Closing</th>'
                f'<th {th}>Action</th>'
                f'<th {th}>Status</th>'
                f'</tr></thead>')
            table_rows.append('<tbody id="tenderTableBody">')

            for i, tender in enumerate(tenders, 1):
                is_new = is_new_tender(tender.get('published_date'))
                is_removed = tender.get('status') == 'Removed'
                agency = tender.get('source_agency', 'TGTS')
                ai_match = is_ai_tender(tender.get('title', ''))

                if is_new:
                    row_style = 'background-color:#C8E6C9;font-weight:bold;'
                    badge = '🆕 '
                    state = 'new'
                elif is_removed:
                    row_style = 'background-color:#FFCDD2;'
                    badge = '🗑 '
                    state = 'removed'
                else:
                    row_style = ''
                    badge = ''
                    state = 'active'

                if ai_match:
                    badge = '🤖 ' + badge

                doc_link = tender.get('document_link', '')
                action_cell = (
                    f'<a href="{doc_link}" target="_blank" style="'
                    f'display:inline-block;background:#1565C0;color:white;'
                    f'padding:5px 12px;border-radius:4px;text-decoration:none;'
                    f'font-size:12px;font-weight:600;letter-spacing:0.3px;'
                    f'box-shadow:0 1px 3px rgba(0,0,0,0.2);white-space:nowrap;">🔗 View Docs</a>'
                ) if doc_link else '<span style="color:#999;font-size:12px;">N/A</span>'

                td = 'style="padding:8px;border:1px solid #ddd;"'
                td_nowrap = 'style="padding:8px;border:1px solid #ddd;white-space:nowrap;"'
                row_html = (f'<tr style="{row_style}border-bottom:1px solid #ddd;" data-state="{state}" data-agency="{agency}" data-ai="{str(ai_match).lower()}">'
                    f'<td {td_nowrap}>{i}</td>'
                    f'<td {td_nowrap}>{tender.get("tender_id", "")}</td>'
                    f'<td {td}>{badge}{tender.get("title", "").replace(chr(13), " ").replace(chr(10), " ").strip()}</td>'
                    f'<td {td_nowrap}>{tender.get("tender_category") or "N/A"}</td>'
                    f'<td {td_nowrap}>{tender.get("published_date", "")}</td>'
                    f'<td {td_nowrap}>{tender.get("bid_submission_start") or "—"}</td>'
                    f'<td {td_nowrap}>{tender.get("closing_date", "")}</td>'
                    f'<td {td_nowrap}>{action_cell}</td>'
                    f'<td {td_nowrap}>{tender.get("status", "")}</td>'
                    f'</tr>')
                table_rows.append(row_html)

            table_rows.append('</tbody>')
            html_table = '<table id="tenderTable" style="border-collapse:collapse;width:100%;">' + ''.join(table_rows) + '</table>'
            new_summary = f'<p style="background:#E8F5E9;padding:10px;border-left:4px solid #4CAF50;"><strong>🆕 {new_count} New Tender(s) Added Today</strong></p>' if new_count > 0 else ''

            # Build agency navbar buttons — scrollable row, TGTS+TSMSIDC highlighted
            FULL_IDS = {'TGTS', 'TSMSIDC'}
            agency_btn_parts = []
            for name in ordered_agencies:
                count = agency_counts.get(name, 0)
                is_full = name in FULL_IDS
                bg = '#1565C0' if is_full else '#455A64'
                label = name if len(name) <= 30 else name[:28] + '…'
                safe = name.replace("'", "\\'").replace('"', '&quot;')
                agency_btn_parts.append(
                    f'<button class="agency-tab" data-agency="{safe}" '
                    f'onclick="filterAgency(\'{safe}\')" '
                    f'style="background:{bg};color:white;padding:7px 14px;border:none;'
                    f'border-radius:4px;margin-right:4px;margin-bottom:4px;font-size:12px;'
                    f'cursor:pointer;white-space:nowrap;flex-shrink:0;">'
                    f'{label} ({count})</button>'
                )
            agency_buttons_html = ''.join(agency_btn_parts)

            # Action buttons + filter tabs
            buttons_html = f"""
            <div style="margin:20px 0;padding:20px;background:#f0f0f0;border-radius:5px;">
                <p style="margin:0 0 15px 0;font-weight:bold;font-size:14px;">📨 Send All {len(tenders)} Tenders:</p>
                <button onclick="sendEmail()" style="background:#007BFF;color:white;padding:12px 20px;border-radius:5px;border:none;margin-right:10px;font-size:14px;font-weight:bold;cursor:pointer;">📧 Send All to Email</button>
                <button onclick="sendWhatsApp()" style="background:#25D366;color:white;padding:12px 20px;border-radius:5px;border:none;margin-right:10px;font-size:14px;font-weight:bold;cursor:pointer;">💬 Send All to WhatsApp</button>
                <a href="http://localhost:5000/api/download-excel" style="background:#FF9800;color:white;padding:12px 20px;border-radius:5px;text-decoration:none;font-size:14px;font-weight:bold;display:inline-block;">📥 Download Excel</a>
                <p id="status" style="margin-top:10px;color:#666;font-size:12px;"></p>
            </div>

            <div style="margin:15px 0 5px 0;">
                <p style="margin:0 0 6px 0;font-size:12px;color:#666;">🏢 Filter by Department (Blue = All tenders, Grey = Steps AI only):</p>
                <div style="display:flex;flex-wrap:wrap;gap:4px;padding:10px;background:#f5f5f5;border-radius:6px;border:1px solid #ddd;">
                    <button class="agency-tab" data-agency="all" onclick="filterAgency('all')" style="background:#1B5E20;color:white;padding:7px 14px;border:none;border-radius:4px;margin-right:4px;margin-bottom:4px;font-size:12px;font-weight:bold;cursor:pointer;white-space:nowrap;flex-shrink:0;">All ({len(tenders)})</button>
                    {agency_buttons_html}
                </div>
            </div>
            <div style="margin:10px 0 15px 0;">
                <button class="filter-tab" data-filter="all" onclick="filterTenders('all')" style="background:#455A64;color:white;padding:7px 16px;border:2px solid transparent;border-radius:5px;margin-right:6px;font-size:13px;cursor:pointer;font-weight:bold;">All ({len(tenders)})</button>
                <button class="filter-tab" data-filter="new" onclick="filterTenders('new')" style="background:#388E3C;color:white;padding:7px 16px;border:2px solid transparent;border-radius:5px;margin-right:6px;font-size:13px;cursor:pointer;">🆕 New ({new_count})</button>
                <button class="filter-tab" data-filter="removed" onclick="filterTenders('removed')" style="background:#C62828;color:white;padding:7px 16px;border:2px solid transparent;border-radius:5px;margin-right:6px;font-size:13px;cursor:pointer;">🗑 Removed ({removed_count})</button>
                <button class="filter-tab" data-filter="ai" onclick="filterTenders('ai')" style="background:#6A1B9A;color:white;padding:7px 16px;border:2px solid transparent;border-radius:5px;font-size:13px;cursor:pointer;">🤖 Steps AI ({ai_count})</button>
            </div>

            <script>
            const tendersData = {tenders_json};
            const emailRecipients = ['shashank@nitiaide.com'];
            const whatsappNumbers = ['+917013536192'];

            async function sendEmail() {{
                const btn = event.target;
                btn.disabled = true;
                btn.textContent = '📧 Sending...';
                const status = document.getElementById('status');

                try {{
                    const response = await fetch('http://localhost:5000/api/send-email', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{
                            tenders: tendersData,
                            recipients: emailRecipients
                        }})
                    }});

                    const result = await response.json();
                    if (response.ok) {{
                        status.style.color = '#4CAF50';
                        status.textContent = '✓ Email sent successfully!';
                    }} else {{
                        status.style.color = '#d32f2f';
                        status.textContent = '✗ Error: ' + result.error;
                    }}
                }} catch (error) {{
                    status.style.color = '#d32f2f';
                    status.textContent = '✗ Server error. Make sure web server is running: python web_server.py';
                }} finally {{
                    btn.disabled = false;
                    btn.textContent = '📧 Send All to Email';
                }}
            }}

            async function sendWhatsApp() {{
                const btn = event.target;
                btn.disabled = true;
                btn.textContent = '💬 Sending...';
                const status = document.getElementById('status');

                try {{
                    const response = await fetch('http://localhost:5000/api/send-whatsapp', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{
                            tenders: tendersData,
                            phone_numbers: whatsappNumbers
                        }})
                    }});

                    const result = await response.json();
                    if (response.ok) {{
                        status.style.color = '#4CAF50';
                        status.textContent = '✓ WhatsApp sent successfully!';
                    }} else {{
                        status.style.color = '#d32f2f';
                        status.textContent = '✗ Error: ' + result.error;
                    }}
                }} catch (error) {{
                    status.style.color = '#d32f2f';
                    status.textContent = '✗ Server error. Make sure web server is running: python web_server.py';
                }} finally {{
                    btn.disabled = false;
                    btn.textContent = '💬 Send All to WhatsApp';
                }}
            }}

            let activeAgency = 'all';
            let activeFilter = 'all';

            function filterAgency(agency) {{
                activeAgency = agency;
                applyFilters();
                document.querySelectorAll('.agency-tab').forEach(btn => {{
                    const isActive = btn.getAttribute('data-agency') === agency;
                    btn.style.background = isActive ? '#1565C0' : '#1976D2';
                    btn.style.borderBottom = isActive ? '3px solid #FFF' : 'none';
                }});
            }}

            function filterTenders(type) {{
                activeFilter = type;
                applyFilters();
                document.querySelectorAll('.filter-tab').forEach(btn => {{
                    const isActive = btn.getAttribute('data-filter') === type;
                    btn.style.fontWeight = isActive ? 'bold' : 'normal';
                    btn.style.border = isActive ? '2px solid #fff' : '2px solid transparent';
                }});
            }}

            function applyFilters() {{
                const rows = document.querySelectorAll('tr[data-state]');
                rows.forEach(row => {{
                    const agency = row.getAttribute('data-agency');
                    const state = row.getAttribute('data-state');
                    const isAi = row.getAttribute('data-ai') === 'true';

                    const agencyMatch = activeAgency === 'all' || agency === activeAgency;
                    let stateMatch = true;
                    if (activeFilter === 'new') stateMatch = state === 'new';
                    else if (activeFilter === 'removed') stateMatch = state === 'removed';
                    else if (activeFilter === 'ai') stateMatch = isAi;

                    row.style.display = (agencyMatch && stateMatch) ? '' : 'none';
                }});
                // Update active agency button highlight
                document.querySelectorAll('.agency-tab').forEach(btn => {{
                    const isActive = btn.getAttribute('data-agency') === activeAgency;
                    btn.style.outline = isActive ? '2px solid #FFD700' : 'none';
                    btn.style.fontWeight = isActive ? 'bold' : 'normal';
                }});
            }}
            </script>
            """

            # Create full HTML document
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>TGTS Tender Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #fafafa; }}
                    h1 {{ color: #333; }}
                    table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                    th {{ background-color: #4CAF50; color: white; padding: 10px; text-align: left; }}
                    td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
                    tr:hover {{ background-color: #f5f5f5; }}
                    .metadata {{ color: #666; font-size: 0.9em; margin-top: 20px; }}
                    a {{ color: #0066cc; text-decoration: none; }}
                    a:hover {{ text-decoration: underline; }}
                </style>
            </head>
            <body>
                <h1>TGTS Tender Report</h1>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST</p>
                <p><strong>Total Tenders:</strong> {len(tenders)}</p>
                {new_summary}

                {buttons_html}

                {html_table}

                <div class="metadata">
                    <p><strong>🆕 Green rows:</strong> Tenders added today (IST).</p>
                    <p><strong>📧 Email button:</strong> Opens your email with all {len(tenders)} tenders listed.</p>
                    <p><strong>💬 WhatsApp button:</strong> Opens WhatsApp with top 10 tenders (WhatsApp has message size limits).</p>
                    <p><strong>Note:</strong> This is an automated report generated by TGTS Tender Scraper. Full Excel attachment is sent via daily email at 9 AM IST.</p>
                </div>
            </body>
            </html>
            """

            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"HTML report exported to {filepath} ({new_count} new tenders)")
            return filepath

        except Exception as e:
            logger.error(f"Error generating HTML report: {e}")
            return None

    def get_latest_files(self) -> Dict[str, Optional[str]]:
        """Get paths to the latest output files"""
        return {
            'csv': os.path.join(self.output_dir, 'tgts_tenders.csv') if os.path.exists(os.path.join(self.output_dir, 'tgts_tenders.csv')) else None,
            'excel': os.path.join(self.output_dir, 'tgts_tenders.xlsx') if os.path.exists(os.path.join(self.output_dir, 'tgts_tenders.xlsx')) else None,
            'html': os.path.join(self.output_dir, 'tgts_report.html') if os.path.exists(os.path.join(self.output_dir, 'tgts_report.html')) else None
        }
