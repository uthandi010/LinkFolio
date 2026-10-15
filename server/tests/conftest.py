import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.deps import get_db
from app.main import app
from app.ratelimit import limiter


@pytest.fixture(autouse=True)
def _no_rate_limit():
    # Individual tests flip limiter.enabled back on to exercise limiting.
    limiter.reset()
    limiter.enabled = False
    yield
    limiter.reset()


@pytest.fixture()
def db_session():
    # A single shared in-memory SQLite connection for the lifetime of the
    # test, so every request the TestClient makes sees the same data.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def register_user(client):
    def _register(name="Test User", email="test@example.com", username="testuser", password="Password123!"):
        response = client.post(
            "/api/auth/register",
            json={"name": name, "email": email, "username": username, "password": password},
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _register


@pytest.fixture()
def auth_header():
    def _header(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    return _header
