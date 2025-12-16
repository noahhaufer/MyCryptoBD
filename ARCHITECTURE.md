# Multi-User Architecture - Telegram Mini App

## Overview
This is a **multi-user SaaS application** built as a **Telegram Mini App**. Users interact with a Telegram bot that opens a web interface inside Telegram.

## Key Components

### 1. **Telegram Bot** (`bot/`)
- Entry point for users
- Handles `/start`, `/help`, `/stats` commands
- Opens Telegram Mini App
- Sends notifications to users
- **Tech:** `python-telegram-bot`

### 2. **Telegram Mini App** (`frontend/`)
- Web UI that runs inside Telegram
- Dashboard to view contacts
- Connect Google Sheets button
- Settings panel
- **Tech:** React + Telegram WebApp API
- **Auth:** Automatic via Telegram (no passwords!)

### 3. **Backend API** (`api/`)
- REST API for Mini App
- Handles user settings, contacts CRUD
- Google OAuth flow
- **Tech:** FastAPI + PostgreSQL
- **Auth:** Validates Telegram WebApp data

### 4. **Background Worker** (`worker/`)
- Monitors multiple users' Telegram sessions
- Detects new contacts for each user
- Routes to correct user's Google Sheet
- AI extraction per contact
- **Tech:** Celery + Telethon (multi-session)

### 5. **Database**
- Multi-tenant PostgreSQL
- Tables: `users`, `user_settings`, `contacts`, `sync_log`
- **Isolation:** All data scoped by `telegram_user_id`

## User Flow

```
1. User opens Telegram bot → /start
2. Bot sends welcome + "Open App" button
3. Mini App opens inside Telegram
   - Authenticated automatically (Telegram WebApp API)
4. User connects Google Sheets (OAuth)
5. User authorizes app to monitor their Telegram
6. Background worker starts monitoring their account
7. New contact detected → AI extraction → User's Google Sheet
8. User gets notification in Telegram
```

## Data Flow

```
User A's Telegram → Worker monitors → New contact detected
                                             ↓
                                    AI extracts company info
                                             ↓
                                    Save to DB (user_id=A)
                                             ↓
                                    Export to User A's Google Sheet
                                             ↓
                                    Notify User A in Telegram

User B's Telegram → (same process, completely isolated)
```

## Key Differences from Current Code

### Current (Single User):
- One `.env` file with YOUR credentials
- One Telegram session
- One Google Sheet
- Runs for one person only

### New (Multi-User):
- Each user has their own settings in database
- Each user connects THEIR Telegram account
- Each user connects THEIR Google Sheet
- Runs for unlimited users simultaneously
- Complete data isolation per user

## Authentication

### No Passwords Needed!
- Users authenticate via Telegram automatically
- Telegram Mini App validates `initData` from Telegram
- Backend verifies signature using bot token
- User identity = `telegram_user_id`

### Google OAuth (Per User)
- Each user authorizes the app to access THEIR Google account
- Refresh tokens stored encrypted in database
- Scoped per user

### Telegram Monitoring (Per User)
- Each user provides phone number + verification code
- Telethon session string stored encrypted
- Background worker maintains multiple sessions

## Security

1. **Data Isolation:** All queries filtered by `user_id`
2. **Encryption:** OAuth tokens and session strings encrypted at rest
3. **Telegram Auth:** WebApp data signature validation
4. **Google OAuth:** Standard OAuth 2.0 flow with refresh tokens
5. **API Security:** CORS restricted to Telegram domains

## Tech Stack

| Component | Technology |
|-----------|------------|
| Bot | python-telegram-bot |
| Mini App | React + Vite |
| Backend API | FastAPI |
| Database | PostgreSQL |
| Background Worker | Celery + Redis |
| Telegram Client | Telethon (multi-session) |
| AI | OpenAI GPT-4 |
| Sheets | Google Sheets API (OAuth per user) |
| Hosting | Docker + Docker Compose |

## Environment Variables

### App-Level (Shared)
```env
BOT_TOKEN=<telegram_bot_token>
TELEGRAM_API_ID=<your_telegram_api_id>
TELEGRAM_API_HASH=<your_telegram_api_hash>
OPENAI_API_KEY=<openai_api_key>
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SECRET_KEY=<random_secret_for_encryption>
```

### User-Level (Stored in Database)
- Google OAuth tokens (per user)
- Telegram session strings (per user)
- Google Sheet names (per user)

## File Structure

```
telegram_contacts_tracker/
├── bot/                    # Telegram bot
│   ├── handlers.py         # Command handlers
│   ├── keyboards.py        # Bot keyboards/buttons
│   └── main.py             # Bot entry point
├── api/                    # FastAPI backend
│   ├── auth.py             # Telegram WebApp auth
│   ├── routes/             # API endpoints
│   │   ├── users.py
│   │   ├── contacts.py
│   │   ├── google.py       # OAuth flow
│   │   └── telegram.py     # Telegram connection
│   ├── models.py           # Database models
│   └── main.py             # FastAPI app
├── worker/                 # Background worker
│   ├── telegram_monitor.py # Multi-session manager
│   ├── contact_processor.py
│   └── tasks.py            # Celery tasks
├── frontend/               # Telegram Mini App
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   └── telegram.js     # Telegram WebApp API
│   └── index.html
├── shared/                 # Shared code
│   ├── database.py         # Multi-user DB manager
│   ├── sheets_manager.py   # Per-user sheets
│   ├── ai_extractor.py     # AI extraction
│   └── encryption.py       # Token encryption
├── schema.sql              # Database schema
├── docker-compose.yml      # All services
└── README.md
```

## Deployment

```bash
# 1. Start all services
docker-compose up -d

# 2. Run migrations
docker-compose exec api alembic upgrade head

# 3. Set bot webhook (if using webhooks)
curl -X POST https://api.telegram.org/bot<TOKEN>/setWebhook \
  -d "url=https://yourdomain.com/webhook"
```

## User Experience

1. **First Time:**
   - Start bot → Opens Mini App
   - Connect Google Sheets (OAuth)
   - Authorize Telegram monitoring (phone + code)
   - Done! Monitoring starts automatically

2. **Daily Use:**
   - New contact messages you on Telegram
   - App detects it automatically
   - AI extracts company info
   - Saves to your Google Sheet
   - You get a Telegram notification

3. **Management:**
   - Open Mini App anytime
   - View all contacts
   - Tag events
   - Edit contact info
   - Export manually
   - View stats

## Scalability

- **Horizontal:** Add more worker instances
- **Database:** PostgreSQL with connection pooling
- **Sessions:** Redis for Celery task queue
- **Telegram:** Each worker handles N user sessions
- **Google Sheets:** Rate limiting per user
