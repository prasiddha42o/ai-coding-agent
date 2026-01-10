"""Knowledge graph endpoints: fetch the full graph, related files, and rebuild."""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.database.session import get_db
from backend.models.user import User
from backend.schemas.knowledge_graph import (
    GraphBuildResponse,
    GraphResponse,
    RelatedFilesResponse,
)
from backend.services import knowledge_graph_service, repository_service

router = APIRouter(prefix="/repositories/{repository_id}/graph", tags=["knowledge-graph"])


@router.get("", response_model=GraphResponse)
def get_graph(
    repository_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GraphResponse:
    repository_service.get_owned_repository(db, repository_id, current_user.id)
    nodes, edges = knowledge_graph_service.get_graph(db, repository_id)
    return GraphResponse(nodes=nodes, edges=edges)


@router.get("/related", response_model=RelatedFilesResponse)
def get_related_files(
    repository_id: uuid.UUID,
    file_path: str = Query(..., description="Repo-relative path, e.g. backend/main.py"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RelatedFilesResponse:
    repository_service.get_owned_repository(db, repository_id, current_user.id)
    related = knowledge_graph_service.get_related_files(db, repository_id, file_path)
    return RelatedFilesResponse(**related)


@router.post("/rebuild", response_model=GraphBuildResponse)
def rebuild_graph(
    repository_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GraphBuildResponse:
    repository = repository_service.get_owned_repository(db, repository_id, current_user.id)
    node_count, edge_count = knowledge_graph_service.build_knowledge_graph(db, repository)
    return GraphBuildResponse(node_count=node_count, edge_count=edge_count)
