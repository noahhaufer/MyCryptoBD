# Setup Guide - Telegram Contacts Tracker

## Important: This is a Telegram Mini App

This app MUST be opened through Telegram. It will NOT work if you open the URL directly in a browser.

## Quick Setup (3 Steps)

### 1. Deploy Frontend to Vercel

Your repo is already connected. Vercel will auto-deploy the `frontend/` folder.

After deployment, you'll get a URL like: `https://mycryptobd.vercel.app`

**You don't need to add any environment variables to Vercel** - it's just static HTML/CSS/JS.

### 2. Deploy Backend to Railway

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub"
3. Select your repo: `noahhaufer/MyCryptoBD`
4. Add these environment variables:
   ```
   BOT_TOKEN=<from your .env>
   TELEGRAM_API_ID=<from your .env>
   TELEGRAM_API_HASH=<from your .env>
   OPENAI_API_KEY=<from your .env>
   DATABASE_URL=<from your .env>
   SECRET_KEY=<from your .env>
   JWT_SECRET=<from your .env>
   FRONTEND_URL=https://mycryptobd.vercel.app
   ```

5. Set start command:
   ```
   python backend/bot.py & uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```

6. Deploy and get your backend URL (e.g., `https://mycryptobd.railway.app`)

### 3. Update Frontend API URL

Edit `frontend/app.js` line 5:

```javascript
const API_URL = 'https://mycryptobd.railway.app';  // Your Railway backend URL
```

Commit and push:
```bash
git add frontend/app.js
git commit -m "Update API URL to production backend"
git push
```

## Connect Your Telegram Bot

### Option 1: BotFather Menu Button (Recommended)

1. Open [@BotFather](https://t.me/BotFather)
2. Send `/mybots`
3. Select your bot (the one with your BOT_TOKEN)
4. Click "Bot Settings" → "Menu Button"
5. Click "Edit Menu Button URL"
6. Enter: `https://mycryptobd.vercel.app`
7. Save

Now users can open your Mini App by clicking the menu button in your bot!

### Option 2: Start Command (Already Working)

Your bot already sends a button in the `/start` command. This is coded in `backend/bot.py`.

## How to Test

1. Open Telegram
2. Find your bot
3. Send `/start`
4. Click "Open Contacts Tracker" button
5. The Mini App opens

**DO NOT** try to open the Vercel URL directly in a browser - it won't work! Telegram Mini Apps only work when opened through Telegram.

## Troubleshooting

### Error: "Open in Telegram"
- You're trying to access the URL directly in a browser
- Mini Apps only work when opened through Telegram
- Use your bot to open the app

### Error: "Authentication failed"
- Backend is not running
- Check Railway logs
- Verify all environment variables are set

### Bot doesn't respond
- Check Railway logs for bot errors
- Verify BOT_TOKEN is correct
- Make sure bot is running (check Railway dashboard)

## Architecture

```
User opens bot → /start command → Bot sends button with WebAppInfo
                                          ↓
                          User clicks "Open Contacts Tracker"
                                          ↓
                          Telegram opens: https://mycryptobd.vercel.app
                                          ↓
                          Frontend authenticates with initData
                                          ↓
                          Backend verifies & returns JWT token
                                          ↓
                          App loads contacts from API
```

## Next Steps

After setup:
1. Test the bot by sending `/start`
2. Grant Telegram permissions when prompted
3. New contacts will appear automatically
4. Use the Mini App to manage and export contacts

Done!
