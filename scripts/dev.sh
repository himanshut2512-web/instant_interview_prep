#!/usr/bin/env bash
# Start backend (FastAPI on :8000) and frontend (Vite on :5173) for development.
# Usage: ./scripts/dev.sh        (macOS / Linux / Git Bash)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ ! -d "$ROOT/backend/.venv" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv "$ROOT/backend/.venv"
  "$ROOT/backend/.venv/bin/pip" install -q -r "$ROOT/backend/requirements.txt"
fi
if [ ! -f "$ROOT/backend/.env" ]; then
  cp "$ROOT/backend/.env.example" "$ROOT/backend/.env"
  echo "Created backend/.env - add ANTHROPIC_API_KEY there for AI mode (demo mode works without it)."
fi
if [ ! -d "$ROOT/frontend/node_modules" ]; then
  echo "Installing frontend dependencies..."
  (cd "$ROOT/frontend" && npm install --no-fund --no-audit)
fi

(cd "$ROOT/backend" && .venv/bin/uvicorn app.main:app --reload --port 8000) &
BACKEND_PID=$!
trap 'kill $BACKEND_PID 2>/dev/null' EXIT

echo "Backend: http://localhost:8000   Frontend: http://localhost:5173"
cd "$ROOT/frontend" && npm run dev
