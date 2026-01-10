"""Resolves raw import statement text to in-repo file paths, for graph edges.

Deliberately heuristic rather than a full module resolver: it only needs to
recognize imports that point at files inside *this* repository so a
dependency edge can be drawn. Anything it can't confidently resolve
(external packages, dynamic imports, path aliases it doesn't recognize) is
skipped rather than guessed at — a missing edge is much less misleading to
the Planning Agent than a wrong one.
"""
import posixpath
import re

_PY_FROM_IMPORT_RE = re.compile(r"^\s*from\s+([.\w]*)\s+import\s+(.+)$")
_PY_IMPORT_RE = re.compile(r"^\s*import\s+([.\w]+)")
_JS_SPECIFIER_RE = re.compile(r"""['"]([^'"]+)['"]""")
_JS_EXTENSIONS = ("", ".ts", ".tsx", ".js", ".jsx")


def _module_to_base(module: str, current_dir: str) -> str:
    if module.startswith("."):
        level = len(module) - len(module.lstrip("."))
        remainder = module[level:]
        base_dir = current_dir
        for _ in range(level - 1):
            base_dir = posixpath.dirname(base_dir)
        parts = remainder.split(".") if remainder else []
        if parts:
            return posixpath.normpath(posixpath.join(base_dir, *parts))
        return posixpath.normpath(base_dir or ".")

    # Assumes the repo root sits on sys.path, i.e. dotted absolute imports
    # map directly onto top-level package directories.
    return module.replace(".", "/")


def _match_known(base: str, known_paths: set[str]) -> str | None:
    for candidate in (f"{base}.py", f"{base}/__init__.py"):
        normalized = posixpath.normpath(candidate)
        if normalized in known_paths:
            return normalized
    return None


def resolve_python_import(raw_import: str, current_file: str, known_paths: set[str]) -> list[str]:
    """Returns every in-repo file the statement plausibly imports from.

    `from pkg import a, b` can point at up to three files at once: the
    package's own `__init__.py`, and — very common in this kind of layered
    codebase — submodules `pkg/a.py` / `pkg/b.py` re-exported by name.
    """
    text = raw_import.strip()
    current_dir = posixpath.dirname(current_file)

    from_match = _PY_FROM_IMPORT_RE.match(text)
    if from_match:
        module, names_part = from_match.groups()
        base = _module_to_base(module, current_dir)
        targets: list[str] = []

        package_target = _match_known(base, known_paths)
        if package_target:
            targets.append(package_target)

        for name in names_part.split(","):
            name = name.strip().split(" as ")[0].strip()
            if not re.fullmatch(r"\w+", name):
                continue
            sub_target = _match_known(posixpath.normpath(posixpath.join(base, name)), known_paths)
            if sub_target and sub_target not in targets:
                targets.append(sub_target)

        return targets

    import_match = _PY_IMPORT_RE.match(text)
    if import_match:
        target = _match_known(_module_to_base(import_match.group(1), current_dir), known_paths)
        return [target] if target else []

    return []


def resolve_js_import(raw_import: str, current_file: str, known_paths: set[str]) -> str | None:
    match = _JS_SPECIFIER_RE.search(raw_import)
    if not match:
        return None
    specifier = match.group(1)
    current_dir = posixpath.dirname(current_file)

    if specifier.startswith("."):
        base = posixpath.normpath(posixpath.join(current_dir, specifier))
    elif specifier.startswith("@/"):
        # Common Next.js/TS path-alias convention mapping "@/" to the project root.
        base = specifier[2:]
    else:
        return None  # bare specifier — external package in node_modules

    for ext in _JS_EXTENSIONS:
        candidate = posixpath.normpath(f"{base}{ext}")
        if candidate in known_paths:
            return candidate
    for ext in (".ts", ".tsx", ".js", ".jsx"):
        candidate = posixpath.normpath(f"{base}/index{ext}")
        if candidate in known_paths:
            return candidate
    return None
