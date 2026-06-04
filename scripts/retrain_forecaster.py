"""
Retrain the v1 Prophet forecaster on cached coordinate data.
Logs metrics to W&B. Saves model artifacts to models/.

Usage:
    python scripts/retrain_forecaster.py [--sample N]
"""

import argparse
import json
import os
import pickle
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import redis
import pandas as pd
import wandb
from prophet import Prophet
from apps.api.config import settings

OUTPUT_DIR = Path("models")
OUTPUT_DIR.mkdir(exist_ok=True)

SIGNALS = ["ndvi", "nighttime_lights", "land_surface_temp", "built_up_extent"]


def load_all_cached_histories(r: redis.Redis, sample: int) -> list[dict]:
    keys = r.scan_iter("history:*")
    histories = []
    for key in keys:
        raw = r.get(key)
        if raw:
            histories.append(json.loads(raw))
        if len(histories) >= sample:
            break
    return histories


def train_signal_model(signal_key: str, all_histories: list[dict]) -> Prophet:
    records = []
    for hist in all_histories:
        series = hist.get(signal_key, [])
        for pt in series:
            if pt["value"] is not None:
                records.append({
                    "ds": pd.Timestamp(f"{pt['year']}-07-01"),
                    "y": pt["value"],
                })
    df = pd.DataFrame(records).dropna()
    model = Prophet(yearly_seasonality=False, weekly_seasonality=False, daily_seasonality=False)
    model.fit(df)
    return model


def main(sample: int = 200):
    run = wandb.init(project="chronos-forecaster", config={"sample": sample, "model": "prophet-v1"})
    r = redis.from_url(settings.redis_url)

    print(f"Loading up to {sample} cached histories…")
    histories = load_all_cached_histories(r, sample)
    print(f"Loaded {len(histories)} histories")
    wandb.log({"n_training_locations": len(histories)})

    models = {}
    for signal in SIGNALS:
        print(f"Training {signal}…")
        model = train_signal_model(signal, histories)
        models[signal] = model
        artifact_path = OUTPUT_DIR / f"prophet_{signal}.pkl"
        with open(artifact_path, "wb") as f:
            pickle.dump(model, f)
        wandb.log({f"{signal}_training_samples": sum(
            1 for h in histories for pt in h.get(signal, []) if pt.get("value") is not None
        )})
        artifact = wandb.Artifact(f"prophet-{signal}", type="model")
        artifact.add_file(str(artifact_path))
        run.log_artifact(artifact)
        print(f"  saved to {artifact_path}")

    # Save combined bundle
    bundle_path = OUTPUT_DIR / "forecaster_v1.pkl"
    with open(bundle_path, "wb") as f:
        pickle.dump(models, f)
    print(f"Bundle saved to {bundle_path}")
    run.finish()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=200)
    args = parser.parse_args()
    main(sample=args.sample)
