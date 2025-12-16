# Deployment Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

All variables are already set in your `.env` file:
- BOT_TOKEN - Your Telegram bot token
- TELEGRAM_API_ID - Telegram API ID
- TELEGRAM_API_HASH - Telegram API Hash
- OPENAI_API_KEY - OpenAI API key
- DATABASE_URL - Supabase PostgreSQL connection string
- SECRET_KEY - For encryption
- JWT_SECRET - For JWT tokens

### 3. Start the Backend

```bash
# Start FastAPI backend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Start the Telegram Bot (in a new terminal)

```bash
# Start Telegram bot
python backend/bot.py
```

### 5. Serve the Frontend

```bash
# Simple HTTP server for the frontend
cd frontend
python -m http.server 5173
```

Or use any static file server.

## Deploy to Production

### Backend Deployment (Render/Railway/Fly.io)

1. Create a new web service
2. Connect your GitHub repository
3. Set environment variables from `.env`
4. Deploy with:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

### Bot Deployment

Deploy bot separately as a background worker:
- Start command: `python backend/bot.py`

### Frontend Deployment (Vercel/Netlify/GitHub Pages)

1. Deploy the `frontend/` folder
2. Update `API_URL` in `frontend/app.js` to your backend URL

## Connecting Your Telegram Bot to the Mini App

### Method 1: BotFather Setup (Recommended)

1. Open [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/mybots`
3. Select your bot
4. Click "Bot Settings" → "Menu Button"
5. Click "Configure Menu Button" or "Edit Menu Button URL"
6. Enter your frontend URL (e.g., `https://your-app.vercel.app`)
7. Save

Now when users click the menu button in your bot, it will open your Mini App!

### Method 2: Inline Keyboard Button (Already Implemented)

The bot already sends a button that opens the Mini App when users send `/start`.
This is implemented in `backend/bot.py`:

```python
web_app = WebAppInfo(url=f"{FRONTEND_URL}")
keyboard = [[KeyboardButton(text="Open Contacts Tracker", web_app=web_app)]]
```

### Method 3: Deep Link

Share this link with users:
```
https://t.me/YOUR_BOT_USERNAME/app
```

Replace `YOUR_BOT_USERNAME` with your bot's username (without @).

To set this up:
1. Go to [@BotFather](https://t.me/BotFather)
2. Send `/mybots`
3. Select your bot
4. Click "Bot Settings" → "Menu Button"
5. Set Web App URL to your frontend URL

## Environment Variables Explained

### Required
- `BOT_TOKEN` - From @BotFather when you create a bot
- `TELEGRAM_API_ID` - From https://my.telegram.org
- `TELEGRAM_API_HASH` - From https://my.telegram.org
- `OPENAI_API_KEY` - From https://platform.openai.com
- `DATABASE_URL` - PostgreSQL connection string from Supabase
- `SECRET_KEY` - For encrypting user sessions
- `JWT_SECRET` - For JWT authentication

### Optional
- `API_URL` - Backend API URL (default: http://localhost:8000)
- `FRONTEND_URL` - Frontend URL (default: http://localhost:5173)
- `LOG_LEVEL` - Logging level (default: INFO)

## Troubleshooting

### Issue: "No Telegram init data available"
- Make sure your frontend is served over HTTPS in production
- Telegram Web Apps only work when opened through Telegram

### Issue: "Authentication failed"
- Check that `BOT_TOKEN` in `.env` matches your bot
- Verify the frontend URL is correctly configured in BotFather

### Issue: "Database connection failed"
- Verify `DATABASE_URL` is correct
- Check that database tables are created (run the schema.sql)

### Issue: "OpenAI API error"
- Verify `OPENAI_API_KEY` is valid
- Check you have credits in your OpenAI account

## Architecture

```
┌─────────────────┐
│  Telegram Bot   │  (backend/bot.py)
│   @YourBot      │
└────────┬────────┘
         │
         ├──► Opens Mini App (frontend/)
         │
┌────────┴────────┐
│   FastAPI API   │  (backend/main.py)
│  (Port 8000)    │
└────────┬────────┘
         │
         ├──► PostgreSQL (Supabase)
         ├──► OpenAI API (GPT-4)
         └──► Contact Tracker (backend/contact_tracker.py)
```

## Next Steps

After deployment:

1. Test the bot by sending `/start` to your bot on Telegram
2. Click "Open Contacts Tracker" to launch the Mini App
3. Grant permissions for contact tracking
4. New contacts will automatically appear in the app

## Support

If you encounter issues:
- Check logs for error messages
- Verify all environment variables are set correctly
- Ensure database schema is properly initialized
- Test API endpoints with curl or Postman

For more help, consult:
- Telegram Bot API docs: https://core.telegram.org/bots
- Telegram Mini Apps docs: https://core.telegram.org/bots/webapps
- FastAPI docs: https://fastapi.tiangolo.com
