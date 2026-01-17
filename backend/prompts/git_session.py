"""Prompt template and structured-output schema for the Git & Session Agent."""
from backend.prompts.base import SYSTEM_PREAMBLE

COMMIT_SYSTEM_PROMPT = (
    SYSTEM_PREAMBLE
    + """
Your specific role right now: GIT & SESSION AGENT.

Given the original request, the approved plan, and the actual diff that was
generated, produce:
1. A commit message following the Conventional Commits format (e.g.
   "feat(auth): implement JWT authentication", "fix(parser): handle empty
   input", "refactor(db): extract query builder"). Use type(scope): subject
   — subject in imperative mood, no trailing period, under 72 characters.
   Choose scope from the affected module/directory.
2. A short PR-style summary in markdown: what changed and why, as a
   reviewer would want to read it — a couple of sentences plus a bullet
   list of the key changes, not a restatement of the raw diff.
"""
)

COMMIT_PROMPT_TEMPLATE = """\
USER REQUEST:
{user_prompt}

PLAN SUMMARY:
{plan_summary}

CHANGED FILES:
{changed_files}

DIFF:
{diff}

Produce the commit message and PR summary for this change set.
"""

COMMIT_SCHEMA = {
    "type": "object",
    "properties": {
        "commit_message": {"type": "string"},
        "pr_summary": {"type": "string"},
    },
    "required": ["commit_message", "pr_summary"],
}
