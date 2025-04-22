from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlmodel import select

from app.database import AsyncSession, get_db_session
from app.models.profile import Profile


class ProfileResponse(BaseModel):
    """Base schema with common profile attributes."""

    email: EmailStr
    name: str | None
    avatar_url: str | None


router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post("/", response_model=ProfileResponse)
async def create_profile(request: Request, db: AsyncSession = Depends(get_db_session)):
    """Create a new user profile."""

    debugEmail = "petr@indiepitcher.com"

    # Check if profile with this firebase_user_id already exists
    result = await db.exec(select(Profile).where(Profile.email == debugEmail))
    existing = result.first()
    if existing:
        if existing.banned_at:
            raise HTTPException(status_code=403, detail="Profile is banned")
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

    profile = Profile(
        email=debugEmail, name="Petr", signup_attribution_data=headers_dict
    )

    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(db: AsyncSession = Depends(get_db_session)):
    """Get profile"""

    debugEmail = "petr@indiepitcher.com"

    result = await db.exec(select(Profile).where(Profile.email == debugEmail))
    existing = result.first()
    if existing:
        if existing.banned_at:
            raise HTTPException(status_code=403, detail="Profile is banned")
        return existing

    raise HTTPException(status_code=404, detail="Profile not found")


# More endpoints for update, delete, etc.
