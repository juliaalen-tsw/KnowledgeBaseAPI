"""
tests/conftest.py
-----------------
pytest fixtures shared across all tests.

A 'fixture' is a function that sets up (and tears down) test dependencies.
They are declared with @pytest.fixture and injected by name into test functions.

Think of fixtures like dependency injection for tests:
  async def test_something(client, test_user):
      # 'client' and 'test_user' are automatically provided by fixtures
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

from app.main import app
from app.database import Base, get_db
from app.redis import get_redis_client
from app.models.user import User, UserRole
from app.utils.security import hash_password, create_access_token

# Use a separate test database to avoid polluting development data
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/knowledge_base_test"

# --- Database fixtures ---

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create a test database engine (once per test session)."""
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db(test_engine):
    """
    Provide a database session that rolls back after each test.
    This ensures tests don't affect each other.
    """
    TestSession = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with TestSession() as session:
        yield session
        await session.rollback()


# --- Redis fixture ---

@pytest_asyncio.fixture
async def mock_redis():
    """
    Use a real Redis instance (on db 1, separate from dev data).
    Flushes the test Redis DB before each test.
    """
    import redis.asyncio as aioredis
    r = aioredis.from_url("redis://localhost:6379/1", decode_responses=True)
    await r.flushdb()
    yield r
    await r.flushdb()
    await r.aclose()


# --- HTTP client fixture ---

@pytest_asyncio.fixture
async def client(db, mock_redis):
    """
    Provide an async HTTP test client.
    Overrides the real DB and Redis dependencies with test versions.
    """
    async def override_get_db():
        yield db

    async def override_get_redis():
        return mock_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis_client] = override_get_redis

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# --- User fixtures ---

@pytest_asyncio.fixture
async def test_user(db) -> User:
    """Create a regular MEMBER user for tests."""
    user = User(
        email="testuser@example.com",
        password_hash=hash_password("TestPass123!"),
        display_name="Test User",
        role=UserRole.MEMBER,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(db) -> User:
    """Create an ADMIN user for tests."""
    admin = User(
        email="admin@example.com",
        password_hash=hash_password("AdminPass123!"),
        display_name="Admin User",
        role=UserRole.ADMIN,
    )
    db.add(admin)
    await db.flush()
    await db.refresh(admin)
    return admin


@pytest_asyncio.fixture
def user_token(test_user) -> str:
    """JWT token for the test member user."""
    return create_access_token({"sub": str(test_user.id)})


@pytest_asyncio.fixture
def admin_token(test_admin) -> str:
    """JWT token for the test admin user."""
    return create_access_token({"sub": str(test_admin.id)})


def auth_headers(token: str) -> dict:
    """Helper to create Authorization header dict."""
    return {"Authorization": f"Bearer {token}"}
