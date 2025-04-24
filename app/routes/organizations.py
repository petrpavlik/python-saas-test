from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import BaseModel
from sqlmodel import select

from app.database import AsyncSession, get_db_session
from app.models.organization import Organization
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
):
    """Get organizations"""
    return await paginate(db, select(Organization).order_by("created_at"))
