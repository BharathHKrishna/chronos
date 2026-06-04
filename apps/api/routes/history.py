import traceback
from fastapi import APIRouter, HTTPException
from apps.api.cache import get_cached, set_cached, coord_key
from apps.api.services.gee_fetcher import fetch_history

router = APIRouter()


@router.get("")
async def get_history(lat: float, lon: float):
    """
    Return time-series 1985–2025 for (lat, lon).
    Signals: ndvi, nighttime_lights, land_surface_temp, built_up_extent.
    Cache-first; runs synchronous Earth Engine fetch on miss.
    """
    lat_k, lon_k = coord_key(lat, lon)
    cache_key = f"history:{lat_k}:{lon_k}"

    cached = await get_cached(cache_key)
    if cached:
        return {"lat": lat, "lon": lon, "source": "cache", "data": cached}

    try:
        data = fetch_history(lat, lon)
        await set_cached(cache_key, data)
        return {"lat": lat, "lon": lon, "source": "live", "data": data}
    except Exception as exc:
        tb = traceback.format_exc()
        raise HTTPException(
            status_code=503,
            detail=f"Earth Engine fetch failed: {exc}\n\n{tb}",
        )
