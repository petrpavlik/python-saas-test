import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import select

from app.database import AsyncSession
from app.models.organization import Organization
from app.models.organization_membership import OrganizationMembership, OrganizationRole


@pytest.mark.asyncio
async def test_create_organization_success(
    test_client: TestClient, db: AsyncSession
) -> None:
    """Test successful organization creation"""

    # First, create a profile
    profile_response = test_client.post(
        "/profiles/", headers={"Authorization": "Bearer petr_token"}
    )
    assert profile_response.status_code == status.HTTP_200_OK
    profile_data = profile_response.json()

    # Now create an organization
    org_data = {"name": "Test Organization"}
    response = test_client.post(
        "/organizations/", json=org_data, headers={"Authorization": "Bearer petr_token"}
    )

    # Check response
    assert response.status_code == status.HTTP_200_OK
    created_org = response.json()
    assert created_org["name"] == "Test Organization"
    assert "id" in created_org

    # Verify organization was created in DB
    org_result = await db.exec(
        select(Organization).where(Organization.name == "Test Organization")
    )
    org = org_result.first()
    assert org is not None
    assert org.name == "Test Organization"

    # Verify membership was created
    membership_result = await db.exec(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == uuid.UUID(created_org["id"])
        )
    )
    membership = membership_result.first()
    assert membership is not None
    assert membership.role == OrganizationRole.ADMIN


@pytest.mark.asyncio
async def test_create_organization_validation_error(test_client: TestClient):
    """Test validation errors during organization creation"""
    # Create profile first
    test_client.post("/profiles/", headers={"Authorization": "Bearer petr_token"})

    # Test with empty name
    empty_name_response = test_client.post(
        "/organizations/",
        json={"name": ""},
        headers={"Authorization": "Bearer petr_token"},
    )
    assert empty_name_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test with missing name field
    missing_name_response = test_client.post(
        "/organizations/", json={}, headers={"Authorization": "Bearer petr_token"}
    )
    assert missing_name_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test with name that's too long
    long_name = "a" * 101  # 101 characters
    long_name_response = test_client.post(
        "/organizations/",
        json={"name": long_name},
        headers={"Authorization": "Bearer petr_token"},
    )
    assert long_name_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_create_organization_unauthorized(test_client: TestClient):
    """Test organization creation without authentication"""
    response = test_client.post("/organizations/", json={"name": "Unauthorized Org"})

    # Should return 401 Unauthorized
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_organization_by_id(test_client: TestClient):
    """Test getting an organization by ID"""

    # First, create a profile
    profile_response = test_client.post(
        "/profiles/", headers={"Authorization": "Bearer petr_token"}
    )
    assert profile_response.status_code == status.HTTP_200_OK

    # Create an organization
    org_data = {"name": "Get By ID Organization"}
    create_response = test_client.post(
        "/organizations/", json=org_data, headers={"Authorization": "Bearer petr_token"}
    )
    assert create_response.status_code == status.HTTP_200_OK
    created_org = create_response.json()
    organization_id = created_org["id"]

    # Get the organization by ID
    get_response = test_client.get(
        f"/organizations/{organization_id}",
        headers={"Authorization": "Bearer petr_token"},
    )

    # Check response
    assert get_response.status_code == status.HTTP_200_OK
    fetched_org = get_response.json()
    assert fetched_org["id"] == organization_id
    assert fetched_org["name"] == "Get By ID Organization"

    # Test with non-existent organization ID
    non_existent_id = str(uuid.uuid4())
    not_found_response = test_client.get(
        f"/organizations/{non_existent_id}",
        headers={"Authorization": "Bearer petr_token"},
    )
    assert not_found_response.status_code == status.HTTP_404_NOT_FOUND

    # Test accessing organization where user is not a member
    # First create another user
    another_profile_response = test_client.post(
        "/profiles/", headers={"Authorization": "Bearer john_token"}
    )
    assert another_profile_response.status_code == status.HTTP_200_OK

    # Try to access the organization as the new user
    forbidden_response = test_client.get(
        f"/organizations/{organization_id}",
        headers={"Authorization": "Bearer john_token"},
    )
    assert forbidden_response.status_code == status.HTTP_404_NOT_FOUND
