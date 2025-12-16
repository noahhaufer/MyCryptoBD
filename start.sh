#!/bin/bash

# Startup script for Telegram Contacts Tracker

echo "🚀 Starting Telegram Contacts Tracker..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create a .env file with your configuration."
    exit 1
fi

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

echo "✅ Dependencies installed"
echo ""

# Start backend in background
echo "🔧 Starting FastAPI backend on port 8000..."
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

sleep 2

# Start bot in background
echo "🤖 Starting Telegram bot..."
python backend/bot.py &
BOT_PID=$!

sleep 2

# Start frontend
echo "🌐 Starting frontend on port 5173..."
cd frontend && python -m http.server 5173 &
FRONTEND_PID=$!

cd ..

echo ""
echo "✅ All services started!"
echo ""
echo "📱 Backend API: http://localhost:8000"
echo "🌐 Frontend: http://localhost:5173"
echo "🤖 Bot: Running"
echo ""
echo "💡 Send /start to your bot on Telegram to begin!"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for Ctrl+C
trap "echo ''; echo '🛑 Stopping services...'; kill $BACKEND_PID $BOT_PID $FRONTEND_PID 2>/dev/null; exit" INT

wait
