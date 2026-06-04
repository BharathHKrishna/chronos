import json
from apps.api.config import settings

# In-memory fallback when Redis is unavailable (local dev without Docker)
_mem_cache: dict = {}

try:
    import redis.asyncio as aioredis
    _pool = aioredis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=2)
    _redis_available = True
except Exception:
    _pool = None
    _redis_available = False


def coord_key(lat: float, lon: float) -> tuple[float, float]:
    """Round to 4 decimal places (~11m precision) for cache keying."""
    return round(lat, 4), round(lon, 4)


async def _redis_ok() -> bool:
    if not _redis_available or _pool is None:
        return False
    try:
        await _pool.ping()
        return True
    except Exception:
        return False


async def get_cached(key: str) -> dict | None:
    if await _redis_ok():
        raw = await _pool.get(key)
        if raw:
            return json.loads(raw)
    return _mem_cache.get(key)


async def set_cached(key: str, value: dict, ttl: int = settings.cache_ttl_seconds):
    _mem_cache[key] = value  # always write mem cache
    if await _redis_ok():
        await _pool.setex(key, ttl, json.dumps(value))
