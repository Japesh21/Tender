"""
Database manager for TGTS Tender Scraper
Handles SQLite operations for tender storage and change tracking
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TenderDatabase:
    """Manages SQLite database operations for tenders"""

    SCHEMA_VERSION = 1

    def __init__(self, db_path: str):
        """Initialize database connection"""
        self.db_path = db_path
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize database schema"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Create tenders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tenders (
                    tender_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    department TEXT,
                    published_date TEXT,
                    closing_date TEXT,
                    emd REAL,
                    tender_value REAL,
                    document_link TEXT,
                    pdf_link TEXT,
                    corrigendum_link TEXT,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Migrate existing DB: add corrigendum_link if not present
            try:
                cursor.execute('ALTER TABLE tenders ADD COLUMN corrigendum_link TEXT')
                conn.commit()
            except sqlite3.OperationalError:
                pass  # Column already exists

            # Create change log table for tracking tender updates
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tender_changelog (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tender_id TEXT NOT NULL,
                    change_type TEXT,
                    field_name TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(tender_id) REFERENCES tenders(tender_id)
                )
            ''')

            # Create indexes for faster queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_department ON tenders(department)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON tenders(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_closing_date ON tenders(closing_date)')

            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise

        finally:
            conn.close()

    def insert_tender(self, tender: Dict) -> bool:
        """
        Insert a new tender into database
        Returns True if successful, False if tender already exists
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Check if tender already exists
            cursor.execute('SELECT tender_id FROM tenders WHERE tender_id = ?', (tender['tender_id'],))
            if cursor.fetchone():
                logger.warning(f"Tender {tender['tender_id']} already exists")
                return False

            cursor.execute('''
                INSERT INTO tenders (
                    tender_id, title, department, published_date, closing_date,
                    emd, tender_value, document_link, pdf_link, corrigendum_link, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tender.get('tender_id'),
                tender.get('title'),
                tender.get('department'),
                tender.get('published_date'),
                tender.get('closing_date'),
                tender.get('emd'),
                tender.get('tender_value'),
                tender.get('document_link'),
                tender.get('pdf_link'),
                tender.get('corrigendum_link'),
                tender.get('status')
            ))

            conn.commit()
            logger.info(f"Inserted tender: {tender['tender_id']}")
            return True

        except sqlite3.Error as e:
            logger.error(f"Error inserting tender: {e}")
            return False

        finally:
            conn.close()

    def update_tender(self, tender_id: str, updates: Dict) -> bool:
        """Update an existing tender and log changes"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Get current tender data
            cursor.execute('SELECT * FROM tenders WHERE tender_id = ?', (tender_id,))
            current = cursor.fetchone()

            if not current:
                logger.warning(f"Tender {tender_id} not found for update")
                return False

            # Log changes
            for key, new_value in updates.items():
                old_value = current[key] if key in current.keys() else None
                if old_value != new_value:
                    cursor.execute('''
                        INSERT INTO tender_changelog (tender_id, change_type, field_name, old_value, new_value)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (tender_id, 'UPDATE', key, str(old_value), str(new_value)))

            # Update tender
            set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
            set_clause += ', updated_at = CURRENT_TIMESTAMP'
            values = list(updates.values()) + [tender_id]

            cursor.execute(f'UPDATE tenders SET {set_clause} WHERE tender_id = ?', values)
            conn.commit()
            logger.info(f"Updated tender: {tender_id}")
            return True

        except sqlite3.Error as e:
            logger.error(f"Error updating tender: {e}")
            return False

        finally:
            conn.close()

    def get_tender(self, tender_id: str) -> Optional[Dict]:
        """Fetch a single tender by ID"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tenders WHERE tender_id = ?', (tender_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

        except sqlite3.Error as e:
            logger.error(f"Error fetching tender: {e}")
            return None

        finally:
            conn.close()

    def get_all_tenders(self, department: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
        """Fetch all tenders with optional filters"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            query = 'SELECT * FROM tenders WHERE 1=1'
            params = []

            if department:
                query += ' AND department = ?'
                params.append(department)

            if status:
                query += ' AND status = ?'
                params.append(status)

            query += ' ORDER BY closing_date ASC'

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Error fetching tenders: {e}")
            return []

        finally:
            conn.close()

    def get_new_tenders_since(self, days: int = 1) -> List[Dict]:
        """Fetch tenders added in the last N days"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM tenders
                WHERE created_at >= datetime('now', ? || ' days')
                ORDER BY created_at DESC
            ''', (f'-{days}',))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Error fetching new tenders: {e}")
            return []

        finally:
            conn.close()

    def get_closing_soon_tenders(self, days: int = 7) -> List[Dict]:
        """Fetch tenders closing within N days"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM tenders
                WHERE status IN ('Active', 'Open')
                AND closing_date IS NOT NULL
                AND julianday(closing_date) - julianday('now') <= ?
                AND julianday(closing_date) - julianday('now') > 0
                ORDER BY closing_date ASC
            ''', (days,))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Error fetching closing tenders: {e}")
            return []

        finally:
            conn.close()

    def get_tender_count(self, department: Optional[str] = None) -> int:
        """Get total count of tenders"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            query = 'SELECT COUNT(*) as count FROM tenders WHERE 1=1'
            params = []

            if department:
                query += ' AND department = ?'
                params.append(department)

            cursor.execute(query, params)
            result = cursor.fetchone()
            return result['count'] if result else 0

        except sqlite3.Error as e:
            logger.error(f"Error counting tenders: {e}")
            return 0

        finally:
            conn.close()

    def mark_tender_seen(self, tender_id: str) -> bool:
        """Update last_seen timestamp for a tender"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('UPDATE tenders SET last_seen = CURRENT_TIMESTAMP WHERE tender_id = ?', (tender_id,))
            conn.commit()
            return True

        except sqlite3.Error as e:
            logger.error(f"Error marking tender as seen: {e}")
            return False

        finally:
            conn.close()

    def delete_tender(self, tender_id: str) -> bool:
        """Delete a tender (soft delete recommended - use status instead)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('DELETE FROM tenders WHERE tender_id = ?', (tender_id,))
            conn.commit()
            logger.info(f"Deleted tender: {tender_id}")
            return True

        except sqlite3.Error as e:
            logger.error(f"Error deleting tender: {e}")
            return False

        finally:
            conn.close()

    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            stats = {}

            # Total tenders
            cursor.execute('SELECT COUNT(*) as count FROM tenders')
            stats['total_tenders'] = cursor.fetchone()['count']

            # Tenders by status
            cursor.execute('SELECT status, COUNT(*) as count FROM tenders GROUP BY status')
            stats['by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}

            # Tenders by department
            cursor.execute('SELECT department, COUNT(*) as count FROM tenders GROUP BY department')
            stats['by_department'] = {row['department']: row['count'] for row in cursor.fetchall()}

            # Recent changes
            cursor.execute('SELECT COUNT(*) as count FROM tender_changelog WHERE changed_at >= datetime("now", "-1 day")')
            stats['changes_last_24h'] = cursor.fetchone()['count']

            return stats

        except sqlite3.Error as e:
            logger.error(f"Error getting database stats: {e}")
            return {}

        finally:
            conn.close()
