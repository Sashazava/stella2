import json
from typing import Any

import redis.asyncio as aioredis

RATE_LIMIT_SCRIPT = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local current = redis.call('GET', key)
if current and tonumber(current) >= limit then return 0 end
current = redis.call('INCR', key)
if current == 1 then redis.call('EXPIRE', key, window) end
return 1
"""


async def init_redis(url: str) -> aioredis.Redis:
    """Create Redis connection pool."""
    pool = aioredis.ConnectionPool.from_url(
        url,
        decode_responses=True,
        max_connections=20,
        health_check_interval=30,
    )
    return aioredis.Redis(connection_pool=pool)


async def close_redis(client: aioredis.Redis) -> None:
    """Close Redis connection."""
    await client.aclose()


async def get_cached(
    client: aioredis.Redis, key: str
) -> dict[str, Any] | None:
    """Get cached data from Redis."""
    data = await client.get(key)
    if data is None:
        return None
    return json.loads(data)


async def set_cached(
    client: aioredis.Redis, key: str, data: dict[str, Any], ttl: int
) -> None:
    """Set cached data in Redis with TTL."""
    await client.setex(key, ttl, json.dumps(data))


async def invalidate(client: aioredis.Redis, *keys: str) -> None:
    """Invalidate cache keys."""
    if keys:
        await client.delete(*keys)


class RateLimiter:
    """Rate limiter using Redis with Lua script for atomic operations."""

    def __init__(
        self, client: aioredis.Redis, limit: int = 100, window: int = 60
    ) -> None:
        """Initialize rate limiter.

        Args:
            client: Redis async client
            limit: Maximum requests per window
            window: Time window in seconds
        """
        self._client = client
        self._limit = limit
        self._window = window
        self._script = client.register_script(RATE_LIMIT_SCRIPT)

    async def is_allowed(self, key: str) -> bool:
        """Check if request is allowed under rate limit.

        Args:
            key: Rate limit key (e.g., user_id, IP address)

        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        result = await self._script(keys=[key], args=[self._limit, self._window])
        return bool(result)
