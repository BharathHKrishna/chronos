"""
Tile renderer.

Past years  (≤ 2025): fetch Landsat/Sentinel RGB composite from GEE and return PNG.
Future years (> 2025): apply color-shift transforms to the most recent real tile
                       based on forecast signal deltas.

v2 extension point: replace _render_future() with a ControlNet diffusion call.
"""

from __future__ import annotations
import io
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


def _landsat_rgb_bytes(lat: float, lon: float, year: int) -> bytes | None:
    """Attempt to fetch a real RGB tile from GEE for a past year."""
    try:
        import ee
        from apps.api.services.gee_fetcher import _init_gee, _point
        _init_gee()

        region = _point(lat, lon)
        scale = 30

        if year <= 2012:
            col_id = "LANDSAT/LT05/C02/T1_L2"
            bands = ["SR_B3", "SR_B2", "SR_B1"]
        elif year <= 2021:
            col_id = "LANDSAT/LC08/C02/T1_L2"
            bands = ["SR_B4", "SR_B3", "SR_B2"]
        else:
            col_id = "LANDSAT/LC09/C02/T1_L2"
            bands = ["SR_B4", "SR_B3", "SR_B2"]

        img = (
            ee.ImageCollection(col_id)
            .filter(ee.Filter.calendarRange(year, year, "year"))
            .filter(ee.Filter.lt("CLOUD_COVER", 20))
            .select(bands)
            .median()
            .multiply(0.0000275)
            .add(-0.2)
            .clamp(0, 1)
        )
        url = img.getThumbURL({"region": region, "dimensions": 256, "format": "png"})
        import httpx
        resp = httpx.get(url, timeout=20)
        if resp.status_code == 200:
            return resp.content
    except Exception:
        pass
    return None


def _synthetic_tile(lat: float, lon: float, year: int, is_future: bool = False) -> bytes:
    """Generate a simple coloured placeholder tile when GEE is unavailable."""
    fig, ax = plt.subplots(figsize=(2.56, 2.56), dpi=100)
    ax.set_axis_off()

    # Colour encodes vegetation presence (lat heuristic) + urban age
    green_base = max(0.1, min(0.8, 0.5 - abs(lat) / 90 * 0.3))
    tan_base = 1 - green_base
    year_norm = (year - 1985) / (2050 - 1985)

    r = tan_base * 0.8 + year_norm * 0.15
    g = green_base * 0.7 - year_norm * 0.1
    b = 0.15 + year_norm * 0.05
    color = np.clip([r, g, b], 0, 1)

    noise = np.random.default_rng(seed=int(abs(lat * 100) + abs(lon * 100) + year)).random((256, 256, 3)) * 0.06
    base = np.full((256, 256, 3), color) + noise
    base = np.clip(base, 0, 1)

    ax.imshow(base)
    label = f"{'~' if is_future else ''}{year}"
    ax.text(0.05, 0.05, label, transform=ax.transAxes, color="white",
            fontsize=8, alpha=0.7, va="bottom")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _render_future(base_tile_bytes: bytes, ndvi_delta: float, lst_delta: float, built_delta: float) -> bytes:
    """
    Apply perceptual shifts to base tile to represent future state.
    ndvi_delta  < 0 → desaturate greens, add brownish tint
    lst_delta   > 0 → slight warm shift
    built_delta > 0 → darken + grey-shift (urbanisation)
    """
    img = Image.open(io.BytesIO(base_tile_bytes)).convert("RGB")
    arr = np.array(img, dtype=np.float32) / 255.0

    # Vegetation loss: reduce green channel relative to red
    if ndvi_delta < 0:
        arr[:, :, 1] = np.clip(arr[:, :, 1] + ndvi_delta * 0.3, 0, 1)
        arr[:, :, 0] = np.clip(arr[:, :, 0] - ndvi_delta * 0.15, 0, 1)

    # Heat: warm the image
    if lst_delta > 0:
        arr[:, :, 0] = np.clip(arr[:, :, 0] + lst_delta * 0.02, 0, 1)
        arr[:, :, 2] = np.clip(arr[:, :, 2] - lst_delta * 0.01, 0, 1)

    # Urbanisation: grey/darken
    if built_delta > 0:
        grey = arr.mean(axis=2, keepdims=True)
        arr = arr * (1 - built_delta * 0.3) + grey * (built_delta * 0.3)

    result = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8))
    buf = io.BytesIO()
    result.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


async def render_tile(lat: float, lon: float, year: int) -> bytes:
    from apps.api.cache import get_cached, coord_key
    lat_k, lon_k = coord_key(lat, lon)

    if year <= 2025:
        real = _landsat_rgb_bytes(lat, lon, year)
        if real:
            return real
        return _synthetic_tile(lat, lon, year, is_future=False)

    # Future: find base tile (2024 or 2025) and apply signal deltas
    base_bytes = None
    for base_year in (2025, 2024, 2023):
        tile_key = f"tile:{lat_k}:{lon_k}:{base_year}"
        cached = await get_cached(tile_key)
        if cached:
            import base64
            base_bytes = base64.b64decode(cached["png_b64"])
            break
    if base_bytes is None:
        base_bytes = _landsat_rgb_bytes(lat, lon, 2024) or _synthetic_tile(lat, lon, 2024)

    # Fetch forecast signals to compute deltas from 2025 baseline
    forecast_key = f"forecast:{lat_k}:{lon_k}:bau"
    forecast_cache = await get_cached(forecast_key)

    ndvi_delta = lst_delta = built_delta = 0.0
    if forecast_cache:
        signals = forecast_cache.get("signals", {})
        for sig, key, target in [
            ("ndvi", "ndvi", ndvi_delta),
            ("land_surface_temp", "lst", lst_delta),
            ("built_up_extent", "built", built_delta),
        ]:
            series = signals.get(sig, [])
            val_at_year = next((r["value"] for r in series if r["year"] == year), None)
            val_at_2025 = next((r["value"] for r in series if r["year"] == 2026), None)
            if val_at_year is not None and val_at_2025 is not None and val_at_2025 != 0:
                if sig == "ndvi":
                    ndvi_delta = val_at_year - val_at_2025
                elif sig == "land_surface_temp":
                    lst_delta = val_at_year - val_at_2025
                elif sig == "built_up_extent":
                    built_delta = (val_at_year - val_at_2025) / max(abs(val_at_2025), 1)

    return _render_future(base_bytes, ndvi_delta, lst_delta, built_delta)
