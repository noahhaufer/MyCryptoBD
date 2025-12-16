"""
Utility functions for the Telegram Contacts Tracker.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from telethon.tl.types import User, Message

logger = logging.getLogger(__name__)


def format_user_info(user: User) -> dict:
    """
    Extract and format user information from Telethon User object.

    Args:
        user: Telethon User object

    Returns:
        Dictionary with formatted user information
    """
    return {
        'user_id': user.id,
        'name': get_display_name(user),
        'username': user.username if user.username else '',
        'bio': '',  # Bio needs to be fetched separately
        'first_seen': datetime.now(),
        'last_contact': datetime.now()
    }


def get_display_name(user: User) -> str:
    """
    Get the best display name for a user.

    Args:
        user: Telethon User object

    Returns:
        Display name (first + last name, or first name, or username)
    """
    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    elif user.first_name:
        return user.first_name
    elif user.username:
        return user.username
    else:
        return f"User {user.id}"


def format_messages_for_context(messages: List[Message]) -> List[str]:
    """
    Extract text content from messages for AI processing.

    Args:
        messages: List of Telethon Message objects

    Returns:
        List of message text strings
    """
    message_texts = []

    for msg in messages:
        if msg.message:  # Only process text messages
            # Clean and format the message
            text = msg.message.strip()
            if text:
                message_texts.append(text)

    return message_texts


def format_timestamp(dt: datetime) -> str:
    """
    Format a datetime object for display.

    Args:
        dt: Datetime object

    Returns:
        Formatted string (YYYY-MM-DD HH:MM:SS)
    """
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def parse_command(text: str) -> tuple:
    """
    Parse a bot command from message text.

    Args:
        text: Message text starting with /

    Returns:
        Tuple of (command, args_list)
    """
    parts = text.strip().split()
    command = parts[0].lower() if parts else ''
    args = parts[1:] if len(parts) > 1 else []

    return command, args


def validate_user_id(user_id_str: str) -> Optional[int]:
    """
    Validate and convert a user ID string to integer.

    Args:
        user_id_str: String representation of user ID

    Returns:
        Integer user ID or None if invalid
    """
    try:
        user_id = int(user_id_str)
        if user_id > 0:
            return user_id
    except ValueError:
        pass

    return None


def format_contact_summary(contact_data: dict) -> str:
    """
    Format a contact summary for display in Telegram messages.

    Args:
        contact_data: Dictionary with contact information

    Returns:
        Formatted string for Telegram message
    """
    lines = []

    # Header
    lines.append("📝 New contact logged:")
    lines.append("")

    # Basic info
    name = contact_data.get('name', 'Unknown')
    lines.append(f"👤 Name: {name}")

    username = contact_data.get('username', '')
    if username:
        lines.append(f"🔗 Username: @{username}")

    # Professional info
    company = contact_data.get('company', 'Unknown')
    if company and company != 'Unknown':
        lines.append(f"🏢 Company: {company}")

    role = contact_data.get('role', 'Unknown')
    if role and role != 'Unknown':
        lines.append(f"💼 Role: {role}")

    # Event tag
    event_tag = contact_data.get('event_tag', '')
    if event_tag:
        lines.append(f"📍 Event: {event_tag}")
    else:
        lines.append("📍 Event: [Use /tag_event to add]")

    # Topics
    topics = contact_data.get('topics', [])
    if topics and len(topics) > 0:
        topics_str = ", ".join(topics)
        lines.append(f"💬 Topics: {topics_str}")

    lines.append("")
    lines.append("Commands:")

    user_id = contact_data.get('user_id', '')
    lines.append(f"/edit {user_id} company Acme Corp")
    lines.append(f"/edit {user_id} notes Met at happy hour")

    return "\n".join(lines)


def format_stats_message(stats: dict) -> str:
    """
    Format statistics for display in Telegram.

    Args:
        stats: Dictionary with statistics data

    Returns:
        Formatted string for Telegram message
    """
    lines = []

    lines.append("📊 Contact Statistics")
    lines.append("")
    lines.append(f"👥 Total Contacts: {stats.get('total_contacts', 0)}")
    lines.append(f"🏢 With Company: {stats.get('contacts_with_company', 0)}")
    lines.append(f"🆕 Recent (7 days): {stats.get('recent_contacts_7d', 0)}")

    # Contacts by event
    by_event = stats.get('contacts_by_event', [])
    if by_event and len(by_event) > 0:
        lines.append("")
        lines.append("📍 By Event:")
        for event in by_event[:5]:  # Show top 5 events
            lines.append(f"  • {event['event_tag']}: {event['count']}")

    return "\n".join(lines)


def sanitize_sheet_value(value: any) -> str:
    """
    Sanitize a value for Google Sheets to prevent formula injection.

    Args:
        value: Value to sanitize

    Returns:
        Safe string value
    """
    if value is None:
        return ''

    str_value = str(value)

    # Prevent formula injection by escaping leading special characters
    if str_value and str_value[0] in ['=', '+', '-', '@']:
        return "'" + str_value

    return str_value


def calculate_time_since(dt: datetime) -> str:
    """
    Calculate human-readable time elapsed since a datetime.

    Args:
        dt: Datetime object

    Returns:
        Human-readable string (e.g., "2 hours ago", "3 days ago")
    """
    if isinstance(dt, str):
        try:
            dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return "unknown time"

    now = datetime.now()
    diff = now - dt

    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < timedelta(days=7):
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif diff < timedelta(days=30):
        weeks = diff.days // 7
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    else:
        months = diff.days // 30
        return f"{months} month{'s' if months != 1 else ''} ago"


def setup_logging(log_level: str):
    """
    Set up logging configuration for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Convert string to logging level
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format
    )

    # Set telethon logging to WARNING to reduce noise
    logging.getLogger('telethon').setLevel(logging.WARNING)

    logger.info(f"Logging configured at {log_level} level")
