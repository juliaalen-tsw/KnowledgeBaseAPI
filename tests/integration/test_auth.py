"""
tests/integration/test_auth.py
--------------------------------
Integration tests for authentication endpoints.

Integration tests make real HTTP requests (via the test client) to test
the full stack: HTTP -> router -> service -> database.

Naming convention: test functions MUST start with 'test_' for pytest to find them.
"""

import pytest
from httpx import AsyncClient
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """A new user can register with valid data."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "display_name": "New User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["display_name"] == "New User"
    assert data["role"] == "MEMBER"
    assert "password_hash" not in data  # Never expose password hash


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user):
    """Registering with an existing email returns 400."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": test_user.email,  # Already exists
            "password": "SecurePass123!",
            "display_name": "Duplicate",
        },
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user):
    """Valid credentials return a JWT token."""
    response = await client.post(
        "/api/v1/auth/login",
        data={  # Login uses form data, not JSON
            "username": test_user.email,
            "password": "TestPass123!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user):
    """Wrong password returns 401."""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "WrongPassword!"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient, test_user, user_token):
    """Authenticated user can get their profile."""
    response = await client.get(
        "/api/v1/auth/me",
        headers=auth_headers(user_token),
    )
    assert response.status_code == 200
    assert response.json()["email"] == test_user.email


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    """No token returns 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_profile(client: AsyncClient, user_token):
    """User can update their display name and bio."""
    response = await client.patch(
        "/api/v1/auth/me",
        json={"display_name": "Updated Name", "bio": "My new bio"},
        headers=auth_headers(user_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "Updated Name"
    assert data["bio"] == "My new bio"
