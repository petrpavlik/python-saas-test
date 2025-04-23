import pytest
from fastapi.testclient import TestClient

from app.database import init_db
from app.main import app


@pytest.fixture
def test_client() -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


# Mock service dependencies
# @pytest.fixture
# def mock_services():
#     """Mock analytics and email services."""
#     with patch("app.routes.profiles.get_analytics_service") as mock_analytics:
#         with patch("app.routes.profiles.get_email_service") as mock_email:
#             with patch("app.routes.profiles.sendWelcomeEmail") as mock_welcome:
#                 mock_analytics_service = AsyncMock()
#                 mock_analytics.return_value = mock_analytics_service

#                 mock_email_service = AsyncMock()
#                 mock_email.return_value = mock_email_service

#                 yield mock_analytics_service, mock_email_service, mock_welcome


# Tests for POST /profiles/ endpoint
@pytest.mark.asyncio
async def test_create_profile_new_user(test_client: TestClient) -> None:
    """Test creating a new profile for a user that doesn't exist yet."""
    # analytics_service, _, _ = mock_services

    await init_db()

    # Make the request with Authorization header
    response = test_client.post(
        "/profiles/", headers={"Authorization": "Bearer petr_token"}
    )

    # Assertions
    assert response.status_code == 200

    # Verify response data
    data = response.json()
    assert data["email"] == "petr@indiepitcher.comx"
    # assert data["name"] == mock_firebase_user.name
    # assert data["avatar_url"] == mock_firebase_user.avatar_url

    # Verify analytics service was called
    # analytics_service.identify.assert_awaited_once()
