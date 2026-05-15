#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# PolicyLab bare-metal dev startup script
# Runs backend (FastAPI + Ray) and frontend (Vite) without Docker.
#
# Usage: ./dev.sh
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; RESET='\033[0m'
info()  { echo -e "${CYAN}[policylab]${RESET} $*"; }
ok()    { echo -e "${GREEN}[policylab]${RESET} $*"; }
err()   { echo -e "${RED}[policylab]${RESET} $*"; exit 1; }

cleanup() {
  info "Shutting down…"
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  ok "Done."
}
trap cleanup INT TERM EXIT

# ── Backend ───────────────────────────────────────────────────────────────────
BACKEND_DIR="$ROOT/backend"

if [[ ! -d "$BACKEND_DIR/.venv" ]]; then
  info "Creating Python virtual environment…"
  python3 -m venv "$BACKEND_DIR/.venv"
fi

info "Installing Python dependencies…"
"$BACKEND_DIR/.venv/bin/pip" install -q --upgrade pip
"$BACKEND_DIR/.venv/bin/pip" install -q -r "$BACKEND_DIR/requirements.txt"

info "Starting FastAPI backend on :8000"
cd "$BACKEND_DIR"
PYTHONPATH="$BACKEND_DIR" \
  "$BACKEND_DIR/.venv/bin/uvicorn" app.main:app \
  --host 0.0.0.0 --port 8000 --reload \
  &> "$ROOT/backend.log" &
BACKEND_PID=$!
ok "Backend PID $BACKEND_PID — logs: $ROOT/backend.log"

# Wait for backend to be ready
info "Waiting for backend health check…"
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    ok "Backend is healthy"
    break
  fi
  sleep 1
done

# ── Frontend ─────────────────────────────────────────────────────────────────
FRONTEND_DIR="$ROOT/frontend"

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  info "Installing npm dependencies…"
  cd "$FRONTEND_DIR" && npm install --silent
fi

info "Starting Vite dev server on :5173"
cd "$FRONTEND_DIR"
npm run dev &> "$ROOT/frontend.log" &
FRONTEND_PID=$!
ok "Frontend PID $FRONTEND_PID — logs: $ROOT/frontend.log"

echo ""
ok "PolicyLab is running!"
echo ""
echo "  Frontend:   http://localhost:5173"
echo "  Backend:    http://localhost:8000"
echo "  API docs:   http://localhost:8000/docs"
echo ""
echo "Press Ctrl-C to stop."
echo ""

# Tail both logs to stdout
tail -f "$ROOT/backend.log" "$ROOT/frontend.log" &
TAIL_PID=$!

# Wait for either process to die
wait -n "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
kill "$TAIL_PID" 2>/dev/null || true
