"""
schemas/user.py
---------------
Pydantic schemas define the "shape" of data coming IN (requests)
and going OUT (responses) from the API.

These are DIFFERENT from SQLAlchemy models:
- SQLAlchemy models = database table structure
- Pydantic schemas = API request/response structure

Why separate? Because you often don't want to expose all DB fields
(like password_hash) in API responses.
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole


class UserCreate(BaseModel):
    """Schema for POST /auth/register - data the user sends to register."""
    email: EmailStr  # Pydantic automatically validates email format
    password: str = Field(min_length=8, description="Minimum 8 characters")
    display_name: str = Field(min_length=1, max_length=100)


class UserUpdate(BaseModel):
    """Schema for PATCH /auth/me - only these fields can be updated."""
    display_name: str | None = Field(default=None, max_length=100)
    bio: str | None = None


class UserResponse(BaseModel):
    """Schema for API responses that include user data. Never exposes password_hash."""
    id: int
    email: str
    display_name: str
    role: UserRole
    bio: str | None
    created_at: datetime

    # model_config tells Pydantic to read data from SQLAlchemy model attributes
    # (not just plain dictionaries). This is required when returning DB objects.
    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Response schema for POST /auth/login."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data stored inside the JWT token payload."""
    user_id: int | None = None
