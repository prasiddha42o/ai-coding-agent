"""Pydantic schemas for Repository."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.models.enums import RepositorySourceType, RepositoryStatus


class RepositoryCreateFromGithub(BaseModel):
    source_url: str = Field(description="Public GitHub repository URL")
    name: str | None = Field(default=None, description="Defaults to the repo name from the URL")
    branch: str | None = None


class RepositoryMetadata(BaseModel):
    """Auto-extracted metadata captured on import."""

    language: str | None = None
    framework: str | None = None
    build_tool: str | None = None
    package_manager: str | None = None
    dependency_files: list[str] = Field(default_factory=list)
    config_files: list[str] = Field(default_factory=list)
    folder_hierarchy: list[str] = Field(default_factory=list)


class RepositoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    source_type: RepositorySourceType
    source_url: str | None
    default_branch: str
    status: RepositoryStatus
    error_message: str | None
    metadata_json: dict
    last_indexed_at: datetime | None
    created_at: datetime
    updated_at: datetime
