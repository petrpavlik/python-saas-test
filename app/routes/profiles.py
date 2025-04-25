from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlmodel import select

from app.database import AsyncSession, get_db_session
from app.models.firebase_auth_user import FirebaseAuthUser
from app.models.organization import Organization
from app.models.organization_membership import OrganizationMembership, OrganizationRole
from app.models.profile import Profile
from app.routes.di import get_firebase_user_from_request, get_profile_from_request
from app.service.analytics_service import (
    AnalyticsServiceProtocol,
    get_analytics_service,
)
from app.service.email_service import EmailServiceProtocol, get_email_service
from app.use_cases.use_cases import sendWelcomeEmail


class ProfileResponse(BaseModel):
    """Base schema with common profile attributes."""

    email: EmailStr
    name: str | None
    avatar_url: str | None


router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post("/", response_model=ProfileResponse)
async def create_profile(
    request: Request,
    background_tasks: BackgroundTasks,
    firebaseUser: FirebaseAuthUser = Depends(get_firebase_user_from_request),
    db: AsyncSession = Depends(get_db_session),
    analyticsService: AnalyticsServiceProtocol = Depends(get_analytics_service),
    emailService: EmailServiceProtocol = Depends(get_email_service),
):
    """Create a new user profile."""

    # Check if profile with this firebase_user_id already exists
    result = await db.exec(select(Profile).where(Profile.email == firebaseUser.email))
    existing = result.first()
    if existing:
        if existing.banned_at:
            raise HTTPException(status_code=403, detail="Profile is banned")
        await analyticsService.identify(profile=existing)
        return existing

    # Create new profile

    # Filter out multiple sensitive headers
    sensitive_headers = {"authorization", "cookie"}
    headers_dict = {
        k: v for k, v in request.headers.items() if k.lower() not in sensitive_headers
    }
    # Add the client's IP address to the headers dictionary
    if request.client:
        client_ip = request.client.host
        headers_dict["client_ip"] = client_ip

    # Start a transaction by beginning a nested transaction
    # async with db.begin():
    # Create the profile
    profile = Profile(
        email=firebaseUser.email,
        signup_attribution_data=headers_dict,
        name=firebaseUser.name,
        avatar_url=str(firebaseUser.avatar_url) if firebaseUser.avatar_url else None,
    )
    db.add(profile)
    await db.flush()
    await db.refresh(profile)

    # # Create a default organization for this new profile
    org_name = (
        f"{profile.name}'s Organization" if profile.name else "Default Organization"
    )

    organization = Organization(
        name=org_name,
    )
    db.add(organization)
    await db.flush()
    await db.refresh(organization)

    # # Create membership linking the profile to the organization
    membership = OrganizationMembership(
        profile_id=profile.id,
        organization_id=organization.id,
        role=OrganizationRole.ADMIN,  # Make them the owner of their org
    )
    db.add(membership)
    await db.flush()
    await db.refresh(membership)

    # Now all the above operations have been committed as a single transaction

    await db.commit()

    await analyticsService.identify(profile=profile)

    # # Track organization creation event
    # analyticsService.track(
    #     event="organization_created",
    #     properties={
    #         "organization_id": str(organization.id),
    #         "organization_name": org_name,
    #     },
    # )

    background_tasks.add_task(sendWelcomeEmail, profile, emailService)

    return profile


@router.get("/", response_model=ProfileResponse)
async def get_profile(profile: Profile = Depends(get_profile_from_request)):
    """Get profile"""
    return profile


@router.delete("/", status_code=204)
async def delete_profile(
    profile: Profile = Depends(get_profile_from_request),
    db: AsyncSession = Depends(get_db_session),
    analyticsService: AnalyticsServiceProtocol = Depends(get_analytics_service),
) -> None:
    """
    Delete the user's profile.

    Returns:
        204 No Content on successful deletion
    """
    # Track the deletion event in analytics
    analyticsService.track(
        event="profile_deleted",
        properties={"profile_id": str(profile.email)},
    )

    await db.refresh(
        # looks like sqlmodel cannot can only load immediate relationships :(
        profile,
        ["organization_memberships"],
    )
    for membership in profile.organization_memberships:
        organization = await db.get(Organization, membership.organization_id)
        if organization is None:
            raise HTTPException(
                status_code=500,
                detail=f"Organization with id {membership.organization_id} not found",
            )
        await db.refresh(
            organization, ["memberships"]
        )  # can this be a part of the get?
        other_admin_memberships = [
            m
            for m in organization.memberships
            if m.role == OrganizationRole.ADMIN and m.profile_id != profile.id
        ]
        if not other_admin_memberships:
            await db.delete(organization)

    # Delete the profile
    await db.delete(profile)

    await db.commit()
