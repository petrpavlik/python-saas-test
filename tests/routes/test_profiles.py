import os
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.database import init_db
from app.main import app
from app.service import analytics_service


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


@pytest.fixture
def mock_analytics_service():
    """Create a mock analytics service."""
    with patch.object(analytics_service, "get_analytics_service") as mock:
        service = AsyncMock()
        mock.return_value = service
        yield service


# Tests for POST /profiles/ endpoint
@pytest.mark.asyncio
async def test_create_profile_new_user(
    test_client: TestClient, mock_analytics_service
) -> None:
    """Test creating a new profile for a user that doesn't exist yet."""

    # Make the request with Authorization header
    response = test_client.post(
        "/profiles/", headers={"Authorization": "Bearer petr_token"}
    )

    # Assertions
    assert response.status_code == 200

    # Verify response data
    data = response.json()
    assert data["email"] == "petr@indiepitcher.com"

    # Verify analytics service was called
    mock_analytics_service.identify.assert_awaited_once()

    # TODO: figure out how to test that sendWelcomeEmail was dispatched in a background task
