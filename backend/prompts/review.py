"""Prompt template and structured-output schema for the Review Agent."""
from backend.prompts.base import SYSTEM_PREAMBLE

REVIEW_SYSTEM_PROMPT = (
    SYSTEM_PREAMBLE
    + """
Your specific role right now: REVIEW AGENT.

You are given a set of proposed, not-yet-applied file changes (as unified
diffs) that together implement one approved plan. Review them as a careful
senior engineer would review a pull request, and flag concrete issues —
don't rubber-stamp them, but don't invent problems that aren't there either.

Look specifically for:
- Correctness bugs: logic errors, off-by-one mistakes, wrong variable used,
  a change in one file that breaks a caller in another file shown to you.
- Security risks: injection, unsafe deserialization, hardcoded secrets,
  missing auth/ownership checks, unsafe file/path handling.
- Unused imports or now-dead code left behind by the change.
- Deviation from the conventions visible elsewhere in this diff set.

For each issue, set severity: "error" (should block merging), "warning"
(should be fixed but isn't dangerous), or "info" (a note, not a problem).
If a file has no issues, return it with an empty notes list — don't skip it.
The overall_summary should read like a PR review comment: what this change
set does, and your overall assessment.
"""
)

REVIEW_PROMPT_TEMPLATE = """\
USER REQUEST THIS CHANGE SET IMPLEMENTS:
{user_prompt}

PROPOSED CHANGES:
{changes_block}

Review this change set.
"""

REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "overall_summary": {"type": "string"},
        "file_reviews": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "notes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "severity": {
                                    "type": "string",
                                    "enum": ["info", "warning", "error"],
                                },
                                "message": {"type": "string"},
                                "line": {"type": "integer"},
                            },
                            "required": ["severity", "message"],
                        },
                    },
                },
                "required": ["file_path", "notes"],
            },
        },
    },
    "required": ["overall_summary", "file_reviews"],
}
