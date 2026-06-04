# Chronos — CLAUDE.md

## What this project is
A web app where a user clicks any coordinate on Earth, then drags a slider from 1985 → 2026 → 2050.
Left of "today" = real historical satellite + climate data.
Right of "today" = AI-projected future under a user-chosen scenario (BAU, solar buildout, grid expansion, climate stress).
An LLM (Llama 3.3-70B via Groq) narrates a 4–6 sentence "diary" for the coordinate.

## Monorepo layout
```
apps/api/      FastAPI backend (Python)
apps/web/      React + Vite + Leaflet frontend
notebooks/     EDA / training notebooks
models/        Trained forecaster artifacts
data/cache/    DVC-tracked, gitignored
scripts/       Seed + retrain utilities
```

## Key environment variables (set in .env)
```
GEE_SERVICE_ACCOUNT_KEY=...   # path to Earth Engine service account JSON
GROQ_API_KEY=...
REDIS_URL=redis://redis:6379/0
DATABASE_URL=postgresql://...
WANDB_API_KEY=...
SENTRY_DSN=...
```

## API routes
- `GET  /history?lat=&lon=`       → cached time-series 1985–2025
- `POST /forecast`  `{lat, lon, scenario}` → projected 2026–2050
- `POST /narrative` `{lat, lon, scenario, history, forecast}` → LLM diary
- `GET  /tile/{year}?lat=&lon=`   → PNG tile for that year

## Scenarios
| id | label | description |
|----|-------|-------------|
| bau | Business as usual | Extrapolate historical trends |
| solar | Aggressive solar buildout | Dampen fossil-linked light growth, reduce LST trend |
| grid | Grid expansion | Nighttime lights grow faster, NDVI pressure increases |
| stress | Climate stress | LST accelerated, NDVI declining faster |

## Data sources
- NDVI: Landsat 5/7/8/9 (Google Earth Engine)
- Nighttime lights: DMSP-OLS (1992–2013) + VIIRS (2012–present), harmonised via Li & Zhou (2017)
- LST: Landsat thermal + MODIS MOD11A2
- Built-up: GHSL Built-S (5-year epochs, 1975–present)

## Forecasting
- v1: Prophet (Meta) per signal, per coordinate. Scenario = multiplicative modifier on trend.
- v2 (future): Tiny PyTorch Transformer encoder trained across all coordinates.

## Caching strategy
Redis key: `history:{lat_rounded_4dp}:{lon_rounded_4dp}`  TTL 30 days.
50 seed coordinates are precomputed (scripts/seed_demo_locations.py).

## Running locally
```bash
docker-compose up --build
# API at http://localhost:8000
# Frontend at http://localhost:5173
```

## Testing
```bash
cd apps/api && pytest -q
```

## Deploy
Push to main → GitHub Actions runs lint/type-check/tests → builds Docker → deploys to Fly.io.
