# Telegram Contacts Tracker - Multi-User Platform

A powerful, multi-user Telegram bot and Mini App for automatically tracking and managing your Telegram contacts with AI-powered company extraction.

## Features

- Multi-user support with secure authentication
- Telegram Mini App with beautiful, intuitive UI
- Automatic contact detection and tracking
- AI-powered company extraction using GPT-4
- Google Sheets integration for exports
- Real-time contact monitoring with Telethon
- RESTful API built with FastAPI
- PostgreSQL database (Supabase)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Your `.env` file is already set up with:
- BOT_TOKEN
- TELEGRAM_API_ID & TELEGRAM_API_HASH
- OPENAI_API_KEY
- DATABASE_URL (Supabase PostgreSQL)
- SECRET_KEY & JWT_SECRET

### 3. Start Everything

```bash
chmod +x start.sh
./start.sh
```

This will start:
- FastAPI backend (port 8000)
- Telegram bot
- Frontend (port 5173)

Or start services individually:

```bash
# Terminal 1: Backend API
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Telegram Bot
python backend/bot.py

# Terminal 3: Frontend
cd frontend && python -m http.server 5173
```

## Architecture

```
Project Structure:
telegram_contacts_tracker/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── bot.py               # Telegram bot
│   ├── models.py            # SQLAlchemy models
│   ├── database.py          # Database connection
│   ├── auth.py              # JWT & authentication
│   └── contact_tracker.py   # Telethon contact monitoring
├── frontend/
│   ├── index.html           # Mini App UI
│   ├── styles.css           # Styling
│   └── app.js               # JavaScript logic
├── start.sh                 # Startup script
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
└── DEPLOYMENT.md           # Deployment guide
```

## Connecting to Your Telegram Bot

### Method 1: BotFather Menu Button (Recommended)

1. Open [@BotFather](https://t.me/BotFather)
2. Send `/mybots`
3. Select your bot
4. Click "Bot Settings" → "Menu Button"
5. Set your frontend URL (e.g., `https://your-app.vercel.app`)

### Method 2: Inline Button (Already Implemented)

The bot sends a button when users type `/start`. This is already coded in `backend/bot.py`.

### Method 3: Deep Link

Share: `https://t.me/YOUR_BOT_USERNAME/app`

## API Endpoints

### Authentication
- `POST /auth/telegram` - Authenticate via Telegram Web App data

### User
- `GET /me` - Get current user info

### Contacts
- `GET /contacts` - List all contacts
- `GET /contacts/{id}` - Get specific contact
- `POST /contacts` - Create contact
- `PATCH /contacts/{id}` - Update contact
- `DELETE /contacts/{id}` - Delete contact

### Export
- `POST /export` - Export contacts to Google Sheets

## How It Works

1. User opens your Telegram bot
2. Clicks "Open Contacts Tracker" button
3. Mini App opens and authenticates
4. User grants Telegram permissions
5. Bot monitors for new contacts
6. AI extracts company info from messages
7. Everything appears in the Mini App
8. Export to Google Sheets anytime

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions to:
- Render/Railway/Fly.io (Backend)
- Vercel/Netlify (Frontend)
- Production configuration

## Technology Stack

- **Backend**: FastAPI, SQLAlchemy, Telethon, python-telegram-bot
- **Database**: PostgreSQL (Supabase)
- **AI**: OpenAI GPT-4
- **Frontend**: HTML, CSS, JavaScript (Telegram Mini App)
- **Authentication**: JWT tokens
- **Encryption**: Fernet for session encryption

## Environment Variables

Required in `.env`:
```
BOT_TOKEN=...
TELEGRAM_API_ID=...
TELEGRAM_API_HASH=...
OPENAI_API_KEY=...
DATABASE_URL=postgresql://...
SECRET_KEY=...
JWT_SECRET=...
```

Optional:
```
API_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
LOG_LEVEL=INFO
```

## Security

- JWT authentication for API
- Telegram Web App data verification
- Encrypted session storage
- PostgreSQL with prepared statements
- HTTPS required in production

## Support

For issues:
1. Check [DEPLOYMENT.md](DEPLOYMENT.md)
2. Review logs
3. Verify environment variables
4. Check Telegram Bot API docs

## License

MIT License - feel free to use and modify.

---

Built with by Noah Haufer
