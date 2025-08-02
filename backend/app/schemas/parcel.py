from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from pydantic import BaseModel


class ParcelBase(BaseModel):
    apn: str
    county: str
    state: str
    owner_name: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class ParcelCreate(ParcelBase):
    pass


class ParcelUpdate(BaseModel):
    owner_name: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class ParcelRead(ParcelBase):
    id: int
    owner_id: Optional[int]

    class Config:
        from_attributes = True

class ParcelLookupRequest(BaseModel):
    apn: str
    street_address: Optional[str] = None
    county: Optional[str] = None
    state: Optional[str] = None

class ParcelUtilityInfo(BaseModel):
    apn: str                           
    electric_available: bool
    electric_provider: Optional[str]
    water_available: bool
    water_provider: Optional[str]
    sewer_available: bool
    sewer_provider: Optional[str]
    well_available: Optional[bool] = None
    well_use: Optional[str] = None
    septic_present: Optional[bool] = None

    class Config:
        from_attributes = True  # allows SQLModel → pydantic if needed

class ParcelUtilityList(BaseModel):
    results: List[ParcelUtilityInfo]