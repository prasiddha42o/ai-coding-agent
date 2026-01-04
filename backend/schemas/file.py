"""Pydantic schemas for File and file-tree responses."""
import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict


class FileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    path: str
    language: str | None
    size_bytes: int
    is_binary: bool


class FileTreeNode(BaseModel):
    """A recursive node used to render the repository file explorer."""

    name: str
    path: str
    type: Literal["file", "directory"]
    language: str | None = None
    children: list["FileTreeNode"] | None = None


class FileContent(BaseModel):
    path: str
    content: str
    language: str | None = None
