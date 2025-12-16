"""
SQLite database management for tracking users and sync operations.
"""

import sqlite3
import logging
from datetime import datetime
from typing import Optional, Dict, List
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager for local caching and tracking."""

    def __init__(self, db_path: str):
        """
        Initialize database connection and create tables if needed.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._create_tables()
        logger.info(f"Database initialized at {db_path}")

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _create_tables(self):
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Tracked users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tracked_users (
                    user_id INTEGER PRIMARY KEY,
                    first_seen TIMESTAMP NOT NULL,
                    name TEXT,
                    username TEXT,
                    company TEXT,
                    role TEXT,
                    bio TEXT,
                    event_tag TEXT,
                    last_contact TIMESTAMP,
                    notes TEXT
                )
            ''')

            # Sync log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT
                )
            ''')

            # Create indexes for better query performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_first_seen
                ON tracked_users(first_seen)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_event_tag
                ON tracked_users(event_tag)
            ''')

            logger.info("Database tables created/verified successfully")

    def user_exists(self, user_id: int) -> bool:
        """
        Check if a user is already tracked in the database.

        Args:
            user_id: Telegram user ID

        Returns:
            True if user exists, False otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT 1 FROM tracked_users WHERE user_id = ?',
                (user_id,)
            )
            result = cursor.fetchone()
            return result is not None

    def add_user(self, user_data: Dict) -> bool:
        """
        Add a new user to the database.

        Args:
            user_data: Dictionary containing user information
                Required keys: user_id, first_seen, name
                Optional keys: username, company, role, bio, event_tag, notes

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO tracked_users
                    (user_id, first_seen, name, username, company, role, bio, event_tag, last_contact, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_data['user_id'],
                    user_data.get('first_seen', datetime.now()),
                    user_data.get('name'),
                    user_data.get('username'),
                    user_data.get('company'),
                    user_data.get('role'),
                    user_data.get('bio'),
                    user_data.get('event_tag'),
                    user_data.get('last_contact', datetime.now()),
                    user_data.get('notes')
                ))
                logger.info(f"Added user {user_data['user_id']} to database")
                return True
        except Exception as e:
            logger.error(f"Error adding user to database: {e}")
            return False

    def get_user(self, user_id: int) -> Optional[Dict]:
        """
        Retrieve user data from the database.

        Args:
            user_id: Telegram user ID

        Returns:
            Dictionary with user data or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM tracked_users WHERE user_id = ?',
                (user_id,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def update_user(self, user_id: int, field: str, value: str) -> bool:
        """
        Update a specific field for a user.

        Args:
            user_id: Telegram user ID
            field: Field name to update
            value: New value for the field

        Returns:
            True if successful, False otherwise
        """
        # Validate field name to prevent SQL injection
        valid_fields = ['name', 'username', 'company', 'role', 'bio', 'event_tag', 'notes']
        if field not in valid_fields:
            logger.error(f"Invalid field name: {field}")
            return False

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = f'UPDATE tracked_users SET {field} = ? WHERE user_id = ?'
                cursor.execute(query, (value, user_id))

                if cursor.rowcount == 0:
                    logger.warning(f"No user found with ID {user_id}")
                    return False

                logger.info(f"Updated {field} for user {user_id}")
                return True
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False

    def update_last_contact(self, user_id: int) -> bool:
        """
        Update the last_contact timestamp for a user.

        Args:
            user_id: Telegram user ID

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE tracked_users SET last_contact = ? WHERE user_id = ?',
                    (datetime.now(), user_id)
                )
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating last contact: {e}")
            return False

    def get_recent_contacts(self, hours: int = 24) -> List[Dict]:
        """
        Get contacts added within the specified number of hours.

        Args:
            hours: Number of hours to look back

        Returns:
            List of user dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM tracked_users
                WHERE first_seen >= datetime('now', '-' || ? || ' hours')
                ORDER BY first_seen DESC
            ''', (hours,))

            return [dict(row) for row in cursor.fetchall()]

    def tag_recent_contacts(self, hours: int, event_name: str) -> int:
        """
        Tag all contacts from the last N hours with an event name.

        Args:
            hours: Number of hours to look back
            event_name: Event name to tag contacts with

        Returns:
            Number of contacts tagged
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE tracked_users
                    SET event_tag = ?
                    WHERE first_seen >= datetime('now', '-' || ? || ' hours')
                    AND (event_tag IS NULL OR event_tag = '')
                ''', (event_name, hours))

                count = cursor.rowcount
                logger.info(f"Tagged {count} contacts with event: {event_name}")
                return count
        except Exception as e:
            logger.error(f"Error tagging contacts: {e}")
            return 0

    def get_all_users(self) -> List[Dict]:
        """
        Get all tracked users from the database.

        Returns:
            List of user dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tracked_users ORDER BY first_seen DESC')
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict:
        """
        Get summary statistics about tracked contacts.

        Returns:
            Dictionary with various statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total contacts
            cursor.execute('SELECT COUNT(*) as total FROM tracked_users')
            total = cursor.fetchone()['total']

            # Contacts by event
            cursor.execute('''
                SELECT event_tag, COUNT(*) as count
                FROM tracked_users
                WHERE event_tag IS NOT NULL AND event_tag != ''
                GROUP BY event_tag
                ORDER BY count DESC
            ''')
            by_event = [dict(row) for row in cursor.fetchall()]

            # Contacts with companies identified
            cursor.execute('''
                SELECT COUNT(*) as count
                FROM tracked_users
                WHERE company IS NOT NULL AND company != '' AND company != 'Unknown'
            ''')
            with_company = cursor.fetchone()['count']

            # Recent contacts (last 7 days)
            cursor.execute('''
                SELECT COUNT(*) as count
                FROM tracked_users
                WHERE first_seen >= datetime('now', '-7 days')
            ''')
            recent = cursor.fetchone()['count']

            return {
                'total_contacts': total,
                'contacts_with_company': with_company,
                'recent_contacts_7d': recent,
                'contacts_by_event': by_event
            }

    def log_sync(self, action: str, details: str = None):
        """
        Log a sync operation to the sync_log table.

        Args:
            action: Description of the sync action
            details: Additional details about the sync
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO sync_log (timestamp, action, details)
                    VALUES (?, ?, ?)
                ''', (datetime.now(), action, details))
                logger.debug(f"Logged sync action: {action}")
        except Exception as e:
            logger.error(f"Error logging sync: {e}")
