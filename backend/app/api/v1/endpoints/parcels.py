from typing import List

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from ...deps import get_current_user, get_session
from ....models.user import User
from ....services.parcel_lookup import get_utilities_for_parcel
from ....services.csv_processor import parse_in_memory
from ....schemas.parcel import (
    ParcelLookupRequest,
    ParcelUtilityInfo,
    ParcelUtilityList,
)

router = APIRouter(prefix="/parcels", tags=["parcels"])


# ------------------------------------------------------------------
#  1️⃣  Single-parcel lookup
# ------------------------------------------------------------------
@router.post(
    "/lookup",
    response_model=ParcelUtilityInfo,
    summary="Lookup utilities for a single parcel",
)
async def lookup_parcel_utilities(
    payload: ParcelLookupRequest,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Provide an APN (and optionally a street address) and get back
    boolean flags for water, power, sewer.
    """
    info = await get_utilities_for_parcel(
        apn=payload.apn,
        address=payload.street_address,
        county=payload.county,
        state=payload.state,
    )
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parcel not found or utility data unavailable",
        )
    return info


# ------------------------------------------------------------------
#  2️⃣  Bulk upload (CSV / Excel)
# ------------------------------------------------------------------
@router.post(
    "/upload",
    response_model=ParcelUtilityList,
    summary="Upload CSV/Excel and enrich with utility columns",
)
async def upload_parcels_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Accepts `.csv`, `.xls`, or `.xlsx` containing at least
    `apn` and `street_address` columns.  
    Returns a list with `water`, `power`, `sewer` columns added.
    """
    if file.content_type not in {
        "text/csv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be CSV or Excel",
        )

    try:
        raw = await file.read()
        results = await parse_in_memory(raw, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ParcelUtilityList(results=results)
