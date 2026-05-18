from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from swift_rag.database import Base, get_session
from swift_rag.main import app
from swift_rag.rag import create_document


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def document_factory(db_session):
    def create(name: str, text: str):
        document = create_document(db_session, name, text.encode("utf-8"))
        db_session.commit()
        return document

    return create


@pytest.fixture()
def client(db_session):
    def override_session():
        yield db_session

    app.dependency_overrides[get_session] = override_session
    try:
        from fastapi.testclient import TestClient

        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
