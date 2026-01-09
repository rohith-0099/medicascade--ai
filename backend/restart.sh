#!/bin/bash
# Restart backend cleanly (kills old process first)

cd /home/rohith/medicascade-ai/backend

echo "🔄 Restarting Universal AI Disease Prediction Engine"
echo "===================================================="
echo ""

# Kill any existing process
echo "Stopping any existing backend..."
pkill -f "python main.py" 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 2

# Start fresh
./start.sh
