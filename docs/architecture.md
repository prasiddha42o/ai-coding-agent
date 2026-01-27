# Architecture

## The pipeline

```
 User prompt
      │
      ▼
 ┌─────────────────┐   reads repo metadata + knowledge graph
 │ Planning Agent   │──────────────────────────────────────────┐
 └─────────────────┘                                           │
      │ Plan (PENDING_APPROVAL)                                │
      ▼                                                        │
 ┌─────────────────┐  explicit user approval — nothing         │
 │  user approves   │  downstream runs without it               │
 └─────────────────┘                                           │
      │ Plan (APPROVED)                                        │
      ▼                                                        │
 ┌─────────────────────┐  writes NOTHING to disk yet — diffs    │
 │ Code Generation Agent│  computed locally (difflib) against   │
 └─────────────────────┘  the real file, stored as Change rows │
      │ Change[] (PROPOSED)                                    │
      ▼                                                        │
 ┌─────────────────┐  advisory notes on each Change —          │
 │  Review Agent    │  never blocks or auto-reverts             │
 └─────────────────┘                                           │
      │                                                        │
      ▼                                                        │
 ┌─────────────────┐  THE moment the filesystem changes.       │
 │  Apply           │  re-validates path safety independently   │
 └─────────────────┘  of Code Generation's own check            │
      │ Change[] (APPLIED)                                     │
      ▼                                                        │
 ┌─────────────────┐  deterministic — no LLM call. Detects &    │
 │  Testing Agent    │  runs pytest / Jest / npm test            │
 └─────────────────┘                                           │
      │                                                        │
      ├─ tests failed ──► stop. Applied changes stay on disk,  │
      │                   uncommitted. User decides what's next.│
      ▼                                                        │
 ┌─────────────────────┐  drafts a Conventional Commit message  │
 │ Git & Session Agent  │  + PR summary, then `git commit`s.     │
 └─────────────────────┘  lazily `git init`s ZIP imports at     │
                          import time, not commit time — see    │
                          tools/git_ops.py.                     │
```

Each stage is its own REST endpoint (`POST /plans/{id}/generate`,
`/review`, `/apply`, `POST /sessions/{id}/tests`, `POST /plans/{id}/commit`)
as well as being chainable end-to-end via `POST /plans/{id}/run`, which
streams progress as newline-delimited JSON events. A user who wants to
inspect and intervene between steps can; a user who just wants to watch it
run can.

## Two approval gates, not one

The PRD's philosophy is "no modification without explicit approval." This
implementation reads that as two separate gates, not one:

1. **Approve the plan** — unlocks Code Generation, which computes real
   diffs but still touches nothing on disk.
2. **Apply the changes** — a second, separate action that actually writes
   to the working directory, after the user has seen the *actual diff* (and
   the Review Agent's notes on it), not just the plan's prose description.

A plan's prose ("add input validation to the login form") is a much weaker
basis for consent than the diff that implements it. Splitting these into
two gates costs one extra API call and is a meaningfully stronger
transparency guarantee.

## Deliberate deviations from the PRD

- **LangGraph → a plain Python generator.** The PRD suggests LangGraph for
  agent orchestration. The actual control flow here — five sequential
  steps, each either succeeding or stopping the pipeline — doesn't need a
  graph library; `agents/orchestrator.py` is a ~100-line generator function.
  Swapping in LangGraph later, if the pipeline grows branches or retries
  that justify it, wouldn't touch any other agent.
- **A separate "Repository Analysis Agent" → deterministic tools.** The
  PRD's pipeline diagram includes a Repository Analysis Agent as its own
  LLM step. Building the knowledge graph (`services/knowledge_graph_service.py`)
  is pure static analysis — tree-sitter parsing plus heuristic import
  resolution (`tools/import_resolver.py`) — with no judgment calls an LLM
  would improve. Likewise the Testing Agent (`agents/testing_agent.py`) is
  fully deterministic: "did the tests pass" is read off a real subprocess's
  exit code and output, not asked of a model. Reserving LLM calls for the
  four steps that actually need judgment (Planning, Code Generation,
  Review, drafting the commit message) is both cheaper and more
  trustworthy than routing everything through a prompt.
- **A "Documentation Agent" is folded into Code Generation.** Rather than a
  separate pass, the Code Generation Agent's prompt (`prompts/code_generation.py`)
  requires an explanation per file, and updating docs is treated the same
  as updating any other file the plan touches.
- **A mock LLM provider.** `services/llm_client.py` implements the same
  `LLMClient` interface for a real Anthropic client and for a deterministic
  `MockClient` that returns schema-shaped empty data. `LLM_PROVIDER=mock`
  runs the entire pipeline — routes, DB writes, streaming, the frontend —
  without an API key, which is what most of this project's own development
  and testing ran against.

## The knowledge graph

One node per source file (not per function/class — that would make the
graph too large to usefully summarize in a prompt), with `imports` edges
resolved heuristically: `tools/import_resolver.py` handles absolute and
relative Python imports (including `from pkg import a, b` resolving to
`pkg/a.py`/`pkg/b.py` as well as `pkg/__init__.py`) and relative
TypeScript/JavaScript imports (including path aliases like `@/`). It
deliberately skips anything it can't confidently resolve — a missing edge
is far less misleading to the Planning Agent than a wrong one. Verified
against this repository's own ~60 Python files: 91 correctly-resolved
edges, with the most-imported files (`core/config.py`, `database/session.py`,
`models/mixins.py`, `core/exceptions.py`) matching what a human reading the
codebase would expect.

`services/context_builder.py` turns the graph into prompt text by ranking
files by fan-in (how many other files import them) and including their
tree-sitter-extracted symbol names — a cheap proxy for "the files that
matter most in this codebase," without embeddings or a vector store.

## Auth

Standard JWT access/refresh split (`backend/auth/`): short-lived access
tokens, longer-lived refresh tokens hashed with SHA-256 before storage
(not bcrypt — refresh tokens are already high-entropy random strings with
no need for salting, and a hashed value needs to support exact-match
lookup, which a salted bcrypt hash can't). Refresh tokens are single-use:
`services/auth_service.rotate_refresh_token` revokes the old one before
issuing a new pair, so a stolen-and-replayed refresh token fails loudly
the next time the legitimate client tries to use it, rather than staying
silently valid indefinitely. The frontend's `services/api-client.ts`
transparently retries a 401 once via the refresh flow before giving up.

## Known accepted risk

`monaco-editor` (latest, 0.56.0) depends on a `dompurify` version with
several disclosed moderate-severity advisories, and there's no newer
`monaco-editor` release yet that pulls a fixed version. `dompurify` is used
internally by Monaco for hover/markdown rendering; this project uses Monaco
purely as a read-only viewer for content fetched from its own backend
(never arbitrary user-supplied HTML), which limits real exploitability.
Tracked as a dependency to watch, not silently ignored — `npm audit` will
continue to flag it until upstream ships a fix.

## Repository layout

See the root [README](../README.md) for the directory tree. Notable
choices not visible from the tree alone:

- `backend/repositories/` is a thin data-access layer (simple query
  functions, no business logic) sitting under `backend/services/`, which
  holds the actual business logic and is what routes call directly.
- `backend/tools/` holds deterministic, LLM-free utilities (tree-sitter
  parsing, ripgrep, git operations, test running, metadata extraction) —
  anything an agent or service calls that doesn't itself make a model
  call.
- `backend/prompts/` holds one file per agent (system prompt + JSON schema
  + template), all built on a shared preamble in `prompts/base.py`.
