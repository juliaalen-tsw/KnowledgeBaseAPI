"""
seed.py
-------
Populates the database with sample data for development/testing.

Run with: docker compose exec api python -m app.seed

This creates:
- 1 admin user
- 2 member users
- 5 tags
- 6 articles (mix of published and draft)
- Comments on some articles
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.article import Article, ArticleStatus
from app.models.tag import Tag
from app.models.comment import Comment
from app.utils.security import hash_password
from app.utils.slug import generate_slug


async def seed():
    print("🌱 Seeding database with sample data...")

    async with AsyncSessionLocal() as db:
        # ---- USERS ----
        admin = User(
            email="admin@example.com",
            password_hash=hash_password("Admin1234!"),
            display_name="Admin User",
            role=UserRole.ADMIN,
            bio="Platform administrator",
        )
        alice = User(
            email="alice@example.com",
            password_hash=hash_password("Alice1234!"),
            display_name="Alice Chen",
            role=UserRole.MEMBER,
            bio="Senior backend developer",
        )
        bob = User(
            email="bob@example.com",
            password_hash=hash_password("Bob12345!"),
            display_name="Bob Smith",
            role=UserRole.MEMBER,
            bio="DevOps engineer",
        )
        db.add_all([admin, alice, bob])
        await db.flush()

        # ---- TAGS ----
        tags_data = [
            ("python", "python"),
            ("fastapi", "fastapi"),
            ("docker", "docker"),
            ("postgresql", "postgresql"),
            ("redis", "redis"),
        ]
        tags = [Tag(name=n, slug=s) for n, s in tags_data]
        db.add_all(tags)
        await db.flush()

        python_tag, fastapi_tag, docker_tag, pg_tag, redis_tag = tags

        # ---- ARTICLES ----
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        article1 = Article(
            title="Getting Started with FastAPI",
            slug="getting-started-with-fastapi",
            content=(
                "FastAPI is a modern, fast web framework for building APIs with Python 3.12+.\n\n"
                "## Installation\n\n```bash\npip install fastapi uvicorn\n```\n\n"
                "## Your First App\n\n```python\nfrom fastapi import FastAPI\napp = FastAPI()\n\n"
                "@app.get('/')\nasync def root():\n    return {'message': 'Hello World'}\n```\n\n"
                "Run with: `uvicorn main:app --reload`"
            ),
            summary="A beginner's guide to building APIs with FastAPI.",
            author_id=alice.id,
            status=ArticleStatus.PUBLISHED,
            published_at=now,
            tags=[fastapi_tag, python_tag],
        )
        article2 = Article(
            title="SQLAlchemy 2.0 with Async Sessions",
            slug="sqlalchemy-2-async-sessions",
            content=(
                "SQLAlchemy 2.0 brings a cleaner async API. Here's how to use it with FastAPI...\n\n"
                "## Setup\n\nInstall: `pip install sqlalchemy asyncpg`\n\n"
                "## Async Engine\n\n```python\nfrom sqlalchemy.ext.asyncio import create_async_engine\n"
                "engine = create_async_engine('postgresql+asyncpg://...')\n```"
            ),
            summary="Learn how to use SQLAlchemy 2.0 async sessions with FastAPI.",
            author_id=alice.id,
            status=ArticleStatus.PUBLISHED,
            published_at=now,
            tags=[python_tag, pg_tag],
        )
        article3 = Article(
            title="Docker Compose for FastAPI",
            slug="docker-compose-fastapi",
            content=(
                "Running FastAPI, PostgreSQL, and Redis together with Docker Compose is straightforward.\n\n"
                "## docker-compose.yml\n\nDefine three services: api, postgres, redis.\n\n"
                "The api service depends on postgres and redis being healthy before starting."
            ),
            summary="Containerize your FastAPI application with Docker Compose.",
            author_id=bob.id,
            status=ArticleStatus.PUBLISHED,
            published_at=now,
            tags=[docker_tag, fastapi_tag],
        )
        article4 = Article(
            title="Redis Caching Strategies",
            slug="redis-caching-strategies",
            content=(
                "Redis is an in-memory data store perfect for caching API responses.\n\n"
                "## Cache-Aside Pattern\n\n1. Check Redis\n2. Cache HIT: return cached data\n"
                "3. Cache MISS: fetch from DB, store in Redis\n\n"
                "## TTL Management\n\nAlways set a TTL to avoid stale data forever."
            ),
            summary="Practical Redis caching patterns for production APIs.",
            author_id=bob.id,
            status=ArticleStatus.PUBLISHED,
            published_at=now,
            is_featured=True,
            tags=[redis_tag, python_tag],
        )
        article5 = Article(
            title="JWT Authentication in FastAPI",
            slug="jwt-auth-fastapi",
            content=(
                "Implementing secure JWT authentication in FastAPI using python-jose and passlib.\n\n"
                "## Setup\n\n```bash\npip install python-jose[cryptography] passlib[bcrypt]\n```\n\n"
                "## Password Hashing\n\nAlways use bcrypt with a cost factor of at least 12."
            ),
            summary="Complete guide to JWT auth with FastAPI dependencies.",
            author_id=alice.id,
            status=ArticleStatus.PUBLISHED,
            published_at=now,
            tags=[fastapi_tag, python_tag],
        )
        article6 = Article(
            title="Draft: Advanced PostgreSQL Patterns",
            slug="draft-advanced-postgresql-patterns",
            content="Work in progress... Coming soon.",
            author_id=alice.id,
            status=ArticleStatus.DRAFT,
        )

        db.add_all([article1, article2, article3, article4, article5, article6])
        await db.flush()

        # ---- COMMENTS ----
        comment1 = Comment(
            content="Great article! This really helped me get started.",
            article_id=article1.id,
            author_id=bob.id,
        )
        comment2 = Comment(
            content="Thank you! Let me know if you have any questions.",
            article_id=article1.id,
            author_id=alice.id,
        )
        db.add_all([comment1, comment2])
        await db.flush()

        # Add a reply to comment1
        reply = Comment(
            content="Really appreciate the examples - they made it click for me!",
            article_id=article1.id,
            author_id=admin.id,
            parent_id=comment1.id,
        )
        db.add(reply)

        await db.commit()

    print("✅ Seed complete!")
    print("   Admin:  admin@example.com / Admin1234!")
    print("   Alice:  alice@example.com / Alice1234!")
    print("   Bob:    bob@example.com   / Bob12345!")
    print("   Articles: 5 published, 1 draft")
    print("   Visit: http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(seed())
