#!/usr/bin/env bash
# Start backend (http://localhost:8000) and frontend (http://localhost:5173) together.
# Ctrl+C stops both.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cleanup() {
  echo; echo "Stopping..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

echo "Starting backend..."
cd "$ROOT/backend"
[ -d venv ] || python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

echo "Starting frontend..."
cd "$ROOT/frontend"
[ -d node_modules ] || npm install
npm run dev &
FRONTEND_PID=$!

echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "Press Ctrl+C to stop both"
wait
