#!/usr/bin/env bash
# Arka uç ve ön yüzü birlikte başlatır.
#
# Kullanım:
#   ./scripts/dev.sh
#
# Arka uç  : http://127.0.0.1:8000  (API belgeleri /docs adresinde)
# Ön yüz   : http://localhost:5173

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

cleanup() {
  echo ""
  echo "Kapatiliyor..."
  jobs -p | xargs -r kill 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# --- Arka uç ---------------------------------------------------------------
if [ ! -d "$BACKEND/.venv" ]; then
  echo "Python sanal ortami kuruluyor..."
  (cd "$BACKEND" && uv venv --python 3.11 && uv pip install -e ".[dev]")
fi

echo "Arka uc baslatiliyor: http://127.0.0.1:8000"
(cd "$BACKEND" && .venv/bin/python -m uvicorn app.main:app --reload --port 8000) &

# --- Ön yüz ----------------------------------------------------------------
if [ ! -d "$FRONTEND/node_modules" ]; then
  echo "Node bagimliliklari kuruluyor..."
  (cd "$FRONTEND" && pnpm install)
fi

echo "On yuz baslatiliyor: http://localhost:5173"
(cd "$FRONTEND" && pnpm dev) &

wait
