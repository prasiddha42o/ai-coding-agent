"""Constants shared across repository analysis tools."""

IGNORED_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", ".next", "dist",
    "build", "target", "vendor", ".pytest_cache", ".mypy_cache", "coverage",
    ".turbo", "out", ".idea", ".vscode",
}

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp", ".bmp", ".pdf",
    ".zip", ".tar", ".gz", ".7z", ".exe", ".dll", ".so", ".dylib",
    ".woff", ".woff2", ".ttf", ".eot", ".mp3", ".mp4", ".mov", ".wasm",
    ".pyc", ".class", ".jar",
}

LANGUAGE_EXTENSIONS = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript",
    ".mjs": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript",
    ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin",
    ".rb": "Ruby", ".php": "PHP", ".c": "C", ".h": "C", ".cpp": "C++",
    ".hpp": "C++", ".cs": "C#", ".swift": "Swift", ".scala": "Scala",
}
