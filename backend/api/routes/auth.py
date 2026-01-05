"""Authentication endpoints: register, login, refresh, logout, current user."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.database.session import get_db
from backend.models.user import User
from backend.schemas.auth import LoginRequest, RefreshRequest, Token
from backend.schemas.user import UserCreate, UserRead
from backend.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    return auth_service.register_user(db, payload.email, payload.password, payload.full_name)


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    user = auth_service.authenticate_user(db, payload.email, payload.password)
    return auth_service.issue_tokens(db, user)


@router.post("/refresh", response_model=Token)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> Token:
    return auth_service.rotate_refresh_token(db, payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)) -> None:
    auth_service.revoke_refresh_token(db, payload.refresh_token)


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
