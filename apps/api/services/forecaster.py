"""
Scenario-conditioned forecaster (v1: Prophet per signal).

Scenarios are implemented as multiplicative modifiers on Prophet's trend
and seasonality. They are indicative, not physical simulations.

Modifier table:
  signal          bau   solar  grid  stress
  ndvi_trend      1.0   1.1    0.95  0.80
  lst_trend       1.0   0.85   1.05  1.25
  lights_trend    1.0   0.90   1.30  1.00
  builtup_trend   1.0   1.00   1.15  1.05
"""

from __future__ import annotations
import warnings
from typing import Any
import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")  # suppress Prophet verbose output

SCENARIO_MODIFIERS: dict[str, dict[str, float]] = {
    "bau":    {"ndvi": 1.00, "lst": 1.00, "lights": 1.00, "builtup": 1.00},
    "solar":  {"ndvi": 1.10, "lst": 0.85, "lights": 0.90, "builtup": 1.00},
    "grid":   {"ndvi": 0.95, "lst": 1.05, "lights": 1.30, "builtup": 1.15},
    "stress": {"ndvi": 0.80, "lst": 1.25, "lights": 1.00, "builtup": 1.05},
}

SIGNAL_KEYS = {
    "ndvi": "ndvi",
    "nighttime_lights": "lights",
    "land_surface_temp": "lst",
    "built_up_extent": "builtup",
}


def _prophet_forecast(
    series: list[dict],
    modifier: float,
    horizon_years: int = 25,
) -> list[dict]:
    """
    Fit Prophet on historical values, project forward, apply scenario modifier.
    Returns list of {year, value, lower, upper} for 2026–2050.
    """
    from prophet import Prophet

    records = [
        {"ds": pd.Timestamp(f"{r['year']}-07-01"), "y": r["value"]}
        for r in series
        if r["value"] is not None
    ]
    if len(records) < 5:
        # Not enough data — return flat extrapolation from last known value
        last = next((r["value"] for r in reversed(series) if r["value"] is not None), 0.0)
        return [
            {"year": y, "value": last * modifier, "lower": last * modifier * 0.9, "upper": last * modifier * 1.1}
            for y in range(2026, 2051)
        ]

    df = pd.DataFrame(records).dropna()
    model = Prophet(
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=False,
        uncertainty_samples=500,
    )
    model.fit(df)

    future = model.make_future_dataframe(periods=horizon_years + 1, freq="YE")
    forecast_df = model.predict(future)

    results = []
    for _, row in forecast_df[forecast_df["ds"].dt.year >= 2026].iterrows():
        year = row["ds"].year
        value = float(row["yhat"]) * modifier
        lower = float(row["yhat_lower"]) * modifier
        upper = float(row["yhat_upper"]) * modifier
        results.append({"year": year, "value": value, "lower": lower, "upper": upper})

    return results


def run_forecast(history: dict[str, list[dict]], scenario: str) -> dict[str, Any]:
    """
    Given cached history and a scenario ID, return projected signals 2026–2050.
    Returns dict keyed by signal name, each a list of {year, value, lower, upper}.
    """
    modifiers = SCENARIO_MODIFIERS.get(scenario, SCENARIO_MODIFIERS["bau"])
    output: dict[str, list[dict]] = {}

    for history_key, mod_key in SIGNAL_KEYS.items():
        series = history.get(history_key, [])
        modifier = modifiers[mod_key]
        output[history_key] = _prophet_forecast(series, modifier)

    return {"scenario": scenario, "signals": output}
