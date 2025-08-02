# app/services/utility_lookup.py
import httpx
import json
from typing import Any, Optional
from pydantic import BaseModel
from slugify import slugify 

from ..schemas.parcel import ParcelUtilityInfo
from ..config.loader import load_catalogue
from ..config.models import LayerCfg, CountyCfg

CATALOGUE = load_catalogue()          #one global source of truth
HTTP_TIMEOUT = httpx.Timeout(10.0)

# services/utility_lookup.py  – inside _parcel_geometry

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
    params = layer.static_params | extra_params
    url: str = str(layer.url)          # <- cast to vanilla str
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        return r.json()
    
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

    return ParcelUtilityInfo(
        apn=apn,
        electric_available=bool(electric),
        electric_provider=electric,
        water_available=bool(water),
        water_provider=water,
        sewer_available=bool(sewer),
        sewer_provider=sewer,
    )
