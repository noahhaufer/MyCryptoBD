"""
Main entry point for the Telegram Conference Contacts Tracker.

This application automatically tracks new Telegram connections made at conferences
and exports them to Google Sheets with AI-powered company extraction.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

from config import config
from database import Database
from sheets_manager import SheetsManager
from ai_extractor import AIExtractor
from telegram_client import ContactTrackerClient
from utils import setup_logging

logger = logging.getLogger(__name__)


class ContactTrackerApp:
    """Main application class for the contact tracker."""

    def __init__(self):
        """Initialize the application."""
        self.db = None
        self.sheets = None
        self.ai = None
        self.telegram_client = None
        self.shutdown_event = asyncio.Event()

    def setup(self):
        """Set up all components of the application."""
        try:
            # Setup logging
            setup_logging(config.LOG_LEVEL)
            logger.info("Starting Telegram Conference Contacts Tracker...")

            # Initialize database
            logger.info(f"Initializing database at {config.DATABASE_PATH}")
            self.db = Database(config.DATABASE_PATH)

            # Initialize Google Sheets manager
            logger.info("Initializing Google Sheets manager")
            self.sheets = SheetsManager(
                config.GOOGLE_SERVICE_ACCOUNT_FILE,
                config.GOOGLE_SHEET_NAME
            )

            # Initialize AI extractor
            logger.info("Initializing AI extractor")
            self.ai = AIExtractor(config.OPENAI_API_KEY)

            # Initialize Telegram client
            logger.info("Initializing Telegram client")
            self.telegram_client = ContactTrackerClient(
                api_id=config.TELEGRAM_API_ID,
                api_hash=config.TELEGRAM_API_HASH,
                phone_number=config.TELEGRAM_PHONE_NUMBER,
                session_name=config.SESSION_NAME,
                database=self.db,
                sheets_manager=self.sheets,
                ai_extractor=self.ai,
                initial_messages_count=config.INITIAL_MESSAGES_COUNT
            )

            logger.info("All components initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Error during setup: {e}", exc_info=True)
            return False

    async def start(self):
        """Start the application."""
        try:
            # Start the Telegram client
            await self.telegram_client.start()

            # Log sheet URL
            sheet_url = self.sheets.get_sheet_url()
            logger.info(f"Google Sheet URL: {sheet_url}")

            logger.info("=" * 60)
            logger.info("🚀 Bot started successfully!")
            logger.info("=" * 60)
            logger.info("Monitoring for new contacts...")
            logger.info("Send messages to yourself with /help to see available commands")
            logger.info("Press Ctrl+C to stop")
            logger.info("=" * 60)

            # Wait for shutdown signal
            await self.shutdown_event.wait()

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Error during runtime: {e}", exc_info=True)
        finally:
            await self.stop()

    async def stop(self):
        """Stop the application gracefully."""
        logger.info("Shutting down...")

        if self.telegram_client:
            try:
                await self.telegram_client.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting Telegram client: {e}")

        logger.info("Shutdown complete")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}")
        self.shutdown_event.set()


def main():
    """Main function to run the application."""
    try:
        # Create and setup the application
        app = ContactTrackerApp()

        if not app.setup():
            logger.error("Failed to setup application. Exiting.")
            sys.exit(1)

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, lambda s, f: app.shutdown_event.set())
        signal.signal(signal.SIGTERM, lambda s, f: app.shutdown_event.set())

        # Run the application
        asyncio.run(app.start())

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
