"""Thin wrapper around the `rg` (ripgrep) CLI for repository-wide text search.

Invoked as an argv list (never through a shell), so an LLM-supplied search
pattern can't be used for shell/command injection.
"""
import json
import shutil
import subprocess
from pathlib import Path

from pydantic import BaseModel

from backend.core.config import get_settings
from backend.core.exceptions import AgentExecutionError


class SearchMatch(BaseModel):
    path: str
    line_number: int
    line: str


def is_available() -> bool:
    return shutil.which("rg") is not None


def search(
    repo_root: Path,
    pattern: str,
    glob: str | None = None,
    max_results: int = 200,
    case_sensitive: bool = False,
) -> list[SearchMatch]:
    if not is_available():
        raise AgentExecutionError(
            "ripgrep (rg) is not installed on this host; code search is unavailable"
        )

    settings = get_settings()
    command = ["rg", "--json", "--max-count", "50", "--", pattern]
    if not case_sensitive:
        command.insert(1, "--ignore-case")
    if glob:
        command[1:1] = ["--glob", glob]

    try:
        result = subprocess.run(
            command,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=settings.command_timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise AgentExecutionError("Search timed out") from exc

    # rg exits 1 when there are simply no matches — not an error condition.
    if result.returncode not in (0, 1):
        raise AgentExecutionError(f"ripgrep failed: {result.stderr.strip()}")

    matches: list[SearchMatch] = []
    for line in result.stdout.splitlines():
        if len(matches) >= max_results:
            break
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "match":
            continue
        data = event["data"]
        matches.append(
            SearchMatch(
                path=data["path"]["text"],
                line_number=data["line_number"],
                line=data["lines"]["text"].rstrip("\n"),
            )
        )
    return matches
