# Chronos — the past and future of any place on Earth

[**Live demo →**](https://chronos.fly.dev)   |   [Video walkthrough](#)   |   [Blog post](#)

> Click Bangalore. Drag to 1985. Watch 40 years happen in 5 seconds. Now drag into the future.

---

## What it is

Chronos is a public web app that lets you explore any coordinate on Earth across 40 years of real satellite history (1985–2025), then project it forward to 2050 under user-selected energy and climate scenarios.

Every drag of the slider updates:
- A **satellite tile** (historical composite or AI-projected visual)
- Four **signal charts** (NDVI, nighttime lights, land-surface temperature, built-up extent)
- An **LLM-written diary** entry narrating what changed and what is projected

---

## Try it

1. Open [chronos.fly.dev](https://chronos.fly.dev)
2. Click any point on the map (or pick a demo location below)
3. Drag the timeline slider
4. Toggle scenarios on the right panel

---

## Demo locations

| Place | Coordinates | Story |
|-------|-------------|-------|
| Bangalore, India | 12.97, 77.59 | Explosive urban growth + heat island |
| Sahara solar belt | 23.0, 5.0 | Minimal history, solar-scenario divergence |
| Amazon deforestation frontier | -8.5, -55.0 | Vegetation collapse |
| Karlsruhe, Germany | 49.0, 8.4 | Stable European city, wind/solar transition |
| Yangtze River delta | 31.2, 121.5 | Fastest urbanisation on record |
| Aral Sea | 45.0, 60.0 | One of Earth's most visible disasters |
| Dubai coast | 25.2, 55.3 | Desert → megacity |
| Inner Mongolia wind farms | 41.0, 111.0 | Green-energy buildout signature |
| Lagos, Nigeria | 6.5, 3.4 | Fastest-growing megacity |
| Houston ship channel | 29.7, -95.0 | Industrial energy fingerprint |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  React + Leaflet frontend (Vite, shadcn/ui)         │
│  Map · Timeline slider · Scenario selector · Diary  │
└────────────────┬────────────────────────────────────┘
                 │ REST
┌────────────────▼────────────────────────────────────┐
│  FastAPI  (/history  /forecast  /narrative  /tile)  │
│           Redis cache  (30-day TTL per coordinate)  │
└──────┬──────────────┬──────────────┬────────────────┘
       │              │              │
  ┌────▼────┐   ┌─────▼─────┐  ┌────▼────┐
  │  GEE    │   │  Prophet  │  │  Groq   │
  │ fetcher │   │ forecaster│  │  LLM    │
  └────┬────┘   └─────┬─────┘  └─────────┘
       │              │
  ┌────▼──────────────▼────┐
  │  PostgreSQL + PostGIS  │
  └────────────────────────┘
```

---

## What's inside

- **Multi-decade satellite time-series** — Landsat 5/7/8/9, DMSP-OLS + VIIRS (harmonised), MODIS LST, GHSL Built-S
- **Per-coordinate trend forecaster** — Prophet v1, PyTorch Transformer v2
- **Scenario-conditioned projection to 2050** — BAU, solar buildout, grid expansion, climate stress
- **LLM-written narrative** — Llama 3.3-70B via Groq, grounded on real numbers
- **Production stack** — FastAPI + Celery + Redis + PostGIS + React + Leaflet
- **MLOps** — GitHub Actions CI/CD, W&B experiment tracking, DVC data versioning, Sentry + Grafana monitoring

---

## Running locally

```bash
git clone https://github.com/yourusername/chronos
cd chronos
cp .env.example .env          # fill in GEE_SERVICE_ACCOUNT_KEY, GROQ_API_KEY, etc.
docker-compose up --build
```

- API: http://localhost:8000/docs
- Frontend: http://localhost:5173

---

## Forecaster training

```bash
cd notebooks
jupyter lab
# Run 01 → 02 → 03 → 04 in order
# Or: python scripts/retrain_forecaster.py
```

Retrain logs to W&B automatically. Model artifacts saved to `models/`.

---

## DMSP → VIIRS harmonisation

Nighttime lights use the [Li & Zhou (2017)](https://doi.org/10.1016/j.rse.2017.07.037) cross-calibration method to bridge the two sensor generations. The bridge notebook is at `notebooks/02_dmsp_viirs_bridge.ipynb`.

---

## Scenario methodology

Scenarios are implemented as **multiplicative modifiers on Prophet trend coefficients**, not as physical simulations. They are indicative, not predictive. Confidence bands are shown at all times.

| Scenario | NDVI trend | LST trend | Lights trend | Built-up trend |
|----------|------------|-----------|--------------|----------------|
| BAU | ×1.0 | ×1.0 | ×1.0 | ×1.0 |
| Solar buildout | ×1.1 | ×0.85 | ×0.9 | ×1.0 |
| Grid expansion | ×0.95 | ×1.05 | ×1.3 | ×1.15 |
| Climate stress | ×0.8 | ×1.25 | ×1.0 | ×1.05 |

---

## CI/CD

Every push to `main`:
1. `ruff` + `mypy` + `pytest`
2. Docker build
3. Deploy to Fly.io

---

## CV bullet

> **Chronos** — a 40-year satellite time-machine + scenario forecaster ([Live](https://chronos.fly.dev))  
> Built a public web app that fetches multi-decade satellite + climate data for any coordinate (Landsat, VIIRS, MODIS, GHSL), forecasts trajectories to 2050 under user-selected scenarios, and generates an LLM-written narrative. Deployed with FastAPI, Celery, Redis, PostGIS on Fly.io with full CI/CD via GitHub Actions, W&B experiment tracking, and Sentry + Grafana monitoring.

---

## License

MIT
