"""Pydantic schemas for the knowledge graph endpoints."""
import uuid

from pydantic import BaseModel, ConfigDict


class GraphSymbol(BaseModel):
    kind: str
    name: str
    start_line: int
    end_line: int


class GraphNodeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    file_path: str
    language: str | None
    symbols: list[GraphSymbol]


class GraphEdgeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_id: uuid.UUID
    target_id: uuid.UUID
    edge_type: str


class GraphResponse(BaseModel):
    nodes: list[GraphNodeRead]
    edges: list[GraphEdgeRead]


class RelatedFilesResponse(BaseModel):
    depends_on: list[str]
    depended_on_by: list[str]


class GraphBuildResponse(BaseModel):
    node_count: int
    edge_count: int
