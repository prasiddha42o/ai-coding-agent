"""Review Agent: evaluates proposed (not-yet-applied) changes for
correctness, security, and style issues, and produces a change summary.

Advisory only — it annotates each Change with review_notes rather than
blocking or auto-reverting anything. A human decides whether a flagged
issue needs a follow-up request before the changes get applied.
"""
import logging

from sqlalchemy.orm import Session

from backend.core.exceptions import AgentExecutionError, ValidationAppError
from backend.models.change import Change
from backend.models.plan import Plan
from backend.prompts.base import render
from backend.prompts.review import REVIEW_PROMPT_TEMPLATE, REVIEW_SCHEMA, REVIEW_SYSTEM_PROMPT
from backend.repositories import change_repository
from backend.services.llm_client import get_llm_client

logger = logging.getLogger(__name__)

_MAX_DIFF_CHARS = 6_000
_MAX_TOTAL_CONTEXT_CHARS = 40_000


def review_changes(db: Session, plan: Plan) -> str:
    """Reviews every Change belonging to `plan`, writes review_notes onto
    each, and returns the reviewer's overall summary."""
    changes = change_repository.list_by_plan(db, plan.id)
    if not changes:
        raise ValidationAppError("Plan has no generated changes to review yet")

    prompt = render(
        REVIEW_PROMPT_TEMPLATE,
        user_prompt=plan.user_prompt,
        changes_block=_build_changes_block(changes),
    )

    client = get_llm_client()
    try:
        result = client.complete_structured(
            system=REVIEW_SYSTEM_PROMPT,
            prompt=prompt,
            schema=REVIEW_SCHEMA,
            schema_name="review_result",
            max_tokens=4096,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Review agent failed for plan %s", plan.id)
        raise AgentExecutionError(f"Review failed: {exc}") from exc

    notes_by_file: dict[str, list[dict]] = {
        review.get("file_path"): review.get("notes", [])
        for review in result.get("file_reviews", [])
    }

    for change in changes:
        change.review_notes = notes_by_file.get(change.file_path, [])

    db.commit()
    return result.get("overall_summary", "")


def _build_changes_block(changes: list[Change]) -> str:
    parts: list[str] = []
    budget = _MAX_TOTAL_CONTEXT_CHARS
    for change in changes:
        if budget <= 0:
            parts.append(f"--- {change.file_path} ({change.change_type.value}) ---\n[omitted: context budget exceeded]")
            continue
        diff = (change.diff or "")[:_MAX_DIFF_CHARS]
        section = (
            f"--- {change.file_path} ({change.change_type.value}) ---\n"
            f"Stated intent: {change.explanation or '(none given)'}\n"
            f"{diff}"
        )
        parts.append(section)
        budget -= len(section)
    return "\n\n".join(parts)
