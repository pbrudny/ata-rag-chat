import os

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

import app.models.chat_query  # noqa: F401
import app.models.chunk  # noqa: F401
import app.models.crawl_run  # noqa: F401
import app.models.page  # noqa: F401
from app.db.session import Base

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://postgres@/ata_rag_chat_test?host=/tmp/ata_pg_test_sock&port=5544",
)


@pytest.fixture(scope="session")
def pg_engine():
    engine = create_engine(TEST_DATABASE_URL)
    with engine.connect() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        connection.commit()
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def pg_db(pg_engine):
    """Yield a Postgres session joined to an external transaction that is
    rolled back after each test, even if the code under test calls
    session.commit() — commits only end a savepoint, which is immediately
    restarted, so the outer transaction (and therefore test isolation) is
    never actually committed. See SQLAlchemy's "Joining a Session into an
    External Transaction" recipe."""
    connection = pg_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection, autocommit=False, autoflush=False)
    session = session_factory()

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, trans):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
