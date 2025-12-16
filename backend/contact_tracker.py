"""
Contact tracking system using Telethon for multi-user monitoring.

This module manages Telethon user clients to monitor new contacts
and extract information from conversations.
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from sqlalchemy.orm import Session
from openai import OpenAI

from backend.database import SessionLocal
from backend.models import User, Contact, Message as DBMessage
from backend.auth import encrypt_session, decrypt_session

logger = logging.getLogger(__name__)

# OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class UserContactTracker:
    """Tracks contacts for a single user."""

    def __init__(self, user_id: int, api_id: int, api_hash: str, session_string: str):
        """Initialize tracker for a user."""
        self.user_id = user_id
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_string = session_string
        self.client: Optional[TelegramClient] = None
        self.is_running = False

    async def start(self):
        """Start monitoring for this user."""
        try:
            # Create Telethon client with stored session
            self.client = TelegramClient(
                StringSession(self.session_string),
                self.api_id,
                self.api_hash
            )

            await self.client.connect()

            if not await self.client.is_user_authorized():
                logger.error(f"User {self.user_id} session is not authorized")
                return False

            # Register event handlers
            self.client.add_event_handler(
                self._on_new_message,
                events.NewMessage(incoming=True, outgoing=False)
            )

            self.is_running = True
            logger.info(f"Started monitoring for user {self.user_id}")

            # Keep the client running
            await self.client.run_until_disconnected()

            return True

        except Exception as e:
            logger.error(f"Error starting tracker for user {self.user_id}: {e}")
            return False

    async def stop(self):
        """Stop monitoring for this user."""
        self.is_running = False
        if self.client:
            await self.client.disconnect()
            logger.info(f"Stopped monitoring for user {self.user_id}")

    async def _on_new_message(self, event):
        """Handle new incoming messages."""
        try:
            sender = await event.get_sender()

            # Skip if not a user (e.g., channels, bots)
            if not sender or not hasattr(sender, 'id'):
                return

            sender_id = sender.id

            # Check if this is a new contact
            db: Session = SessionLocal()

            try:
                # Get user from database
                user = db.query(User).filter(User.id == self.user_id).first()
                if not user:
                    logger.error(f"User {self.user_id} not found in database")
                    return

                # Check if contact exists
                contact = db.query(Contact).filter(
                    Contact.user_id == self.user_id,
                    Contact.telegram_id == sender_id
                ).first()

                if not contact:
                    # New contact! Create it
                    contact = Contact(
                        user_id=self.user_id,
                        telegram_id=sender_id,
                        username=sender.username,
                        first_name=sender.first_name,
                        last_name=sender.last_name,
                        phone_number=sender.phone if hasattr(sender, 'phone') else None,
                        first_message_date=datetime.utcnow()
                    )
                    db.add(contact)
                    db.commit()
                    db.refresh(contact)

                    logger.info(f"New contact detected for user {self.user_id}: {sender_id}")

                    # Fetch initial messages for AI extraction
                    await self._fetch_and_analyze_messages(contact, user.initial_messages_count)

                # Save the message
                message = DBMessage(
                    contact_id=contact.id,
                    telegram_message_id=event.message.id,
                    sender_id=sender_id,
                    text=event.message.text or "",
                    sent_at=event.message.date,
                    is_outgoing=False
                )
                db.add(message)

                # Update last interaction
                contact.last_interaction_date = datetime.utcnow()

                db.commit()

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error handling new message for user {self.user_id}: {e}")

    async def _fetch_and_analyze_messages(self, contact: Contact, message_count: int = 5):
        """Fetch initial messages and extract company information with AI."""
        try:
            # Fetch messages from this contact
            messages = []
            async for message in self.client.iter_messages(contact.telegram_id, limit=message_count):
                if message.text:
                    messages.append({
                        'text': message.text,
                        'date': message.date,
                        'is_outgoing': message.out
                    })

            if not messages:
                logger.info(f"No messages found for contact {contact.telegram_id}")
                return

            # Extract company with AI
            company = await self._extract_company_with_ai(messages)

            if company:
                # Update contact with company info
                db: Session = SessionLocal()
                try:
                    db_contact = db.query(Contact).filter(Contact.id == contact.id).first()
                    if db_contact:
                        db_contact.company = company
                        db.commit()
                        logger.info(f"Extracted company for contact {contact.id}: {company}")
                finally:
                    db.close()

        except Exception as e:
            logger.error(f"Error analyzing messages for contact {contact.id}: {e}")

    async def _extract_company_with_ai(self, messages: list) -> Optional[str]:
        """Use OpenAI to extract company name from messages."""
        try:
            # Format messages for AI
            conversation = "\n".join([
                f"{'Me' if msg['is_outgoing'] else 'Them'}: {msg['text']}"
                for msg in messages
            ])

            # Call OpenAI
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Extract the company name from the conversation. "
                                   "Return only the company name, nothing else. "
                                   "If no company is mentioned, return 'Unknown'."
                    },
                    {
                        "role": "user",
                        "content": f"Conversation:\n{conversation}"
                    }
                ],
                temperature=0.3,
                max_tokens=50
            )

            company = response.choices[0].message.content.strip()

            if company and company.lower() != "unknown":
                return company

            return None

        except Exception as e:
            logger.error(f"Error extracting company with AI: {e}")
            return None


class ContactTrackerManager:
    """Manages contact trackers for all users."""

    def __init__(self):
        """Initialize the manager."""
        self.trackers: Dict[int, UserContactTracker] = {}
        self.api_id = int(os.getenv("TELEGRAM_API_ID"))
        self.api_hash = os.getenv("TELEGRAM_API_HASH")

    async def start_tracking_for_user(self, user_id: int, session_string: str) -> bool:
        """Start tracking contacts for a user."""
        try:
            if user_id in self.trackers:
                logger.info(f"Tracker already running for user {user_id}")
                return True

            # Decrypt session
            decrypted_session = decrypt_session(session_string)

            # Create tracker
            tracker = UserContactTracker(
                user_id=user_id,
                api_id=self.api_id,
                api_hash=self.api_hash,
                session_string=decrypted_session
            )

            # Start tracking in background
            asyncio.create_task(tracker.start())

            self.trackers[user_id] = tracker

            return True

        except Exception as e:
            logger.error(f"Error starting tracking for user {user_id}: {e}")
            return False

    async def stop_tracking_for_user(self, user_id: int):
        """Stop tracking contacts for a user."""
        if user_id in self.trackers:
            tracker = self.trackers[user_id]
            await tracker.stop()
            del self.trackers[user_id]

    async def start_all_active_users(self):
        """Start tracking for all active users in database."""
        db: Session = SessionLocal()

        try:
            # Get all users with active sessions
            users = db.query(User).filter(
                User.telegram_session_string.isnot(None)
            ).all()

            logger.info(f"Starting trackers for {len(users)} users")

            for user in users:
                await self.start_tracking_for_user(
                    user.id,
                    user.telegram_session_string
                )

        finally:
            db.close()

    async def stop_all(self):
        """Stop all trackers."""
        for user_id in list(self.trackers.keys()):
            await self.stop_tracking_for_user(user_id)


# Global manager instance
tracker_manager = ContactTrackerManager()
