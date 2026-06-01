"""
services/user_service.py
------------------------
Business logic for user operations.

The Service layer sits between routers (HTTP) and models (database).
Routers handle HTTP concerns (request parsing, response formatting).
Services handle business logic (rules, validation, data manipulation).

This separation makes testing easier - you can test business logic
without making HTTP requests.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.utils.security import hash_password, verify_password, create_access_token


async def register_user(data: UserCreate, db: AsyncSession) -> User:
    """
    Create a new user account.
    
    Steps:
    1. Check if email is already taken
    2. Hash the password (NEVER store plain-text passwords)
    3. Create and save the user
    """
    # Check for duplicate email
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        display_name=data.display_name,
        role=UserRole.MEMBER,
    )
    db.add(user)
    await db.flush()  # flush assigns the id without committing
    await db.refresh(user)
    return user


async def authenticate_user(email: str, password: str, db: AsyncSession) -> str:
    """
    Verify credentials and return a JWT access token.
    
    Returns the token string on success.
    Raises 401 if credentials are invalid.
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # We check both "user exists" and "password correct" in one step
    # to avoid leaking whether an email is registered (timing attack prevention)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 'sub' (subject) is a standard JWT claim - we use the user's ID
    token = create_access_token({"sub": str(user.id)})
    return token


async def update_user_profile(user: User, data: UserUpdate, db: AsyncSession) -> User:
    """Update display_name and/or bio. Only provided fields are changed."""
    if data.display_name is not None:
        user.display_name = data.display_name
    if data.bio is not None:
        user.bio = data.bio
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def get_all_users(db: AsyncSession) -> list[User]:
    """Admin-only: get list of all users."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return list(result.scalars().all())


async def update_user_role(user_id: int, role: UserRole, db: AsyncSession) -> User:
    """Admin-only: change a user's role."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user
