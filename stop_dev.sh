#!/bin/bash

# WakeDock Development Stop Script

echo "🛑 Stopping WakeDock Development Environment"
echo "==========================================="

# Kill processes by PID if files exist
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    echo "Stopping backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || true
    rm -f .backend.pid
fi

if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    echo "Stopping frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null || true
    rm -f .frontend.pid
fi

# Kill by process name as backup
echo "Killing any remaining WakeDock processes..."
pkill -f "uvicorn.*wakedock" || true
pkill -f "vite.*wakedock" || true

# Wait a moment for processes to stop
sleep 2

echo "✅ All WakeDock services stopped"
