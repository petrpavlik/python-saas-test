import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import BaseModel, Field
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
    name: str = Field(
        min_length=1,
        max_length=100,
        description="Organization name",
        examples=["My Organization"],
    )


class OrganizationUpdate(BaseModel):
    """Schema for updating an existing organization."""

    name: str = Field(
        min_length=1,
        max_length=100,
        description="Organization name",
        examples=["My Organization"],
    )


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
        raise HTTPException(status_code=404, detail="Organization not found")

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


@router.post("/", response_model=OrganizationResponse)
async def create_organization(
    org_data: OrganizationCreate,
    profile: Profile = Depends(get_profile_from_request),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Create a new organization.

    The authenticated user will automatically be added as an admin of the new organization.
    Returns the created organization details.
    """
    # Create the new organization
    organization = Organization(
        name=org_data.name,
    )
    db.add(organization)

    # Flush to generate the ID for the organization
    await db.flush()

    # Create membership for the current user as admin
    membership = OrganizationMembership(
        profile_id=profile.id,
        organization_id=organization.id,
        role=OrganizationRole.ADMIN,
    )
    db.add(membership)

    # Commit both the organization and membership
    await db.commit()
    await db.refresh(organization)

    # Return the created organization
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


@router.patch("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: uuid.UUID,
    org_data: OrganizationUpdate,
    profile: Profile = Depends(get_profile_from_request),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Update an existing organization.

    Only admin users can update organization details.
    Returns the updated organization.
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
        # Return 404 for consistency with delete endpoint
        raise HTTPException(status_code=404, detail="Organization not found")

    # Get the organization
    org_result = await db.exec(
        select(Organization).where(Organization.id == organization_id)
    )
    organization = org_result.first()

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Update the organization with new values
    update_data = org_data.dict(exclude_unset=True)

    if not update_data:
        # No fields to update
        return OrganizationResponse(id=str(organization.id), name=organization.name)

    # Apply updates
    for key, value in update_data.items():
        setattr(organization, key, value)

    # Save changes
    await db.commit()
    await db.refresh(organization)

    # Return the updated organization
    return OrganizationResponse(id=str(organization.id), name=organization.name)
