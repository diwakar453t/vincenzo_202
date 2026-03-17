from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class CRUDService:
    def __init__(self, model):
        self.model = model

    async def list(self, db: AsyncSession, tenant_id: str, limit: int = 100, offset: int = 0):
        result = await db.execute(
            select(self.model).where(self.model.tenant_id == tenant_id).offset(offset).limit(limit).order_by(self.model.id.desc())
        )
        return result.scalars().all()

    async def get(self, db: AsyncSession, tenant_id: str, resource_id: int):
        result = await db.execute(select(self.model).where(self.model.tenant_id == tenant_id, self.model.id == resource_id))
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, tenant_id: str, payload: dict[str, Any]):
        record = self.model(**payload, tenant_id=tenant_id)
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record

    async def update(self, db: AsyncSession, tenant_id: str, resource_id: int, payload: dict[str, Any]):
        record = await self.get(db, tenant_id, resource_id)
        if not record:
            return None
        for key, value in payload.items():
            setattr(record, key, value)
        await db.commit()
        await db.refresh(record)
        return record

    async def delete(self, db: AsyncSession, tenant_id: str, resource_id: int):
        record = await self.get(db, tenant_id, resource_id)
        if not record:
            return False
        await db.delete(record)
        await db.commit()
        return True

    async def count(self, db: AsyncSession, tenant_id: str) -> int:
        result = await db.execute(select(func.count()).select_from(self.model).where(self.model.tenant_id == tenant_id))
        return int(result.scalar_one())
