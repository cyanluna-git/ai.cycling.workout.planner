#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
RESET='\033[0m'

log_backend()  { echo -e "${BLUE}[backend]${RESET}  $*"; }
log_frontend() { echo -e "${GREEN}[frontend]${RESET} $*"; }
log_error()    { echo -e "${RED}[error]${RESET}    $*"; }

# .env check
if [ ! -f "$ROOT/.env" ]; then
  log_error ".env file not found at $ROOT/.env"
  log_error "Copy .env.example to .env and fill in your credentials."
  exit 1
fi

# Kill child processes on Ctrl+C
cleanup() {
  echo ""
  echo "Stopping servers..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
  echo "Done."
  exit 0
}
trap cleanup SIGINT SIGTERM

# Backend
log_backend "Starting FastAPI on http://localhost:8005 ..."
source "$ROOT/.venv/bin/activate" 2>/dev/null || true
cd "$ROOT"
uvicorn api.main:app --reload --port 8005 2>&1 | sed "s/^/$(echo -e "${BLUE}[backend]${RESET}")  /" &
BACKEND_PID=$!

# Frontend
log_frontend "Starting Vite on http://localhost:3101 ..."
cd "$ROOT/frontend"
pnpm dev --port 3101 2>&1 | sed "s/^/$(echo -e "${GREEN}[frontend]${RESET}") /" &
FRONTEND_PID=$!

echo ""
echo "  Backend:  http://localhost:8005"
echo "  Frontend: http://localhost:3101"
echo "  API docs: http://localhost:8005/docs"
echo ""
echo "Press Ctrl+C to stop both servers."
echo ""

wait
