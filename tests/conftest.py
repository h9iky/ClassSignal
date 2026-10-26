import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db, make_engine
from app.main import app
from app import models  # noqa: F401 - ensure all model tables are registered


@pytest.fixture
def client():
    test_engine = make_engine("sqlite://")
    Base.metadata.create_all(bind=test_engine)
    TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture
def base_records(client):
    subject_response = client.post("/api/v1/subjects", json={"name": "Mathematics"})
    quarter_response = client.post(
        "/api/v1/quarters", json={"school_year": "2025-2026", "number": 1}
    )
    return subject_response.json(), quarter_response.json()
