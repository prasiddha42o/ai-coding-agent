"""Minimal git operations shared between repository import and the Git &
Session Agent.
"""
from pathlib import Path

import git


def ensure_git_repo(repo_root: Path) -> git.Repo:
    """Returns `repo_root`'s git.Repo, initializing one with a first commit
    of the current on-disk state if it isn't a git repo yet (true for
    ZIP-imported projects — GitHub-cloned ones already have `.git`).

    Called once at import time specifically so it runs *before* any agent
    writes changes to disk: otherwise a ZIP-imported repo's first-ever
    commit would fold the pristine imported state and the first session's
    changes together into one "initial snapshot" commit instead of keeping
    the session's own change history separate.
    """
    if (repo_root / ".git").exists():
        return git.Repo(repo_root)

    repo = git.Repo.init(repo_root)
    repo.git.add(A=True)
    if repo.is_dirty() or repo.untracked_files:
        repo.index.commit("chore: initial import snapshot")
    return repo
