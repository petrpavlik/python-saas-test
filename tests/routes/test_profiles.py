from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from sqlmodel import select

from app.database import AsyncSession
from app.models.organization import Organization
from app.models.profile import Profile
from app.service.analytics_service import MockAnalyticsService


@pytest_asyncio.fixture
def mock_analytics_service_identify(mocker: MockerFixture) -> AsyncMock:
    return mocker.patch.object(
        MockAnalyticsService,
        attribute="identify",
        new_callable=AsyncMock,
    )


# Tests for POST /profiles/ endpoint
@pytest.mark.asyncio
async def test_create_and_delete_profile(
    test_client: TestClient, db: AsyncSession, mock_analytics_service_identify
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

    mock_analytics_service_identify.assert_awaited_once()

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

    # TODO: figure out how to test that sendWelcomeEmail was dispatched in a background task


@pytest.mark.asyncio
async def test_create_profile_with_invalid_token(test_client, db):
    """Test that profile creation fails with an invalid authentication token."""

    # Attempt to create a profile with an invalid token
    invalid_token_response = test_client.post(
        "/profiles/",
        headers={"Authorization": "Bearer invalid_token_that_doesnt_exist"},
    )

    # Should return 401 Unauthorized
    assert invalid_token_response.status_code == 401

    # Verify error message
    error_data = invalid_token_response.json()
    assert "detail" in error_data
    assert "Invalid token" in error_data["detail"]

    # Verify no profile was created in the database
    assert len((await db.exec(select(Profile))).all()) == 0

    # Try with malformed authorization header
    malformed_auth_response = test_client.post(
        "/profiles/", headers={"Authorization": "NotBearer some_token"}
    )
    assert malformed_auth_response.status_code == 401

    # Try with missing authorization header
    missing_auth_response = test_client.post("/profiles/")
    assert missing_auth_response.status_code == 401

    # Verify still no profiles in database
    assert len((await db.exec(select(Profile))).all()) == 0
