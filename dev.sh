#!/bin/bash

# dev.sh - Start both backend and frontend development servers

echo "🚀 Starting development servers..."
echo ""
echo "This script is designed to run from VSCode terminal."
echo "It will start both servers in the current terminal session."
echo ""
echo "For separate terminal windows, manually run:"
echo "  Terminal 1: cd backend && source ../.venv/bin/activate && fastapi dev app.py"
echo "  Terminal 2: cd platform && npm run dev"
echo ""
echo "Starting servers in 3 seconds... (Ctrl+C to cancel)"
sleep 3

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $(jobs -p) 2>/dev/null
    exit
}

# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

# Get the current directory
PROJECT_DIR="$(pwd)"

# Start backend server in background
echo "📦 Starting FastAPI backend on http://localhost:8000"
cd "$PROJECT_DIR/backend" && source ".venv/bin/activate" && fastapi dev app.py &
BACKEND_PID=$!

# Give backend a moment to start
sleep 2

# Start frontend server in background
echo "⚛️  Starting Next.js frontend on http://localhost:3000"
cd "$PROJECT_DIR/platform" && npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Both servers are running!"
echo ""
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for background processes
wait
