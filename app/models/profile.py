import uuid
from datetime import datetime
from typing import TYPE_CHECKING, ClassVar

from pydantic import EmailStr
from sqlalchemy import JSON, Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.organization_membership import OrganizationMembership


class Profile(SQLModel, table=True):
    """User profile model with identification and status information."""

    __tablename__: ClassVar[str] = "profiles"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )
    email: EmailStr = Field(unique=True, index=True)
    name: str | None = Field(default=None, min_length=1)
    avatar_url: str | None = Field(default=None, min_length=1)

    # Timestamp fields
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=func.now()),
    )
    banned_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    last_seen_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    # Attribution data stored as JSON
    signup_attribution_data: dict[str, str] = Field(
        default_factory=dict, sa_column=Column(JSON, nullable=False)
    )

    organization_memberships: list["OrganizationMembership"] = Relationship(
        back_populates="profile", cascade_delete=True
    )

    class Config:
        arbitrary_types_allowed = True
