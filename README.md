# Chronos — the past & future of any place on Earth

**[Live demo →](https://web-alpha-steel-36.vercel.app)**  &nbsp;|&nbsp;  [API docs →](https://chronos-api-8ok9.onrender.com/docs)  &nbsp;|&nbsp;  [API health →](https://chronos-api-8ok9.onrender.com/health)

> Click Bangalore. Drag to 1985. Watch 40 years happen in 5 seconds.  
> Drag past 2025 — choose a scenario. See what 2050 looks like.

---

## What it is

Chronos is a web app that fetches 40 years of real satellite data for any coordinate on Earth, then projects it forward to 2050 under user-selected energy and climate scenarios. Every drag of the timeline updates a satellite thumbnail, four signal charts, and an LLM-written diary entry.

**Left of 2025** → real Landsat / VIIRS / MODIS / GHSL data  
**Right of 2025** → AI-projected future, scenario-conditioned to 2050

---

## Demo locations

| Location | Coordinates | Story |
|----------|-------------|-------|
| [Bangalore](https://web-alpha-steel-36.vercel.app/?lat=12.97&lon=77.59) | 12.97, 77.59 | Explosive urban growth + heat island |
| [Sahara solar belt](https://web-alpha-steel-36.vercel.app/?lat=23.0&lon=5.0) | 23.0, 5.0 | Minimal history; solar scenario diverges most |
| [Amazon frontier](https://web-alpha-steel-36.vercel.app/?lat=-8.5&lon=-55.0) | −8.5, −55.0 | Vegetation collapse in real time |
| [Karlsruhe](https://web-alpha-steel-36.vercel.app/?lat=49.0&lon=8.4) | 49.0, 8.4 | Stable European city; clean wind/solar signal |
| [Yangtze delta](https://web-alpha-steel-36.vercel.app/?lat=31.2&lon=121.5) | 31.2, 121.5 | Fastest urbanisation on record |
| [Aral Sea](https://web-alpha-steel-36.vercel.app/?lat=45.0&lon=60.0) | 45.0, 60.0 | One of Earth's most visible disasters |
| [Dubai](https://web-alpha-steel-36.vercel.app/?lat=25.2&lon=55.3) | 25.2, 55.3 | Desert → megacity |
| [Inner Mongolia](https://web-alpha-steel-36.vercel.app/?lat=41.0&lon=111.0) | 41.0, 111.0 | Wind farm buildout signature |
| [Lagos](https://web-alpha-steel-36.vercel.app/?lat=6.5&lon=3.4) | 6.5, 3.4 | Fastest-growing megacity |
| [Houston](https://web-alpha-steel-36.vercel.app/?lat=29.7&lon=-95.0) | 29.7, −95.0 | Industrial energy fingerprint |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│   React 18 + Vite + Leaflet + Recharts + Tailwind (Vercel)  │
│   Map · Timeline slider · Scenario selector · Diary panel   │
└───────────────────────┬──────────────────────────────────────┘
                        │ HTTPS REST
┌───────────────────────▼──────────────────────────────────────┐
│            FastAPI  (Render — Singapore)                     │
│   GET /history   POST /forecast   POST /narrative  GET /tile │
│   Redis cache (30-day TTL · in-memory fallback)              │
│   Prometheus metrics · Sentry error tracking                 │
└──────────┬─────────────────┬────────────────┬────────────────┘
           │                 │                │
    ┌──────▼──────┐  ┌───────▼──────┐  ┌─────▼──────┐
    │ Google Earth│  │   Prophet    │  │  Groq API  │
    │   Engine   │  │  forecaster  │  │ Llama 3.3  │
    │  (GEE API) │  │  2026–2050   │  │   70B LLM  │
    └──────┬──────┘  └──────────────┘  └────────────┘
           │
    ┌──────▼────────────────────────────────────────┐
    │  Landsat 5/7/8/9 · DMSP-OLS · VIIRS-DNB      │
    │  MODIS MOD11A2 · GHSL Built-S                 │
    └───────────────────────────────────────────────┘
```

---

## Signals

| Signal | Source | Years |
|--------|--------|-------|
| NDVI (vegetation health) | Landsat 5/7/8/9, cloud-masked, growing season | 1985–2025 |
| Nighttime lights | DMSP-OLS → VIIRS-DNB, harmonised via [Li & Zhou (2017)](https://doi.org/10.1016/j.rse.2017.07.037) | 1992–2025 |
| Land surface temperature | MODIS MOD11A2 daytime LST (°C) | 2000–2025 |
| Built-up extent | GHSL Built-S, 5-year epochs interpolated | 1985–2025 |

---

## Scenarios (2026–2050)

Scenarios are multiplicative modifiers on Prophet trend coefficients — indicative, not physical simulations. Confidence bands are shown at all times.

| Scenario | NDVI | LST | Lights | Built-up |
|----------|------|-----|--------|----------|
| Business as usual | ×1.0 | ×1.0 | ×1.0 | ×1.0 |
| Solar buildout | ×1.1 | ×0.85 | ×0.9 | ×1.0 |
| Grid expansion | ×0.95 | ×1.05 | ×1.3 | ×1.15 |
| Climate stress | ×0.8 | ×1.25 | ×1.0 | ×1.05 |

---

## Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Data | Google Earth Engine Python API | Free, global, Landsat back to 1972 |
| Forecasting | Prophet (Meta) v1 | Ships in a weekend; Transformer is v2 |
| LLM | Llama 3.3-70B via Groq | Fast, free tier, grounded on real numbers |
| Backend | FastAPI + Celery + Redis | Standard Python ML serving |
| Frontend | React 18 + Vite + Leaflet + Recharts | Fast, modern, recruiter-legible |
| Deploy | Render (API) + Vercel (frontend) | Free, no card |
| MLOps | W&B experiment tracking, DVC data versioning | Every keyword a recruiter scans for |
| Monitoring | Sentry (errors) + Prometheus (metrics) | Production-grade without overkill |

---

## Running locally

```bash
git clone https://github.com/BharathHKrishna/chronos
cd chronos
cp .env.example .env       # fill in GROQ_API_KEY, GEE_PROJECT
pip install -r apps/api/requirements.txt
cd apps/web && npm install

# Terminal 1 — API
cd /path/to/chronos
PYTHONPATH=. uvicorn apps.api.main:app --port 8002 --reload

# Terminal 2 — Frontend
cd apps/web && npm run dev
```

Open http://localhost:5173

---

## Forecaster retraining

```bash
# After seeding coordinates into Redis:
python scripts/seed_demo_locations.py
python scripts/retrain_forecaster.py --sample 200
# Logs to W&B project: chronos-forecaster
```

---

## Tests

```bash
cd /path/to/chronos
PYTHONPATH=. pytest apps/api/tests/ -v
```

---

## DMSP → VIIRS harmonisation

Nighttime lights bridge the two sensor generations using the [Li & Zhou (2017)](https://doi.org/10.1016/j.rse.2017.07.037) log-linear calibration:

```
DN_equiv = 10.062 × ln(avg_rad + 1)
```

Validated across 4 cities in `notebooks/02_dmsp_viirs_bridge.ipynb`.

---

## CV bullet

> **Chronos** — 40-year satellite time-machine + scenario forecaster &nbsp;([Live](https://web-alpha-steel-36.vercel.app) · [Code](https://github.com/BharathHKrishna/chronos))  
> Built a public web app that fetches multi-decade satellite + climate data for any coordinate on Earth (Landsat 5/7/8/9, DMSP-OLS + VIIRS harmonised, MODIS LST, GHSL), forecasts trajectories to 2050 under user-selected energy scenarios using Prophet, and generates grounded LLM narratives via Groq (Llama 3.3-70B). Deployed FastAPI + Redis on Render with React + Leaflet frontend on Vercel. W&B experiment tracking, Sentry monitoring, DVC data versioning.

---

## License

MIT
