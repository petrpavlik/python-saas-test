import uuid

import pytest
from fastapi import status
from sqlmodel import select

from app.models.organization import Organization
from app.models.organization_membership import OrganizationMembership, OrganizationRole
from app.models.profile import Profile


@pytest.mark.asyncio
async def test_create_organization_success(test_client, db):
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

    # Verify profile is linked correctly
    profile_result = await db.exec(
        select(Profile).where(Profile.email == "petr@indiepitcher.com")
    )
    profile = profile_result.first()
    assert membership.profile_id == profile.id


@pytest.mark.asyncio
async def test_create_organization_validation_error(test_client):
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
async def test_create_organization_unauthorized(test_client):
    """Test organization creation without authentication"""
    response = test_client.post("/organizations/", json={"name": "Unauthorized Org"})

    # Should return 401 Unauthorized
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
