"""
Configuration management for Telegram Contacts Tracker.
Loads and validates environment variables from .env file.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class that loads and validates all required settings."""

    def __init__(self):
        """Initialize configuration and validate required variables."""
        self._load_telegram_config()
        self._load_openai_config()
        self._load_google_config()
        self._load_optional_config()
        self._validate_config()

    def _load_telegram_config(self):
        """Load Telegram API configuration."""
        self.TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
        self.TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
        self.TELEGRAM_PHONE_NUMBER = os.getenv('TELEGRAM_PHONE_NUMBER')

        # Convert API ID to integer if present
        if self.TELEGRAM_API_ID:
            try:
                self.TELEGRAM_API_ID = int(self.TELEGRAM_API_ID)
            except ValueError:
                raise ValueError("TELEGRAM_API_ID must be a valid integer")

    def _load_openai_config(self):
        """Load OpenAI API configuration."""
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    def _load_google_config(self):
        """Load Google Sheets configuration."""
        self.GOOGLE_SHEET_NAME = os.getenv('GOOGLE_SHEET_NAME', 'Conference Contacts')
        self.GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')

        # Validate that the service account file exists
        if self.GOOGLE_SERVICE_ACCOUNT_FILE:
            service_account_path = Path(self.GOOGLE_SERVICE_ACCOUNT_FILE)
            if not service_account_path.exists():
                raise FileNotFoundError(
                    f"Google service account file not found: {self.GOOGLE_SERVICE_ACCOUNT_FILE}"
                )

    def _load_optional_config(self):
        """Load optional configuration with defaults."""
        self.DATABASE_PATH = os.getenv('DATABASE_PATH', './contacts.db')
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.LOG_LEVEL not in valid_log_levels:
            raise ValueError(
                f"Invalid LOG_LEVEL: {self.LOG_LEVEL}. "
                f"Must be one of {valid_log_levels}"
            )

        # Number of initial messages to collect
        try:
            self.INITIAL_MESSAGES_COUNT = int(os.getenv('INITIAL_MESSAGES_COUNT', '5'))
        except ValueError:
            raise ValueError("INITIAL_MESSAGES_COUNT must be a valid integer")

        # Session file name for Telethon
        self.SESSION_NAME = 'telegram_contacts_tracker'

    def _validate_config(self):
        """Validate that all required configuration is present."""
        required_vars = {
            'TELEGRAM_API_ID': self.TELEGRAM_API_ID,
            'TELEGRAM_API_HASH': self.TELEGRAM_API_HASH,
            'TELEGRAM_PHONE_NUMBER': self.TELEGRAM_PHONE_NUMBER,
            'OPENAI_API_KEY': self.OPENAI_API_KEY,
            'GOOGLE_SERVICE_ACCOUNT_FILE': self.GOOGLE_SERVICE_ACCOUNT_FILE,
        }

        missing_vars = [key for key, value in required_vars.items() if not value]

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                "Please create a .env file based on .env.example and fill in all required values."
            )

    def __repr__(self):
        """Return a safe string representation of the config (without sensitive data)."""
        return (
            f"Config("
            f"TELEGRAM_API_ID={'*' * 8}, "
            f"GOOGLE_SHEET_NAME={self.GOOGLE_SHEET_NAME}, "
            f"DATABASE_PATH={self.DATABASE_PATH}, "
            f"LOG_LEVEL={self.LOG_LEVEL}"
            f")"
        )


# Global config instance
config = Config()
