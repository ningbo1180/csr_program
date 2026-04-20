"""
Pytest fixtures for CSR GenAI backend tests
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import get_db
from app.models.models import Base, Project, Chapter, Document, ActionLog

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

from sqlalchemy.pool import StaticPool
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden database dependency"""
    from main import app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def sample_project(client):
    """Create a sample project and return its data"""
    response = client.post("/api/projects/", json={
        "name": "Test-Project-001",
        "description": "A test project for CSR generation",
        "language": "zh-CN"
    })
    assert response.status_code == 200
    return response.json()


@pytest.fixture(scope="function")
def sample_chapter(client, sample_project):
    """Create a sample chapter and return its data"""
    response = client.post(f"/api/chapters/{sample_project['id']}", json={
        "title": "研究设计讨论",
        "number": "10.2",
        "content": "",
        "order": 0
    })
    assert response.status_code == 200
    return response.json()
