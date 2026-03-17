from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, create_model
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_roles
from app.core.database import get_db
from app.models.core import *
from app.schemas.common import (
    DashboardStatistics,
    GenericSchema,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    StudentCreate,
    StudentRead,
    TeacherCreate,
    TeacherRead,
    TokenResponse,
    UserRead,
)
from app.services.auth import AuthService
from app.services.base import CRUDService
from app.services.specialized import DashboardService, StudentService, TeacherService

router = APIRouter()
auth_service = AuthService()
student_service = StudentService()
teacher_service = TeacherService()
dashboard_service = DashboardService()


@router.post("/auth/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.login(db, payload)


@router.post("/auth/register", response_model=UserRead, dependencies=[Depends(require_roles("admin", "super_admin"))])
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "super_admin" and current_user.tenant_id != payload.tenant_id:
        raise HTTPException(status_code=403, detail="Tenant mismatch")
    user = await auth_service.register(db, payload)
    return UserRead.model_validate(user)


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    from jose import jwt
    from app.core.config import get_settings
    from app.core.auth import create_access_token, create_refresh_token

    settings = get_settings()
    decoded = jwt.decode(payload.refresh_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    user = await db.get(User, int(decoded["sub"]))
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return TokenResponse(access_token=create_access_token(user), refresh_token=create_refresh_token(user), user=UserRead.model_validate(user))


@router.get("/health")
async def health():
    return {"status": "healthy"}


@router.get("/health/detailed")
async def health_detailed(db: AsyncSession = Depends(get_db)):
    await db.execute(select(1))
    return {"status": "healthy", "database": "connected"}


@router.get("/dashboard/statistics", response_model=DashboardStatistics)
async def dashboard_statistics(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await dashboard_service.statistics(db, current_user.tenant_id, current_user.role == "super_admin")


@router.get("/search")
async def search(q: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    results = {}
    for name, model in {"students": Student, "teachers": Teacher, "classes": ClassRoom, "subjects": Subject}.items():
        column = getattr(model, "name", None) or getattr(model, "first_name", None)
        if column is None:
            continue
        query = select(model).where(model.tenant_id == current_user.tenant_id, column.ilike(f"%{q}%")).limit(10)
        rows = (await db.execute(query)).scalars().all()
        results[name] = rows
    return results


@router.post("/students/", response_model=StudentRead, dependencies=[Depends(require_roles("admin", "super_admin"))])
async def create_student(payload: StudentCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    student = await student_service.create_student(db, current_user.tenant_id, payload)
    return StudentRead.model_validate(student)


@router.get("/students/", response_model=list[StudentRead])
async def list_students(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = CRUDService(Student)
    return await service.list(db, current_user.tenant_id)


@router.get("/students/{resource_id}", response_model=StudentRead)
async def get_student(resource_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = CRUDService(Student)
    student = await service.get(db, current_user.tenant_id, resource_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.put("/students/{resource_id}", response_model=StudentRead, dependencies=[Depends(require_roles("admin", "super_admin"))])
async def update_student(resource_id: int, payload: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = CRUDService(Student)
    student = await service.update(db, current_user.tenant_id, resource_id, payload)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.delete("/students/{resource_id}", dependencies=[Depends(require_roles("admin", "super_admin"))])
async def delete_student(resource_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = CRUDService(Student)
    deleted = await service.delete(db, current_user.tenant_id, resource_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"success": True}


@router.post("/teachers/", response_model=TeacherRead, dependencies=[Depends(require_roles("admin", "super_admin"))])
async def create_teacher(payload: TeacherCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    teacher = await teacher_service.create_teacher(db, current_user.tenant_id, payload)
    return TeacherRead.model_validate(teacher)


@router.get("/teachers/", response_model=list[TeacherRead])
async def list_teachers(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = CRUDService(Teacher)
    return await service.list(db, current_user.tenant_id)


@router.get("/teachers/{resource_id}", response_model=TeacherRead)
async def get_teacher(resource_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = CRUDService(Teacher)
    teacher = await service.get(db, current_user.tenant_id, resource_id)
    if teacher is None:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return teacher


@router.put("/teachers/{resource_id}", response_model=TeacherRead, dependencies=[Depends(require_roles("admin", "super_admin"))])
async def update_teacher(resource_id: int, payload: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = CRUDService(Teacher)
    teacher = await service.update(db, current_user.tenant_id, resource_id, payload)
    if teacher is None:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return teacher


@router.delete("/teachers/{resource_id}", dependencies=[Depends(require_roles("admin", "super_admin"))])
async def delete_teacher(resource_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = CRUDService(Teacher)
    deleted = await service.delete(db, current_user.tenant_id, resource_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return {"success": True}


@router.get("/attendance/class/{class_id}/date/{attendance_date}")
async def get_attendance_by_class(class_id: int, attendance_date: date, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = CRUDService(StudentAttendance)
    items = await service.list(db, current_user.tenant_id)
    return [item for item in items if item.class_id == class_id and item.date == attendance_date]


class AttendanceBulkPayload(BaseModel):
    records: list[dict]


@router.post("/attendance/class/{class_id}/bulk")
async def bulk_attendance(class_id: int, payload: AttendanceBulkPayload, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = CRUDService(StudentAttendance)
    created = []
    for record in payload.records:
        record["class_id"] = class_id
        created.append(await service.create(db, current_user.tenant_id, record))
    return created


@router.get("/timetable/class/{class_id}")
async def timetable_by_class(class_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Timetable).where(Timetable.tenant_id == current_user.tenant_id, Timetable.class_id == class_id).order_by(Timetable.day_of_week, Timetable.period_number))
    return result.scalars().all()


@router.get("/timetable/teacher/{teacher_id}")
async def timetable_by_teacher(teacher_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Timetable).where(Timetable.tenant_id == current_user.tenant_id, Timetable.teacher_id == teacher_id).order_by(Timetable.day_of_week, Timetable.period_number))
    return result.scalars().all()


@router.get("/fees/student/{student_id}/summary")
async def fee_summary(student_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StudentFeeAssignment).where(StudentFeeAssignment.tenant_id == current_user.tenant_id, StudentFeeAssignment.student_id == student_id))
    assignments = result.scalars().all()
    total = sum(item.net_amount for item in assignments)
    paid = sum(item.paid_amount for item in assignments)
    return {"student_id": student_id, "total": total, "paid": paid, "balance": total - paid, "items": assignments}


class FeeCollectionPayload(BaseModel):
    student_id: int
    fee_type_id: int
    assignment_id: int
    receipt_number: str
    amount: float
    payment_method: str
    payment_date: date
    transaction_id: str | None = None
    remarks: str | None = None


@router.post("/fees/collect")
async def collect_fee(payload: FeeCollectionPayload, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = CRUDService(FeeCollection)
    collection = await service.create(db, current_user.tenant_id, payload.model_dump())
    assignment = await db.get(StudentFeeAssignment, payload.assignment_id)
    if assignment and assignment.tenant_id == current_user.tenant_id:
        assignment.paid_amount += payload.amount
        assignment.balance = assignment.net_amount - assignment.paid_amount
        assignment.status = "paid" if assignment.balance <= 0 else "partial"
        await db.commit()
    return collection


@router.get("/reports/generate/{report_type}")
async def generate_report(report_type: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    data = await dashboard_service.statistics(db, current_user.tenant_id, current_user.role == "super_admin")
    return {"report_type": report_type, "generated_at": date.today().isoformat(), "data": data.model_dump()}


def build_generic_router(path: str, model, schema_name: str):
    resource_router = APIRouter(prefix=f"/{path}", tags=[schema_name])
    service = CRUDService(model)
    schema = create_model(f"{schema_name}Schema", __base__=GenericSchema)

    @resource_router.get("/", response_model=list[schema])
    async def list_items(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        items = await service.list(db, current_user.tenant_id)
        return items

    @resource_router.get("/{resource_id}", response_model=schema)
    async def get_item(resource_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        item = await service.get(db, current_user.tenant_id, resource_id)
        if item is None:
            raise HTTPException(status_code=404, detail=f"{schema_name} not found")
        return item

    @resource_router.post("/", response_model=schema, dependencies=[Depends(require_roles("admin", "super_admin", "teacher"))])
    async def create_item(payload: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        return await service.create(db, current_user.tenant_id, payload)

    @resource_router.put("/{resource_id}", response_model=schema, dependencies=[Depends(require_roles("admin", "super_admin", "teacher"))])
    async def update_item(resource_id: int, payload: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        item = await service.update(db, current_user.tenant_id, resource_id, payload)
        if item is None:
            raise HTTPException(status_code=404, detail=f"{schema_name} not found")
        return item

    @resource_router.delete("/{resource_id}", dependencies=[Depends(require_roles("admin", "super_admin"))])
    async def delete_item(resource_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        deleted = await service.delete(db, current_user.tenant_id, resource_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"{schema_name} not found")
        return {"success": True}

    return resource_router


generic_resources = [
    ("users", User, "User"),
    ("classes", ClassRoom, "ClassRoom"),
    ("subjects", Subject, "Subject"),
    ("class-subjects", ClassSubject, "ClassSubject"),
    ("departments", Department, "Department"),
    ("subject-groups", SubjectGroup, "SubjectGroup"),
    ("syllabus", Syllabus, "Syllabus"),
    ("timetable", Timetable, "Timetable"),
    ("attendance", StudentAttendance, "StudentAttendance"),
    ("staff-attendance", StaffAttendance, "StaffAttendance"),
    ("exams", Exam, "Exam"),
    ("grades", Grade, "Grade"),
    ("fee-groups", FeeGroup, "FeeGroup"),
    ("fee-types", FeeType, "FeeType"),
    ("student-fee-assignments", StudentFeeAssignment, "StudentFeeAssignment"),
    ("fee-collections", FeeCollection, "FeeCollection"),
    ("leave", Leave, "Leave"),
    ("salary-structures", SalaryStructure, "SalaryStructure"),
    ("salary-payments", SalaryPayment, "SalaryPayment"),
    ("books", Book, "Book"),
    ("library-members", LibraryMember, "LibraryMember"),
    ("issue-returns", IssueReturn, "IssueReturn"),
    ("hostel", Hostel, "Hostel"),
    ("hostel-rooms", HostelRoom, "HostelRoom"),
    ("room-allocations", RoomAllocation, "RoomAllocation"),
    ("transport", TransportRoute, "TransportRoute"),
    ("vehicles", Vehicle, "Vehicle"),
    ("transport-assignments", TransportAssignment, "TransportAssignment"),
    ("sports", Sport, "Sport"),
    ("sport-participation", SportParticipation, "SportParticipation"),
    ("sport-achievements", SportAchievement, "SportAchievement"),
    ("rooms", Room, "Room"),
    ("notifications", Notification, "Notification"),
    ("files", UploadedFile, "UploadedFile"),
    ("payments", Payment, "Payment"),
    ("guardians", Guardian, "Guardian"),
    ("settings", Setting, "Setting"),
    ("plugins", Plugin, "Plugin"),
    ("reports", Report, "Report"),
    ("audit-logs", AuditLog, "AuditLog"),
    ("tenants", Tenant, "Tenant"),
]

for prefix, model, name in generic_resources:
    router.include_router(build_generic_router(prefix, model, name))
