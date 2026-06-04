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

    # GEE auth (cheap: just check credentials file exists, don't make a network call)
    import os
    gee_ok = os.path.exists(os.path.expanduser("~/.config/earthengine/credentials"))
    checks["gee_credentials"] = "ok" if gee_ok else "missing"

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
