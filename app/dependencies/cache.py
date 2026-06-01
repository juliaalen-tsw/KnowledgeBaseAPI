"""
dependencies/cache.py
---------------------
Reusable caching utilities using Redis.

Cache-aside (lazy loading) pattern:
1. Check Redis for cached data
2. If found (cache HIT) -> return cached data immediately (fast!)
3. If not found (cache MISS) -> fetch from DB, store in Redis, return data

This means the first request is slow (hits DB), but all subsequent requests
are fast (hits Redis) until the cache expires (TTL).
"""

import json
from redis.asyncio import Redis
from app.redis import get_redis_client


class CacheService:
    """
    A simple cache service wrapping Redis operations.
    
    Keys are namespaced with prefixes like "articles:", "tags:" to avoid
    collisions between different types of data.
    """

    def __init__(self, redis: Redis):
        self.redis = redis

    async def get(self, key: str) -> dict | list | None:
        """
        Get a value from cache.
        Returns the parsed Python object, or None if not found.
        """
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def set(self, key: str, value: dict | list, ttl: int = 300) -> None:
        """
        Store a value in cache with a TTL (time-to-live) in seconds.
        The key automatically expires after 'ttl' seconds.
        """
        await self.redis.setex(key, ttl, json.dumps(value))

    async def delete(self, key: str) -> None:
        """Delete a specific cache key."""
        await self.redis.delete(key)

    async def delete_pattern(self, pattern: str) -> None:
        """
        Delete all keys matching a pattern (e.g., "articles:*" deletes all article caches).
        Use carefully - this scans all keys and can be slow on large datasets.
        """
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)


async def get_cache(redis: Redis = __import__("fastapi").Depends(get_redis_client)) -> CacheService:
    """FastAPI dependency that provides a CacheService instance."""
    return CacheService(redis)


# Cache TTL constants (in seconds)
ARTICLES_TTL = 300      # 5 minutes
TAGS_TTL = 900          # 15 minutes
ARTICLE_DETAIL_TTL = 60 # 1 minute

# Cache key helpers - functions that generate consistent cache keys
def article_list_key(page: int, per_page: int, tag: str | None = None) -> str:
    return f"articles:list:{page}:{per_page}:{tag or 'all'}"

def article_detail_key(slug: str) -> str:
    return f"articles:detail:{slug}"

def tags_list_key() -> str:
    return "tags:list"

def tag_articles_key(slug: str, page: int, per_page: int) -> str:
    return f"tags:{slug}:articles:{page}:{per_page}"
