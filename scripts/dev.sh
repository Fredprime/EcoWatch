#!/usr/bin/env bash
# One command for a local/intranet EcoWatch: DB + migrations + API/worker + frontend.
# The cloudflare/phone-check tunnel can keep pointing at the frontend port (5173).
set -euo pipefail

rootDir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$rootDir"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example — review ECOWATCH_AUTH_SECRET before sharing."
fi

if [ ! -x .venv/bin/python ]; then
  echo "Missing .venv — run 'make venv' and '.venv/bin/pip install -e \"backend[dev]\"' first." >&2
  exit 1
fi
if [ ! -x frontend/node_modules/.bin/vite ]; then
  echo "Missing frontend dependencies — run 'cd frontend && npm ci' first." >&2
  exit 1
fi

# Export .env so Alembic and the API resolve the same database settings.
set -a
# shellcheck disable=SC1091
. ./.env
set +a
# The worker belongs to the API process; enable it regardless of an older .env.
export ECOWATCH_WORKER_ENABLED=true

echo "==> Starting database"
scripts/compose.sh up -d --wait

echo "==> Applying migrations"
(cd backend && ../.venv/bin/alembic upgrade head)

apiPid=""
webPid=""
cleanup() {
  [ -n "$apiPid" ] && kill "$apiPid" 2>/dev/null || true
  [ -n "$webPid" ] && kill "$webPid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "==> API + worker on http://127.0.0.1:8000"
.venv/bin/uvicorn ecowatch.main:app --app-dir backend/src \
  --host 127.0.0.1 --port 8000 --reload &
apiPid=$!

echo "==> Frontend on http://127.0.0.1:5173"
(cd frontend && exec npm run dev -- --host 127.0.0.1) &
webPid=$!

echo "Ready. Ctrl-C stops the API and frontend; the database stays up (make down)."
# If either process exits, tear down the other and leave the DB running.
wait -n
