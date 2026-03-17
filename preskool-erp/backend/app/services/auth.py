from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_access_token, create_refresh_token, get_password_hash, verify_password
from app.models.core import Tenant, User
from app.schemas.common import LoginRequest, RegisterRequest, TokenResponse, UserRead


class AuthService:
    async def login(self, db: AsyncSession, payload: LoginRequest) -> TokenResponse:
        result = await db.execute(select(User).where(User.email == payload.email))
        user = result.scalar_one_or_none()
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return TokenResponse(
            access_token=create_access_token(user),
            refresh_token=create_refresh_token(user),
            user=UserRead.model_validate(user),
        )

    async def register(self, db: AsyncSession, payload: RegisterRequest) -> User:
        tenant = await db.get(Tenant, payload.tenant_id)
        if tenant is None:
            tenant = Tenant(id=payload.tenant_id, name=payload.tenant_id.title(), domain=f"{payload.tenant_id}.preskool.app")
            db.add(tenant)
            await db.flush()
        user = User(
            email=payload.email,
            hashed_password=get_password_hash(payload.password),
            full_name=payload.full_name,
            role=payload.role,
            tenant_id=payload.tenant_id,
            is_active=payload.is_active,
            is_verified=payload.is_verified,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
