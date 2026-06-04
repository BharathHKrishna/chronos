from fastapi import APIRouter, HTTPException, BackgroundTasks
from apps.api.cache import get_cached, set_cached, coord_key
from apps.api.services.gee_fetcher import fetch_history
from apps.api.workers.tasks import fetch_history_task

router = APIRouter()


@router.get("")
async def get_history(lat: float, lon: float, background_tasks: BackgroundTasks):
    """
    Return time-series 1985–2025 for (lat, lon).
    Signals: ndvi, nighttime_lights, land_surface_temp, built_up_extent.
    Each signal is a list of {year, value, source} dicts.
    Cache-first; triggers async Earth Engine fetch on miss.
    """
    lat_k, lon_k = coord_key(lat, lon)
    cache_key = f"history:{lat_k}:{lon_k}"

    cached = await get_cached(cache_key)
    if cached:
        return {"lat": lat, "lon": lon, "source": "cache", "data": cached}

    # Attempt synchronous fetch for small areas; fall back to task for large
    try:
        data = fetch_history(lat, lon)
        await set_cached(cache_key, data)
        return {"lat": lat, "lon": lon, "source": "live", "data": data}
    except Exception as exc:
        # Queue async task and return 202
        task = fetch_history_task.delay(lat, lon)
        return {
            "lat": lat,
            "lon": lon,
            "source": "queued",
            "task_id": task.id,
            "message": "Data fetch queued. Poll /history/task/{task_id} for status.",
        }


@router.get("/task/{task_id}")
async def poll_history_task(task_id: str):
    from apps.api.workers.tasks import celery_app
    result = celery_app.AsyncResult(task_id)
    if result.ready():
        return {"status": "done", "data": result.result}
    return {"status": result.state.lower()}
