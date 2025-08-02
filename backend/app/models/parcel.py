from datetime import datetime
from typing import Optional, Dict, Any

from sqlmodel import SQLModel, Field, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column


class Parcel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    apn: str = Field(index=True, nullable=False)
    county: str
    state: str
    owner_name: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB))
    owner_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
