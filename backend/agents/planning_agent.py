"""Planning Agent: turns a natural-language request into a reviewable,
itemized execution plan.

Produces a Plan row in PENDING_APPROVAL status. Per the project's core
philosophy — explicit approval before any modification — nothing
downstream (code generation) runs until a human approves it; see
services/plan_service.py for the approve/reject transition.
"""
import logging

from sqlalchemy.orm import Session

from backend.core.exceptions import AgentExecutionError
from backend.models.enums import ComplexityLevel, PlanStatus
from backend.models.plan import Plan
from backend.models.session import CodingSession
from backend.prompts.base import render
from backend.prompts.planning import PLAN_SCHEMA, PLANNING_PROMPT_TEMPLATE, PLANNING_SYSTEM_PROMPT
from backend.services.context_builder import build_repository_summary
from backend.services.llm_client import get_llm_client

logger = logging.getLogger(__name__)


_TITLE_MAX_LENGTH = 80


def create_plan(db: Session, session: CodingSession, user_prompt: str) -> Plan:
    if session.title is None:
        # First prompt in the session doubles as its title, so the session
        # history list (frontend) shows something more useful than a
        # timestamp — truncated since prompts can run much longer than a
        # one-line label should.
        session.title = (
            user_prompt if len(user_prompt) <= _TITLE_MAX_LENGTH else user_prompt[: _TITLE_MAX_LENGTH - 1] + "…"
        )

    repository_context = build_repository_summary(db, session.repository)
    prompt = render(
        PLANNING_PROMPT_TEMPLATE, repository_context=repository_context, user_prompt=user_prompt
    )

    client = get_llm_client()
    try:
        result = client.complete_structured(
            system=PLANNING_SYSTEM_PROMPT,
            prompt=prompt,
            schema=PLAN_SCHEMA,
            schema_name="execution_plan",
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Planning agent failed for session %s", session.id)
        raise AgentExecutionError(f"Planning failed: {exc}") from exc

    steps = result.get("steps") or []
    affected_files = sorted({path for step in steps for path in step.get("affected_files", [])})

    try:
        complexity = ComplexityLevel(result.get("complexity", "moderate"))
    except ValueError:
        complexity = ComplexityLevel.MODERATE

    plan = Plan(
        session_id=session.id,
        user_prompt=user_prompt,
        summary=result.get("summary"),
        status=PlanStatus.PENDING_APPROVAL,
        complexity=complexity,
        steps=steps,
        affected_files=affected_files,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan
