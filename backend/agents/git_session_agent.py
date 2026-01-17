"""Git & Session Agent: turns a plan's applied changes into a real git
commit with a conventional commit message and PR-style summary, and closes
out the session.

The only agent that touches git directly — Planning/Code Generation/Review/
Testing never call git themselves, so this is the single place commit
behavior lives and can be audited.
"""
import logging
from datetime import datetime, timezone
from pathlib import Path

import git
from sqlalchemy.orm import Session

from backend.core.exceptions import AgentExecutionError, ValidationAppError
from backend.models.change import Change
from backend.models.commit import Commit
from backend.models.enums import ChangeStatus, CommitStatus, PlanStatus, SessionStatus
from backend.models.plan import Plan
from backend.prompts.base import render
from backend.prompts.git_session import COMMIT_PROMPT_TEMPLATE, COMMIT_SCHEMA, COMMIT_SYSTEM_PROMPT
from backend.repositories import change_repository
from backend.services.llm_client import get_llm_client
from backend.tools.git_ops import ensure_git_repo

logger = logging.getLogger(__name__)

_MAX_DIFF_CHARS = 20_000


def create_commit(db: Session, plan: Plan) -> Commit:
    if plan.status != PlanStatus.EXECUTING:
        raise ValidationAppError(f"Plan must be executing to commit (is {plan.status.value})")

    changes = change_repository.list_by_plan(db, plan.id)
    applied = [change for change in changes if change.status == ChangeStatus.APPLIED]
    if not applied:
        raise ValidationAppError("No applied changes to commit for this plan")

    session = plan.session
    repository = session.repository
    repo_root = Path(repository.local_path)

    prompt = render(
        COMMIT_PROMPT_TEMPLATE,
        user_prompt=plan.user_prompt,
        plan_summary=plan.summary or "",
        changed_files=_summarize_files(applied),
        diff=_aggregate_diff(applied),
    )

    client = get_llm_client()
    try:
        result = client.complete_structured(
            system=COMMIT_SYSTEM_PROMPT,
            prompt=prompt,
            schema=COMMIT_SCHEMA,
            schema_name="commit_message",
            max_tokens=1024,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Git & Session agent failed to draft a commit message for plan %s", plan.id)
        raise AgentExecutionError(f"Commit message generation failed: {exc}") from exc

    commit_message = result.get("commit_message") or f"chore: apply changes for session {session.id}"
    pr_summary = result.get("pr_summary", "")

    repo = ensure_git_repo(repo_root)
    repo.git.add(A=True)
    if not repo.is_dirty() and not repo.untracked_files:
        raise ValidationAppError("Nothing to commit — working tree matches HEAD")

    try:
        commit_result = repo.index.commit(commit_message)
    except git.GitCommandError as exc:
        logger.exception("git commit failed for plan %s", plan.id)
        raise AgentExecutionError(f"git commit failed: {exc}") from exc

    commit = Commit(
        session_id=session.id,
        message=commit_message,
        diff_summary=pr_summary or _aggregate_diff(applied)[:5000],
        branch=repository.default_branch,
        sha=commit_result.hexsha,
        status=CommitStatus.COMMITTED,
    )
    db.add(commit)

    plan.status = PlanStatus.COMPLETED
    session.status = SessionStatus.COMPLETED
    session.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(commit)
    return commit


def _summarize_files(changes: list[Change]) -> str:
    return "\n".join(f"- {change.change_type.value}: {change.file_path}" for change in changes)


def _aggregate_diff(changes: list[Change]) -> str:
    parts: list[str] = []
    budget = _MAX_DIFF_CHARS
    for change in changes:
        if budget <= 0:
            break
        diff = change.diff or ""
        parts.append(diff)
        budget -= len(diff)
    return "\n".join(parts)
