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
    """
    Interprets a wide variety of truthy / falsy tokens used in ArcGIS layers.
    Returns True, False, or None if indeterminate.
    """
    if v is None:
        return None
    if isinstance(v, bool):
        return v

    s = str(v).strip().lower()

    truthy = {
        "y", "yes", "true", "1",
        "knownwell", "known septic", "knownseptic",  # FL DOH layer
        "knownwellandseptic", "known well", "known septic",
        "private", "onsite", "available", "LikelySeptic", "LikelyWell", 
        "LikelySewer", "Known Public", "Likely Public", "Known Sewer"
    }
    falsy = {
        "n", "no", "false", "0",
        "none", "public", "notavailable", "unknown", "na"
    }

    if s.replace(" ", "") in truthy:
        return True
    if s.replace(" ", "") in falsy:
        return False
    return None


def _parse_date(s: Any) -> datetime | None:
    if not s: return None
    try:
        if isinstance(s, (int, float)):
            return datetime.utcfromtimestamp(float(s)/1000.0)  # epoch ms
        return datetime.fromisoformat(str(s).replace("Z",""))
    except Exception:
        return None

async def _utilities_for_parcel(layer: LayerCfg, strap: str) -> list[dict]:
    """
    Query statewide FL DOH well/septic layer by parcel identifiers.
    Tries both PARCELNO and ALT_KEY; falls back to geometry (point-in-poly)
    if the ID lookup fails.
    """
    # attribute query by PARCELNO or ALT_KEY
    attr_where = f"PARCELNO='{strap}' OR ALT_KEY='{strap}'"
    resp = await _arcgis_query(
        layer,
        {"where": attr_where, "returnGeometry": False, "outSR": 4326},
    )
    feats = resp.get("features", [])
    if feats:
        return [f["attributes"] for f in feats]

    # no record by ID → optional geometry fallback (centroid within 25 m buffer)
    # (Useful for vacant parcels whose IDs weren’t captured.)
    return []

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

def _norm(s: Optional[str]) -> str:
    return (s or "").strip().lower()

def _classify_water_sewer(dw: str | None, ww: str | None) -> tuple[bool | None, bool | None, bool | None]:
    """
    Map FLWMI DrinkingWater (DW) / WasteWater (WW) strings to:
      (well_available, water_connected, sewer_connected)

    DW examples seen:
      "KnownWell", "Known Private Well", "Public", "Known Public", "None", "Unknown"
    WW examples seen:
      "KnownSeptic", "Known Onsite Septic", "Known Sewer", "Public", "None", "Unknown"
    """
    dw_s = _norm(dw)
    ww_s = _norm(ww)

    # ---- WELL / CITY WATER ---------------------------------------------------
    well_available: Optional[bool] = None
    water_connected: Optional[bool] = None

    if dw_s:
        if "public" in dw_s:
            # City/Public water service connected
            well_available = False
            water_connected = True
        elif "well" in dw_s:  # catches "KnownWell", "Known Private Well", etc.
            well_available = True
            water_connected = False
        elif dw_s in {"none", "unknown"}:
            well_available = None
            water_connected = None

    # ---- CITY SEWER / SEPTIC -------------------------------------------------
    sewer_connected: Optional[bool] = None
    if ww_s:
        # Prioritize "septic" vs "sewer"
        if "sewer" in ww_s and "septic" not in ww_s:
            sewer_connected = True
        elif "septic" in ww_s:
            sewer_connected = False
        elif ww_s in {"public"}:
            # "Public" in WW context generally implies connection to public sewer,
            # but FLWMI sometimes uses "Public" as a generic source tag.
            sewer_connected = True
        elif ww_s in {"none", "unknown"}:
            sewer_connected = None

    return well_available, water_connected, sewer_connected

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

    if geom:
        lon, lat = geom["lon"], geom["lat"]
        electric = await _point_in_layer(cfg.electric_territory_layer, lon, lat)
        water = await _point_in_layer(cfg.water_layer, lon, lat) 
        sewer = await _point_in_layer(cfg.sewer_layer, lon, lat)
    else:
        electric = None
        water =  None
        sewer = None


    well_available: Optional[bool] = None
    septic_present: Optional[bool] = None
    water_connected: Optional[bool] = None
    sewer_connected: Optional[bool] = None

    wells_layer = getattr(cfg, "wells_layer", None)
    if wells_layer:
        rows = await _utilities_for_parcel(wells_layer, apn)
        if rows:
            row = rows[0]                      # FLWMI = one row per parcel
            well_available, water_connected, sewer_connected = _classify_water_sewer(
                row.get("DW"), row.get("WW")
            )
            # septic_present duplicated for clarity
            septic_present = None
            if sewer_connected is not None:
                septic_present = not sewer_connected
            elif row.get("WW"):
                septic_present = _parse_bool(row["WW"])

    return ParcelUtilityInfo(
        apn=apn,
        electric_available=bool(electric),
        electric_provider=electric,
        water_available=bool(water),
        water_provider=water,
        sewer_available=bool(sewer),
        sewer_provider=sewer,
        well_available=well_available if well_available else False,
        septic_present=septic_present if septic_present else False,
        water_connected=water_connected if water_connected else False,
        sewer_connected=sewer_connected if sewer_connected else False
    )
