from fastapi import APIRouter
from pydantic import BaseModel


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
