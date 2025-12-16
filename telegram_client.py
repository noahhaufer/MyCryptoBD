"""
Telegram client setup and event handlers for the contact tracker.
"""

import logging
from datetime import datetime
from typing import Optional
from telethon import TelegramClient, events
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import User

from database import Database
from sheets_manager import SheetsManager
from ai_extractor import AIExtractor
from utils import (
    format_user_info,
    format_messages_for_context,
    format_contact_summary,
    format_stats_message,
    parse_command,
    validate_user_id
)

logger = logging.getLogger(__name__)


class ContactTrackerClient:
    """Telegram client wrapper for contact tracking functionality."""

    def __init__(
        self,
        api_id: int,
        api_hash: str,
        phone_number: str,
        session_name: str,
        database: Database,
        sheets_manager: SheetsManager,
        ai_extractor: AIExtractor,
        initial_messages_count: int = 5
    ):
        """
        Initialize the Telegram contact tracker client.

        Args:
            api_id: Telegram API ID
            api_hash: Telegram API hash
            phone_number: Phone number for authentication
            session_name: Name for the session file
            database: Database instance
            sheets_manager: SheetsManager instance
            ai_extractor: AIExtractor instance
            initial_messages_count: Number of initial messages to collect
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.session_name = session_name
        self.db = database
        self.sheets = sheets_manager
        self.ai = ai_extractor
        self.initial_messages_count = initial_messages_count

        # Create the Telethon client
        self.client = TelegramClient(session_name, api_id, api_hash)

        # Register event handlers
        self._register_handlers()

        logger.info("ContactTrackerClient initialized")

    def _register_handlers(self):
        """Register all event handlers."""
        # Handler for incoming private messages
        self.client.add_event_handler(
            self._handle_new_message,
            events.NewMessage(incoming=True, func=lambda e: e.is_private)
        )

        # Handler for bot commands
        self.client.add_event_handler(
            self._handle_command,
            events.NewMessage(outgoing=True, pattern=r'^/')
        )

        logger.info("Event handlers registered")

    async def start(self):
        """Start the Telegram client."""
        await self.client.start(phone=self.phone_number)
        logger.info("Telegram client started successfully")

        # Get bot info
        me = await self.client.get_me()
        logger.info(f"Logged in as: {me.first_name} (@{me.username})")

    async def disconnect(self):
        """Disconnect the Telegram client."""
        await self.client.disconnect()
        logger.info("Telegram client disconnected")

    async def run_until_disconnected(self):
        """Run the client until disconnected."""
        await self.client.run_until_disconnected()

    async def _handle_new_message(self, event):
        """
        Handle incoming private messages to detect new contacts.

        Args:
            event: Telethon NewMessage event
        """
        try:
            sender = await event.get_sender()

            # Skip if sender is not a user (e.g., a bot or channel)
            if not isinstance(sender, User):
                return

            user_id = sender.id

            # Check if this is a new contact
            if self.db.user_exists(user_id):
                # Update last contact time for existing contacts
                self.db.update_last_contact(user_id)
                logger.debug(f"Message from existing contact: {user_id}")
                return

            # New contact detected!
            logger.info(f"New contact detected: {user_id}")

            # Process the new contact
            await self._process_new_contact(sender, event.chat_id)

        except Exception as e:
            logger.error(f"Error handling new message: {e}", exc_info=True)

    async def _process_new_contact(self, user: User, chat_id: int):
        """
        Process a new contact: collect info, extract data, and save.

        Args:
            user: Telethon User object
            chat_id: Chat ID for retrieving messages
        """
        try:
            # Get basic user info
            user_info = format_user_info(user)

            # Get full user info including bio
            try:
                full_user = await self.client(GetFullUserRequest(user.id))
                bio = full_user.full_user.about if full_user.full_user.about else ''
                user_info['bio'] = bio
            except Exception as e:
                logger.warning(f"Could not fetch full user info: {e}")
                user_info['bio'] = ''

            # Get initial messages for context
            messages = await self.client.get_messages(
                chat_id,
                limit=self.initial_messages_count
            )

            message_texts = format_messages_for_context(messages)

            # Use AI to extract company and role
            logger.info("Extracting company info using AI...")
            extracted_info = self.ai.extract_company_info(
                bio=user_info['bio'],
                messages=message_texts
            )

            # Merge extracted info with user info
            user_info['company'] = extracted_info.get('company', 'Unknown')
            user_info['role'] = extracted_info.get('role', 'Unknown')
            user_info['topics'] = extracted_info.get('topics', [])

            # Save to database
            if self.db.add_user(user_info):
                logger.info(f"Saved contact to database: {user_info['name']}")

                # Log sync action
                self.db.log_sync(
                    'new_contact_added',
                    f"User ID: {user_info['user_id']}, Name: {user_info['name']}"
                )

                # Save to Google Sheets
                if self.sheets.append_contact(user_info):
                    logger.info(f"Saved contact to Google Sheets: {user_info['name']}")
                else:
                    logger.warning("Failed to save contact to Google Sheets")

                # Send confirmation to Saved Messages
                await self._send_confirmation(user_info)

            else:
                logger.error(f"Failed to save contact to database: {user_info['name']}")

        except Exception as e:
            logger.error(f"Error processing new contact: {e}", exc_info=True)

    async def _send_confirmation(self, contact_data: dict):
        """
        Send a confirmation message to Saved Messages.

        Args:
            contact_data: Dictionary with contact information
        """
        try:
            # Format the summary message
            summary = format_contact_summary(contact_data)

            # Send to Saved Messages (send message to self)
            await self.client.send_message('me', summary)

            logger.info("Confirmation sent to Saved Messages")

        except Exception as e:
            logger.error(f"Error sending confirmation: {e}")

    async def _handle_command(self, event):
        """
        Handle bot commands sent by the user.

        Args:
            event: Telethon NewMessage event
        """
        try:
            command, args = parse_command(event.message.text)

            # Route to appropriate handler
            if command == '/tag_event':
                await self._cmd_tag_event(event, args)
            elif command == '/edit':
                await self._cmd_edit(event, args)
            elif command == '/export':
                await self._cmd_export(event)
            elif command == '/stats':
                await self._cmd_stats(event)
            elif command == '/help':
                await self._cmd_help(event)
            else:
                # Unknown command, do nothing
                pass

        except Exception as e:
            logger.error(f"Error handling command: {e}", exc_info=True)

    async def _cmd_tag_event(self, event, args):
        """
        Handle /tag_event command to tag recent contacts.

        Usage: /tag_event <event_name> [hours]

        Args:
            event: Telethon event
            args: Command arguments
        """
        if len(args) < 1:
            await event.reply(
                "Usage: /tag_event <event_name> [hours]\n"
                "Example: /tag_event \"ETHDenver 2024\" 24\n\n"
                "Tags all contacts from the last N hours (default: 24)"
            )
            return

        event_name = args[0]
        hours = 24

        # Check if hours parameter is provided
        if len(args) >= 2:
            try:
                hours = int(args[1])
            except ValueError:
                await event.reply("Error: hours must be a number")
                return

        # Get recent contacts from database
        recent_contacts = self.db.get_recent_contacts(hours)

        if not recent_contacts:
            await event.reply(f"No contacts found in the last {hours} hours")
            return

        # Tag contacts in database
        count = self.db.tag_recent_contacts(hours, event_name)

        # Update Google Sheets
        user_ids = [c['user_id'] for c in recent_contacts]
        sheets_count = self.sheets.batch_tag_event(user_ids, event_name)

        await event.reply(
            f"✅ Tagged {count} contact(s) with event: {event_name}\n"
            f"📊 Updated {sheets_count} entries in Google Sheets"
        )

        logger.info(f"Tagged {count} contacts with event: {event_name}")

    async def _cmd_edit(self, event, args):
        """
        Handle /edit command to manually update contact details.

        Usage: /edit <user_id> <field> <value>

        Args:
            event: Telethon event
            args: Command arguments
        """
        if len(args) < 3:
            await event.reply(
                "Usage: /edit <user_id> <field> <value>\n\n"
                "Available fields: company, role, notes, event_tag\n\n"
                "Example: /edit 123456789 company \"Solana Foundation\""
            )
            return

        user_id = validate_user_id(args[0])
        if not user_id:
            await event.reply("Error: Invalid user_id")
            return

        field = args[1].lower()
        value = ' '.join(args[2:])  # Join remaining args as value

        # Check if user exists
        if not self.db.user_exists(user_id):
            await event.reply(f"Error: Contact with user_id {user_id} not found")
            return

        # Update in database
        if self.db.update_user(user_id, field, value):
            # Update in Google Sheets
            sheets_success = self.sheets.update_contact(user_id, field, value)

            if sheets_success:
                await event.reply(
                    f"✅ Updated {field} for user {user_id}\n"
                    f"New value: {value}"
                )
            else:
                await event.reply(
                    f"⚠️ Updated {field} in database but failed to update Google Sheets\n"
                    f"New value: {value}"
                )

            logger.info(f"Updated {field} for user {user_id}")
        else:
            await event.reply(f"Error: Failed to update {field}")

    async def _cmd_export(self, event):
        """
        Handle /export command to trigger immediate sync to Google Sheets.

        Args:
            event: Telethon event
        """
        await event.reply("🔄 Starting export to Google Sheets...")

        try:
            # Get all contacts from database
            all_contacts = self.db.get_all_users()

            # Sync to Google Sheets
            added = self.sheets.sync_from_database(all_contacts)

            # Log the sync
            self.db.log_sync(
                'manual_export',
                f"Synced {added} contacts to Google Sheets"
            )

            sheet_url = self.sheets.get_sheet_url()
            await event.reply(
                f"✅ Export complete!\n\n"
                f"📊 Added {added} new contact(s) to Google Sheets\n"
                f"🔗 View sheet: {sheet_url}"
            )

            logger.info(f"Manual export completed: {added} contacts synced")

        except Exception as e:
            logger.error(f"Error during export: {e}", exc_info=True)
            await event.reply(f"❌ Export failed: {str(e)}")

    async def _cmd_stats(self, event):
        """
        Handle /stats command to show contact statistics.

        Args:
            event: Telethon event
        """
        try:
            # Get statistics from database
            stats = self.db.get_stats()

            # Format and send the stats message
            stats_message = format_stats_message(stats)
            await event.reply(stats_message)

            logger.info("Stats command executed")

        except Exception as e:
            logger.error(f"Error getting stats: {e}", exc_info=True)
            await event.reply(f"Error: Failed to retrieve statistics")

    async def _cmd_help(self, event):
        """
        Handle /help command to show available commands.

        Args:
            event: Telethon event
        """
        help_text = """
🤖 Telegram Conference Contacts Tracker

Available Commands:

/tag_event <event_name> [hours]
  Tag contacts from the last N hours with an event name
  Example: /tag_event "ETHDenver 2024" 24

/edit <user_id> <field> <value>
  Update contact information
  Fields: company, role, notes, event_tag
  Example: /edit 123456789 company "Acme Corp"

/export
  Manually sync all contacts to Google Sheets

/stats
  Show summary statistics of tracked contacts

/help
  Show this help message

The bot automatically tracks new contacts when they message you for the first time.
"""
        await event.reply(help_text)
