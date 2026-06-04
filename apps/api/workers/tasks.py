from celery import Celery
from apps.api.config import settings

celery_app = Celery(
    "chronos",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.timezone = "UTC"


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def fetch_history_task(self, lat: float, lon: float) -> dict:
    """Async GEE fetch — runs in Celery worker, stores result in Redis."""
    import asyncio
    from apps.api.services.gee_fetcher import fetch_history
    from apps.api.cache import set_cached, coord_key

    try:
        data = fetch_history(lat, lon)
        lat_k, lon_k = coord_key(lat, lon)
        cache_key = f"history:{lat_k}:{lon_k}"
        # Redis cache write is sync-safe from Celery context
        import redis as sync_redis
        import json
        r = sync_redis.from_url(settings.redis_url)
        r.setex(cache_key, settings.cache_ttl_seconds, json.dumps(data))
        return data
    except Exception as exc:
        raise self.retry(exc=exc)
