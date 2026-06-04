"""
Google Earth Engine data fetcher.

Uses sequential per-year getInfo() calls — simple and reliable.
For production Render deployment, demo-location data is pre-seeded
at startup from data/seed/demo_locations.json (generated offline).

Signals:
  ndvi               Landsat 5/7/8/9 median NDVI (growing season, cloud-masked)
  nighttime_lights   DMSP-OLS (1992–2013) → VIIRS-DNB (2012–2025), harmonised
                     via Li & Zhou (2017) DOI:10.1016/j.rse.2017.07.037
  land_surface_temp  MODIS MOD11A2 daytime LST annual mean (°C)
  built_up_extent    GHSL Built-S fraction (5-year epochs, linearly interpolated)
"""

from __future__ import annotations
import math
import os
import ee
from apps.api.config import settings

_initialized = False


def _init_gee():
    global _initialized
    if _initialized:
        return
    if settings.gee_credentials_b64:
        import base64, pathlib
        cred_dir = pathlib.Path.home() / ".config" / "earthengine"
        cred_dir.mkdir(parents=True, exist_ok=True)
        (cred_dir / "credentials").write_text(
            base64.b64decode(settings.gee_credentials_b64).decode()
        )
    if settings.gee_service_account_email and os.path.exists(settings.gee_service_account_key):
        creds = ee.ServiceAccountCredentials(
            settings.gee_service_account_email, settings.gee_service_account_key
        )
        ee.Initialize(creds, project=settings.gee_project)
    else:
        ee.Initialize(project=settings.gee_project)
    _initialized = True


def _point(lat: float, lon: float) -> ee.Geometry:
    return ee.Geometry.Point([lon, lat]).buffer(500)


def _fetch_ndvi(region: ee.Geometry) -> list[dict]:
    results = []
    for year in range(1985, 2026):
        if year <= 2012:
            col_id, red, nir = "LANDSAT/LT05/C02/T1_L2", "SR_B3", "SR_B4"
        elif year <= 2021:
            col_id, red, nir = "LANDSAT/LC08/C02/T1_L2", "SR_B4", "SR_B5"
        else:
            col_id, red, nir = "LANDSAT/LC09/C02/T1_L2", "SR_B4", "SR_B5"
        img = (
            ee.ImageCollection(col_id)
            .filter(ee.Filter.calendarRange(year, year, "year"))
            .filter(ee.Filter.calendarRange(5, 9, "month"))
            .filter(ee.Filter.lt("CLOUD_COVER", 30))
            .select([red, nir])
            .median()
        )
        r = img.select(0).multiply(0.0000275).add(-0.2)
        n = img.select(1).multiply(0.0000275).add(-0.2)
        val = n.subtract(r).divide(n.add(r)).rename("NDVI") \
               .reduceRegion(ee.Reducer.mean(), region, 30).getInfo().get("NDVI")
        results.append({"year": year, "value": val, "source": "Landsat"})
    return results


def _fetch_nighttime_lights(region: ee.Geometry) -> list[dict]:
    results = [{"year": y, "value": None, "source": "no_data"} for y in range(1985, 1992)]
    dmsp = ee.ImageCollection("NOAA/DMSP-OLS/NIGHTTIME_LIGHTS")
    for year in range(1992, 2014):
        val = (dmsp.filter(ee.Filter.calendarRange(year, year, "year"))
                   .select("stable_lights").mean()
                   .reduceRegion(ee.Reducer.mean(), region, 1000).getInfo().get("stable_lights"))
        results.append({"year": year, "value": val, "source": "DMSP-OLS"})
    viirs = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMCFG")
    for year in range(2014, 2026):
        val = (viirs.filter(ee.Filter.calendarRange(year, year, "year"))
                    .select("avg_rad").mean()
                    .reduceRegion(ee.Reducer.mean(), region, 500).getInfo().get("avg_rad"))
        if val is not None:
            val = 10.062 * math.log(val + 1)
        results.append({"year": year, "value": val, "source": "VIIRS-DNB"})
    return results


def _fetch_lst(region: ee.Geometry) -> list[dict]:
    results = [{"year": y, "value": None, "source": "no_data"} for y in range(1985, 2000)]
    modis = ee.ImageCollection("MODIS/061/MOD11A2").select("LST_Day_1km")
    for year in range(2000, 2026):
        val = (modis.filter(ee.Filter.calendarRange(year, year, "year")).mean()
                    .reduceRegion(ee.Reducer.mean(), region, 1000).getInfo().get("LST_Day_1km"))
        if val is not None:
            val = val * 0.02 - 273.15
        results.append({"year": year, "value": val, "source": "MODIS-LST"})
    return results


def _fetch_builtup(region: ee.Geometry) -> list[dict]:
    epochs = [1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020]
    ghsl = ee.ImageCollection("JRC/GHSL/P2023A/GHS_BUILT_S").select("built_surface")
    epoch_vals = {}
    for ep in epochs:
        img = ghsl.filter(ee.Filter.eq("system:index", str(ep))).first()
        if img:
            v = img.reduceRegion(ee.Reducer.mean(), region, 100).getInfo().get("built_surface")
            epoch_vals[ep] = v
    results = []
    for year in range(1985, 2026):
        lo = max((e for e in epochs if e <= year), default=epochs[0])
        hi = min((e for e in epochs if e >= year), default=epochs[-1])
        lo_v, hi_v = epoch_vals.get(lo), epoch_vals.get(hi)
        if lo_v is None or hi_v is None:
            val = lo_v or hi_v
        elif lo == hi:
            val = lo_v
        else:
            t = (year - lo) / (hi - lo)
            val = lo_v + t * (hi_v - lo_v)
        results.append({"year": year, "value": val, "source": "GHSL"})
    return results


def fetch_history(lat: float, lon: float) -> dict[str, list[dict]]:
    _init_gee()
    region = _point(lat, lon)
    return {
        "ndvi": _fetch_ndvi(region),
        "nighttime_lights": _fetch_nighttime_lights(region),
        "land_surface_temp": _fetch_lst(region),
        "built_up_extent": _fetch_builtup(region),
    }
