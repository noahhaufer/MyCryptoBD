"""
Authentication utilities for JWT tokens and Telegram authentication.
"""

import os
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
SECRET_KEY = os.getenv("SECRET_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not JWT_SECRET or not SECRET_KEY:
    raise ValueError("JWT_SECRET and SECRET_KEY must be set in environment variables")

# Generate encryption key from SECRET_KEY
def get_fernet_key() -> bytes:
    """Generate a Fernet key from SECRET_KEY."""
    return Fernet.generate_key()  # In production, derive this from SECRET_KEY

# Initialize Fernet cipher
cipher = Fernet(get_fernet_key())

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def encrypt_session(session_string: str) -> str:
    """Encrypt Telegram session string for storage."""
    return cipher.encrypt(session_string.encode()).decode()


def decrypt_session(encrypted_session: str) -> str:
    """Decrypt stored Telegram session string."""
    return cipher.decrypt(encrypted_session.encode()).decode()


def verify_telegram_webapp_data(init_data: str) -> Optional[Dict]:
    """
    Verify Telegram Web App init data.

    Args:
        init_data: The initData string from Telegram Web App

    Returns:
        Parsed data dict if valid, None otherwise
    """
    try:
        # Parse init_data
        params = {}
        for item in init_data.split("&"):
            key, value = item.split("=", 1)
            params[key] = value

        # Extract hash
        received_hash = params.pop("hash", None)
        if not received_hash:
            return None

        # Create data-check-string
        data_check_arr = [f"{k}={v}" for k, v in sorted(params.items())]
        data_check_string = "\n".join(data_check_arr)

        # Calculate hash
        secret_key = hmac.new(
            "WebAppData".encode(),
            BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        # Verify hash
        if calculated_hash != received_hash:
            return None

        return params

    except Exception:
        return None
