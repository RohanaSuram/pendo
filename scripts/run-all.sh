#!/bin/bash
# Run backend and frontend (use in separate terminals or with a process manager)
cd "$(dirname "$0")/.."

echo "Starting backend..."
cd backend && python -m venv venv 2>/dev/null || true
source venv/bin/activate 2>/dev/null || true
pip install -r requirements.txt -q
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

echo "Starting frontend..."
cd ../frontend && npm install && npm run dev &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "Press Ctrl+C to stop"

wait
