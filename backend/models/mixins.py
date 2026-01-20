"""Shared declarative mixins for ORM models."""
import uuid
from datetime import datetime, timezone
from typing import TypeVar

from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

_E = TypeVar("_E")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def enum_column(enum_cls: type[_E], **kwargs) -> SAEnum:
    """SAEnum configured to store the Enum's `.value` (e.g. "github") rather
    than SQLAlchemy's default of the member `.name` (e.g. "GITHUB").

    Every enum in this project is a `str, Enum` mixin specifically so its
    `.value` is the lowercase wire format shared with Pydantic schemas and
    the Postgres enum types created in the Alembic migrations — without
    `values_callable`, SQLAlchemy inserts `.name` instead, which doesn't
    exist in those Postgres enum types and fails on every insert.
    """
    return SAEnum(enum_cls, values_callable=lambda obj: [member.value for member in obj], **kwargs)


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
