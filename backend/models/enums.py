"""Shared enums used across ORM models and Pydantic schemas."""
import enum


class RepositorySourceType(str, enum.Enum):
    GITHUB = "github"
    ZIP = "zip"


class RepositoryStatus(str, enum.Enum):
    PENDING = "pending"
    CLONING = "cloning"
    INDEXING = "indexing"
    READY = "ready"
    ERROR = "error"


class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class ComplexityLevel(str, enum.Enum):
    TRIVIAL = "trivial"
    MODERATE = "moderate"
    COMPLEX = "complex"


class PlanStatus(str, enum.Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class ChangeType(str, enum.Enum):
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"


class ChangeStatus(str, enum.Enum):
    PROPOSED = "proposed"
    APPLIED = "applied"
    REVERTED = "reverted"


class TestRunner(str, enum.Enum):
    PYTEST = "pytest"
    JEST = "jest"
    NPM = "npm"
    UNKNOWN = "unknown"


class TestStatus(str, enum.Enum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class CommitStatus(str, enum.Enum):
    DRAFT = "draft"
    COMMITTED = "committed"
