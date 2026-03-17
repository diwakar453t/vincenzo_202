from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()
engine = create_async_engine(settings.database_url, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def set_tenant_context(db: AsyncSession, tenant_id: str | None, is_superadmin: bool) -> None:
    tenant_value = tenant_id or settings.default_tenant_id
    await db.execute(text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"), {"tenant_id": tenant_value})
    await db.execute(text("SELECT set_config('app.is_superadmin', :is_superadmin, true)"), {"is_superadmin": str(is_superadmin).lower()})


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
