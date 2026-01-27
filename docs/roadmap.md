# Roadmap

## Implemented

- **Auth**: registration, login, JWT access/refresh with single-use
  refresh-token rotation, `/auth/me`.
- **Repository import**: public GitHub URL (shallow clone) or ZIP upload,
  with zip-slip/zip-bomb protection and automatic language/framework/
  dependency-file detection.
- **Knowledge graph**: per-file nodes with tree-sitter-extracted symbols,
  heuristically-resolved import edges, rebuildable on demand.
- **Full agent pipeline**: Planning → Code Generation → Review → Apply →
  Testing → Git & Session, each independently callable and chainable via a
  streamed end-to-end run.
- **Testing Agent**: real pytest and Jest execution with pass/fail counts
  and stack traces (verified against real fixture projects, not mocked).
- **Git integration**: real commits with Conventional Commit messages and
  PR-style summaries; ZIP-imported repos get a real git history from
  import time onward.
- **Frontend**: dashboard, Monaco-based workspace with a live file tree,
  a chat-style agent panel with plan approval and a live pipeline
  timeline, a diff viewer, and full session history (past plans, changes,
  test runs, commits).
- **Docker Compose** for the full stack; **GitHub Actions CI** running the
  backend test suite against a real Postgres service container and the
  frontend build/lint.

## Explicitly out of scope for this implementation

Carried over from the PRD's own "Future Enhancements" list — genuinely
future work, not gaps in what's described above:

- GitHub OAuth for private repositories (public repos and ZIP upload only,
  for now).
- Automated dependency installation before running a repo's own test suite
  (the Testing Agent runs whatever's already available in its environment
  — see `docs/architecture.md`'s note on why auto-installing arbitrary
  third-party packages on every test run is its own trust boundary that
  this project doesn't cross without a sandboxing story first).
- Multi-agent collaborative editing, autonomous bug detection/fixing,
  automated PR code review of *external* PRs, standalone security
  vulnerability scanning, a dependency-upgrade engine, an interactive
  architecture visualizer beyond the raw knowledge-graph endpoints, voice
  commands, live multi-user collaboration, a VS Code extension / CLI,
  Kubernetes manifests.
- A second LLM provider. `services/llm_client.py` is written against a
  provider-agnostic interface specifically so this is a contained addition
  (implement one more `LLMClient` subclass) rather than a rewrite — but
  only Anthropic and the offline mock are implemented today.
