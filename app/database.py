"""
database.py
-----------
Sets up the async database connection using SQLAlchemy 2.0.

Key concepts:
- 'engine': The connection pool to PostgreSQL (like a database driver).
- 'AsyncSession': A unit of work - all queries in one request share one session.
- 'get_db': A FastAPI dependency that provides a session per request and
  automatically closes it when the request is done (like a finally block).
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()

# The engine manages a pool of database connections.
# pool_pre_ping=True tests each connection before use (handles dropped connections).
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=(settings.APP_ENV == "development"),  # Log SQL queries in development
)

# AsyncSessionLocal is a factory (blueprint) for creating sessions.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keeps model attributes accessible after commit
)


# Base class for all SQLAlchemy models.
# Every model (User, Article, etc.) will inherit from this.
class Base(DeclarativeBase):
    pass


async def get_db():
    """
    FastAPI dependency that yields a database session.
    
    Usage in a router:
        async def my_endpoint(db: AsyncSession = Depends(get_db)):
            ...
    
    The 'async with' block ensures the session is always closed,
    even if an error occurs - equivalent to try/finally.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
