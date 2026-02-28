import time
import redis.asyncio as aioredis
from fastapi import HTTPException, Request

from config.settings import settings

redis_conn = aioredis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    encoding="utf-8"
)



with open("rate_limit/rate-counter.lua", "r", encoding="utf-8") as f:
    script_text = f.read()
lua_script = redis_conn.register_script(script_text)

def allow_request(user_id: str, service: str) -> bool:
    key = f"rate:{service}:{user_id}"
    now = int(time.time())
    return bool(lua_script(
        keys=[key],
        args=[now, settings.WINDOW_SECONDS, settings.RATE_LIMIT]
    ))


def rate_limit(service_name: str):
    async def limiter(request: Request):
        user_id = request.headers.get("X-User-Id", request.client.host)

        if not allow_request(user_id, service_name):
            raise HTTPException(
                status_code=429,
                detail="Too Many Requests"
            )
    return limiter