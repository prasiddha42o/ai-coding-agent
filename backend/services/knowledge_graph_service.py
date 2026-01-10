"""Builds and queries the per-repository import/dependency knowledge graph.

Deterministic static analysis (tree-sitter + heuristic import resolution) —
no LLM call is needed to know that `auth_service.py` imports `jwt.py`. This
graph is what lets the Planning Agent answer "what else might this change
touch?" without re-reading the whole repository on every request.
"""
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from backend.models.knowledge_graph import KnowledgeGraphEdge, KnowledgeGraphNode
from backend.models.repository import Repository
from backend.tools import ast_parser
from backend.tools.constants import LANGUAGE_EXTENSIONS
from backend.tools.file_tree import list_files
from backend.tools.import_resolver import resolve_js_import, resolve_python_import

_JS_PARSER_LANGUAGES = {"javascript", "typescript", "tsx"}


def build_knowledge_graph(db: Session, repository: Repository) -> tuple[int, int]:
    """(Re)builds the full graph for a repository. Returns (node_count, edge_count)."""
    repo_root = Path(repository.local_path)
    files = list_files(repo_root)
    relative_paths = {f.relative_to(repo_root).as_posix() for f in files}

    # A from-scratch rebuild is simpler and more robust than diffing against
    # the previous graph, and this only runs on import/refresh, not per-request.
    db.query(KnowledgeGraphEdge).filter(KnowledgeGraphEdge.repository_id == repository.id).delete()
    db.query(KnowledgeGraphNode).filter(KnowledgeGraphNode.repository_id == repository.id).delete()
    db.flush()

    nodes: dict[str, KnowledgeGraphNode] = {}
    parsed_by_path: dict[str, ast_parser.ParsedFile] = {}

    for path in files:
        relative = path.relative_to(repo_root).as_posix()
        language = LANGUAGE_EXTENSIONS.get(path.suffix)
        if language is None:
            continue  # not a recognized source-code file — excluded from the component graph

        parsed = ast_parser.parse_file(path)
        symbols = (
            [
                {
                    "kind": symbol.kind,
                    "name": symbol.name,
                    "start_line": symbol.start_line,
                    "end_line": symbol.end_line,
                }
                for symbol in parsed.symbols
            ]
            if parsed
            else []
        )

        node = KnowledgeGraphNode(
            repository_id=repository.id, file_path=relative, language=language, symbols=symbols
        )
        db.add(node)
        nodes[relative] = node
        if parsed:
            parsed_by_path[relative] = parsed

    db.flush()  # assign node primary keys before edges reference them

    edge_pairs: set[tuple[uuid.UUID, uuid.UUID]] = set()
    for relative, parsed in parsed_by_path.items():
        source_node = nodes[relative]

        for raw_import in parsed.imports:
            if parsed.language == "python":
                targets = resolve_python_import(raw_import, relative, relative_paths)
            elif parsed.language in _JS_PARSER_LANGUAGES:
                resolved = resolve_js_import(raw_import, relative, relative_paths)
                targets = [resolved] if resolved else []
            else:
                targets = []

            for target_path in targets:
                target_node = nodes.get(target_path)
                if target_node is None or target_node.id == source_node.id:
                    continue
                pair = (source_node.id, target_node.id)
                if pair in edge_pairs:
                    continue
                edge_pairs.add(pair)
                db.add(
                    KnowledgeGraphEdge(
                        repository_id=repository.id,
                        source_id=source_node.id,
                        target_id=target_node.id,
                        edge_type="imports",
                    )
                )

    db.commit()
    return len(nodes), len(edge_pairs)


def get_graph(
    db: Session, repository_id: uuid.UUID
) -> tuple[list[KnowledgeGraphNode], list[KnowledgeGraphEdge]]:
    nodes = (
        db.query(KnowledgeGraphNode)
        .filter(KnowledgeGraphNode.repository_id == repository_id)
        .order_by(KnowledgeGraphNode.file_path)
        .all()
    )
    edges = (
        db.query(KnowledgeGraphEdge).filter(KnowledgeGraphEdge.repository_id == repository_id).all()
    )
    return nodes, edges


def get_related_files(db: Session, repository_id: uuid.UUID, file_path: str) -> dict[str, list[str]]:
    """Used by the Planning Agent to estimate the blast radius of a change:
    what `file_path` depends on, and what would break if `file_path` changed.
    """
    nodes, edges = get_graph(db, repository_id)
    node_by_id = {node.id: node for node in nodes}
    target_node = next((node for node in nodes if node.file_path == file_path), None)
    if target_node is None:
        return {"depends_on": [], "depended_on_by": []}

    depends_on = [
        node_by_id[edge.target_id].file_path
        for edge in edges
        if edge.source_id == target_node.id and edge.target_id in node_by_id
    ]
    depended_on_by = [
        node_by_id[edge.source_id].file_path
        for edge in edges
        if edge.target_id == target_node.id and edge.source_id in node_by_id
    ]
    return {"depends_on": depends_on, "depended_on_by": depended_on_by}
