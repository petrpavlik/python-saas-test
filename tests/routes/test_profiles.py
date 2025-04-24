import pytest
from fastapi.testclient import TestClient
from sqlmodel import select

from app.database import AsyncSession
from app.models.organization import Organization
from app.models.profile import Profile

# @pytest.fixture
# def mock_analytics_service():
#     """Create a mock analytics service."""
#     with patch("app.service.analytics_service.get_analytics_service") as mock_analytics:
#         service = AsyncMock()
#         mock_analytics.return_value = service
#         yield service


# Tests for POST /profiles/ endpoint
@pytest.mark.asyncio
async def test_create_and_delete_profile(
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
