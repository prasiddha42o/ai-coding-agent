# Setup

The database is [Neon](https://neon.tech) (serverless Postgres) — there's
no local Postgres to install or run, in Docker or otherwise. Everything
else offers two ways to run: Docker Compose (fastest, matches production),
or running the backend/frontend directly (better for active development —
hot reload, breakpoints, etc).

## Database: Neon

1. Create a project at [neon.tech](https://neon.tech) (or use an existing
   one) and grab its connection string from the Neon console — Dashboard
   → your project → **Connection Details**.
2. Use the **direct** connection string, not the `-pooler` one. This app
   is a persistent server process with its own SQLAlchemy connection
   pool, so it doesn't need Neon's built-in PgBouncer the way a
   serverless/edge function would — and skipping it avoids PgBouncer
   transaction-mode caveats (e.g. server-side prepared statements)
   entirely.
3. Put it in `backend/.env` as `DATABASE_URL` (see `.env.example` for the
   shape). Neon requires TLS — the connection string needs
   `?sslmode=require`.

`backend/database/session.py` is already tuned for a remote/serverless
Postgres: `pool_pre_ping` catches connections Neon has already dropped
server-side before a query tries to use them, and `pool_recycle=300`
proactively retires pooled connections every 5 minutes rather than
assuming they stay open indefinitely.

CI is the one place that still uses a disposable local Postgres — see
`.github/workflows/ci.yml`. That's a deliberate, separate choice: a
throwaway `postgres:16-alpine` service container is faster, free, and
keeps test runs from touching a real Neon branch, regardless of what the
app itself connects to elsewhere.

## Option A — Docker Compose

Requires Docker and a `backend/.env` with `DATABASE_URL` set (see above —
`backend-migrate` and `backend` both load that file via `env_file`).

```bash
cd docker
docker compose up -d
```

This builds and starts three things: a one-shot `backend-migrate`
container that applies Alembic migrations against Neon and exits, the
FastAPI backend, and the Next.js frontend.

- Frontend: http://localhost:3000
- Backend: http://localhost:8000 (docs at `/docs`)

By default the backend runs with `LLM_PROVIDER=mock`, so the full pipeline
(plan → generate → review → apply → test → commit) runs end-to-end without
any API key — the Planning/Code Generation/Review/Git agents just return
empty/placeholder structured output instead of real model completions. To
use real Claude completions, set `LLM_PROVIDER=anthropic` and
`ANTHROPIC_API_KEY` in `backend/.env` instead.

Stop everything with `docker compose stop`.

## Option B — Run directly

### Backend

Requires Python 3.11+, a Neon connection string (see above), and
`ripgrep` (`brew install ripgrep` / `apt install ripgrep`) on PATH for
code search.

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env    # then edit DATABASE_URL, JWT_SECRET_KEY, etc.

# Alembic's script_location is relative to backend/, so run it from there:
python -m alembic upgrade head

# from the repo root, so `backend.*` imports resolve:
cd ..
uvicorn backend.main:app --reload --port 8000
```

Run the test suite (uses whatever `DATABASE_URL` is set in your
environment — including Neon; each test runs inside a rolled-back
SAVEPOINT, so it's safe to point at a real database):

```bash
pytest backend/tests -v
```

### Frontend

Requires Node 22+.

```bash
cd frontend
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_BASE_URL
npm run dev
```

Visit http://localhost:3000 (the frontend's own dev server defaults to
port 3000; several examples above used 3100/3100 purely to run alongside a
Dockerized instance on the same machine during development).

## Common gotchas

- **`ModuleNotFoundError: No module named 'backend'`** running Alembic or
  pytest directly: you're running from the wrong directory, or without the
  repo root on `PYTHONPATH`. `pytest.ini` at the repo root sets this up
  automatically for pytest; for Alembic, `cd backend` first (see above).
- **bcrypt/passlib error on registration** (`password cannot be longer than
  72 bytes...` at import time): passlib 1.7.4 (unmaintained) is
  incompatible with `bcrypt>=4.1`'s self-test. `requirements.txt` pins
  `bcrypt==4.0.1` for this reason — if you've installed dependencies some
  other way, make sure that pin held.
- **`tree-sitter-languages` import errors**: it's incompatible with
  `tree-sitter>=0.22`; `requirements.txt` pins `tree-sitter==0.21.3`.
- **`sslmode` errors / connection refused to Neon**: make sure
  `?sslmode=require` is on the connection string, and that you copied the
  direct (not pooled) host from the Neon console.
