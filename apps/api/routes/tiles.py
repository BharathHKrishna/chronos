import io
import base64
from fastapi import APIRouter, Response
from apps.api.cache import get_cached, set_cached, coord_key
from apps.api.services.tile_renderer import render_tile
from apps.api.config import settings

router = APIRouter()


@router.get("/{year}")
async def get_tile(year: int, lat: float, lon: float):
    """
    Return a PNG tile for (lat, lon, year).
    For past years: actual Landsat composite (from GEE).
    For future years: color-shifted extrapolation based on forecast signals.
    """
    lat_k, lon_k = coord_key(lat, lon)
    tile_key = f"tile:{lat_k}:{lon_k}:{year}"

    cached = await get_cached(tile_key)
    if cached:
        img_bytes = base64.b64decode(cached["png_b64"])
        return Response(content=img_bytes, media_type="image/png")

    png_bytes = await render_tile(lat, lon, year)
    b64 = base64.b64encode(png_bytes).decode()
    await set_cached(tile_key, {"png_b64": b64}, ttl=settings.tile_cache_ttl_seconds)
    return Response(content=png_bytes, media_type="image/png")
