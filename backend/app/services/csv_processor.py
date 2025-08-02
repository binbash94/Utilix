import io
from typing import List

import pandas as pd

from ..schemas.parcel import ParcelUtilityInfo
from .parcel_lookup import get_utilities_for_parcel


async def parse_in_memory(buffer: bytes, filename: str) -> List[ParcelUtilityInfo]:
    """
    Lightweight parser used synchronously in dev.
    For prod you'll likely off-load to a Celery task and give
    the client a polling endpoint or websocket to stream results.
    """
    ext = filename.lower().split(".")[-1]
    if ext == "csv":
        df = pd.read_csv(io.BytesIO(buffer))
    elif ext in {"xls", "xlsx"}:
        df = pd.read_excel(io.BytesIO(buffer))
    else:
        raise ValueError("Unsupported file type")

    required_cols = {"apn", "street_address"}
    missing = required_cols - set(df.columns.str.lower())
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    results: list[ParcelUtilityInfo] = []
    for _, row in df.iterrows():
        info = await get_utilities_for_parcel(
            apn=str(row["apn"]),
            address=row.get("street_address"),
        )
        if info:
            results.append(info)

    return results

# Note: Later you can wrap parse_in_memory with a Celery task so the HTTP request returns immediately with a task-id; for now it runs inline.