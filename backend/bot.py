"""
Telegram Bot for multi-user contact tracking.

This bot handles:
- User registration and authentication
- Starting contact monitoring
- Launching the Mini App
- Managing user settings
"""

import os
import logging
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from backend.database import SessionLocal
from backend.models import User

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_or_create_user(telegram_user) -> User:
    """Get or create a user in the database."""
    db: Session = SessionLocal()

    try:
        user = db.query(User).filter(
            User.telegram_user_id == telegram_user.id
        ).first()

        if not user:
            user = User(
                telegram_user_id=telegram_user.id,
                telegram_username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created new user: {telegram_user.id}")
        else:
            logger.info(f"User already exists: {telegram_user.id}")

        return user

    finally:
        db.close()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user

    # Get or create user in database
    db_user = get_or_create_user(user)

    # Create Web App button
    web_app = WebAppInfo(url=f"{FRONTEND_URL}")
    keyboard = [
        [KeyboardButton(text="Open Contacts Tracker", web_app=web_app)]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    welcome_message = f"""
Welcome to Telegram Contacts Tracker, {user.first_name}!

This bot helps you track and manage your Telegram connections automatically.

What you can do:
• Track new Telegram contacts
• Extract company information with AI
• Export contacts to Google Sheets
• View and manage your contact list

Click the button below to open the app:
    """

    await update.message.reply_text(
        welcome_message.strip(),
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_text = """
Available Commands:

/start - Start the bot and open the app
/help - Show this help message
/settings - Configure your settings
/export - Export contacts to Google Sheets
/stats - View your statistics

How it works:
1. Grant permissions to access your Telegram contacts
2. The bot automatically tracks new connections
3. AI extracts company information from conversations
4. Export everything to Google Sheets

Need help? Contact @your_support_username
    """

    await update.message.reply_text(help_text.strip())


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /settings command."""
    user = update.effective_user
    db: Session = SessionLocal()

    try:
        db_user = db.query(User).filter(User.telegram_user_id == user.id).first()

        if not db_user:
            await update.message.reply_text("Please use /start first to register.")
            return

        settings_text = f"""
Your Settings:

• Auto-export: {'Enabled' if db_user.auto_export_enabled else 'Disabled'}
• Initial messages to scan: {db_user.initial_messages_count}
• Google Sheet: {'Configured' if db_user.google_sheet_id else 'Not configured'}

To change settings, use the web app.
        """

        await update.message.reply_text(settings_text.strip())

    finally:
        db.close()


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command."""
    user = update.effective_user
    db: Session = SessionLocal()

    try:
        db_user = db.query(User).filter(User.telegram_user_id == user.id).first()

        if not db_user:
            await update.message.reply_text("Please use /start first to register.")
            return

        total_contacts = len(db_user.contacts)
        exported_contacts = sum(1 for c in db_user.contacts if c.is_exported)

        stats_text = f"""
Your Statistics:

• Total contacts: {total_contacts}
• Exported to sheets: {exported_contacts}
• Not exported: {total_contacts - exported_contacts}
• Member since: {db_user.created_at.strftime('%Y-%m-%d')}
        """

        await update.message.reply_text(stats_text.strip())

    finally:
        db.close()


async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /export command."""
    user = update.effective_user
    db: Session = SessionLocal()

    try:
        db_user = db.query(User).filter(User.telegram_user_id == user.id).first()

        if not db_user:
            await update.message.reply_text("Please use /start first to register.")
            return

        if not db_user.google_sheet_id:
            await update.message.reply_text(
                "Google Sheet not configured. Please configure it in the web app first."
            )
            return

        # Get unexported contacts
        unexported = [c for c in db_user.contacts if not c.is_exported]

        if not unexported:
            await update.message.reply_text("No new contacts to export!")
            return

        # TODO: Implement actual export
        await update.message.reply_text(
            f"Exporting {len(unexported)} contacts to Google Sheets...\n"
            f"(Export functionality will be implemented with the contact tracking system)"
        )

    finally:
        db.close()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular messages."""
    await update.message.reply_text(
        "Use /start to open the Contacts Tracker app, or /help for available commands."
    )


def main() -> None:
    """Run the bot."""
    logger.info("Starting Telegram bot...")

    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("export", export_command))

    # Handle regular messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    logger.info("Bot started successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
