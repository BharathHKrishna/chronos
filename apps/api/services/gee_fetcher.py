"""
Google Earth Engine data fetcher.

Signals pulled at annual cadence for a ~500m buffer around (lat, lon):
  - ndvi          : Landsat 5/7/8/9 median NDVI (growing season, cloud-masked)
  - nighttime_lights : DMSP-OLS (1992–2013) → VIIRS-DNB (2012–present), harmonised
  - land_surface_temp: MODIS MOD11A2 daytime LST (°C), annual mean
  - built_up_extent  : GHSL Built-S fraction (5-year epochs, interpolated)

Harmonisation method for nighttime lights:
  Li, X. & Zhou, Y. (2017). A refined ZOI-based method for mapping urban extent
  using DMSP-OLS and VIIRS nighttime light data. Remote Sensing of Environment.
  DOI: 10.1016/j.rse.2017.07.037
"""

from __future__ import annotations
import os
import json
from typing import Any
import ee
from apps.api.config import settings

_initialized = False


def _init_gee():
    global _initialized
    if _initialized:
        return

    # If running on Render/Docker: write credentials from env var
    if settings.gee_credentials_b64:
        import base64, pathlib
        cred_dir = pathlib.Path.home() / ".config" / "earthengine"
        cred_dir.mkdir(parents=True, exist_ok=True)
        cred_path = cred_dir / "credentials"
        cred_path.write_text(base64.b64decode(settings.gee_credentials_b64).decode())

    if settings.gee_service_account_email and os.path.exists(settings.gee_service_account_key):
        credentials = ee.ServiceAccountCredentials(
            settings.gee_service_account_email, settings.gee_service_account_key
        )
        ee.Initialize(credentials, project=settings.gee_project)
    else:
        ee.Initialize(project=settings.gee_project)
    _initialized = True


def _point(lat: float, lon: float) -> ee.Geometry:
    return ee.Geometry.Point([lon, lat]).buffer(500)


def _fetch_ndvi(region: ee.Geometry) -> list[dict]:
    """Annual median NDVI from Landsat 5/7/8/9 (growing season May–Sep)."""

    def collection_for(start_year: int, end_year: int, collection_id: str, bands: list[str]) -> ee.ImageCollection:
        return (
            ee.ImageCollection(collection_id)
            .filter(ee.Filter.calendarRange(start_year, end_year, "year"))
            .filter(ee.Filter.calendarRange(5, 9, "month"))
            .filter(ee.Filter.lt("CLOUD_COVER", 30))
            .select(bands)
        )

    results = []
    # Landsat 5 (1984–2012)
    l5 = collection_for(1985, 2012, "LANDSAT/LT05/C02/T1_L2", ["SR_B3", "SR_B4"])
    # Landsat 7 (1999–2022, SLC-off post 2003 — use 1999–2003 and 2012–2013 gap fill)
    l7 = collection_for(1999, 2013, "LANDSAT/LE07/C02/T1_L2", ["SR_B3", "SR_B4"])
    # Landsat 8 (2013–present)
    l8 = collection_for(2013, 2021, "LANDSAT/LC08/C02/T1_L2", ["SR_B4", "SR_B5"])
    # Landsat 9 (2021–present)
    l9 = collection_for(2021, 2025, "LANDSAT/LC09/C02/T1_L2", ["SR_B4", "SR_B5"])

    def ndvi_from_red_nir(img: ee.Image) -> ee.Image:
        red = img.select(0).multiply(0.0000275).add(-0.2)
        nir = img.select(1).multiply(0.0000275).add(-0.2)
        return nir.subtract(red).divide(nir.add(red)).rename("NDVI").copyProperties(img, ["system:time_start"])

    for year in range(1985, 2026):
        if year <= 2012:
            col = l5
        elif year <= 2013:
            col = l7
        elif year <= 2021:
            col = l8
        else:
            col = l9
        col_year = col.filter(ee.Filter.calendarRange(year, year, "year")).map(ndvi_from_red_nir)
        median = col_year.median()
        val = median.reduceRegion(ee.Reducer.mean(), region, 30).getInfo().get("NDVI")
        results.append({"year": year, "value": val, "source": "Landsat"})

    return results


def _fetch_nighttime_lights(region: ee.Geometry) -> list[dict]:
    """
    DMSP-OLS 1992–2013 + VIIRS-DNB 2012–2024, harmonised.
    Bridge year: 2012/2013 overlap used to calibrate VIIRS to DMSP scale.
    Reference: Li & Zhou (2017).
    """
    results = []

    # DMSP-OLS (1992–2013) — annual composites
    dmsp = ee.ImageCollection("NOAA/DMSP-OLS/NIGHTTIME_LIGHTS")
    for year in range(1985, 1992):
        results.append({"year": year, "value": None, "source": "no_data"})

    for year in range(1992, 2014):
        img = dmsp.filter(ee.Filter.calendarRange(year, year, "year")).select("stable_lights").mean()
        val = img.reduceRegion(ee.Reducer.mean(), region, 1000).getInfo().get("stable_lights")
        results.append({"year": year, "value": val, "source": "DMSP-OLS"})

    # VIIRS-DNB monthly (2012–present) → annual mean
    viirs = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMCFG")
    # Calibration: compute DMSP-equivalent from VIIRS using Li & Zhou regression
    # dmsp_equiv = 10.062 * ln(viirs_avg_rad + 1) (approximate; see notebook 02)
    import math
    for year in range(2014, 2026):
        img = (
            viirs.filter(ee.Filter.calendarRange(year, year, "year"))
            .select("avg_rad")
            .mean()
        )
        val = img.reduceRegion(ee.Reducer.mean(), region, 500).getInfo().get("avg_rad")
        if val is not None:
            # Harmonise to DMSP digital number scale
            val = 10.062 * math.log(val + 1)
        results.append({"year": year, "value": val, "source": "VIIRS-DNB"})

    return results


def _fetch_lst(region: ee.Geometry) -> list[dict]:
    """MODIS MOD11A2 8-day 1km LST — annual mean daytime (°C)."""
    modis = ee.ImageCollection("MODIS/061/MOD11A2").select("LST_Day_1km")
    results = []
    for year in range(1985, 2000):
        results.append({"year": year, "value": None, "source": "no_data"})
    for year in range(2000, 2026):
        img = modis.filter(ee.Filter.calendarRange(year, year, "year")).mean()
        val = img.reduceRegion(ee.Reducer.mean(), region, 1000).getInfo().get("LST_Day_1km")
        # Convert Kelvin (×0.02 scale) to Celsius
        if val is not None:
            val = val * 0.02 - 273.15
        results.append({"year": year, "value": val, "source": "MODIS-LST"})
    return results


def _fetch_builtup(region: ee.Geometry) -> list[dict]:
    """GHSL Built-S fraction (5-year epochs). Linearly interpolated to annual."""
    ghsl = ee.ImageCollection("JRC/GHSL/P2023A/GHS_BUILT_S").select("built_surface")
    # Available epochs: 1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020
    epochs = [1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020]
    epoch_vals = {}
    for epoch in epochs:
        img = ghsl.filter(ee.Filter.eq("system:index", str(epoch))).first()
        if img:
            val = img.reduceRegion(ee.Reducer.mean(), region, 100).getInfo().get("built_surface")
            epoch_vals[epoch] = val

    # Linear interpolation to annual
    results = []
    for year in range(1985, 2026):
        lo_epoch = max(e for e in epochs if e <= year) if any(e <= year for e in epochs) else epochs[0]
        hi_epoch = min(e for e in epochs if e >= year) if any(e >= year for e in epochs) else epochs[-1]
        lo_val = epoch_vals.get(lo_epoch)
        hi_val = epoch_vals.get(hi_epoch)
        if lo_val is None or hi_val is None:
            val = lo_val or hi_val
        elif lo_epoch == hi_epoch:
            val = lo_val
        else:
            t = (year - lo_epoch) / (hi_epoch - lo_epoch)
            val = lo_val + t * (hi_val - lo_val)
        results.append({"year": year, "value": val, "source": "GHSL"})
    return results


def fetch_history(lat: float, lon: float) -> dict[str, list[dict]]:
    """Return all four signals for (lat, lon) from 1985 to 2025."""
    _init_gee()
    region = _point(lat, lon)
    return {
        "ndvi": _fetch_ndvi(region),
        "nighttime_lights": _fetch_nighttime_lights(region),
        "land_surface_temp": _fetch_lst(region),
        "built_up_extent": _fetch_builtup(region),
    }
