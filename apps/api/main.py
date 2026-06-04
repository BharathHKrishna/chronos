from contextlib import asynccontextmanager
import time
import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from apps.api.routes import history, forecast, narrative, tiles
from apps.api.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        from apps.api.db import init_db
        await init_db()
    except Exception:
        pass
    # Pre-load demo locations so they're instant for new visitors
    try:
        from apps.api.seed_loader import load_seed_data
        await load_seed_data()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Seed load failed: %s", e)
    yield


if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=0.1,
        environment="production",
        release="chronos@1.0.0",
    )

app = FastAPI(
    title="Chronos API",
    description="Satellite time-series + AI forecasting for any coordinate on Earth",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app, include_in_schema=False)

app.include_router(history.router, prefix="/history", tags=["history"])
app.include_router(forecast.router, prefix="/forecast", tags=["forecast"])
app.include_router(narrative.router, prefix="/narrative", tags=["narrative"])
app.include_router(tiles.router, prefix="/tile", tags=["tiles"])


@app.get("/gee-test", tags=["monitoring"])
def gee_test():
    """Quick GEE connectivity test — returns NDVI value or error."""
    try:
        import ee
        from apps.api.services.gee_fetcher import _init_gee
        _init_gee()
        region = ee.Geometry.Point([77.59, 12.97]).buffer(500)
        val = (
            ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
            .filter(ee.Filter.calendarRange(2020, 2020, "year"))
            .filter(ee.Filter.calendarRange(5, 9, "month"))
            .select(["SR_B4", "SR_B5"])
            .median()
            .normalizedDifference(["SR_B5", "SR_B4"])
            .reduceRegion(ee.Reducer.mean(), region, 30)
            .getInfo()
        )
        return {"gee": "ok", "bangalore_ndvi_2020": val}
    except Exception as e:
        import traceback
        return {"gee": "error", "detail": str(e), "traceback": traceback.format_exc()}


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}


@app.get("/status", tags=["monitoring"])
async def status():
    """Deep health check — Redis, GEE auth, and key config."""
    checks: dict = {}
    t0 = time.time()

    # Redis
    try:
        from apps.api.cache import _pool, _redis_available
        if _redis_available and _pool:
            await _pool.ping()
            checks["redis"] = "ok"
        else:
            checks["redis"] = "in-memory fallback"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    # GEE auth — check env var (Render) or local credentials file
    import os
    has_b64 = bool(settings.gee_credentials_b64)
    has_file = os.path.exists(os.path.expanduser("~/.config/earthengine/credentials"))
    has_sa = bool(settings.gee_service_account_email)
    checks["gee_credentials"] = "ok" if (has_b64 or has_file or has_sa) else "missing"

    # Groq key configured
    checks["groq_key"] = "ok" if settings.groq_api_key else "missing"

    # Cache stats
    try:
        from apps.api.cache import _mem_cache
        checks["mem_cache_keys"] = len(_mem_cache)
    except Exception:
        pass

    checks["latency_ms"] = round((time.time() - t0) * 1000, 1)
    checks["version"] = "1.0.0"

    return checks
