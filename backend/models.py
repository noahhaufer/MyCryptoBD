"""
SQLAlchemy models for the multi-user Telegram contacts tracker.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, Text, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User model for multi-user authentication."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_user_id = Column(BigInteger, unique=True, nullable=False, index=True)
    telegram_username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))

    # Authentication
    telegram_session_string = Column(Text)  # Encrypted Telethon session

    # Settings
    google_sheet_id = Column(String(255))
    initial_messages_count = Column(Integer, default=5)
    auto_export_enabled = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime)

    # Relationships
    contacts = relationship("Contact", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("TelegramSession", back_populates="user", cascade="all, delete-orphan")


class Contact(Base):
    """Contact model for tracking Telegram connections."""
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Contact information
    telegram_id = Column(BigInteger, nullable=False)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    phone_number = Column(String(50))

    # AI-extracted information
    company = Column(String(255))
    notes = Column(Text)

    # Metadata
    added_date = Column(DateTime, default=datetime.utcnow)
    first_message_date = Column(DateTime)
    last_interaction_date = Column(DateTime)

    # Status
    is_exported = Column(Boolean, default=False)
    is_mutual = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="contacts")
    messages = relationship("Message", back_populates="contact", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index('idx_user_telegram', 'user_id', 'telegram_id', unique=True),
        Index('idx_user_added_date', 'user_id', 'added_date'),
    )


class Message(Base):
    """Message model for storing contact conversations."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)

    # Message content
    telegram_message_id = Column(BigInteger, nullable=False)
    sender_id = Column(BigInteger, nullable=False)
    text = Column(Text)

    # Metadata
    sent_at = Column(DateTime, default=datetime.utcnow)
    is_outgoing = Column(Boolean, default=False)

    # Relationships
    contact = relationship("Contact", back_populates="messages")

    # Indexes
    __table_args__ = (
        Index('idx_contact_sent_at', 'contact_id', 'sent_at'),
    )


class TelegramSession(Base):
    """Active Telegram sessions for real-time monitoring."""
    __tablename__ = "telegram_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Session info
    session_string = Column(Text, nullable=False)  # Encrypted
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="sessions")


class ExportLog(Base):
    """Log of exports to Google Sheets."""
    __tablename__ = "export_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Export details
    contact_count = Column(Integer, default=0)
    sheet_id = Column(String(255))

    # Status
    status = Column(String(50), default="pending")  # pending, success, failed
    error_message = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
