import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlmodel import select

from app.database import AsyncSession, async_session, init_db
from app.main import app
from app.models.organization import Organization
from app.models.profile import Profile


@pytest.fixture
def test_client() -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest_asyncio.fixture(autouse=True)
async def db_setup_and_teardown():
    """Setup and teardown for each test."""

    # app.dependency_overrides[get_analytics_service] = AsyncMock()

    # Setup: Initialize the database
    await init_db()

    # Teardown: Clean up the database after each test
    yield
    # Here you can add any cleanup code if needed
    # For example, you might want to drop the tables or clear data
    # await drop_all_tables()  # Example function to drop all tables
    # Delete the test.db file if it exists
    if os.path.exists("test.db"):
        os.remove("test.db")


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession]:
    """Create a fresh database session for a test."""
    async with async_session() as session:
        yield session


# @pytest.fixture
# def mock_analytics_service():
#     """Create a mock analytics service."""
#     with patch("app.service.analytics_service.get_analytics_service") as mock_analytics:
#         service = AsyncMock()
#         mock_analytics.return_value = service
#         yield service


# Tests for POST /profiles/ endpoint
@pytest.mark.asyncio
async def test_create_profile_new_user(
    test_client: TestClient, db: AsyncSession
) -> None:
    """Test creating a new profile for a user that doesn't exist yet."""

    # Check that there are no profiles in the database initially
    assert len((await db.exec(select(Profile))).all()) == 0

    # Make the request with Authorization header
    response = test_client.post(
        "/profiles/", headers={"Authorization": "Bearer petr_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "petr@indiepitcher.com"

    assert len((await db.exec(select(Profile))).all()) == 1
    assert len((await db.exec(select(Organization))).all()) == 1

    response = test_client.post(
        "/profiles/", headers={"Authorization": "Bearer petr_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "petr@indiepitcher.com"

    response = test_client.get(
        "/profiles/", headers={"Authorization": "Bearer petr_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "petr@indiepitcher.com"

    response = test_client.delete(
        "/profiles/", headers={"Authorization": "Bearer petr_token"}
    )

    assert response.status_code == 204

    assert len((await db.exec(select(Profile))).all()) == 0
    assert len((await db.exec(select(Organization))).all()) == 0

    # Verify analytics service was called
    # mock_analytics_service.identify.assert_awaited_once()

    # TODO: figure out how to test that sendWelcomeEmail was dispatched in a background task
