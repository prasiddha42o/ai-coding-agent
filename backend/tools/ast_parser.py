"""AST-based symbol extraction via tree-sitter.

Feeds the knowledge graph builder with per-file structure (top-level
functions/classes and import statements) without needing to fully compile
or execute the target repository. Unsupported languages degrade gracefully
to `None` rather than raising — the file still gets a graph node from its
metadata, it just has no extracted symbols.
"""
from dataclasses import dataclass, field
from pathlib import Path

import tree_sitter_languages

EXTENSION_LANGUAGE = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".go": "go",
    ".java": "java",
    ".rs": "rust",
}

_QUERIES = {
    "python": """
        (function_definition name: (identifier) @function.name) @function.def
        (class_definition name: (identifier) @class.name) @class.def
        (import_statement) @import
        (import_from_statement) @import
    """,
    "javascript": """
        (function_declaration name: (identifier) @function.name) @function.def
        (class_declaration name: (identifier) @class.name) @class.def
        (import_statement) @import
    """,
    "typescript": """
        (function_declaration name: (identifier) @function.name) @function.def
        (class_declaration name: (type_identifier) @class.name) @class.def
        (import_statement) @import
    """,
    "tsx": """
        (function_declaration name: (identifier) @function.name) @function.def
        (class_declaration name: (type_identifier) @class.name) @class.def
        (import_statement) @import
    """,
    "go": """
        (function_declaration name: (identifier) @function.name) @function.def
        (method_declaration name: (field_identifier) @function.name) @function.def
        (import_declaration) @import
    """,
    "java": """
        (class_declaration name: (identifier) @class.name) @class.def
        (method_declaration name: (identifier) @function.name) @function.def
        (import_declaration) @import
    """,
    "rust": """
        (function_item name: (identifier) @function.name) @function.def
        (struct_item name: (type_identifier) @class.name) @class.def
        (use_declaration) @import
    """,
}

_parser_cache: dict[str, object] = {}
_query_cache: dict[str, object] = {}


@dataclass
class Symbol:
    kind: str  # "function" | "class"
    name: str
    start_line: int
    end_line: int


@dataclass
class ParsedFile:
    language: str
    symbols: list[Symbol] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)


def supported_language(path: Path) -> str | None:
    language = EXTENSION_LANGUAGE.get(path.suffix)
    return language if language in _QUERIES else None


def _get_parser(language: str):
    if language not in _parser_cache:
        _parser_cache[language] = tree_sitter_languages.get_parser(language)
    return _parser_cache[language]


def _get_query(language: str):
    if language not in _query_cache:
        lang_obj = tree_sitter_languages.get_language(language)
        _query_cache[language] = lang_obj.query(_QUERIES[language])
    return _query_cache[language]


def parse_file(path: Path, max_bytes: int = 1_000_000) -> ParsedFile | None:
    language = supported_language(path)
    if language is None:
        return None

    try:
        source = path.read_bytes()
    except OSError:
        return None
    if len(source) > max_bytes:
        return None

    tree = _get_parser(language).parse(source)
    captures = _get_query(language).captures(tree.root_node)

    pending_defs: dict[int, Symbol] = {}
    imports: list[str] = []

    for node, tag in captures:
        if tag in ("function.def", "class.def"):
            pending_defs[node.id] = Symbol(
                kind="function" if tag == "function.def" else "class",
                name="",
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
            )
        elif tag in ("function.name", "class.name"):
            parent = node.parent
            if parent is not None and parent.id in pending_defs:
                pending_defs[parent.id].name = node.text.decode("utf-8", errors="replace")
        elif tag == "import":
            imports.append(node.text.decode("utf-8", errors="replace").strip())

    symbols = sorted(
        (symbol for symbol in pending_defs.values() if symbol.name),
        key=lambda symbol: symbol.start_line,
    )

    return ParsedFile(language=language, symbols=symbols, imports=imports)
