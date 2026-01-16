"""Pydantic schema for the Review Agent endpoint's response."""
from pydantic import BaseModel

from backend.schemas.change import ChangeRead


class ReviewResponse(BaseModel):
    summary: str
    changes: list[ChangeRead]
