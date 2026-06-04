"""
Pre-compute and cache historical data + all 4 scenario forecasts
for the 10 demo locations. Hits the live API so Render's Redis gets
populated — demo coordinates will load instantly for recruiters.

Usage (against Render):
    python scripts/seed_demo_locations.py --api https://chronos-api-8ok9.onrender.com

Usage (local):
    python scripts/seed_demo_locations.py --api http://localhost:8002
"""

import argparse
import sys
import time
import httpx

DEMO_LOCATIONS = [
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


def seed(api: str):
    client = httpx.Client(base_url=api, timeout=180.0)
    total = len(DEMO_LOCATIONS) * (1 + len(SCENARIOS))
    done = 0

    for name, lat, lon in DEMO_LOCATIONS:
        print(f"\n[{name}]  ({lat}, {lon})")

        # History
        print(f"  history… ", end="", flush=True)
        t0 = time.time()
        r = client.get("/history", params={"lat": lat, "lon": lon})
        if r.status_code == 200:
            d = r.json()
            src = d.get("source", "?")
            ndvi_pts = len([p for p in d["data"]["ndvi"] if p["value"] is not None])
            print(f"✓  ({src}, {ndvi_pts} NDVI pts, {time.time()-t0:.1f}s)")
        else:
            print(f"✗  HTTP {r.status_code}")
        done += 1

        # Forecasts
        for scenario in SCENARIOS:
            print(f"  forecast/{scenario}… ", end="", flush=True)
            t0 = time.time()
            r = client.post("/forecast", json={"lat": lat, "lon": lon, "scenario": scenario})
            if r.status_code == 200:
                src = r.json().get("source", "?")
                print(f"✓  ({src}, {time.time()-t0:.1f}s)")
            else:
                print(f"✗  HTTP {r.status_code}: {r.text[:80]}")
            done += 1

        pct = done / total * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"  [{bar}] {pct:.0f}% ({done}/{total})")

    print(f"\n✓ Seeding complete — {len(DEMO_LOCATIONS)} locations × {len(SCENARIOS)} scenarios cached.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="https://chronos-api-8ok9.onrender.com")
    args = parser.parse_args()
    print(f"Seeding against {args.api}")
    seed(args.api)
