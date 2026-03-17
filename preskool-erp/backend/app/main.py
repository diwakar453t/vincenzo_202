from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import router as api_router
from app.core.auth import get_password_hash
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal, Base, engine
from app.services.specialized import ensure_super_admin

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_prefix)


@app.on_event("startup")
async def startup() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT 1"))
        await ensure_super_admin(
            session,
            settings.default_tenant_id,
            settings.superadmin_email,
            get_password_hash(settings.superadmin_password),
            settings.superadmin_name,
        )
