"""Shared pytest fixtures: an isolated DB session per test (real Postgres,
wrapped in a transaction that's rolled back afterwards) and a FastAPI
TestClient wired to use it instead of the app's normal engine.

Requires a running Postgres reachable at $DATABASE_URL (defaults to the
docker-compose service — see docker/docker-compose.yml). Run
`alembic upgrade head` once against that database before running tests.
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend.auth.hashing import hash_password
from backend.core.config import get_settings
from backend.database.session import get_db
from backend.main import app
from backend.models.user import User

settings = get_settings()
_engine = create_engine(settings.database_url, future=True)
_SessionFactory = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)


@pytest.fixture
def db_session():
    """A session bound to a SAVEPOINT, not a plain transaction.

    Several services (repository_service, plan_service, ...) call
    `db.commit()` internally as part of normal request handling. A plain
    `connection.begin()` + `transaction.rollback()` fixture would break the
    moment a test touches one of those: an inner commit ends the outer
    transaction early, so the teardown rollback has nothing left to undo.
    Binding the session to a SAVEPOINT and restarting it after every commit
    (SQLAlchemy's documented pattern for this) keeps every commit the code
    under test issues fully contained and reversible.
    """
    connection = _engine.connect()
    outer_transaction = connection.begin()
    session = _SessionFactory(bind=connection)

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    try:
        yield session
    finally:
        session.close()
        outer_transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    user = User(
        email=f"{uuid.uuid4().hex}@example.com",
        hashed_password=hash_password("correct-horse-battery-staple"),
        full_name="Test User",
    )
    db_session.add(user)
    db_session.flush()
    return user
