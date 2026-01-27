# Setup

Two ways to run this locally: Docker Compose (fastest, matches production),
or running the backend/frontend directly (better for active development —
hot reload, breakpoints, etc).

## Option A — Docker Compose

Requires Docker.

```bash
cd docker
docker compose up -d
```

This builds and starts four things: Postgres, a one-shot `backend-migrate`
container that applies Alembic migrations and exits, the FastAPI backend,
and the Next.js frontend.

- Frontend: http://localhost:3000
- Backend: http://localhost:8000 (docs at `/docs`)
- Postgres: exposed on host port `55432` (not the default `5432`, so it
  doesn't collide with a Postgres you may already have running) — connect
  with `postgresql://postgres:postgres@localhost:55432/ai_coding_agent`

By default the backend runs with `LLM_PROVIDER=mock`, so the full pipeline
(plan → generate → review → apply → test → commit) runs end-to-end without
any API key — the Planning/Code Generation/Review/Git agents just return
empty/placeholder structured output instead of real model completions. To
use real Claude completions, set an API key before starting:

```bash
ANTHROPIC_API_KEY=sk-ant-... LLM_PROVIDER=anthropic docker compose up -d
```

Stop everything with `docker compose stop`; `docker compose down -v` also
drops the Postgres volume (and therefore all data).

## Option B — Run directly

### Backend

Requires Python 3.11+, a Postgres instance, and `ripgrep` (`brew install
ripgrep` / `apt install ripgrep`) on PATH for code search.

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

Run the test suite (needs its own reachable Postgres — `DATABASE_URL` env
var, migrated the same way):

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
