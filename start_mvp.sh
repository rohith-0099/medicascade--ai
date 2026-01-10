#!/bin/bash

echo "🚀 Starting MedicaScade AI MVP..."
echo ""

# Start backend
echo "📡 Starting Backend..."
cd ~/medicascade-ai/backend
source venv/bin/activate
uvicorn main:app --reload &
BACKEND_PID=$!

# Wait for backend to initialize
sleep 5

# Start frontend
echo "🎨 Starting Frontend..."
cd ~/medicascade-ai/frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Backend running (PID: $BACKEND_PID) - http://localhost:8000"
echo "✅ Frontend running (PID: $FRONTEND_PID) - http://localhost:5173"
echo ""
echo "🌐 Open in browser: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both services"

# Function to cleanup
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Services stopped"
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT

# Wait for user interrupt
wait
