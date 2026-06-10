import asyncio
import json
import traceback
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from apps.api.cache import get_cached, set_cached, coord_key
from apps.api.services.gee_fetcher import fetch_history

router = APIRouter()


@router.get("")
async def get_history(lat: float, lon: float):
    """
    Return time-series 1985–2025 for (lat, lon) as an SSE stream.
    Cache hits respond instantly with a single 'done' event.
    Live GEE fetches stream keep-alive pings every 15 s so Render's
    30-second idle timeout never fires, then send 'done' when ready.
    """
    lat_k, lon_k = coord_key(lat, lon)
    cache_key = f"history:{lat_k}:{lon_k}"

    cached = await get_cached(cache_key)
    if cached:
        payload = json.dumps({"status": "done", "source": "cache",
                              "lat": lat, "lon": lon, "data": cached})
        async def instant():
            yield f"data: {payload}\n\n"
        return StreamingResponse(instant(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache",
                                          "X-Accel-Buffering": "no"})

    async def live_stream():
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(None, fetch_history, lat, lon)
        while not future.done():
            yield ": keep-alive\n\n"
            try:
                await asyncio.wait_for(asyncio.shield(future), timeout=15)
            except asyncio.TimeoutError:
                pass
        try:
            data = future.result()
            await set_cached(cache_key, data)
            payload = json.dumps({"status": "done", "source": "live",
                                   "lat": lat, "lon": lon, "data": data})
            yield f"data: {payload}\n\n"
        except Exception as exc:
            err = json.dumps({"status": "error",
                              "detail": str(exc),
                              "traceback": traceback.format_exc()})
            yield f"data: {err}\n\n"

    return StreamingResponse(live_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})
