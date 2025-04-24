from fastapi import Depends, HTTPException, Request
from sqlmodel import select

from app.database import AsyncSession, get_db_session
from app.models.firebase_auth_user import FirebaseAuthUser
from app.models.profile import Profile


def get_firebase_user_from_request(request: Request) -> FirebaseAuthUser:
    if not hasattr(request.state, "firebase_user"):
        raise HTTPException(
            status_code=401, detail="Firebase user not found in request state"
        )

    firebase_user = request.state.firebase_user
    if not isinstance(firebase_user, FirebaseAuthUser):
        raise HTTPException(
            status_code=401, detail="Invalid firebase user in request state"
        )
    return firebase_user


async def get_profile_from_request(
    request: Request, db: AsyncSession = Depends(get_db_session)
) -> Profile:
    """Get the profile from the request state."""
    firebaseUser = get_firebase_user_from_request(request)
    result = await db.exec(select(Profile).where(Profile.email == firebaseUser.email))
    existing = result.first()
    if existing:
        if existing.banned_at:
            raise HTTPException(status_code=403, detail="Profile is banned")
        return existing
    raise HTTPException(status_code=404, detail="Profile not found")
