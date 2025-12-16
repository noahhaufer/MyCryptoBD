"""
Google Sheets integration for exporting and syncing contact data.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import SpreadsheetNotFound, APIError

logger = logging.getLogger(__name__)


class SheetsManager:
    """Manage Google Sheets operations for contact tracking."""

    # Define the column headers for the spreadsheet
    HEADERS = [
        'User ID',
        'Timestamp',
        'Name',
        'Username',
        'Company',
        'Role',
        'Bio',
        'Initial Context',
        'Event Tag',
        'Last Contact',
        'Notes'
    ]

    def __init__(self, service_account_file: str, sheet_name: str):
        """
        Initialize Google Sheets manager.

        Args:
            service_account_file: Path to Google service account JSON file
            sheet_name: Name of the Google Sheet to use
        """
        self.service_account_file = service_account_file
        self.sheet_name = sheet_name
        self.client = None
        self.spreadsheet = None
        self.worksheet = None

        self._authenticate()
        logger.info(f"Sheets Manager initialized for sheet: {sheet_name}")

    def _authenticate(self):
        """Authenticate with Google Sheets API using service account."""
        try:
            # Define the required scopes
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]

            # Load credentials from service account file
            credentials = Credentials.from_service_account_file(
                self.service_account_file,
                scopes=scopes
            )

            # Authorize the client
            self.client = gspread.authorize(credentials)
            logger.info("Successfully authenticated with Google Sheets API")

            # Open or create the spreadsheet
            self._open_or_create_spreadsheet()

        except FileNotFoundError:
            logger.error(f"Service account file not found: {self.service_account_file}")
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise

    def _open_or_create_spreadsheet(self):
        """Open existing spreadsheet or create a new one."""
        try:
            # Try to open existing spreadsheet
            self.spreadsheet = self.client.open(self.sheet_name)
            self.worksheet = self.spreadsheet.sheet1
            logger.info(f"Opened existing spreadsheet: {self.sheet_name}")

            # Check if headers exist, if not, set them up
            existing_headers = self.worksheet.row_values(1)
            if not existing_headers or existing_headers != self.HEADERS:
                self._setup_headers()

        except SpreadsheetNotFound:
            logger.info(f"Spreadsheet not found, creating new one: {self.sheet_name}")
            self._create_spreadsheet()

    def _create_spreadsheet(self):
        """Create a new spreadsheet with proper formatting."""
        try:
            # Create new spreadsheet
            self.spreadsheet = self.client.create(self.sheet_name)
            self.worksheet = self.spreadsheet.sheet1

            # Setup headers and formatting
            self._setup_headers()
            self._apply_formatting()

            logger.info(f"Created new spreadsheet: {self.sheet_name}")
            logger.info(f"Share this sheet with others or view it at: {self.spreadsheet.url}")

        except Exception as e:
            logger.error(f"Error creating spreadsheet: {e}")
            raise

    def _setup_headers(self):
        """Set up column headers in the spreadsheet."""
        try:
            # Clear the first row
            self.worksheet.delete_rows(1)
            self.worksheet.insert_row(self.HEADERS, 1)

            # Format headers: bold and freeze
            self.worksheet.format('1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
            })

            # Freeze the header row
            self.worksheet.freeze(rows=1)

            logger.info("Headers set up successfully")

        except Exception as e:
            logger.error(f"Error setting up headers: {e}")

    def _apply_formatting(self):
        """Apply additional formatting to the spreadsheet."""
        try:
            # Auto-resize columns
            self.worksheet.columns_auto_resize(0, len(self.HEADERS))

            # Set column widths for better readability
            column_widths = [
                (0, 100),   # User ID
                (1, 180),   # Timestamp
                (2, 150),   # Name
                (3, 130),   # Username
                (4, 180),   # Company
                (5, 150),   # Role
                (6, 250),   # Bio
                (7, 300),   # Initial Context
                (8, 120),   # Event Tag
                (9, 180),   # Last Contact
                (10, 250)   # Notes
            ]

            for col_idx, width in column_widths:
                self.worksheet.set_column_width(col_idx + 1, width)

            logger.info("Formatting applied successfully")

        except Exception as e:
            logger.error(f"Error applying formatting: {e}")

    def append_contact(self, contact_data: Dict) -> bool:
        """
        Append a new contact to the spreadsheet.

        Args:
            contact_data: Dictionary containing contact information

        Returns:
            True if successful, False otherwise
        """
        try:
            # Format topics list as comma-separated string
            topics = contact_data.get('topics', [])
            initial_context = ', '.join(topics) if topics else ''

            # Format datetime fields
            timestamp = contact_data.get('first_seen', datetime.now())
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')

            last_contact = contact_data.get('last_contact', datetime.now())
            if isinstance(last_contact, datetime):
                last_contact = last_contact.strftime('%Y-%m-%d %H:%M:%S')

            # Prepare row data matching HEADERS order
            row = [
                str(contact_data.get('user_id', '')),
                timestamp,
                contact_data.get('name', ''),
                contact_data.get('username', ''),
                contact_data.get('company', 'Unknown'),
                contact_data.get('role', 'Unknown'),
                contact_data.get('bio', ''),
                initial_context,
                contact_data.get('event_tag', ''),
                last_contact,
                contact_data.get('notes', '')
            ]

            # Append the row
            self.worksheet.append_row(row, value_input_option='USER_ENTERED')
            logger.info(f"Appended contact: {contact_data.get('name', 'Unknown')} (ID: {contact_data.get('user_id')})")
            return True

        except APIError as e:
            logger.error(f"Google Sheets API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error appending contact: {e}")
            return False

    def get_contact_by_user_id(self, user_id: int) -> Optional[Dict]:
        """
        Find a contact in the spreadsheet by user ID.

        Args:
            user_id: Telegram user ID

        Returns:
            Dictionary with contact data or None if not found
        """
        try:
            # Find all cells with the user ID in the first column
            cell = self.worksheet.find(str(user_id), in_column=1)

            if cell:
                # Get the entire row
                row_values = self.worksheet.row_values(cell.row)

                # Map values to dictionary using headers
                contact_data = {}
                for i, header in enumerate(self.HEADERS):
                    if i < len(row_values):
                        contact_data[header.lower().replace(' ', '_')] = row_values[i]

                return contact_data

            return None

        except Exception as e:
            logger.error(f"Error finding contact: {e}")
            return None

    def update_contact(self, user_id: int, field: str, value: str) -> bool:
        """
        Update a specific field for a contact.

        Args:
            user_id: Telegram user ID
            field: Field name to update (must match header)
            value: New value

        Returns:
            True if successful, False otherwise
        """
        try:
            # Find the contact row
            cell = self.worksheet.find(str(user_id), in_column=1)

            if not cell:
                logger.warning(f"Contact with user_id {user_id} not found")
                return False

            # Map field name to column
            field_map = {
                'name': 'Name',
                'username': 'Username',
                'company': 'Company',
                'role': 'Role',
                'bio': 'Bio',
                'event_tag': 'Event Tag',
                'notes': 'Notes'
            }

            header_name = field_map.get(field)
            if not header_name:
                logger.error(f"Invalid field name: {field}")
                return False

            # Find the column index
            try:
                col_idx = self.HEADERS.index(header_name) + 1
            except ValueError:
                logger.error(f"Header not found: {header_name}")
                return False

            # Update the cell
            self.worksheet.update_cell(cell.row, col_idx, value)
            logger.info(f"Updated {field} for user {user_id} in Google Sheets")
            return True

        except Exception as e:
            logger.error(f"Error updating contact: {e}")
            return False

    def batch_tag_event(self, user_ids: List[int], event_name: str) -> int:
        """
        Tag multiple contacts with an event name.

        Args:
            user_ids: List of Telegram user IDs
            event_name: Event name to tag contacts with

        Returns:
            Number of contacts successfully tagged
        """
        count = 0
        for user_id in user_ids:
            if self.update_contact(user_id, 'event_tag', event_name):
                count += 1

        logger.info(f"Tagged {count}/{len(user_ids)} contacts with event: {event_name}")
        return count

    def get_all_contacts(self) -> List[Dict]:
        """
        Get all contacts from the spreadsheet.

        Returns:
            List of contact dictionaries
        """
        try:
            # Get all rows except header
            all_values = self.worksheet.get_all_values()[1:]

            contacts = []
            for row in all_values:
                contact = {}
                for i, header in enumerate(self.HEADERS):
                    if i < len(row):
                        contact[header.lower().replace(' ', '_')] = row[i]
                contacts.append(contact)

            return contacts

        except Exception as e:
            logger.error(f"Error getting all contacts: {e}")
            return []

    def sync_from_database(self, contacts: List[Dict]) -> int:
        """
        Sync multiple contacts from database to Google Sheets.
        Only adds contacts that don't already exist in the sheet.

        Args:
            contacts: List of contact dictionaries from database

        Returns:
            Number of contacts added
        """
        try:
            # Get existing user IDs in the sheet
            existing_ids = set()
            user_id_col = self.worksheet.col_values(1)[1:]  # Skip header
            existing_ids = set(user_id_col)

            # Add only new contacts
            added = 0
            for contact in contacts:
                user_id = str(contact.get('user_id', ''))
                if user_id not in existing_ids:
                    if self.append_contact(contact):
                        added += 1
                        existing_ids.add(user_id)

            logger.info(f"Synced {added} new contacts to Google Sheets")
            return added

        except Exception as e:
            logger.error(f"Error syncing from database: {e}")
            return 0

    def get_sheet_url(self) -> str:
        """
        Get the URL of the spreadsheet.

        Returns:
            URL string
        """
        if self.spreadsheet:
            return self.spreadsheet.url
        return ""
