from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from apps.api.cache import get_cached, set_cached, coord_key
from apps.api.services.forecaster import run_forecast
from apps.api.config import settings

router = APIRouter()

VALID_SCENARIOS = {"bau", "solar", "grid", "stress"}


class ForecastRequest(BaseModel):
    lat: float
    lon: float
    scenario: str = "bau"


@router.post("")
async def post_forecast(req: ForecastRequest):
    """
    Return projected time-series 2026–2050 for (lat, lon) under scenario.
    Requires historical data to already be cached.
    """
    if req.scenario not in VALID_SCENARIOS:
        raise HTTPException(400, f"scenario must be one of {VALID_SCENARIOS}")

    lat_k, lon_k = coord_key(req.lat, req.lon)
    forecast_cache_key = f"forecast:{lat_k}:{lon_k}:{req.scenario}"
    cached = await get_cached(forecast_cache_key)
    if cached:
        return {"source": "cache", "data": cached}

    history_key = f"history:{lat_k}:{lon_k}"
    history = await get_cached(history_key)
    if not history:
        raise HTTPException(
            404,
            "No historical data cached for this coordinate. "
            "Call GET /history?lat=&lon= first.",
        )

    forecast = run_forecast(history, req.scenario)
    await set_cached(forecast_cache_key, forecast, ttl=settings.cache_ttl_seconds)
    return {"source": "live", "data": forecast}
