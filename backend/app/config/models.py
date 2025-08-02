# config/models.py
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, HttpUrl, ValidationError, Field

class LayerCfg(BaseModel):
    url: HttpUrl
    static_params: Dict[str, Any]
    dynamic_params: List[str] = Field(default_factory=list)
    provider_field: str = "UtilityName"

class CountyCfg(BaseModel):
    id_field: str = "APN" 
    parcel_layer: LayerCfg
    electric_territory_layer: LayerCfg
    water_layer: LayerCfg
    sewer_layer: LayerCfg
    wells_layer: LayerCfg
    # add optional layers as needed, e.g. water_layer: LayerCfg | None = None

Catalogue = Dict[str, CountyCfg]
