"""Registration, login, and refresh-token business logic."""
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.auth.hashing import hash_password, hash_token, verify_password
from backend.auth.jwt import create_access_token, create_refresh_token, decode_token
from backend.core.exceptions import ConflictError, UnauthorizedError
from backend.models.user import RefreshToken, User
from backend.schemas.auth import Token


def register_user(db: Session, email: str, password: str, full_name: str | None) -> User:
    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        raise ConflictError("An account with this email already exists")

    user = User(email=email, hashed_password=hash_password(password), full_name=full_name)
    db.add(user)
    db.flush()
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(password, user.hashed_password):
        raise UnauthorizedError("Incorrect email or password")
    if not user.is_active:
        raise UnauthorizedError("Account is disabled")
    return user


def issue_tokens(db: Session, user: User) -> Token:
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    payload = decode_token(refresh_token, expected_type="refresh")

    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        )
    )
    db.flush()

    return Token(access_token=access_token, refresh_token=refresh_token)


def rotate_refresh_token(db: Session, refresh_token: str) -> Token:
    """Validate a refresh token, revoke it, and issue a fresh access/refresh pair.

    Single-use rotation means a stolen refresh token can be used at most once
    before the legitimate client's next refresh fails loudly, which is a
    reasonable tripwire for detecting token theft.
    """
    payload = decode_token(refresh_token, expected_type="refresh")
    token_hash = hash_token(refresh_token)

    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if stored is None or stored.revoked or stored.expires_at < datetime.now(timezone.utc):
        raise UnauthorizedError("Refresh token is invalid or has been revoked")

    user = db.get(User, uuid.UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or inactive")

    stored.revoked = True
    db.flush()

    return issue_tokens(db, user)


def revoke_refresh_token(db: Session, refresh_token: str) -> None:
    token_hash = hash_token(refresh_token)
    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if stored is not None:
        stored.revoked = True
        db.flush()
