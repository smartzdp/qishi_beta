#!/bin/bash

# Start development servers (backend + frontend)

set -e

echo "🚀 Starting Excel Agent development servers..."

# Check if .env exists
if [[ ! -f ".env" ]]; then
    echo "⚠️  .env file not found"
    echo "Please create .env from .env.example and fill in your API keys"
    exit 1
fi

# Check if virtual environment exists
if [[ ! -d ".venv" ]]; then
    echo "⚠️  Virtual environment not found"
    echo "Please run: bash scripts/setup_venv.sh"
    exit 1
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
source .venv/bin/activate

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend
echo "🔧 Starting backend server (FastAPI)..."
cd "$(dirname "$0")/.."
python -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"
echo "   URL: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"

# Wait a bit for backend to start
sleep 3

# Start frontend
echo ""
echo "🎨 Starting frontend server (Vite + React)..."
cd frontend

# Check if node_modules exists
if [[ ! -d "node_modules" ]]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!
echo "✅ Frontend started (PID: $FRONTEND_PID)"
echo "   URL: http://localhost:5173"

echo ""
echo "🎉 Both servers are running!"
echo ""
echo "📝 Access points:"
echo "  Frontend:  http://localhost:5173"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID

