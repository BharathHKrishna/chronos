import pytest
from apps.api.services.forecaster import run_forecast, SCENARIO_MODIFIERS

MOCK_HISTORY = {
    "ndvi": [{"year": y, "value": 0.5 - (y - 1985) * 0.003, "source": "Landsat"} for y in range(1985, 2026)],
    "nighttime_lights": [{"year": y, "value": 5.0 + (y - 1985) * 0.8, "source": "DMSP-OLS"} for y in range(1985, 2026)],
    "land_surface_temp": [{"year": y, "value": 27.0 + (y - 1985) * 0.04, "source": "MODIS-LST"} for y in range(2000, 2026)],
    "built_up_extent": [{"year": y, "value": 0.05 + (y - 1985) * 0.005, "source": "GHSL"} for y in range(1985, 2026)],
}


def test_bau_forecast_returns_2026_2050():
    result = run_forecast(MOCK_HISTORY, "bau")
    assert result["scenario"] == "bau"
    years = [r["year"] for r in result["signals"]["ndvi"]]
    assert 2026 in years
    assert 2050 in years


def test_all_scenarios_run():
    for scenario in SCENARIO_MODIFIERS:
        result = run_forecast(MOCK_HISTORY, scenario)
        assert result["scenario"] == scenario


def test_solar_ndvi_higher_than_stress():
    solar = run_forecast(MOCK_HISTORY, "solar")
    stress = run_forecast(MOCK_HISTORY, "stress")
    solar_2050 = next(r["value"] for r in solar["signals"]["ndvi"] if r["year"] == 2050)
    stress_2050 = next(r["value"] for r in stress["signals"]["ndvi"] if r["year"] == 2050)
    assert solar_2050 > stress_2050


def test_sparse_series_falls_back_gracefully():
    sparse_history = {k: [] for k in MOCK_HISTORY}
    result = run_forecast(sparse_history, "bau")
    assert len(result["signals"]["ndvi"]) == 25  # 2026–2050
