"""Repository metadata extraction: language, framework, dependency/config files.

Runs once at import time (and on refresh) to populate `Repository.metadata_json`
with enough structural information for the UI to render an overview without
needing a full indexing pass.
"""
import json
import tomllib
from pathlib import Path

from backend.schemas.repository import RepositoryMetadata

IGNORED_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", ".next", "dist",
    "build", "target", "vendor", ".pytest_cache", ".mypy_cache", "coverage",
    ".turbo", "out", ".idea", ".vscode",
}

LANGUAGE_EXTENSIONS = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript",
    ".mjs": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript",
    ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin",
    ".rb": "Ruby", ".php": "PHP", ".c": "C", ".h": "C", ".cpp": "C++",
    ".hpp": "C++", ".cs": "C#", ".swift": "Swift", ".scala": "Scala",
}

DEPENDENCY_FILES = {
    "package.json", "requirements.txt", "requirements-dev.txt", "pyproject.toml",
    "Pipfile", "go.mod", "Cargo.toml", "pom.xml", "build.gradle",
    "build.gradle.kts", "Gemfile", "composer.json",
}

CONFIG_FILES = {
    "tsconfig.json", "next.config.js", "next.config.ts", "next.config.mjs",
    "vite.config.ts", "vite.config.js", "webpack.config.js",
    "docker-compose.yml", "docker-compose.yaml", "Dockerfile",
    ".eslintrc.json", ".eslintrc.js", ".eslintrc.cjs", "alembic.ini",
    "tailwind.config.js", "tailwind.config.ts", ".env.example",
    "jest.config.js", "pytest.ini", "setup.cfg", "ruff.toml",
}

LOCKFILE_PACKAGE_MANAGER = {
    "package-lock.json": "npm", "yarn.lock": "yarn", "pnpm-lock.yaml": "pnpm",
    "poetry.lock": "poetry", "Pipfile.lock": "pipenv", "go.sum": "go modules",
    "Cargo.lock": "cargo", "composer.lock": "composer",
}

BUILD_TOOL_FILES = {
    "webpack.config.js": "Webpack", "vite.config.ts": "Vite", "vite.config.js": "Vite",
    "rollup.config.js": "Rollup", "Makefile": "Make", "build.gradle": "Gradle",
    "build.gradle.kts": "Gradle", "pom.xml": "Maven",
    "next.config.js": "Next.js", "next.config.ts": "Next.js", "next.config.mjs": "Next.js",
}

NODE_FRAMEWORK_HINTS = {
    "next": "Next.js", "react": "React", "vue": "Vue", "nuxt": "Nuxt",
    "express": "Express", "@nestjs/core": "NestJS", "fastify": "Fastify",
    "svelte": "Svelte", "gatsby": "Gatsby", "@angular/core": "Angular",
}

PYTHON_FRAMEWORK_HINTS = {
    "fastapi": "FastAPI", "django": "Django", "flask": "Flask", "celery": "Celery",
}


def _iter_files(repo_path: Path, max_depth: int = 6):
    for path in repo_path.rglob("*"):
        if path.is_dir():
            continue
        if any(part in IGNORED_DIRS for part in path.relative_to(repo_path).parts):
            continue
        if len(path.relative_to(repo_path).parts) > max_depth:
            continue
        yield path


def _detect_language(files: list[Path]) -> str | None:
    counts: dict[str, int] = {}
    for path in files:
        language = LANGUAGE_EXTENSIONS.get(path.suffix)
        if language:
            counts[language] = counts.get(language, 0) + 1
    if not counts:
        return None
    return max(counts, key=counts.get)


def _detect_node_framework(repo_path: Path) -> str | None:
    package_json = repo_path / "package.json"
    if not package_json.exists():
        return None
    try:
        data = json.loads(package_json.read_text(encoding="utf-8", errors="ignore"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
    for package_name, framework in NODE_FRAMEWORK_HINTS.items():
        if package_name in deps:
            return framework
    return None


def _detect_python_framework(repo_path: Path) -> str | None:
    text = ""
    requirements = repo_path / "requirements.txt"
    if requirements.exists():
        text += requirements.read_text(encoding="utf-8", errors="ignore").lower()

    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8", errors="ignore"))
        except tomllib.TOMLDecodeError:
            data = {}
        text += json.dumps(data).lower()

    for package_name, framework in PYTHON_FRAMEWORK_HINTS.items():
        if package_name in text:
            return framework
    return None


def _folder_hierarchy(repo_path: Path, max_depth: int = 2) -> list[str]:
    entries: list[str] = []
    for path in sorted(repo_path.rglob("*")):
        if any(part in IGNORED_DIRS for part in path.relative_to(repo_path).parts):
            continue
        depth = len(path.relative_to(repo_path).parts)
        if depth > max_depth:
            continue
        relative = path.relative_to(repo_path).as_posix()
        entries.append(f"{relative}/" if path.is_dir() else relative)
    return entries


def extract_metadata(repo_path: Path) -> RepositoryMetadata:
    files = list(_iter_files(repo_path))
    top_level_names = {f.name for f in repo_path.iterdir()} if repo_path.exists() else set()

    language = _detect_language(files)
    framework = _detect_node_framework(repo_path) or _detect_python_framework(repo_path)

    dependency_files = sorted(top_level_names & DEPENDENCY_FILES)
    config_files = sorted(top_level_names & CONFIG_FILES)

    build_tool = next(
        (label for filename, label in BUILD_TOOL_FILES.items() if filename in top_level_names),
        None,
    )
    package_manager = next(
        (label for filename, label in LOCKFILE_PACKAGE_MANAGER.items() if filename in top_level_names),
        None,
    )
    if package_manager is None and "requirements.txt" in top_level_names:
        package_manager = "pip"

    return RepositoryMetadata(
        language=language,
        framework=framework,
        build_tool=build_tool,
        package_manager=package_manager,
        dependency_files=dependency_files,
        config_files=config_files,
        folder_hierarchy=_folder_hierarchy(repo_path),
    )
