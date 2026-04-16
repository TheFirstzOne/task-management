"""
Shared pytest fixtures for TaskFlow test suite.
Uses in-memory SQLite so tests are fast and isolated.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base


@pytest.fixture(scope="function")
def db():
    """
    Provide a fresh in-memory SQLite session per test function.
    All tables are created before each test and dropped after.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    # Register all models
    from app.models import user, team, task, history, diary, time_log, milestone  # noqa: F401
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
