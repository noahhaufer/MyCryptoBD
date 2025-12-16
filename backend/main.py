"""
FastAPI backend for multi-user Telegram contacts tracker.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from backend.database import get_db, init_db
from backend.models import User, Contact, Message
from backend.auth import create_access_token, verify_token, verify_telegram_webapp_data

# Initialize FastAPI app
app = FastAPI(
    title="Telegram Contacts Tracker API",
    description="Multi-user Telegram contacts tracking and management system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()


# Pydantic models
class TelegramAuthData(BaseModel):
    init_data: str


class ContactResponse(BaseModel):
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    phone_number: Optional[str]
    company: Optional[str]
    notes: Optional[str]
    added_date: datetime
    is_exported: bool

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: int
    telegram_user_id: int
    telegram_username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    google_sheet_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ContactCreate(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None


class ContactUpdate(BaseModel):
    company: Optional[str] = None
    notes: Optional[str] = None


# Dependency: Get current user from JWT
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Verify JWT token and return current user."""
    token = credentials.credentials
    payload = verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


# Routes
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Telegram Contacts Tracker API"}


@app.post("/auth/telegram")
async def auth_telegram(
    auth_data: TelegramAuthData,
    db: Session = Depends(get_db)
):
    """
    Authenticate user via Telegram Web App data.

    This verifies the initData from Telegram and creates/updates the user.
    """
    # Verify Telegram data
    telegram_data = verify_telegram_webapp_data(auth_data.init_data)

    if not telegram_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram authentication data"
        )

    # Parse user data from telegram_data
    # In real implementation, parse from telegram_data['user']
    user_data = telegram_data.get("user", {})
    telegram_user_id = int(user_data.get("id"))

    # Get or create user
    user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()

    if not user:
        # Create new user
        user = User(
            telegram_user_id=telegram_user_id,
            telegram_username=user_data.get("username"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            last_login_at=datetime.utcnow()
        )
        db.add(user)
    else:
        # Update last login
        user.last_login_at = datetime.utcnow()

    db.commit()
    db.refresh(user)

    # Create JWT token
    access_token = create_access_token({"user_id": user.id})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }


@app.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@app.get("/contacts", response_model=List[ContactResponse])
async def get_contacts(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all contacts for the current user."""
    contacts = (
        db.query(Contact)
        .filter(Contact.user_id == current_user.id)
        .order_by(Contact.added_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return contacts


@app.get("/contacts/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific contact."""
    contact = (
        db.query(Contact)
        .filter(Contact.id == contact_id, Contact.user_id == current_user.id)
        .first()
    )

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )

    return contact


@app.post("/contacts", response_model=ContactResponse)
async def create_contact(
    contact_data: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new contact."""
    # Check if contact already exists
    existing_contact = (
        db.query(Contact)
        .filter(
            Contact.user_id == current_user.id,
            Contact.telegram_id == contact_data.telegram_id
        )
        .first()
    )

    if existing_contact:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contact already exists"
        )

    # Create new contact
    contact = Contact(
        user_id=current_user.id,
        **contact_data.dict()
    )

    db.add(contact)
    db.commit()
    db.refresh(contact)

    return contact


@app.patch("/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    contact_data: ContactUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a contact."""
    contact = (
        db.query(Contact)
        .filter(Contact.id == contact_id, Contact.user_id == current_user.id)
        .first()
    )

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )

    # Update fields
    for field, value in contact_data.dict(exclude_unset=True).items():
        setattr(contact, field, value)

    db.commit()
    db.refresh(contact)

    return contact


@app.delete("/contacts/{contact_id}")
async def delete_contact(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a contact."""
    contact = (
        db.query(Contact)
        .filter(Contact.id == contact_id, Contact.user_id == current_user.id)
        .first()
    )

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )

    db.delete(contact)
    db.commit()

    return {"status": "success", "message": "Contact deleted"}


@app.post("/export")
async def export_to_sheets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export contacts to Google Sheets."""
    if not current_user.google_sheet_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Sheet ID not configured"
        )

    # Get all unexported contacts
    contacts = (
        db.query(Contact)
        .filter(Contact.user_id == current_user.id, Contact.is_exported == False)
        .all()
    )

    if not contacts:
        return {"status": "success", "message": "No new contacts to export"}

    # TODO: Implement actual Google Sheets export
    # For now, mark contacts as exported
    for contact in contacts:
        contact.is_exported = True

    db.commit()

    return {
        "status": "success",
        "message": f"Exported {len(contacts)} contacts",
        "count": len(contacts)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
