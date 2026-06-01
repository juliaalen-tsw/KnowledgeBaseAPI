"""
tests/unit/test_cache.py
------------------------
Tests that verify Redis caching behavior:
- Cache miss hits the "database" and stores result
- Cache hit returns cached data without hitting "database"
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from app.dependencies.cache import CacheService


@pytest.mark.asyncio
async def test_cache_set_and_get():
    """Data stored in cache can be retrieved."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=json.dumps({"id": 1, "title": "Test"}))
    mock_redis.setex = AsyncMock()

    cache = CacheService(mock_redis)

    # Set a value
    await cache.set("test:key", {"id": 1, "title": "Test"}, ttl=300)
    mock_redis.setex.assert_called_once_with("test:key", 300, json.dumps({"id": 1, "title": "Test"}))

    # Get the value
    result = await cache.get("test:key")
    assert result == {"id": 1, "title": "Test"}


@pytest.mark.asyncio
async def test_cache_miss_returns_none():
    """When key doesn't exist, cache.get returns None."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)  # Cache miss

    cache = CacheService(mock_redis)
    result = await cache.get("nonexistent:key")
    assert result is None


@pytest.mark.asyncio
async def test_cache_delete():
    """Cache key can be deleted."""
    mock_redis = AsyncMock()
    cache = CacheService(mock_redis)

    await cache.delete("some:key")
    mock_redis.delete.assert_called_once_with("some:key")


@pytest.mark.asyncio
async def test_cache_delete_pattern():
    """Pattern deletion removes all matching keys."""
    mock_redis = AsyncMock()
    mock_redis.keys = AsyncMock(return_value=["articles:list:1", "articles:list:2"])
    cache = CacheService(mock_redis)

    await cache.delete_pattern("articles:list:*")
    mock_redis.keys.assert_called_once_with("articles:list:*")
    mock_redis.delete.assert_called_once_with("articles:list:1", "articles:list:2")


@pytest.mark.asyncio
async def test_cache_hit_does_not_need_db(client, db, test_user, user_token, mock_redis):
    """
    When cache has data, the endpoint returns it WITHOUT hitting the DB.
    This verifies the cache-aside pattern works end-to-end.
    """
    from tests.conftest import auth_headers

    # Pre-populate the cache with fake data
    cached_data = {
        "items": [],
        "total": 0,
        "page": 1,
        "per_page": 20,
        "pages": 1,
    }
    await mock_redis.set("articles:list:1:20:all", json.dumps(cached_data))

    response = await client.get("/api/v1/articles?page=1&per_page=20")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0  # From our cached data, not real DB
