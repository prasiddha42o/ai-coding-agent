"""Applies proposed Changes to the actual repository working directory.

This is the one point where the pipeline touches the filesystem — kept as
its own explicit step (rather than folded into code generation) so a user
reviews real diffs, and the Review Agent's notes on them, before anything
moves. Path safety is re-checked here independently of the Code Generation
Agent's own check: this function must never trust that a Change row loaded
from the database is safe just because it was safe when it was created.
"""
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from backend.core.exceptions import ValidationAppError
from backend.models.change import Change
from backend.models.enums import ChangeStatus, ChangeType, PlanStatus
from backend.models.plan import Plan
from backend.repositories import change_repository

logger = logging.getLogger(__name__)


def _resolve_safe_path(repo_root: Path, file_path: str) -> Path:
    repo_root = repo_root.resolve()
    target = (repo_root / file_path).resolve()
    if not target.is_relative_to(repo_root):
        raise ValidationAppError(f"Refusing to apply change outside the repository: {file_path}")
    return target


def apply_changes(db: Session, plan: Plan) -> list[Change]:
    if plan.status != PlanStatus.EXECUTING:
        raise ValidationAppError(
            f"Plan changes can only be applied while executing (is {plan.status.value})"
        )

    changes = change_repository.list_by_plan(db, plan.id)
    proposed = [change for change in changes if change.status == ChangeStatus.PROPOSED]
    if not proposed:
        raise ValidationAppError("No proposed changes to apply for this plan")

    repo_root = Path(plan.session.repository.local_path)

    for change in proposed:
        target = _resolve_safe_path(repo_root, change.file_path)

        if change.change_type == ChangeType.DELETE:
            target.unlink(missing_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(change.new_content or "", encoding="utf-8")

        change.status = ChangeStatus.APPLIED

    db.commit()
    for change in proposed:
        db.refresh(change)
    return proposed
