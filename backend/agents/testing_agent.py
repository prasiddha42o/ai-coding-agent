"""Testing Agent: detects and runs the repository's test suite against the
current working directory, and persists the result.

Deterministic — no LLM call. Unlike Planning/Code Generation/Review, "did
the tests pass" isn't a judgment call to hand to a model; it's the actual
output of actual tooling. This only produces a meaningful signal once a
plan's changes have been applied to disk (see services/change_service.py).
"""
from pathlib import Path

from sqlalchemy.orm import Session

from backend.models.session import CodingSession
from backend.models.test_run import TestRun
from backend.tools.test_runner import detect_runner, run_tests


def run_session_tests(db: Session, session: CodingSession) -> TestRun:
    repository = session.repository
    repo_root = Path(repository.local_path)

    runner = detect_runner(repo_root, repository.metadata_json)
    result = run_tests(repo_root, runner)

    test_run = TestRun(
        session_id=session.id,
        runner=result.runner,
        command=result.command,
        status=result.status,
        passed_count=result.passed_count,
        failed_count=result.failed_count,
        skipped_count=result.skipped_count,
        duration_ms=result.duration_ms,
        output=result.output,
        stack_traces=[
            {"test_name": entry.test_name, "message": entry.message, "trace": entry.trace}
            for entry in result.stack_traces
        ],
    )
    db.add(test_run)
    db.commit()
    db.refresh(test_run)
    return test_run
