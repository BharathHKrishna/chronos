"""
LLM narrative writer via Groq (Llama 3.3-70B).

Prompt is grounded: we extract concrete numbers from the history/forecast dicts
and force the model to cite them. This prevents hallucination and satisfies
the "epistemic honesty" principle (confidence bands, scenario labelling).
"""

from __future__ import annotations
import json
from groq import AsyncGroq
from apps.api.config import settings

SCENARIO_LABELS = {
    "bau": "business as usual",
    "solar": "aggressive solar buildout",
    "grid": "grid expansion",
    "stress": "climate stress",
}


def _extract_stats(signals: dict) -> dict:
    """Pull first/last/change stats from a signal list."""
    stats = {}
    for sig_name, series in signals.items():
        valid = [r for r in series if r.get("value") is not None]
        if not valid:
            continue
        first = valid[0]
        last = valid[-1]
        delta = last["value"] - first["value"] if first["value"] else None
        pct = (delta / abs(first["value"]) * 100) if (delta is not None and first["value"]) else None
        stats[sig_name] = {
            "first_year": first["year"],
            "first_value": round(first["value"], 3),
            "last_year": last["year"],
            "last_value": round(last["value"], 3),
            "absolute_change": round(delta, 3) if delta is not None else None,
            "percent_change": round(pct, 1) if pct is not None else None,
        }
    return stats


SYSTEM_PROMPT = """You are a geospatial scientist writing a short data diary about a specific location on Earth.
Write exactly 4–6 sentences. You MUST cite the actual numbers provided — do not invent values.
Be precise, grounded, and slightly poetic. Avoid jargon overload.
Label future projections as indicative, not certain.
Do not use bullet points or headers."""

USER_TEMPLATE = """Location: ({lat:.4f}, {lon:.4f})

Historical signals (1985–2025):
{history_stats}

Projected signals (2026–2050) under scenario: "{scenario_label}"
{forecast_stats}

Write the diary entry."""


async def write_narrative(
    lat: float,
    lon: float,
    scenario: str,
    history: dict,
    forecast: dict,
) -> str:
    client = AsyncGroq(api_key=settings.groq_api_key)

    history_stats = _extract_stats(history)
    forecast_stats = _extract_stats(forecast.get("signals", {}))
    scenario_label = SCENARIO_LABELS.get(scenario, scenario)

    user_msg = USER_TEMPLATE.format(
        lat=lat,
        lon=lon,
        history_stats=json.dumps(history_stats, indent=2),
        forecast_stats=json.dumps(forecast_stats, indent=2),
        scenario_label=scenario_label,
    )

    completion = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=300,
        temperature=0.6,
    )

    return completion.choices[0].message.content.strip()
