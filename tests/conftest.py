import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.db.dependencies import get_db
from app.main import app

# Import all models so they are registered with Base.metadata.
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.task_history import TaskHistory


if not settings.TEST_DATABASE_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL is not configured in .env"
    )


test_engine = create_engine(
    settings.TEST_DATABASE_URL,
    pool_pre_ping=True,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Create all tables before the test suite and
    remove them after the test suite finishes.
    """

    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def clean_database():
    """
    Clean all tables before every test.
    """

    db = TestingSessionLocal()

    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())

        db.commit()

    finally:
        db.close()


@pytest.fixture()
def db_session():
    """
    Provide a SQLAlchemy session connected to the test database.
    """

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client():
    """
    FastAPI TestClient connected to the test database.
    """

    def override_get_db():
        db = TestingSessionLocal()

        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def registered_user(client):
    """
    Create a standard user for a test.
    """

    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "Test@1234",
    }

    response = client.post(
        "/auth/register",
        json=payload,
    )

    assert response.status_code == 201

    return payload


@pytest.fixture()
def access_token(client, registered_user):
    """
    Login the registered user and return the access token.
    """

    response = client.post(
        "/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )

    assert response.status_code == 200

    return response.json()["data"]["access_token"]


@pytest.fixture()
def auth_headers(access_token):
    """
    Authorization header for authenticated API requests.
    """

    return {
        "Authorization": f"Bearer {access_token}"
    }


@pytest.fixture()
def registered_admin(client):
    """
    Create a user and promote it to admin.
    """

    payload = {
        "username": "adminuser",
        "email": "admin@example.com",
        "password": "Admin@1234",
    }

    response = client.post(
        "/auth/register",
        json=payload,
    )

    assert response.status_code == 201

    # Use the test database directly to promote the user.
    db = TestingSessionLocal()

    try:
        user = (
            db.query(User)
            .filter(User.email == payload["email"])
            .first()
        )

        assert user is not None

        user.role = "admin"

        db.commit()

    finally:
        db.close()

    return payload


@pytest.fixture()
def admin_access_token(client, registered_admin):
    """
    Login the admin user and return the access token.
    """

    response = client.post(
        "/auth/login",
        json={
            "email": registered_admin["email"],
            "password": registered_admin["password"],
        },
    )

    assert response.status_code == 200

    return response.json()["data"]["access_token"]


@pytest.fixture()
def admin_auth_headers(admin_access_token):
    """
    Authorization header for an admin user.
    """

    return {
        "Authorization": f"Bearer {admin_access_token}"
    }
