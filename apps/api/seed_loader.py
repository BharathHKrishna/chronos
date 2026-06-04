"""
Load pre-generated demo location data into the cache on startup.
This ensures demo coordinates work instantly on Render without GEE calls.
"""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
SEED_FILE = Path(__file__).parent.parent.parent / "data" / "seed" / "demo_locations.json"


async def load_seed_data():
    if not SEED_FILE.exists():
        logger.info("No seed file found at %s — skipping", SEED_FILE)
        return

    from apps.api.cache import set_cached
    from apps.api.config import settings

    with open(SEED_FILE) as f:
        seed = json.load(f)

    loaded = 0
    for coord_key, entry in seed.items():
        lat_k, lon_k = coord_key.split(":")
        hist_key = f"history:{lat_k}:{lon_k}"
        await set_cached(hist_key, entry["history"], ttl=settings.cache_ttl_seconds)

        for scenario, forecast in entry.get("forecasts", {}).items():
            fore_key = f"forecast:{lat_k}:{lon_k}:{scenario}"
            await set_cached(fore_key, forecast, ttl=settings.cache_ttl_seconds)

        loaded += 1

    logger.info("Loaded %d demo locations from seed file into cache", loaded)
