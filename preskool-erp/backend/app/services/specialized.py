from __future__ import annotations

from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_password_hash
from app.models.core import (
    ClassRoom,
    FeeCollection,
    Leave,
    Notification,
    Student,
    StudentAttendance,
    StudentFeeAssignment,
    Teacher,
    Tenant,
    User,
)
from app.schemas.common import DashboardStatistics, StudentCreate, TeacherCreate


class StudentService:
    async def create_student(self, db: AsyncSession, tenant_id: str, payload: StudentCreate) -> Student:
        user = None
        if payload.email:
            user = User(
                email=payload.email,
                hashed_password=get_password_hash(payload.password or "Student@1234"),
                full_name=f"{payload.first_name} {payload.last_name}",
                role="student",
                tenant_id=tenant_id,
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            await db.flush()
        student = Student(**payload.model_dump(exclude={"password"}), tenant_id=tenant_id, user_id=user.id if user else None)
        db.add(student)
        await db.commit()
        await db.refresh(student)
        return student


class TeacherService:
    async def create_teacher(self, db: AsyncSession, tenant_id: str, payload: TeacherCreate) -> Teacher:
        email = payload.email or f"{payload.employee_id.lower()}@preskool.local"
        user = User(
            email=email,
            hashed_password=get_password_hash(payload.password or "Teacher@1234"),
            full_name=f"{payload.first_name} {payload.last_name}",
            role="teacher",
            tenant_id=tenant_id,
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        await db.flush()
        teacher = Teacher(**payload.model_dump(exclude={"password", "user_id"}), tenant_id=tenant_id, user_id=user.id)
        db.add(teacher)
        await db.commit()
        await db.refresh(teacher)
        return teacher


class DashboardService:
    async def statistics(self, db: AsyncSession, tenant_id: str, is_superadmin: bool) -> DashboardStatistics:
        def tenant_filter(model):
            return True if is_superadmin else model.tenant_id == tenant_id

        total_students = int((await db.execute(select(func.count()).select_from(Student).where(tenant_filter(Student)))).scalar_one())
        total_teachers = int((await db.execute(select(func.count()).select_from(Teacher).where(tenant_filter(Teacher)))).scalar_one())
        active_classes = int((await db.execute(select(func.count()).select_from(ClassRoom).where(tenant_filter(ClassRoom)))).scalar_one())
        revenue_this_month = float((await db.execute(select(func.coalesce(func.sum(FeeCollection.amount), 0)).where(tenant_filter(FeeCollection)))).scalar_one())
        attendance_rate = float(
            (
                await db.execute(
                    select(
                        func.coalesce(
                            func.avg(case((StudentAttendance.status == "present", 100.0), else_=0.0)),
                            0.0,
                        )
                    ).where(tenant_filter(StudentAttendance), StudentAttendance.date == date.today())
                )
            ).scalar_one()
        )
        assigned = float((await db.execute(select(func.coalesce(func.sum(StudentFeeAssignment.net_amount), 0)).where(tenant_filter(StudentFeeAssignment)))).scalar_one())
        collected = float((await db.execute(select(func.coalesce(func.sum(StudentFeeAssignment.paid_amount), 0)).where(tenant_filter(StudentFeeAssignment)))).scalar_one())
        fee_collection_rate = round((collected / assigned) * 100, 2) if assigned else 0.0
        pending_leaves = int((await db.execute(select(func.count()).select_from(Leave).where(tenant_filter(Leave), Leave.status == "pending"))).scalar_one())
        open_issues = int((await db.execute(select(func.count()).select_from(Notification).where(tenant_filter(Notification), Notification.is_read.is_(False)))).scalar_one())
        total_tenants = int((await db.execute(select(func.count()).select_from(Tenant))).scalar_one())
        total_users = int((await db.execute(select(func.count()).select_from(User).where(tenant_filter(User)))).scalar_one())

        return DashboardStatistics(
            total_students=total_students,
            total_teachers=total_teachers,
            active_classes=active_classes,
            revenue_this_month=revenue_this_month,
            attendance_rate=round(attendance_rate, 2),
            fee_collection_rate=fee_collection_rate,
            pending_leaves=pending_leaves,
            open_issues=open_issues,
            total_tenants=total_tenants,
            total_users=total_users,
        )


async def ensure_super_admin(db: AsyncSession, tenant_id: str, email: str, password_hash: str, full_name: str) -> None:
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        return
    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        db.add(Tenant(id=tenant_id, name="Default Tenant", domain="default.preskool.app"))
        await db.flush()
    db.add(
        User(
            email=email,
            hashed_password=password_hash,
            full_name=full_name,
            role="super_admin",
            tenant_id=tenant_id,
            is_active=True,
            is_verified=True,
        )
    )
    await db.commit()
