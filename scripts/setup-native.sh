#!/usr/bin/env bash
# Native (no-Docker) setup for cadence on macOS.
# Installs Postgres 16 + pgvector via Homebrew, creates the db and role,
# sets up a Python venv, installs deps, runs migrations, installs frontend deps.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

say() { printf "\n\033[1;36m==>\033[0m %s\n" "$*"; }
warn() { printf "\n\033[1;33m!!\033[0m %s\n" "$*"; }
die() { printf "\n\033[1;31mxx\033[0m %s\n" "$*"; exit 1; }

# ── prereqs ──────────────────────────────────────────────────────────────────
command -v brew >/dev/null 2>&1 || die "Homebrew not installed. Get it at https://brew.sh and re-run."
command -v python3.11 >/dev/null 2>&1 || command -v python3 >/dev/null 2>&1 || die "Python 3.11+ not found."
command -v node >/dev/null 2>&1 || die "Node not found. brew install node@20"

PY=$(command -v python3.11 || command -v python3)
PY_VER=$($PY -c 'import sys; print("{}.{}".format(*sys.version_info[:2]))')
say "Using Python $PY_VER ($PY)"

# ── Postgres + pgvector ─────────────────────────────────────────────────────
if ! brew list postgresql@16 >/dev/null 2>&1; then
  say "Installing postgresql@16 via Homebrew…"
  brew install postgresql@16
fi
if ! brew list pgvector >/dev/null 2>&1; then
  say "Installing pgvector via Homebrew…"
  brew install pgvector
fi

say "Starting postgresql@16…"
brew services start postgresql@16 >/dev/null

# Wait for the server to actually accept connections
for i in $(seq 1 20); do
  if pg_isready -q 2>/dev/null; then break; fi
  sleep 0.5
done
pg_isready -q || die "Postgres did not come up. Try 'brew services restart postgresql@16'."

say "Creating role + database 'cadence'…"
psql postgres -tc "SELECT 1 FROM pg_roles WHERE rolname='cadence'" | grep -q 1 || \
  psql postgres -c "CREATE ROLE cadence WITH LOGIN SUPERUSER PASSWORD 'cadence';"
psql postgres -tc "SELECT 1 FROM pg_database WHERE datname='cadence'" | grep -q 1 || \
  psql postgres -c "CREATE DATABASE cadence OWNER cadence;"
psql -U cadence -d cadence -c "CREATE EXTENSION IF NOT EXISTS vector;"

# ── Backend ─────────────────────────────────────────────────────────────────
say "Setting up backend venv…"
cd "$ROOT/backend"
[ -d .venv ] || $PY -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -e ".[dev]"

# Audio + PDF system deps (best-effort)
for f in libsndfile ffmpeg poppler tesseract; do
  brew list "$f" >/dev/null 2>&1 || { say "Installing $f…"; brew install "$f"; }
done

say "Running migrations…"
alembic upgrade head

# ── Frontend ────────────────────────────────────────────────────────────────
say "Installing frontend deps…"
cd "$ROOT/frontend"
npm install --no-audit --no-fund

# ── Done ────────────────────────────────────────────────────────────────────
cat <<'EOF'

────────────────────────────────────────────────────────────────────────────
✓ Setup complete.

Before you start the servers, open backend/.env and fill in:
  ANTHROPIC_API_KEY=sk-ant-...
  VOYAGE_API_KEY=pa-...

Then in two terminals:

  # terminal 1 — backend
  cd backend
  source .venv/bin/activate
  uvicorn app.main:app --reload

  # terminal 2 — frontend
  cd frontend
  npm run dev

Open http://localhost:3000

To stop Postgres later:
  brew services stop postgresql@16
────────────────────────────────────────────────────────────────────────────
EOF
