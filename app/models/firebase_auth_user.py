from pydantic import BaseModel, EmailStr, Field, HttpUrl


class FirebaseAuthUser(BaseModel):
    """
    Represents a user extracted from a JWT token.
    Contains the essential user information needed for authentication and authorization.
    """

    email: EmailStr
    user_id: str  # Firebase user ID
    name: str | None = None
    avatar_url: HttpUrl | None = Field(default=None, min_length=1)

    class Config:
        """Pydantic configuration."""

        frozen = True  # Makes the model immutable once created for security
