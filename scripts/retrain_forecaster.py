"""
Retrain the v1 Prophet forecaster on cached coordinate data.
Logs metrics and artifacts to W&B (or offline if no key set).

Usage:
    python scripts/retrain_forecaster.py [--sample N] [--offline]
"""

import argparse
import json
import os
import pickle
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import redis
import wandb
from prophet import Prophet
from sklearn.metrics import mean_absolute_error

from apps.api.config import settings

OUTPUT_DIR = Path("models")
OUTPUT_DIR.mkdir(exist_ok=True)

SIGNALS = ["ndvi", "nighttime_lights", "land_surface_temp", "built_up_extent"]

HOLDOUT_YEARS = [2021, 2022, 2023, 2024, 2025]


def load_all_cached_histories(r: redis.Redis, sample: int) -> list[dict]:
    histories = []
    for key in r.scan_iter("history:*"):
        raw = r.get(key)
        if raw:
            histories.append(json.loads(raw))
        if len(histories) >= sample:
            break
    return histories


def build_df(signal_key: str, all_histories: list[dict]) -> pd.DataFrame:
    records = []
    for hist in all_histories:
        for pt in hist.get(signal_key, []):
            if pt["value"] is not None:
                records.append({
                    "ds": pd.Timestamp(f"{pt['year']}-07-01"),
                    "y": float(pt["value"]),
                })
    return pd.DataFrame(records).dropna().sort_values("ds")


def train_and_evaluate(signal_key: str, df: pd.DataFrame) -> tuple[Prophet, dict]:
    train = df[~df["ds"].dt.year.isin(HOLDOUT_YEARS)]
    test = df[df["ds"].dt.year.isin(HOLDOUT_YEARS)]

    model = Prophet(
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=False,
        uncertainty_samples=200,
    )
    t0 = time.time()
    model.fit(train)
    fit_time = time.time() - t0

    metrics = {"signal": signal_key, "n_train": len(train), "n_test": len(test), "fit_seconds": round(fit_time, 2)}

    if len(test) > 0:
        future = model.make_future_dataframe(periods=len(test) + 1, freq="YE")
        pred = model.predict(future)
        pred_test = pred[pred["ds"].dt.year.isin(HOLDOUT_YEARS)].set_index(pred["ds"].dt.year)
        actual_test = test.set_index(test["ds"].dt.year)
        common = pred_test.index.intersection(actual_test.index)
        if len(common) > 0:
            mae = mean_absolute_error(actual_test.loc[common, "y"], pred_test.loc[common, "yhat"])
            mape = (abs(actual_test.loc[common, "y"] - pred_test.loc[common, "yhat"]) /
                    actual_test.loc[common, "y"].abs().clip(lower=1e-6)).mean() * 100
            metrics["holdout_mae"] = round(float(mae), 4)
            metrics["holdout_mape_pct"] = round(float(mape), 2)

    return model, metrics


def main(sample: int = 200, offline: bool = False):
    if offline or not settings.wandb_api_key:
        os.environ["WANDB_MODE"] = "offline"
    else:
        os.environ["WANDB_API_KEY"] = settings.wandb_api_key

    run = wandb.init(
        project="chronos-forecaster",
        name=f"prophet-v1-n{sample}",
        config={"model": "prophet-v1", "sample": sample, "holdout_years": HOLDOUT_YEARS},
        tags=["prophet", "v1"],
    )

    r = redis.from_url(settings.redis_url, socket_connect_timeout=3)
    try:
        r.ping()
    except Exception:
        print("Redis unavailable — cannot load training data. Run seed_demo_locations.py first.")
        return

    print(f"Loading up to {sample} cached histories from Redis…")
    histories = load_all_cached_histories(r, sample)
    print(f"Loaded {len(histories)} histories")
    wandb.log({"n_training_locations": len(histories)})

    if len(histories) < 3:
        print("Too few histories to train. Run scripts/seed_demo_locations.py first.")
        return

    models: dict[str, Prophet] = {}
    all_metrics: list[dict] = []

    for signal in SIGNALS:
        print(f"\nTraining {signal}…")
        df = build_df(signal, histories)
        print(f"  {len(df)} training samples")

        if len(df) < 5:
            print(f"  Skipping — insufficient data")
            continue

        model, metrics = train_and_evaluate(signal, df)
        models[signal] = model
        all_metrics.append(metrics)

        wandb.log({f"{signal}/{k}": v for k, v in metrics.items() if isinstance(v, (int, float))})

        # Save individual artifact
        path = OUTPUT_DIR / f"prophet_{signal}.pkl"
        with open(path, "wb") as f:
            pickle.dump(model, f)

        artifact = wandb.Artifact(f"prophet-{signal.replace('_', '-')}", type="model",
                                   description=f"Prophet model for {signal}")
        artifact.add_file(str(path))
        run.log_artifact(artifact)

        mae_str = f"MAE={metrics.get('holdout_mae', 'n/a')}"
        print(f"  Done — {mae_str}, fit in {metrics['fit_seconds']}s")

    # Save combined bundle
    bundle_path = OUTPUT_DIR / "forecaster_v1.pkl"
    with open(bundle_path, "wb") as f:
        pickle.dump(models, f)
    print(f"\nBundle saved → {bundle_path}")

    # Summary table
    table = wandb.Table(columns=["signal", "n_train", "holdout_mae", "holdout_mape_pct", "fit_seconds"])
    for m in all_metrics:
        table.add_data(m["signal"], m.get("n_train", 0),
                       m.get("holdout_mae", None), m.get("holdout_mape_pct", None),
                       m.get("fit_seconds", 0))
    wandb.log({"results": table})

    bundle_artifact = wandb.Artifact("forecaster-v1-bundle", type="model")
    bundle_artifact.add_file(str(bundle_path))
    run.log_artifact(bundle_artifact)

    run.finish()
    print("\nDone. W&B run:", run.url if not offline else "(offline mode)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=200)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    main(sample=args.sample, offline=args.offline)
