"""Pipeline orchestration: chains Code Generation -> Review -> Apply ->
Testing -> Commit for an already-approved plan, yielding a stream of
progress events so a client can show live status rather than wait on one
long blocking request.

Deliberately stops — rather than auto-committing — if the test run fails.
The whole point of running tests before committing is to give the user a
real decision point, not to have the pipeline paper over a broken build.
Each stage is also independently callable via its own REST endpoint
(POST /plans/{id}/generate, /review, /apply, ...sessions/{id}/tests,
/plans/{id}/commit) for a user who wants to inspect and intervene between
steps instead of running the whole thing at once.
"""
import json
import logging
from collections.abc import Iterator
from typing import Any

from sqlalchemy.orm import Session

from backend.agents.code_generation_agent import generate_changes
from backend.agents.git_session_agent import create_commit
from backend.agents.review_agent import review_changes
from backend.agents.testing_agent import run_session_tests
from backend.models.enums import PlanStatus, TestStatus
from backend.models.plan import Plan
from backend.schemas.change import ChangeRead
from backend.schemas.commit import CommitRead
from backend.schemas.test_run import TestRunRead
from backend.services.change_service import apply_changes

logger = logging.getLogger(__name__)


def _event(stage: str, status: str, **data: Any) -> str:
    payload = {"stage": stage, "status": status, **data}
    return f"data: {json.dumps(payload, default=str)}\n\n"


def run_pipeline(db: Session, plan: Plan) -> Iterator[str]:
    if plan.status != PlanStatus.APPROVED:
        yield _event(
            "pipeline",
            "error",
            message=f"Plan must be approved before running the pipeline (is {plan.status.value})",
        )
        return

    yield _event("code_generation", "started")
    try:
        changes = generate_changes(db, plan)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Pipeline: code generation failed for plan %s", plan.id)
        yield _event("code_generation", "error", message=str(exc))
        return
    yield _event(
        "code_generation",
        "completed",
        changes=[ChangeRead.model_validate(c).model_dump(mode="json") for c in changes],
    )

    yield _event("review", "started")
    try:
        summary = review_changes(db, plan)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Pipeline: review failed for plan %s", plan.id)
        yield _event("review", "error", message=str(exc))
        return
    yield _event("review", "completed", summary=summary)

    yield _event("apply", "started")
    try:
        applied = apply_changes(db, plan)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Pipeline: apply failed for plan %s", plan.id)
        yield _event("apply", "error", message=str(exc))
        return
    yield _event(
        "apply",
        "completed",
        changes=[ChangeRead.model_validate(c).model_dump(mode="json") for c in applied],
    )

    yield _event("testing", "started")
    try:
        test_run = run_session_tests(db, plan.session)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Pipeline: testing failed for plan %s", plan.id)
        yield _event("testing", "error", message=str(exc))
        return
    yield _event(
        "testing", "completed", test_run=TestRunRead.model_validate(test_run).model_dump(mode="json")
    )

    if test_run.status in (TestStatus.FAILED, TestStatus.ERROR):
        yield _event(
            "pipeline",
            "awaiting_decision",
            message=(
                "Tests failed — changes were applied but not committed. Review the "
                "failures, then call POST /plans/{plan_id}/commit explicitly if you "
                "still want to commit."
            ),
        )
        return

    yield _event("commit", "started")
    try:
        commit = create_commit(db, plan)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Pipeline: commit failed for plan %s", plan.id)
        yield _event("commit", "error", message=str(exc))
        return
    yield _event("commit", "completed", commit=CommitRead.model_validate(commit).model_dump(mode="json"))

    yield _event("pipeline", "completed")
