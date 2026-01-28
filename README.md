# AI Coding Agent

AI Coding Agent is a full-stack, multi-agent software engineering assistant. It imports a
repository, builds a structural understanding of the codebase, and turns natural-language
requests ("add JWT auth", "convert SQLite to PostgreSQL") into reviewed, tested, multi-file
changes — always with an explicit plan-approval step before anything touches disk.

It is a portfolio implementation inspired by tools like Cursor, GitHub Copilot Workspace,
Claude Code, and Windsurf — not a clone of any of them.

## Core philosophy

No file is modified without the user first approving a concrete, itemized plan. Every agent
in the pipeline produces structured, inspectable output rather than opaque free text, so every
change the system makes can be explained and audited after the fact.

## Architecture

```
                     ┌────────────────────┐
 User prompt  ─────▶ │   Planning Agent    │  reads the project graph, proposes steps
                     └─────────┬──────────┘
                               │ user approval
                               ▼
                     ┌────────────────────┐
                     │ Code Generation     │  edits files, updates imports/deps
                     │ Agent               │
                     └─────────┬──────────┘
                               ▼
                     ┌────────────────────┐
                     │  Review Agent       │  correctness, security, style, unused imports
                     └─────────┬──────────┘
                               ▼
                     ┌────────────────────┐
                     │  Testing Agent      │  detects & runs pytest / jest / npm test
                     └─────────┬──────────┘
                               ▼
                     ┌────────────────────┐
                     │ Git & Session Agent │  diff, commit message, session record
                     └────────────────────┘
```

Each agent is an independent module with a narrow responsibility and a typed input/output
contract, orchestrated as a graph rather than one large prompt. See
[`docs/architecture.md`](docs/architecture.md) for the full design and the reasoning behind
deviations from a single-prompt agent.

## Tech stack

| Layer | Choices |
|---|---|
| Frontend | Next.js (App Router), TypeScript, TailwindCSS, shadcn/ui, Monaco Editor, TanStack Query |
| Backend | FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, JWT auth |
| Database | PostgreSQL ([Neon](https://neon.tech), serverless) |
| AI layer | Anthropic Claude (default), pluggable provider interface for OpenAI/Gemini |
| Code analysis | Tree-sitter, GitPython, ripgrep |
| Tooling | Docker, Pytest, ESLint, Ruff, GitHub Actions |

## Repository layout

```
ai-coding-agent/
├── backend/          FastAPI application, agents, services, models
├── frontend/          Next.js application
├── docker/             Dockerfiles & compose config
├── tests/               cross-stack / e2e tests
├── docs/                architecture & API documentation
└── .github/workflows/   CI
```

## Getting started

See [`docs/setup.md`](docs/setup.md) for local development setup (backend, frontend, and
Docker Compose paths).

## Status

Actively developed. See [`docs/architecture.md`](docs/architecture.md) for design notes and
[`docs/roadmap.md`](docs/roadmap.md) for what's implemented vs. planned.
