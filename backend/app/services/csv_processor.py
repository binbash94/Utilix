import io
from typing import List

import pandas as pd

from ..schemas.parcel import ParcelUtilityInfo
from .parcel_lookup import get_utilities_for_parcel


async def parse_in_memory(buffer: bytes, filename: str) -> List[ParcelUtilityInfo]:
    ext = filename.lower().split(".")[-1]
    if ext == "csv":
        df = pd.read_csv(io.BytesIO(buffer))
    elif ext in {"xls", "xlsx"}:
        df = pd.read_excel(io.BytesIO(buffer))
    else:
        raise ValueError("Unsupported file type")

    # Normalize column names (strip spaces, lower-case, replace spaces with underscores)
    df.columns = (
        df.columns.str.strip().str.lower().str.replace(r"\s+", "_", regex=True)
    )

    # Accept common variants
    rename_map = {}
    if "address" in df.columns and "street_address" not in df.columns:
        rename_map["address"] = "street_address"
    if "pan" in df.columns and "apn" not in df.columns:
        rename_map["pan"] = "apn"
    df = df.rename(columns=rename_map)

    required_cols = ["apn", "street_address", "county", "state"]
    missing = set(required_cols) - set(df.columns)

    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    df = df[required_cols]

    results: list[ParcelUtilityInfo] = []
    for _, row in df.iterrows():
        info = await get_utilities_for_parcel(
            apn=str(row["apn"]),
            address=row.get("street_address"),
            county=row.get("county"),
            state=row.get("state"),
        )
        if info:
            results.append(info)

    return results

# Note: Later you can wrap parse_in_memory with a Celery task so the HTTP request returns immediately with a task-id; for now it runs inline.