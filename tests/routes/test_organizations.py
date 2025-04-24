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
async def test_create_organization_validation_error(test_client: TestClient) -> None:
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
async def test_create_organization_unauthorized(test_client: TestClient) -> None:
    """Test organization creation without authentication"""
    response = test_client.post("/organizations/", json={"name": "Unauthorized Org"})

    # Should return 401 Unauthorized
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_organization_by_id(test_client: TestClient) -> None:
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


@pytest.mark.asyncio
async def test_get_paginated_organizations(
    test_client: TestClient, db: AsyncSession
) -> None:
    """Test getting a paginated list of organizations"""

    # Create a profile
    profile_response = test_client.post(
        "/profiles/", headers={"Authorization": "Bearer petr_token"}
    )
    assert profile_response.status_code == status.HTTP_200_OK

    # Create multiple organizations
    org_names = [f"Organization {i}" for i in range(1, 6)]  # 5 organizations
    created_org_ids = []

    for name in org_names:
        response = test_client.post(
            "/organizations/",
            json={"name": name},
            headers={"Authorization": "Bearer petr_token"},
        )
        assert response.status_code == status.HTTP_200_OK
        created_org_ids.append(response.json()["id"])

    # Test default pagination (first page)
    response = test_client.get(
        "/organizations/", headers={"Authorization": "Bearer petr_token"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Check pagination structure
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert "pages" in data

    # Verify content (6 organizations total - 5 created + 1 from profile creation)
    assert data["total"] == 6
    assert len(data["items"]) == 6  # Should match the size parameter

    # Test second page with custom page size
    response = test_client.get(
        "/organizations/?page=2&size=2",  # 2 items per page, page 2
        headers={"Authorization": "Bearer petr_token"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Verify second page has correct parameters
    assert data["page"] == 2
    assert data["size"] == 2
    assert len(data["items"]) == 2

    # Test with invalid page parameters
    response = test_client.get(
        "/organizations/?page=0&size=2",  # Page 0 is invalid
        headers={"Authorization": "Bearer petr_token"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test with another user who isn't a member of these organizations
    # Create another profile
    test_client.post("/profiles/", headers={"Authorization": "Bearer john_token"})

    # New user creates their own organization
    test_client.post(
        "/organizations/",
        json={"name": "John's Organization"},
        headers={"Authorization": "Bearer john_token"},
    )

    # Get organizations for the new user
    response = test_client.get(
        "/organizations/", headers={"Authorization": "Bearer john_token"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # New user should only see their own organizations (1 + 1 from profile creation)
    assert data["total"] == 2

    # Verify organization names are correct
    org_names = [org["name"] for org in data["items"]]
    assert "John's Organization" in org_names

    # Ensure they can't see other user's organizations
    for name in [f"Organization {i}" for i in range(1, 6)]:
        assert name not in org_names
