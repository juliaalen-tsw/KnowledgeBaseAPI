"""
redis.py
--------
Sets up the async Redis client.

Redis is used as a cache (fast temporary storage).
Think of it like a super-fast key-value store (dictionary) that lives in RAM.

We use it to store API responses so we don't have to hit the database on
every request for popular data (like the list of all articles or tags).
"""

import redis.asyncio as aioredis
from app.config import get_settings

settings = get_settings()

# Global Redis client instance.
# Created once when the app starts, reused for all requests.
redis_client: aioredis.Redis | None = None


async def get_redis_client() -> aioredis.Redis:
    """
    FastAPI dependency that provides the Redis client.
    
    Usage in a router:
        async def my_endpoint(cache: Redis = Depends(get_redis_client)):
            cached = await cache.get("some_key")
    """
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,  # Automatically decode bytes to strings
        )
    return redis_client


async def close_redis():
    """Called on app shutdown to cleanly close the Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.aclose()
        redis_client = None
