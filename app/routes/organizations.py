import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import BaseModel
from sqlmodel import select

from app.database import AsyncSession, get_db_session
from app.models.organization import Organization
from app.models.organization_membership import OrganizationMembership, OrganizationRole
from app.models.profile import Profile
from app.routes.di import get_profile_from_request


class OrganizationResponse(BaseModel):
    """Base schema with common organization attributes."""

    name: str
    id: str


class OrganizationCreate(BaseModel):
    """Schema for creating a new organization."""

    name: str


class OrganizationUpdate(BaseModel):
    """Schema for updating an existing organization."""

    name: str | None = None


router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("/", response_model=Page[OrganizationResponse])
async def get_organizations(
    profile: Profile = Depends(get_profile_from_request),
    db: AsyncSession = Depends(get_db_session),
    x="aaa",
):
    """Get organizations the current user is a member of."""
    query = (
        select(Organization)
        .join(OrganizationMembership)
        .where(OrganizationMembership.profile_id == profile.id)
        .order_by("created_at")
    )

    return await paginate(db, query)


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: uuid.UUID,
    profile: Profile = Depends(get_profile_from_request),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get a specific organization by its ID.

    Only returns the organization if the authenticated user is a member of it.
    """
    # Check if the user is a member of this organization
    membership_result = await db.exec(
        select(OrganizationMembership).where(
            OrganizationMembership.profile_id == profile.id,
            OrganizationMembership.organization_id == organization_id,
        )
    )
    membership = membership_result.first()

    if not membership:
        raise HTTPException(
            status_code=403, detail="You don't have access to this organization"
        )

    # Get the organization
    result = await db.exec(
        # could be eager loaded in the query above, I was just getting some bullshit typing errors when trying to do that.
        # https://github.com/fastapi/sqlmodel/discussions/871
        select(Organization).where(Organization.id == organization_id)
    )
    organization = result.first()

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    return OrganizationResponse(id=str(organization.id), name=organization.name)


@router.delete("/{organization_id}", status_code=204)
async def delete_organization(
    organization_id: uuid.UUID,
    profile: Profile = Depends(get_profile_from_request),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Delete an organization.

    Only admin users can delete an organization.
    Returns 204 No Content on successful deletion.
    """
    # Check if the user is an admin of this organization
    membership_result = await db.exec(
        select(OrganizationMembership).where(
            OrganizationMembership.profile_id == profile.id,
            OrganizationMembership.organization_id == organization_id,
        )
    )
    membership = membership_result.first()

    if not membership or membership.role != OrganizationRole.ADMIN:
        # just return 404 when don't have access to the organization
        raise HTTPException(status_code=404, detail="Organization not found")

    # Get the organization
    org_result = await db.exec(
        # this could be eager loaded above, but I was getting some bullshit typing errors when trying to do that.
        # https://github.com/fastapi/sqlmodel/discussions/871
        select(Organization).where(Organization.id == organization_id)
    )
    organization = org_result.first()

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Delete the organization
    # Note: memberships will be deleted automatically by cascade
    await db.delete(organization)
    await db.commit()

    # Return no content on successful deletion
    return None
