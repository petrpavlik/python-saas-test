import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, ClassVar

from sqlalchemy import Column, DateTime, String, UniqueConstraint, func
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.profile import Profile


class OrganizationRole(str, Enum):
    """Roles a user can have within an organization."""

    ADMIN = "admin"
    MEMBER = "member"
    GUEST = "guest"


class OrganizationMembership(SQLModel, table=True):
    """
    Model representing a profile's membership in an organization.
    Establishes a many-to-many relationship between profiles and organizations.
    """

    __tablename__: ClassVar[str] = "organization_memberships"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )

    # Foreign keys to link profiles and organizations
    profile_id: uuid.UUID = Field(
        foreign_key="profiles.id",
        index=True,
        ondelete="CASCADE",
    )
    organization_id: uuid.UUID = Field(
        foreign_key="organizations.id",
        index=True,
        ondelete="CASCADE",
    )

    # Role of the profile in the organization
    role: OrganizationRole = Field(
        default=OrganizationRole.MEMBER,
        sa_column=Column(String(50), nullable=False),
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=func.now()),
    )
    joined_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    profile: "Profile" = Relationship(
        back_populates="organization_memberships"  # Points to the 'organization_memberships' attribute in Profile
    )
    organization: "Organization" = Relationship(
        back_populates="memberships"  # Points to the 'memberships' attribute in Organization
    )

    class Config:
        arbitrary_types_allowed = True

    # Composite unique constraint to ensure a profile can only be a member of an org once
    __table_args__ = (
        UniqueConstraint(
            "profile_id", "organization_id", name="uix_profile_organization"
        ),
    )
