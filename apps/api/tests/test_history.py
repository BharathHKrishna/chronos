import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from apps.api.main import app

client = TestClient(app)

MOCK_HISTORY = {
    "ndvi": [{"year": y, "value": 0.5, "source": "Landsat"} for y in range(1985, 2026)],
    "nighttime_lights": [{"year": y, "value": 20.0, "source": "DMSP-OLS"} for y in range(1985, 2026)],
    "land_surface_temp": [{"year": y, "value": 28.0, "source": "MODIS-LST"} for y in range(1985, 2026)],
    "built_up_extent": [{"year": y, "value": 0.1, "source": "GHSL"} for y in range(1985, 2026)],
}


@pytest.mark.asyncio
async def test_history_cache_hit():
    with patch("apps.api.routes.history.get_cached", new=AsyncMock(return_value=MOCK_HISTORY)):
        response = client.get("/history?lat=12.97&lon=77.59")
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "cache"
    assert "ndvi" in data["data"]


@pytest.mark.asyncio
async def test_history_cache_miss_live():
    with (
        patch("apps.api.routes.history.get_cached", new=AsyncMock(return_value=None)),
        patch("apps.api.routes.history.fetch_history", return_value=MOCK_HISTORY),
        patch("apps.api.routes.history.set_cached", new=AsyncMock()),
    ):
        response = client.get("/history?lat=12.97&lon=77.59")
    assert response.status_code == 200
    assert response.json()["source"] == "live"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
