from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.database import AsyncSession, async_session, init_db, nuke_db
from app.main import app


@pytest.fixture
def test_client() -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest_asyncio.fixture(autouse=True, scope="function", loop_scope="function")
async def db_setup_and_teardown():
    """Setup and teardown for each test."""
    # Setup: Initialize the database
    await nuke_db()
    await init_db()

    yield


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession]:
    """Create a fresh database session for a test."""
    async with async_session() as session:
        yield session


@pytest.fixture
def mock_analytics_service():
    """Create a mock analytics service."""
    with patch("app.service.analytics_service.get_analytics_service") as mock_analytics:
        service = AsyncMock()
        mock_analytics.return_value = service
        yield service
