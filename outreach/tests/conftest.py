"""Shared pytest fixtures for the outreach test suite."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Force in-memory SQLite for all tests
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("DRY_RUN", "true")
os.environ.setdefault("SEND_ENABLED", "false")


@pytest.fixture()
def engine():
    from een_outreach.config import reset_settings
    from een_outreach.models import Base

    reset_settings()
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture()
def db(engine):
    with Session(engine) as session:
        yield session
        session.rollback()
