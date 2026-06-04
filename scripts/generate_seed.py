"""
Generate data/seed/demo_locations.json by hitting the local API.
Run this once offline; the result ships in the Docker image.

Usage:
    python scripts/generate_seed.py [--api http://localhost:8002]
"""
import argparse, json, time, sys
from pathlib import Path
import httpx

LOCATIONS = [
    ("Bangalore",        12.97,   77.59),
    ("Sahara Solar Belt", 23.0,    5.0),
    ("Amazon Frontier",  -8.5,  -55.0),
    ("Karlsruhe",        49.0,    8.4),
    ("Yangtze Delta",    31.2,  121.5),
    ("Aral Sea",         45.0,   60.0),
    ("Dubai",            25.2,   55.3),
    ("Inner Mongolia",   41.0,  111.0),
    ("Lagos",             6.5,    3.4),
    ("Houston",          29.7,  -95.0),
]
SCENARIOS = ["bau", "solar", "grid", "stress"]
OUT = Path("data/seed/demo_locations.json")


def main(api: str):
    OUT.parent.mkdir(parents=True, exist_ok=True)
    client = httpx.Client(base_url=api, timeout=300.0)
    seed = {}

    for i, (name, lat, lon) in enumerate(LOCATIONS, 1):
        key = f"{round(lat,4)}:{round(lon,4)}"
        print(f"[{i}/{len(LOCATIONS)}] {name} ({lat}, {lon})", flush=True)

        t0 = time.time()
        r = client.get("/history", params={"lat": lat, "lon": lon})
        r.raise_for_status()
        history = r.json()["data"]
        print(f"  history: {time.time()-t0:.0f}s", flush=True)

        forecasts = {}
        for sc in SCENARIOS:
            r = client.post("/forecast", json={"lat": lat, "lon": lon, "scenario": sc})
            r.raise_for_status()
            forecasts[sc] = r.json()["data"]
        print(f"  forecasts: done", flush=True)

        seed[key] = {"lat": lat, "lon": lon, "name": name, "history": history, "forecasts": forecasts}

        # Save incrementally so progress isn't lost
        with open(OUT, "w") as f:
            json.dump(seed, f)

    print(f"\n✓ Saved {len(seed)} locations → {OUT}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--api", default="http://localhost:8002")
    args = p.parse_args()
    main(args.api)
