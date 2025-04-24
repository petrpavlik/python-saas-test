import uuid
from datetime import datetime
from typing import TYPE_CHECKING, ClassVar

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.organization_membership import OrganizationMembership


class Organization(SQLModel, table=True):
    """Organization model with identification and status information."""

    __tablename__: ClassVar[str] = "organizations"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )
    name: str = Field()

    # Timestamp fields
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=func.now()),
    )

    memberships: list["OrganizationMembership"] = Relationship(
        back_populates="organization", cascade_delete=True
    )
