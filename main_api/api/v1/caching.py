import json
import backoff
import redis.asyncio as aioredis
from redis.exceptions import ConnectionError as RedisConnectionError
from config.config import settings

CACHE_TTL = 300  # seconds

# Create global Redis client
redis = aioredis.from_url(
    f"redis://redis:{settings.redis_port}",
    decode_responses=True,
    encoding="utf-8",
)


@backoff.on_exception(
    backoff.expo,
    RedisConnectionError,
    max_time=60,  # stop after 60 seconds total
    max_tries=5,  # or after 5 attempts
    jitter=backoff.full_jitter,
    on_backoff=lambda d: print(
        f"⚠️ Retrying Redis connection (attempt {d['tries']})..."
    ),
)
async def get_from_cache(key: str):
    """Retrieve value from Redis cache (with retry if Redis temporarily unavailable)."""
    try:
        data = await redis.get(key)
        if data:
            return json.loads(data)
        return None
    except RedisConnectionError as e:
        raise e


@backoff.on_exception(
    backoff.expo,
    RedisConnectionError,
    max_time=60,
    max_tries=5,
    jitter=backoff.full_jitter,
    on_backoff=lambda d: print(f"⚠️ Retrying Redis set (attempt {d['tries']})..."),
)
async def set_to_cache(key: str, value, ttl: int = CACHE_TTL):
    """Store value in Redis cache as JSON (with retry if Redis temporarily unavailable)."""
    try:
        await redis.set(key, json.dumps(value, default=str), ex=ttl)
    except RedisConnectionError as e:
        raise e
