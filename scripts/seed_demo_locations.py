"""
Pre-compute and cache historical data for the 10 demo locations.
Run once before launch to ensure the demo is instant for recruiters.

Usage:
    python scripts/seed_demo_locations.py
"""

import asyncio
import json
import redis
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from apps.api.config import settings
from apps.api.services.gee_fetcher import fetch_history
from apps.api.services.forecaster import run_forecast
from apps.api.cache import coord_key

DEMO_LOCATIONS = [
    ("Bangalore", 12.97, 77.59),
    ("Sahara Solar Belt", 23.0, 5.0),
    ("Amazon Frontier", -8.5, -55.0),
    ("Karlsruhe", 49.0, 8.4),
    ("Yangtze Delta", 31.2, 121.5),
    ("Aral Sea", 45.0, 60.0),
    ("Dubai", 25.2, 55.3),
    ("Inner Mongolia", 41.0, 111.0),
    ("Lagos", 6.5, 3.4),
    ("Houston", 29.7, -95.0),
]

SCENARIOS = ["bau", "solar", "grid", "stress"]


def main():
    r = redis.from_url(settings.redis_url)
    for name, lat, lon in DEMO_LOCATIONS:
        print(f"\n[{name}] ({lat}, {lon})")
        lat_k, lon_k = coord_key(lat, lon)

        hist_key = f"history:{lat_k}:{lon_k}"
        if r.exists(hist_key):
            print("  history: cached (skip)")
            history = json.loads(r.get(hist_key))
        else:
            print("  history: fetching from GEE…")
            history = fetch_history(lat, lon)
            r.setex(hist_key, settings.cache_ttl_seconds, json.dumps(history))
            print("  history: saved")

        for scenario in SCENARIOS:
            fore_key = f"forecast:{lat_k}:{lon_k}:{scenario}"
            if r.exists(fore_key):
                print(f"  forecast/{scenario}: cached (skip)")
                continue
            print(f"  forecast/{scenario}: computing…")
            forecast = run_forecast(history, scenario)
            r.setex(fore_key, settings.cache_ttl_seconds, json.dumps(forecast))
            print(f"  forecast/{scenario}: saved")

    print("\nSeeding complete.")


if __name__ == "__main__":
    main()
