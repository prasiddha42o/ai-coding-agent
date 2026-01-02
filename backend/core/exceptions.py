"""Domain-level exceptions, translated to HTTP responses in main.py."""


class AppError(Exception):
    """Base class for all application-raised errors."""

    status_code: int = 500
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.detail
        super().__init__(self.detail)


class NotFoundError(AppError):
    status_code = 404
    detail = "Resource not found"


class ConflictError(AppError):
    status_code = 409
    detail = "Resource already exists"


class UnauthorizedError(AppError):
    status_code = 401
    detail = "Not authenticated"


class ForbiddenError(AppError):
    status_code = 403
    detail = "Not permitted to perform this action"


class ValidationAppError(AppError):
    status_code = 422
    detail = "Invalid request"


class AgentExecutionError(AppError):
    status_code = 502
    detail = "Agent execution failed"
