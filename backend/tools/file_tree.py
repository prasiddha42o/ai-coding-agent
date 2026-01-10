"""Builds the repository file-tree explorer and flat file listings."""
from pathlib import Path

from backend.schemas.file import FileTreeNode
from backend.tools.constants import BINARY_EXTENSIONS, IGNORED_DIRS, LANGUAGE_EXTENSIONS


def is_ignored(path: Path, repo_root: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.relative_to(repo_root).parts)


def is_binary_extension(path: Path) -> bool:
    return path.suffix.lower() in BINARY_EXTENSIONS


def list_files(repo_root: Path) -> list[Path]:
    """Flat list of every non-ignored file, used for indexing and search."""
    return [
        path
        for path in repo_root.rglob("*")
        if path.is_file() and not is_ignored(path, repo_root)
    ]


def build_file_tree(repo_root: Path) -> FileTreeNode:
    """Recursive tree for the workspace file explorer."""
    root = FileTreeNode(name=repo_root.name, path="", type="directory", children=[])
    nodes_by_path: dict[str, FileTreeNode] = {"": root}

    # Depth-first-safe: parents must exist in nodes_by_path before their
    # children are attached, so process shallower paths first regardless of
    # the OS-dependent order rglob() happens to yield them in.
    all_paths = sorted(
        (p for p in repo_root.rglob("*") if not is_ignored(p, repo_root)),
        key=lambda p: (len(p.relative_to(repo_root).parts), p.as_posix()),
    )

    for path in all_paths:
        relative = path.relative_to(repo_root)
        parent_key = relative.parent.as_posix() if str(relative.parent) != "." else ""
        parent = nodes_by_path.get(parent_key)
        if parent is None:
            continue

        node = FileTreeNode(
            name=path.name,
            path=relative.as_posix(),
            type="directory" if path.is_dir() else "file",
            language=LANGUAGE_EXTENSIONS.get(path.suffix) if path.is_file() else None,
            children=[] if path.is_dir() else None,
        )
        parent.children.append(node)
        if path.is_dir():
            nodes_by_path[relative.as_posix()] = node

    return root
