"""
routers/auth.py
---------------
Handles user registration, login, and profile management.

Each function decorated with @router.get/post/patch is an API endpoint.
FastAPI reads the function's type hints to:
  1. Validate incoming request data
  2. Generate Swagger documentation automatically
  3. Serialize the return value to JSON
"""

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate, Token
from app.services import user_service

# APIRouter is like Express Router - groups related endpoints together
# All routes in this file will be prefixed with /auth (set in main.py)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new MEMBER user account.
    
    - **email**: Must be a valid, unique email address
    - **password**: Minimum 8 characters (will be hashed before storage)
    - **display_name**: Your name as it appears in the app
    """
    return await user_service.register_user(data, db)


@router.post(
    "/login",
    response_model=Token,
    summary="Login and receive an access token",
)
async def login(
    # OAuth2PasswordRequestForm reads 'username' and 'password' from form data
    # (not JSON). This is the OAuth2 standard that Swagger UI understands.
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Login with email and password. Returns a JWT Bearer token.
    
    Use the returned token in the `Authorization: Bearer <token>` header
    for all authenticated endpoints.
    """
    token = await user_service.authenticate_user(form_data.username, form_data.password, db)
    return {"access_token": token, "token_type": "bearer"}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_me(current_user: User = Depends(get_current_user)):
    """Returns the profile of the currently authenticated user."""
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update your display name and/or bio."""
    return await user_service.update_user_profile(current_user, data, db)
