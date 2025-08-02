from typing import Optional, List

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.parcel import Parcel
from ..schemas.parcel import ParcelCreate, ParcelUpdate


class CRUDParcel:
    # ---------- basic getters ----------
    async def get(self, db: AsyncSession, parcel_id: int) -> Optional[Parcel]:
        return await db.get(Parcel, parcel_id)

    async def get_by_apn(self, db: AsyncSession, apn: str) -> Optional[Parcel]:
        result = await db.execute(select(Parcel).where(Parcel.apn == apn))
        return result.scalar_one_or_none()

    async def get_multi_by_owner(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Parcel]:
        result = await db.execute(
            select(Parcel)
            .where(Parcel.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    # ---------- create / update / delete ----------
    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: ParcelCreate,
        owner_id: int,
    ) -> Parcel:
        db_obj = Parcel(**obj_in.model_dump(), owner_id=owner_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: Parcel,
        obj_in: ParcelUpdate,
    ) -> Parcel:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, parcel_id: int) -> Optional[Parcel]:
        obj = await self.get(db, parcel_id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj


crud_parcel = CRUDParcel()
