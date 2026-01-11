"""Builds a compact, LLM-ready summary of a repository from its metadata and
knowledge graph — grounds the Planning/Code-Generation/Review agents in the
actual project instead of a generic one, without dumping the whole codebase
into the prompt.
"""
from sqlalchemy.orm import Session

from backend.models.repository import Repository
from backend.services import knowledge_graph_service


def build_repository_summary(db: Session, repository: Repository, max_files: int = 40) -> str:
    metadata = repository.metadata_json or {}
    lines = [
        f"Repository: {repository.name}",
        f"Primary language: {metadata.get('language') or 'unknown'}",
        f"Framework: {metadata.get('framework') or 'none detected'}",
        f"Build tool: {metadata.get('build_tool') or 'none detected'}",
        f"Package manager: {metadata.get('package_manager') or 'none detected'}",
    ]

    dependency_files = metadata.get("dependency_files") or []
    if dependency_files:
        lines.append(f"Dependency files: {', '.join(dependency_files)}")

    folder_hierarchy = metadata.get("folder_hierarchy") or []
    if folder_hierarchy:
        lines.append("Top-level structure:")
        lines.extend(f"  {entry}" for entry in folder_hierarchy[:60])

    nodes, edges = knowledge_graph_service.get_graph(db, repository.id)
    if nodes:
        fan_in: dict = {}
        for edge in edges:
            fan_in[edge.target_id] = fan_in.get(edge.target_id, 0) + 1
        ranked = sorted(nodes, key=lambda node: fan_in.get(node.id, 0), reverse=True)[:max_files]

        lines.append("")
        lines.append(
            f"Key files (of {len(nodes)} indexed, ranked by how many other files depend on them):"
        )
        for node in ranked:
            symbol_names = ", ".join(symbol["name"] for symbol in node.symbols[:8])
            suffix = f" — defines: {symbol_names}" if symbol_names else ""
            lines.append(f"  {node.file_path} ({node.language}){suffix}")

    return "\n".join(lines)
