# app/services/utility_lookup.py
import httpx
import json
import asyncio, random

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel
from slugify import slugify 

from ..services.http_client import esri_client, esri_ipv4_guard
from ..schemas.parcel import ParcelUtilityInfo
from ..config.loader import load_catalogue
from ..config.models import LayerCfg, CountyCfg

CATALOGUE = load_catalogue()          #one global source of truth
HTTP_TIMEOUT = httpx.Timeout(10.0)

# services/utility_lookup.py  – inside _parcel_geometry


def _parse_bool(v: Any) -> bool | None:
    if v is None: return None
    if isinstance(v, bool): return v
    s = str(v).strip().lower()
    if s in {"y","yes","true","1"}: return True
    if s in {"n","no","false","0"}: return False
    return None

def _parse_date(s: Any) -> datetime | None:
    if not s: return None
    try:
        if isinstance(s, (int, float)):
            return datetime.utcfromtimestamp(float(s)/1000.0)  # epoch ms
        return datetime.fromisoformat(str(s).replace("Z",""))
    except Exception:
        return None

async def _wells_for_parcel(layer: LayerCfg, strap: str) -> list[dict]:
    """
    Attribute-only query 
    """
    by_attr = await _arcgis_query(
        layer,
        {
            "where": f"PARCEL_STRAP_NUMBER='{strap}'",  # use as-is
            "returnGeometry": False,
            "outSR": 4326,
        },
    )
    feats = by_attr.get("features", [])
    if feats:
        return [f["attributes"] for f in feats]

def _pick_most_recent(rows: list[dict]) -> dict | None:
    if not rows: return None
    def key(r: dict):
        return _parse_date(r.get("last_edited_date")) or _parse_date(r.get("ISSUE_DATE")) or datetime.min
    return max(rows, key=key)


def _catalogue_entry(place: str, state: str) -> CountyCfg | None:
    """
    Try a few slug patterns so callers can supply either a city
    ('Lehigh Acres') or a county ('Lee County' or 'Lee').
    """
    if not place:
        return None

    variants = {
        f"{slugify(place)}_{state.lower()}",
        f"{slugify(place).replace('-', '')}_{state.lower()}",
        f"{slugify(place).replace('-', '_')}_{state.lower()}",
    }
    for key in variants:
        if key in CATALOGUE:
            return CATALOGUE[key]
    return None

async def _arcgis_query(layer: LayerCfg, extra_params: dict[str, Any]) -> dict:
    """
    Central ArcGIS call path:
    - Uses shared client (HTTP/1.1, certifi, retries)
    - Optional IPv4-only DNS (like curl -4)
    - Small extra retry for transient timeouts
    """
    params = layer.static_params | extra_params
    url: str = str(layer.url)
    client = esri_client()

    for attempt in range(1, 3):  # extra retry layer over transport retries
        try:
            # Force IPv4 DNS resolution if enabled (matches your working one-shot)
            with esri_ipv4_guard():
                r = await client.get(url, params=params)
            r.raise_for_status()
            return r.json()
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.RemoteProtocolError):
            if attempt >= 2:
                raise
            await asyncio.sleep(0.25 * attempt + random.random() * 0.25)
    
async def _parcel_geometry(layer: LayerCfg, apn: str, address: Optional[str], id_field: str) -> Optional[dict]:
    """Return centroid geometry for the parcel—or None if not found."""
    where = f"{id_field}='{apn}'" if apn else f"SiteAddress ILIKE '{address}%'" 
    data = await _arcgis_query(
        layer,
        {"where": where, "returnGeometry": True, "outSR": 4326}
    )
    if not data.get("features"):
        return None
    geom = data["features"][0]["geometry"]
    # ArcGIS geometries are in arrays; get centroid for point-in‑polygon query
    centroid = geom.get("centroid") or geom["rings"][0][0]
    return {"lon": centroid[0], "lat": centroid[1]}

async def _point_in_layer(layer: LayerCfg, lon: float, lat: float) -> Optional[str]:
    payload = {
        "geometry": json.dumps({
            "x": lon,
            "y": lat,
            "spatialReference": {"wkid": 4326}
        }),
        "geometryType": "esriGeometryPoint",
        "spatialRel": "esriSpatialRelIntersects",
        "returnGeometry": False,
        **layer.static_params,               # f=json, outFields=..., outSR=...
    }

    data = await _arcgis_query(layer, payload)
    feats = data.get("features", [])
    field = layer.provider_field            # ← pulled from JSON catalogue
    return feats[0]["attributes"].get(field) if feats else None

# ──────────────────────────────────────────────────────────────────────────────
#  Public API
# ──────────────────────────────────────────────────────────────────────────────

# geometry query → point‑in‑polygon → build ParcelUtilityInfo
async def get_utilities_for_parcel(
    apn: str,
    address: Optional[str],
    county: str,
    state: str,
) -> Optional[ParcelUtilityInfo]:
    """Core business logic—kept framework agnostic for re use in Celery, etc."""
    cfg = _catalogue_entry(county, state)
    if not cfg:
        return None

    # 1) Fetch parcel geometry
    geom = await _parcel_geometry(cfg.parcel_layer, apn, address, cfg.id_field)
    if not geom:
        return None

    lon, lat = geom["lon"], geom["lat"]

    # 2) Hit each utility layer (use .getattr in case some counties lack water/sewer)
    electric = await _point_in_layer(cfg.electric_territory_layer, lon, lat)
    water = await _point_in_layer(cfg.water_layer, lon, lat) 
    sewer = await _point_in_layer(cfg.sewer_layer, lon, lat)

    well_available: Optional[bool] = None
    well_use: Optional[str] = None
    septic_present: Optional[bool] = None

    if getattr(cfg, "wells_layer", None):
        rows = await _wells_for_parcel(cfg.wells_layer, apn)
        if rows:
            # Decide presence in the simplest way possible:
            # - well_available: at least one record exists (you can tighten later if needed)
            well_available = True
            # - well_use: take the most recent non-empty WELL_USE
            recent = _pick_most_recent([r for r in rows if (r.get("WELL_USE") or "").strip()])
            well_use = (recent or {}).get("WELL_USE")
            # - septic_present: True if any record shows SEPTIC truthy
            septic_vals = [_parse_bool(r.get("SEPTIC")) for r in rows]
            septic_present = True if any(v is True for v in septic_vals) else (False if any(v is False for v in septic_vals) else None)

    return ParcelUtilityInfo(
        apn=apn,
        electric_available=bool(electric),
        electric_provider=electric,
        water_available=bool(water),
        water_provider=water,
        sewer_available=bool(sewer),
        sewer_provider=sewer,
        well_available=well_available,
        well_use=well_use,
        septic_present=septic_present
    )
