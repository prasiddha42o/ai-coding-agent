"""Code Generation Agent: turns an approved Plan into concrete, reviewable
file changes.

Deliberately does NOT touch the working directory — it produces Change rows
(status=PROPOSED) with a diff computed locally (difflib) from the model's
full rewritten file content against what's actually on disk today. Writing
those changes to disk is a separate, explicit step
(services/change_service.apply_changes), so a user reviews real diffs — not
just plan prose — before anything on the filesystem moves.
"""
import difflib
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from backend.core.exceptions import AgentExecutionError, ValidationAppError
from backend.models.change import Change
from backend.models.enums import ChangeStatus, ChangeType, PlanStatus
from backend.models.plan import Plan
from backend.prompts.base import render
from backend.prompts.code_generation import (
    CODE_GENERATION_PROMPT_TEMPLATE,
    CODE_GENERATION_SCHEMA,
    CODE_GENERATION_SYSTEM_PROMPT,
)
from backend.services.context_builder import build_repository_summary
from backend.services.llm_client import get_llm_client

logger = logging.getLogger(__name__)

_MAX_FILE_CHARS_IN_PROMPT = 8_000
_MAX_TOTAL_CONTEXT_CHARS = 40_000


def _read_files_for_prompt(repo_root: Path, file_paths: list[str]) -> dict[str, str]:
    """Truncated file contents for prompt context only — never used for the
    stored diff, which always reads the file fresh and untruncated."""
    contents: dict[str, str] = {}
    budget = _MAX_TOTAL_CONTEXT_CHARS
    for file_path in file_paths:
        if budget <= 0:
            break
        target = _resolve_safe_path(repo_root, file_path)
        if target is None or not target.is_file():
            continue
        try:
            text = target.read_text(encoding="utf-8", errors="ignore")[:_MAX_FILE_CHARS_IN_PROMPT]
        except OSError:
            continue
        contents[file_path] = text
        budget -= len(text)
    return contents


def _resolve_safe_path(repo_root: Path, file_path: str) -> Path | None:
    repo_root = repo_root.resolve()
    target = (repo_root / file_path).resolve()
    if not target.is_relative_to(repo_root):
        return None
    return target


def generate_changes(db: Session, plan: Plan) -> list[Change]:
    if plan.status != PlanStatus.APPROVED:
        raise ValidationAppError(
            f"Plan must be approved before generating code (is {plan.status.value})"
        )

    repository = plan.session.repository
    repo_root = Path(repository.local_path)

    plan.status = PlanStatus.EXECUTING
    db.commit()

    repository_context = build_repository_summary(db, repository)
    existing_files = _read_files_for_prompt(repo_root, plan.affected_files)

    plan_steps = "\n".join(
        f"- {step.get('title')}: {step.get('description')} "
        f"(files: {', '.join(step.get('affected_files', [])) or 'unspecified'})"
        for step in plan.steps
    )
    existing_files_block = (
        "\n\n".join(f"--- {path} ---\n{content}" for path, content in existing_files.items())
        or "(none of the affected files exist yet — this plan creates new files)"
    )

    prompt = render(
        CODE_GENERATION_PROMPT_TEMPLATE,
        repository_context=repository_context,
        user_prompt=plan.user_prompt,
        plan_summary=plan.summary or "",
        plan_steps=plan_steps,
        existing_files=existing_files_block,
    )

    client = get_llm_client()
    try:
        result = client.complete_structured(
            system=CODE_GENERATION_SYSTEM_PROMPT,
            prompt=prompt,
            schema=CODE_GENERATION_SCHEMA,
            schema_name="code_changes",
            max_tokens=8192,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Code generation failed for plan %s", plan.id)
        plan.status = PlanStatus.FAILED
        db.commit()
        raise AgentExecutionError(f"Code generation failed: {exc}") from exc

    changes: list[Change] = []
    for raw_change in result.get("changes", []):
        file_path = (raw_change.get("file_path") or "").strip().lstrip("/")
        if not file_path:
            continue

        target = _resolve_safe_path(repo_root, file_path)
        if target is None:
            logger.warning("Skipping unsafe path from code generation: %s", file_path)
            continue

        existed = target.is_file()
        new_content = raw_change.get("content", "")
        llm_change_type = raw_change.get("change_type")

        if llm_change_type == "delete":
            if not existed:
                continue  # nothing to delete
            change_type = ChangeType.DELETE
            new_content = None
        else:
            change_type = ChangeType.MODIFY if existed else ChangeType.CREATE

        original_content = target.read_text(encoding="utf-8", errors="ignore") if existed else None
        diff = _compute_diff(file_path, original_content, new_content)

        change = Change(
            plan_id=plan.id,
            file_path=file_path,
            change_type=change_type,
            status=ChangeStatus.PROPOSED,
            original_content=original_content,
            new_content=new_content,
            diff=diff,
            explanation=raw_change.get("explanation"),
        )
        db.add(change)
        changes.append(change)

    db.commit()
    for change in changes:
        db.refresh(change)
    return changes


def _compute_diff(file_path: str, original: str | None, new: str | None) -> str:
    original_lines = (original or "").splitlines(keepends=True)
    new_lines = (new or "").splitlines(keepends=True)
    diff_lines = difflib.unified_diff(
        original_lines, new_lines, fromfile=f"a/{file_path}", tofile=f"b/{file_path}"
    )
    return "".join(diff_lines)
