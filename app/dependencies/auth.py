"""
dependencies/auth.py
--------------------
FastAPI dependencies for authentication and authorization.

In FastAPI, a "dependency" is a function that runs before your endpoint handler.
It's like middleware, but scoped to specific endpoints instead of all requests.

Usage in a router:
    @router.get("/protected")
    async def protected_endpoint(current_user: User = Depends(get_current_user)):
        # current_user is automatically provided by FastAPI
        return {"user": current_user.email}

This is similar to Angular's @Injectable() services or React's context hooks.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User, UserRole
from app.utils.security import decode_token

# OAuth2PasswordBearer reads the JWT from the "Authorization: Bearer <token>" header
# tokenUrl points to the login endpoint (used by Swagger UI to show the login form)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency that validates the JWT and returns the current user.
    
    Steps:
    1. Extract the token from the Authorization header
    2. Decode and verify the token
    3. Look up the user in the database
    4. Return the user (or raise 401 if anything fails)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id: int | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency that checks the current user is an ADMIN.
    
    This builds on top of get_current_user - FastAPI resolves dependencies
    in the right order automatically.
    
    If the user is not an admin, a 403 Forbidden error is returned.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
