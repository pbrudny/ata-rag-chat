"""Shared pytest fixtures for backend tests."""
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.db.session import Base, get_db  # noqa: E402

SQLALCHEMY_TEST_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def _engine():
    engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db(_engine):
    """Yield a transactional DB session that is rolled back after each test."""
    connection = _engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection, autocommit=False, autoflush=False)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    """TestClient with SQLite in-memory DB."""
    from app.main import app

    def _override_db():
        yield db

    app.dependency_overrides[get_db] = _override_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()
