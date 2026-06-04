from contextlib import asynccontextmanager
import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from apps.api.routes import history, forecast, narrative, tiles
from apps.api.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: init DB tables
    try:
        from apps.api.db import init_db
        await init_db()
    except Exception:
        pass  # DB optional for local dev without postgres
    yield


if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)

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

Instrumentator().instrument(app).expose(app)

app.include_router(history.router, prefix="/history", tags=["history"])
app.include_router(forecast.router, prefix="/forecast", tags=["forecast"])
app.include_router(narrative.router, prefix="/narrative", tags=["narrative"])
app.include_router(tiles.router, prefix="/tile", tags=["tiles"])


@app.get("/health")
def health():
    return {"status": "ok"}
