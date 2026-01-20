"""Tests for backend.services.auth_service: registration, login, and the
refresh-token rotation security property (a used refresh token must not be
usable a second time).
"""
import pytest

from backend.core.exceptions import ConflictError, UnauthorizedError
from backend.services import auth_service


def test_register_user_creates_account(db_session):
    user = auth_service.register_user(
        db_session, email="new.user@example.com", password="s3cure-password", full_name="New User"
    )

    assert user.id is not None
    assert user.email == "new.user@example.com"
    assert user.hashed_password != "s3cure-password"  # never store the plaintext


def test_register_user_duplicate_email_raises_conflict(db_session, test_user):
    with pytest.raises(ConflictError):
        auth_service.register_user(
            db_session, email=test_user.email, password="another-password", full_name=None
        )


def test_authenticate_user_success(db_session, test_user):
    authenticated = auth_service.authenticate_user(
        db_session, test_user.email, "correct-horse-battery-staple"
    )
    assert authenticated.id == test_user.id


def test_authenticate_user_wrong_password_raises_unauthorized(db_session, test_user):
    with pytest.raises(UnauthorizedError):
        auth_service.authenticate_user(db_session, test_user.email, "wrong-password")


def test_authenticate_user_unknown_email_raises_unauthorized(db_session):
    with pytest.raises(UnauthorizedError):
        auth_service.authenticate_user(db_session, "nobody@example.com", "whatever")


def test_issue_tokens_returns_access_and_refresh(db_session, test_user):
    tokens = auth_service.issue_tokens(db_session, test_user)
    assert tokens.access_token
    assert tokens.refresh_token
    assert tokens.token_type == "bearer"


def test_rotate_refresh_token_issues_a_new_pair(db_session, test_user):
    first = auth_service.issue_tokens(db_session, test_user)
    rotated = auth_service.rotate_refresh_token(db_session, first.refresh_token)

    assert rotated.refresh_token != first.refresh_token
    assert rotated.access_token != first.access_token


def test_rotate_refresh_token_is_single_use(db_session, test_user):
    """A refresh token that's already been rotated must be rejected on
    reuse — this is the tripwire that turns a stolen-and-reused token into
    a detectable event instead of a silent, indefinite compromise."""
    first = auth_service.issue_tokens(db_session, test_user)
    auth_service.rotate_refresh_token(db_session, first.refresh_token)

    with pytest.raises(UnauthorizedError):
        auth_service.rotate_refresh_token(db_session, first.refresh_token)


def test_revoke_refresh_token_blocks_further_rotation(db_session, test_user):
    tokens = auth_service.issue_tokens(db_session, test_user)
    auth_service.revoke_refresh_token(db_session, tokens.refresh_token)

    with pytest.raises(UnauthorizedError):
        auth_service.rotate_refresh_token(db_session, tokens.refresh_token)
