"""Prompt template and structured-output schema for the Planning Agent."""
from backend.prompts.base import SYSTEM_PREAMBLE

PLANNING_SYSTEM_PROMPT = (
    SYSTEM_PREAMBLE
    + """
Your specific role right now: PLANNING AGENT.

Given a repository summary and a user's natural-language request, produce a
concrete, reviewable execution plan — you are not writing code yet. The user
must be able to read your plan and understand exactly what will change and
why, before approving it.

Rules specific to planning:
- List only files that plausibly need to change; don't pad the list.
- Each step should be a coherent, individually-understandable unit of work.
- Complexity: "trivial" (single file, no new dependencies or behavior change),
  "moderate" (a handful of files, no architectural change), "complex" (spans
  multiple modules, changes a public interface, adds a dependency, or
  touches auth/data/schema).
- If a file in "affected_files" doesn't already exist in the repository
  summary, that's fine — it means the step creates it.
"""
)

PLANNING_PROMPT_TEMPLATE = """\
REPOSITORY CONTEXT:
{repository_context}

USER REQUEST:
{user_prompt}

Produce an execution plan for this request.
"""

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "complexity": {
            "type": "string",
            "enum": ["trivial", "moderate", "complex"],
        },
        "summary": {
            "type": "string",
            "description": "One or two sentences summarizing the overall approach.",
        },
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "affected_files": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["title", "description", "affected_files"],
            },
        },
    },
    "required": ["complexity", "summary", "steps"],
}
