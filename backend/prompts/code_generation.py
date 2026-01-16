"""Prompt template and structured-output schema for the Code Generation Agent."""
from backend.prompts.base import SYSTEM_PREAMBLE

CODE_GENERATION_SYSTEM_PROMPT = (
    SYSTEM_PREAMBLE
    + """
Your specific role right now: CODE GENERATION AGENT.

An execution plan has already been approved by the user. Your job is to
produce the actual file contents needed to carry it out.

Rules specific to code generation:
- For every file you touch, return its COMPLETE new contents — not a diff,
  not a snippet, not "// ... rest unchanged". The system computes the diff
  from your full file content against what's currently on disk, so a
  partial file would corrupt the rest of it.
- For files shown to you under EXISTING FILES, preserve everything not
  relevant to this task exactly as-is: formatting, unrelated functions,
  comments, imports you don't need to change.
- Match the existing codebase's conventions (naming, import style, quote
  style, docstring style) rather than your own defaults.
- Only include files that actually need to change. Don't touch files just
  because they were mentioned in the repository context.
- change_type must be "create" for a file that doesn't exist yet, "modify"
  for an existing file, or "delete" — for "delete", content can be empty.
- explanation should be one or two sentences a developer could read to
  understand *why* this specific file changed, not a restatement of the diff.
"""
)

CODE_GENERATION_PROMPT_TEMPLATE = """\
REPOSITORY CONTEXT:
{repository_context}

USER REQUEST:
{user_prompt}

APPROVED PLAN:
{plan_summary}

Steps:
{plan_steps}

EXISTING FILES (current contents of files this plan will touch, where they \
already exist):
{existing_files}

Generate the file changes needed to carry out this plan.
"""

CODE_GENERATION_SCHEMA = {
    "type": "object",
    "properties": {
        "changes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Repo-relative path, e.g. backend/services/foo.py",
                    },
                    "change_type": {
                        "type": "string",
                        "enum": ["create", "modify", "delete"],
                    },
                    "content": {
                        "type": "string",
                        "description": "Complete new file contents. Empty for delete.",
                    },
                    "explanation": {"type": "string"},
                },
                "required": ["file_path", "change_type", "content", "explanation"],
            },
        },
    },
    "required": ["changes"],
}
