from pathlib import Path
import textwrap


ROOT = Path("/Users/dineshpatel4027gmail.com/Documents/Playground/vincenzo_202")


def write(rel_path: str, content: str) -> None:
    path = ROOT / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")


def main() -> None:
    backend_requirements = """
    fastapi==0.116.1
    uvicorn[standard]==0.35.0
    sqlalchemy==2.0.43
    asyncpg==0.30.0
    psycopg2-binary==2.9.10
    alembic==1.16.4
    pydantic==2.11.7
    pydantic-settings==2.10.1
    email-validator==2.3.0
    python-jose[cryptography]==3.5.0
    passlib[bcrypt]==1.7.4
    python-multipart==0.0.20
    orjson==3.11.3
    httpx==0.28.1
    pytest==8.4.1
    pytest-asyncio==1.1.0
    """
    write("preskool-erp/backend/requirements.txt", backend_requirements)

    write(
        "preskool-erp/backend/Dockerfile",
        """
        FROM python:3.11-slim
        WORKDIR /app
        ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
        RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
        COPY requirements.txt .
        RUN pip install --no-cache-dir -r requirements.txt
        COPY . .
        CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
        """,
    )

    write(
        "docker-compose.yml",
        """
        version: "3.9"
        services:
          db:
            image: postgres:16
            environment:
              POSTGRES_DB: preskool
              POSTGRES_USER: preskool
              POSTGRES_PASSWORD: preskool
            ports:
              - "5432:5432"
          backend:
            build: ./preskool-erp/backend
            environment:
              DATABASE_URL: postgresql+asyncpg://preskool:preskool@db:5432/preskool
              SYNC_DATABASE_URL: postgresql+psycopg2://preskool:preskool@db:5432/preskool
              JWT_SECRET_KEY: changeme
              CORS_ORIGINS: http://localhost:5173
            ports:
              - "8000:8000"
            depends_on:
              - db
          frontend:
            image: node:20
            working_dir: /app
            command: sh -c "npm install && npm run dev -- --host 0.0.0.0"
            environment:
              VITE_API_URL: http://localhost:8000/api/v1
            volumes:
              - ./preskool-erp/frontend:/app
            ports:
              - "5173:5173"
            depends_on:
              - backend
        """,
    )

    write(
        "preskool-erp/backend/app/core/config.py",
        """
        from functools import lru_cache
        from typing import List

        from pydantic import Field
        from pydantic_settings import BaseSettings, SettingsConfigDict


        class Settings(BaseSettings):
            model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

            app_name: str = "PreSkool ERP"
            app_env: str = "development"
            api_prefix: str = "/api/v1"
            database_url: str = "postgresql+asyncpg://preskool:preskool@localhost:5432/preskool"
            sync_database_url: str = "postgresql+psycopg2://preskool:preskool@localhost:5432/preskool"
            jwt_secret_key: str = "changeme"
            jwt_algorithm: str = "HS256"
            access_token_expire_minutes: int = 60
            refresh_token_expire_minutes: int = 60 * 24 * 7
            cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:5173"])
            default_tenant_id: str = "default"
            superadmin_email: str = "admin@preskool.com"
            superadmin_password: str = "Admin@1234"
            superadmin_name: str = "Super Admin"


        @lru_cache
        def get_settings() -> Settings:
            return Settings()
        """,
    )

    write(
        "preskool-erp/backend/app/core/database.py",
        """
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
        """,
    )

    write(
        "preskool-erp/backend/app/core/auth.py",
        """
        from datetime import datetime, timedelta, timezone
        from typing import Any

        from fastapi import Depends, HTTPException, status
        from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
        from jose import JWTError, jwt
        from passlib.context import CryptContext
        from pydantic import BaseModel
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import AsyncSession

        from app.core.config import get_settings
        from app.core.database import get_db, set_tenant_context
        from app.models.core import User

        settings = get_settings()
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        security = HTTPBearer(auto_error=False)


        class TokenPayload(BaseModel):
            sub: str
            tenant_id: str
            role: str
            exp: int


        def get_password_hash(password: str) -> str:
            return pwd_context.hash(password)


        def verify_password(plain_password: str, hashed_password: str) -> bool:
            return pwd_context.verify(plain_password, hashed_password)


        def create_token(data: dict[str, Any], expires_minutes: int) -> str:
            to_encode = data.copy()
            expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
            to_encode.update({"exp": expire})
            return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


        def create_access_token(user: User) -> str:
            return create_token({"sub": str(user.id), "tenant_id": user.tenant_id, "role": user.role}, settings.access_token_expire_minutes)


        def create_refresh_token(user: User) -> str:
            return create_token({"sub": str(user.id), "tenant_id": user.tenant_id, "role": user.role, "token_type": "refresh"}, settings.refresh_token_expire_minutes)


        async def get_current_user(
            credentials: HTTPAuthorizationCredentials | None = Depends(security),
            db: AsyncSession = Depends(get_db),
        ) -> User:
            if credentials is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
            token = credentials.credentials
            try:
                payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
                token_data = TokenPayload.model_validate(payload)
            except JWTError as exc:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
            result = await db.execute(select(User).where(User.id == int(token_data.sub)))
            user = result.scalar_one_or_none()
            if not user or not user.is_active:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
            await set_tenant_context(db, user.tenant_id, user.role == "super_admin")
            return user


        def require_roles(*allowed_roles: str):
            async def dependency(current_user: User = Depends(get_current_user)) -> User:
                if current_user.role not in allowed_roles:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
                return current_user

            return dependency
        """,
    )

    write(
        "preskool-erp/backend/app/models/core.py",
        """
        from datetime import date, datetime

        from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
        from sqlalchemy.dialects.postgresql import JSONB
        from sqlalchemy.orm import Mapped, mapped_column

        from app.core.database import Base


        class Tenant(Base):
            __tablename__ = "tenants"

            id: Mapped[str] = mapped_column(String(50), primary_key=True)
            name: Mapped[str] = mapped_column(String(255), nullable=False)
            domain: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
            is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
            created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
            updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)


        class BaseModelMixin:
            id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
            tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
            created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
            updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)


        class User(Base, BaseModelMixin):
            __tablename__ = "users"
            email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
            hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
            full_name: Mapped[str] = mapped_column(String(255), nullable=False)
            role: Mapped[str] = mapped_column(String(20), nullable=False)
            is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
            is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


        def json_type():
            return JSONB().with_variant(Text, "sqlite")


        class Student(Base, BaseModelMixin):
            __tablename__ = "students"
            student_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
            first_name: Mapped[str] = mapped_column(String(100), nullable=False)
            last_name: Mapped[str] = mapped_column(String(100), nullable=False)
            date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
            gender: Mapped[str] = mapped_column(String(20), nullable=False)
            email: Mapped[str | None] = mapped_column(String(255))
            phone: Mapped[str | None] = mapped_column(String(20))
            address: Mapped[str | None] = mapped_column(Text)
            enrollment_date: Mapped[date] = mapped_column(Date, nullable=False)
            class_id: Mapped[int | None] = mapped_column(ForeignKey("classes.id"))
            parent_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
            status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
            photo_url: Mapped[str | None] = mapped_column(String(500))
            emergency_contact: Mapped[str | None] = mapped_column(String(20))
            emergency_contact_name: Mapped[str | None] = mapped_column(String(100))
            medical_info: Mapped[str | None] = mapped_column(Text)
            user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))


        class Teacher(Base, BaseModelMixin):
            __tablename__ = "teachers"
            employee_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
            user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
            first_name: Mapped[str] = mapped_column(String(100), nullable=False)
            last_name: Mapped[str] = mapped_column(String(100), nullable=False)
            date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
            gender: Mapped[str] = mapped_column(String(20), nullable=False)
            phone: Mapped[str | None] = mapped_column(String(20))
            address: Mapped[str | None] = mapped_column(Text)
            hire_date: Mapped[date] = mapped_column(Date, nullable=False)
            qualification: Mapped[str | None] = mapped_column(String(255))
            specialization: Mapped[str | None] = mapped_column(String(255))
            salary: Mapped[float | None] = mapped_column(Numeric(10, 2))
            status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
            photo_url: Mapped[str | None] = mapped_column(String(500))
            email: Mapped[str | None] = mapped_column(String(255))


        class ClassRoom(Base, BaseModelMixin):
            __tablename__ = "classes"
            name: Mapped[str] = mapped_column(String(100), nullable=False)
            grade_level: Mapped[int] = mapped_column(Integer, nullable=False)
            section: Mapped[str] = mapped_column(String(10), nullable=False)
            academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
            room_number: Mapped[str | None] = mapped_column(String(20))
            capacity: Mapped[int] = mapped_column(Integer, default=40, nullable=False)
            class_teacher_id: Mapped[int | None] = mapped_column(ForeignKey("teachers.id"))


        class Subject(Base, BaseModelMixin):
            __tablename__ = "subjects"
            name: Mapped[str] = mapped_column(String(100), nullable=False)
            code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
            description: Mapped[str | None] = mapped_column(Text)
            credits: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


        class ClassSubject(Base, BaseModelMixin):
            __tablename__ = "class_subjects"
            class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False)
            subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)
            teacher_id: Mapped[int | None] = mapped_column(ForeignKey("teachers.id"))


        class Department(Base, BaseModelMixin):
            __tablename__ = "departments"
            name: Mapped[str] = mapped_column(String(100), nullable=False)
            code: Mapped[str] = mapped_column(String(20), nullable=False)
            head_teacher_id: Mapped[int | None] = mapped_column(ForeignKey("teachers.id"))
            description: Mapped[str | None] = mapped_column(Text)
            is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


        class SubjectGroup(Base, BaseModelMixin):
            __tablename__ = "subject_groups"
            name: Mapped[str] = mapped_column(String(100), nullable=False)
            code: Mapped[str] = mapped_column(String(20), nullable=False)
            description: Mapped[str | None] = mapped_column(Text)
            class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False)
            is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


        class Syllabus(Base, BaseModelMixin):
            __tablename__ = "syllabus"
            subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)
            class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False)
            title: Mapped[str] = mapped_column(String(200), nullable=False)
            description: Mapped[str | None] = mapped_column(Text)
            topics: Mapped[str | None] = mapped_column(Text)
            academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
            completion_percentage: Mapped[float] = mapped_column(Float, default=0, nullable=False)


        class Timetable(Base, BaseModelMixin):
            __tablename__ = "timetable"
            class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False)
            subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)
            teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False)
            day_of_week: Mapped[str] = mapped_column(String(15), nullable=False)
            start_time: Mapped[str] = mapped_column(String(10), nullable=False)
            end_time: Mapped[str] = mapped_column(String(10), nullable=False)
            period_number: Mapped[int] = mapped_column(Integer, nullable=False)
            room_number: Mapped[str | None] = mapped_column(String(20))
            academic_year: Mapped[str] = mapped_column(String(20), nullable=False)


        class StudentAttendance(Base, BaseModelMixin):
            __tablename__ = "student_attendance"
            student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
            class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False)
            date: Mapped[date] = mapped_column(Date, nullable=False)
            status: Mapped[str] = mapped_column(String(20), nullable=False)
            remarks: Mapped[str | None] = mapped_column(Text)
            academic_year: Mapped[str] = mapped_column(String(20), nullable=False)


        class StaffAttendance(Base, BaseModelMixin):
            __tablename__ = "staff_attendance"
            teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False)
            date: Mapped[date] = mapped_column(Date, nullable=False)
            status: Mapped[str] = mapped_column(String(20), nullable=False)
            check_in: Mapped[str | None] = mapped_column(String(10))
            check_out: Mapped[str | None] = mapped_column(String(10))
            remarks: Mapped[str | None] = mapped_column(Text)


        class Exam(Base, BaseModelMixin):
            __tablename__ = "exams"
            name: Mapped[str] = mapped_column(String(200), nullable=False)
            exam_type: Mapped[str] = mapped_column(String(50), nullable=False)
            class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False)
            subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)
            date: Mapped[date] = mapped_column(Date, nullable=False)
            start_time: Mapped[str | None] = mapped_column(String(10))
            end_time: Mapped[str | None] = mapped_column(String(10))
            total_marks: Mapped[float] = mapped_column(Float, nullable=False)
            passing_marks: Mapped[float] = mapped_column(Float, nullable=False)
            room_number: Mapped[str | None] = mapped_column(String(20))
            academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
            is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


        class Grade(Base, BaseModelMixin):
            __tablename__ = "grades"
            student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
            exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id"), nullable=False)
            subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)
            marks_obtained: Mapped[float] = mapped_column(Float, nullable=False)
            grade: Mapped[str] = mapped_column(String(5), nullable=False)
            remarks: Mapped[str | None] = mapped_column(Text)
            academic_year: Mapped[str] = mapped_column(String(20), nullable=False)


        class FeeGroup(Base, BaseModelMixin):
            __tablename__ = "fee_groups"
            name: Mapped[str] = mapped_column(String(100), nullable=False)
            code: Mapped[str] = mapped_column(String(20), nullable=False)
            description: Mapped[str | None] = mapped_column(Text)
            is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


        class FeeType(Base, BaseModelMixin):
            __tablename__ = "fee_types"
            fee_group_id: Mapped[int] = mapped_column(ForeignKey("fee_groups.id"), nullable=False)
            name: Mapped[str] = mapped_column(String(100), nullable=False)
            code: Mapped[str] = mapped_column(String(20), nullable=False)
            amount: Mapped[float] = mapped_column(Float, nullable=False)
            due_date: Mapped[date | None] = mapped_column(Date)
            is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
            frequency: Mapped[str | None] = mapped_column(String(20))
            academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
            class_id: Mapped[int | None] = mapped_column(ForeignKey("classes.id"))
            is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


        class StudentFeeAssignment(Base, BaseModelMixin):
            __tablename__ = "student_fee_assignments"
            student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
            fee_type_id: Mapped[int] = mapped_column(ForeignKey("fee_types.id"), nullable=False)
            amount: Mapped[float] = mapped_column(Float, nullable=False)
            discount: Mapped[float] = mapped_column(Float, default=0, nullable=False)
            net_amount: Mapped[float] = mapped_column(Float, nullable=False)
            paid_amount: Mapped[float] = mapped_column(Float, default=0, nullable=False)
            balance: Mapped[float] = mapped_column(Float, nullable=False)
            status: Mapped[str] = mapped_column(String(20), nullable=False)
            due_date: Mapped[date | None] = mapped_column(Date)


        class FeeCollection(Base, BaseModelMixin):
            __tablename__ = "fee_collections"
            student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
            fee_type_id: Mapped[int] = mapped_column(ForeignKey("fee_types.id"), nullable=False)
            assignment_id: Mapped[int] = mapped_column(ForeignKey("student_fee_assignments.id"), nullable=False)
            receipt_number: Mapped[str] = mapped_column(String(50), nullable=False)
            amount: Mapped[float] = mapped_column(Float, nullable=False)
            payment_method: Mapped[str] = mapped_column(String(20), nullable=False)
            payment_date: Mapped[date] = mapped_column(Date, nullable=False)
            transaction_id: Mapped[str | None] = mapped_column(String(100))
            remarks: Mapped[str | None] = mapped_column(Text)


        class Leave(Base, BaseModelMixin):
            __tablename__ = "leaves"
            user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
            leave_type: Mapped[str] = mapped_column(String(50), nullable=False)
            start_date: Mapped[date] = mapped_column(Date, nullable=False)
            end_date: Mapped[date] = mapped_column(Date, nullable=False)
            reason: Mapped[str] = mapped_column(Text, nullable=False)
            status: Mapped[str] = mapped_column(String(20), nullable=False)
            approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
            remarks: Mapped[str | None] = mapped_column(Text)


        class SalaryStructure(Base, BaseModelMixin):
            __tablename__ = "salary_structures"
            teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False)
            basic_salary: Mapped[float] = mapped_column(Float, nullable=False)
            hra: Mapped[float] = mapped_column(Float, default=0, nullable=False)
            da: Mapped[float] = mapped_column(Float, default=0, nullable=False)
            ta: Mapped[float] = mapped_column(Float, default=0, nullable=False)
            other_allowances: Mapped[float] = mapped_column(Float, default=0, nullable=False)
            pf_deduction: Mapped[float] = mapped_column(Float, default=0, nullable=False)
            tax_deduction: Mapped[float] = mapped_column(Float, default=0, nullable=False)
            other_deductions: Mapped[float] = mapped_column(Float, default=0, nullable=False)
            net_salary: Mapped[float] = mapped_column(Float, nullable=False)
            effective_from: Mapped[date] = mapped_column(Date, nullable=False)
            is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


        class SalaryPayment(Base, BaseModelMixin):
            __tablename__ = "salary_payments"
            teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False)
            salary_structure_id: Mapped[int] = mapped_column(ForeignKey("salary_structures.id"), nullable=False)
            month: Mapped[int] = mapped_column(Integer, nullable=False)
            year: Mapped[int] = mapped_column(Integer, nullable=False)
            amount: Mapped[float] = mapped_column(Float, nullable=False)
            payment_date: Mapped[date | None] = mapped_column(Date)
            payment_method: Mapped[str | None] = mapped_column(String(20))
            transaction_id: Mapped[str | None] = mapped_column(String(100))
            status: Mapped[str] = mapped_column(String(20), nullable=False)


        class Book(Base, BaseModelMixin):
            __tablename__ = "books"
            title: Mapped[str] = mapped_column(String(255), nullable=False)
            isbn: Mapped[str | None] = mapped_column(String(50))
            author: Mapped[str | None] = mapped_column(String(255))
            publisher: Mapped[str | None] = mapped_column(String(255))
            edition: Mapped[str | None] = mapped_column(String(50))
            category: Mapped[str | None] = mapped_column(String(100))
            subject: Mapped[str | None] = mapped_column(String(100))
            language: Mapped[str | None] = mapped_column(String(50))
            pages: Mapped[int | None] = mapped_column(Integer)
            price: Mapped[float | None] = mapped_column(Float)
            rack_number: Mapped[str | None] = mapped_column(String(50))
            total_copies: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
            available_copies: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
            status: Mapped[str] = mapped_column(String(20), nullable=False)


        class LibraryMember(Base, BaseModelMixin):
            __tablename__ = "library_members"
            member_code: Mapped[str] = mapped_column(String(50), nullable=False)
            member_type: Mapped[str] = mapped_column(String(20), nullable=False)
            student_id: Mapped[int | None] = mapped_column(ForeignKey("students.id"))
            teacher_id: Mapped[int | None] = mapped_column(ForeignKey("teachers.id"))
            name: Mapped[str] = mapped_column(String(255), nullable=False)
            email: Mapped[str | None] = mapped_column(String(255))
            phone: Mapped[str | None] = mapped_column(String(20))
            max_books_allowed: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
            status: Mapped[str] = mapped_column(String(20), nullable=False)


        class IssueReturn(Base, BaseModelMixin):
            __tablename__ = "issue_returns"
            book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False)
            member_id: Mapped[int] = mapped_column(ForeignKey("library_members.id"), nullable=False)
            issue_date: Mapped[date] = mapped_column(Date, nullable=False)
            due_date: Mapped[date] = mapped_column(Date, nullable=False)
            return_date: Mapped[date | None] = mapped_column(Date)
            status: Mapped[str] = mapped_column(String(20), nullable=False)
            fine_amount: Mapped[float] = mapped_column(Float, default=0, nullable=False)
            fine_per_day: Mapped[float] = mapped_column(Float, default=0, nullable=False)


        class Hostel(Base, BaseModelMixin):
            __tablename__ = "hostels"
            name: Mapped[str] = mapped_column(String(100), nullable=False)
            code: Mapped[str] = mapped_column(String(20), nullable=False)
            hostel_type: Mapped[str] = mapped_column(String(20), nullable=False)
            address: Mapped[str | None] = mapped_column(Text)
            warden_name: Mapped[str | None] = mapped_column(String(100))
            warden_phone: Mapped[str | None] = mapped_column(String(20))
            warden_email: Mapped[str | None] = mapped_column(String(255))
            total_rooms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
            total_beds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
            occupied_beds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
            monthly_fee: Mapped[float | None] = mapped_column(Float)
            is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


        class HostelRoom(Base, BaseModelMixin):
            __tablename__ = "hostel_rooms"
            hostel_id: Mapped[int] = mapped_column(ForeignKey("hostels.id"), nullable=False)
            room_number: Mapped[str] = mapped_column(String(20), nullable=False)
            floor: Mapped[int | None] = mapped_column(Integer)
            room_type: Mapped[str] = mapped_column(String(20), nullable=False)
            capacity: Mapped[int] = mapped_column(Integer, nullable=False)
            occupied: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
            status: Mapped[str] = mapped_column(String(30), nullable=False)
            has_attached_bathroom: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
            has_ac: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
            has_wifi: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
            monthly_rent: Mapped[float | None] = mapped_column(Float)


        class RoomAllocation(Base, BaseModelMixin):
            __tablename__ = "room_allocations"
            hostel_id: Mapped[int] = mapped_column(ForeignKey("hostels.id"), nullable=False)
            room_id: Mapped[int] = mapped_column(ForeignKey("hostel_rooms.id"), nullable=False)
            student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
            bed_number: Mapped[str | None] = mapped_column(String(20))
            allocation_date: Mapped[date] = mapped_column(Date, nullable=False)
            vacating_date: Mapped[date | None] = mapped_column(Date)
            status: Mapped[str] = mapped_column(String(20), nullable=False)
            monthly_fee: Mapped[float | None] = mapped_column(Float)


        class TransportRoute(Base, BaseModelMixin):
            __tablename__ = "transport_routes"
            route_name: Mapped[str] = mapped_column(String(100), nullable=False)
            route_code: Mapped[str] = mapped_column(String(20), nullable=False)
            start_point: Mapped[str] = mapped_column(String(100), nullable=False)
            end_point: Mapped[str] = mapped_column(String(100), nullable=False)
            stops: Mapped[str | None] = mapped_column(Text)
            distance_km: Mapped[float | None] = mapped_column(Float)
            morning_departure: Mapped[str | None] = mapped_column(String(10))
            evening_departure: Mapped[str | None] = mapped_column(String(10))
            monthly_fee: Mapped[float | None] = mapped_column(Float)
            max_capacity: Mapped[int | None] = mapped_column(Integer)
            vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id"))
            status: Mapped[str] = mapped_column(String(20), nullable=False)


        class Vehicle(Base, BaseModelMixin):
            __tablename__ = "vehicles"
            vehicle_number: Mapped[str] = mapped_column(String(20), nullable=False)
            vehicle_type: Mapped[str] = mapped_column(String(20), nullable=False)
            make: Mapped[str | None] = mapped_column(String(50))
            model: Mapped[str | None] = mapped_column(String(50))
            year: Mapped[int | None] = mapped_column(Integer)
            capacity: Mapped[int | None] = mapped_column(Integer)
            driver_name: Mapped[str | None] = mapped_column(String(100))
            driver_phone: Mapped[str | None] = mapped_column(String(20))
            license: Mapped[str | None] = mapped_column(String(100))
            conductor_name: Mapped[str | None] = mapped_column(String(100))
            conductor_phone: Mapped[str | None] = mapped_column(String(20))
            insurance_expiry: Mapped[date | None] = mapped_column(Date)
            fitness_expiry: Mapped[date | None] = mapped_column(Date)
            gps_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
            status: Mapped[str] = mapped_column(String(20), nullable=False)


        class TransportAssignment(Base, BaseModelMixin):
            __tablename__ = "transport_assignments"
            student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
            route_id: Mapped[int] = mapped_column(ForeignKey("transport_routes.id"), nullable=False)
            pickup_stop: Mapped[str | None] = mapped_column(String(100))
            drop_stop: Mapped[str | None] = mapped_column(String(100))
            assignment_date: Mapped[date] = mapped_column(Date, nullable=False)
            monthly_fee: Mapped[float | None] = mapped_column(Float)
            status: Mapped[str] = mapped_column(String(20), nullable=False)


        class Sport(Base, BaseModelMixin):
            __tablename__ = "sports"
            name: Mapped[str] = mapped_column(String(100), nullable=False)
            code: Mapped[str] = mapped_column(String(20), nullable=False)
            category: Mapped[str] = mapped_column(String(20), nullable=False)
            coach_name: Mapped[str | None] = mapped_column(String(100))
            coach_phone: Mapped[str | None] = mapped_column(String(20))
            venue: Mapped[str | None] = mapped_column(String(100))
            practice_schedule: Mapped[str | None] = mapped_column(Text)
            max_participants: Mapped[int | None] = mapped_column(Integer)
            registration_fee: Mapped[float | None] = mapped_column(Float)
            status: Mapped[str] = mapped_column(String(20), nullable=False)


        class SportParticipation(Base, BaseModelMixin):
            __tablename__ = "sport_participation"
            sport_id: Mapped[int] = mapped_column(ForeignKey("sports.id"), nullable=False)
            student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
            registration_date: Mapped[date] = mapped_column(Date, nullable=False)
            position: Mapped[str | None] = mapped_column(String(50))
            jersey_number: Mapped[str | None] = mapped_column(String(20))
            status: Mapped[str] = mapped_column(String(20), nullable=False)


        class SportAchievement(Base, BaseModelMixin):
            __tablename__ = "sport_achievements"
            sport_id: Mapped[int] = mapped_column(ForeignKey("sports.id"), nullable=False)
            student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
            title: Mapped[str] = mapped_column(String(200), nullable=False)
            achievement_type: Mapped[str] = mapped_column(String(20), nullable=False)
            level: Mapped[str] = mapped_column(String(20), nullable=False)
            event_name: Mapped[str] = mapped_column(String(200), nullable=False)
            event_date: Mapped[date] = mapped_column(Date, nullable=False)


        class Room(Base, BaseModelMixin):
            __tablename__ = "rooms"
            name: Mapped[str] = mapped_column(String(100), nullable=False)
            room_number: Mapped[str] = mapped_column(String(20), nullable=False)
            building: Mapped[str | None] = mapped_column(String(100))
            floor: Mapped[int | None] = mapped_column(Integer)
            capacity: Mapped[int | None] = mapped_column(Integer)
            room_type: Mapped[str | None] = mapped_column(String(50))
            is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


        class Notification(Base, BaseModelMixin):
            __tablename__ = "notifications"
            title: Mapped[str] = mapped_column(String(200), nullable=False)
            message: Mapped[str] = mapped_column(Text, nullable=False)
            notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
            priority: Mapped[str] = mapped_column(String(20), nullable=False)
            sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
            recipient_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
            recipient_role: Mapped[str | None] = mapped_column(String(20))
            is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


        class UploadedFile(Base, BaseModelMixin):
            __tablename__ = "uploaded_files"
            filename: Mapped[str] = mapped_column(String(255), nullable=False)
            original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
            file_type: Mapped[str | None] = mapped_column(String(50))
            file_size: Mapped[int] = mapped_column(Integer, nullable=False)
            file_path: Mapped[str] = mapped_column(String(500), nullable=False)
            uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
            category: Mapped[str | None] = mapped_column(String(50))


        class Payment(Base, BaseModelMixin):
            __tablename__ = "payments"
            student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
            amount: Mapped[float] = mapped_column(Float, nullable=False)
            payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
            payment_date: Mapped[date] = mapped_column(Date, nullable=False)
            status: Mapped[str] = mapped_column(String(20), nullable=False)
            transaction_id: Mapped[str | None] = mapped_column(String(100))
            receipt_number: Mapped[str | None] = mapped_column(String(50))


        class Guardian(Base, BaseModelMixin):
            __tablename__ = "guardians"
            user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
            student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
            relationship: Mapped[str] = mapped_column(String(50), nullable=False)
            phone: Mapped[str | None] = mapped_column(String(20))
            occupation: Mapped[str | None] = mapped_column(String(100))
            address: Mapped[str | None] = mapped_column(Text)
            is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


        class Setting(Base, BaseModelMixin):
            __tablename__ = "settings"
            key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
            value: Mapped[str] = mapped_column(Text, nullable=False)
            category: Mapped[str | None] = mapped_column(String(50))
            description: Mapped[str | None] = mapped_column(Text)


        class Plugin(Base, BaseModelMixin):
            __tablename__ = "plugins"
            name: Mapped[str] = mapped_column(String(100), nullable=False)
            version: Mapped[str] = mapped_column(String(20), nullable=False)
            description: Mapped[str | None] = mapped_column(Text)
            is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
            config: Mapped[str | None] = mapped_column(Text)


        class Report(Base, BaseModelMixin):
            __tablename__ = "reports"
            title: Mapped[str] = mapped_column(String(200), nullable=False)
            report_type: Mapped[str] = mapped_column(String(50), nullable=False)
            generated_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
            format: Mapped[str] = mapped_column(String(20), nullable=False)
            file_path: Mapped[str | None] = mapped_column(String(500))
            parameters: Mapped[str | None] = mapped_column(Text)


        class AuditLog(Base, BaseModelMixin):
            __tablename__ = "audit_logs"
            user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
            action: Mapped[str] = mapped_column(String(100), nullable=False)
            entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
            entity_id: Mapped[str] = mapped_column(String(50), nullable=False)
            old_values: Mapped[str | None] = mapped_column(Text)
            new_values: Mapped[str | None] = mapped_column(Text)
            ip_address: Mapped[str | None] = mapped_column(String(50))
        """,
    )

    write(
        "preskool-erp/backend/app/models/__init__.py",
        """
        from app.models.core import *  # noqa: F401,F403
        """,
    )

    write(
        "preskool-erp/backend/app/schemas/common.py",
        """
        from datetime import date, datetime
        from typing import Any

        from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


        class ORMModel(BaseModel):
            model_config = ConfigDict(from_attributes=True)


        class ResourceBase(ORMModel):
            id: int | None = None
            tenant_id: str | None = None
            created_at: datetime | None = None
            updated_at: datetime | None = None


        class UserRead(ResourceBase):
            email: EmailStr
            full_name: str
            role: str
            is_active: bool
            is_verified: bool


        class LoginRequest(BaseModel):
            email: EmailStr
            password: str


        class RegisterRequest(BaseModel):
            email: EmailStr
            password: str
            full_name: str
            role: str
            tenant_id: str
            is_active: bool = True
            is_verified: bool = True


        class TokenResponse(BaseModel):
            access_token: str
            refresh_token: str
            user: UserRead


        class RefreshRequest(BaseModel):
            refresh_token: str


        class GenericSchema(ResourceBase):
            pass


        class StudentBase(BaseModel):
            student_id: str
            first_name: str
            last_name: str
            date_of_birth: date
            gender: str
            email: EmailStr | None = None
            phone: str | None = None
            address: str | None = None
            enrollment_date: date
            class_id: int | None = None
            parent_id: int | None = None
            status: str = "active"
            photo_url: str | None = None
            emergency_contact: str | None = None
            emergency_contact_name: str | None = None
            medical_info: str | None = None
            password: str | None = None

            @field_validator("email", mode="before")
            @classmethod
            def blank_email_to_none(cls, value: Any) -> Any:
                if value == "":
                    return None
                return value


        class StudentCreate(StudentBase):
            pass


        class StudentRead(StudentBase, ResourceBase):
            user_id: int | None = None


        class TeacherBase(BaseModel):
            employee_id: str
            first_name: str
            last_name: str
            date_of_birth: date
            gender: str
            phone: str | None = None
            address: str | None = None
            hire_date: date
            qualification: str | None = None
            specialization: str | None = None
            salary: float | None = None
            status: str = "active"
            photo_url: str | None = None
            email: EmailStr | None = None
            password: str | None = None

            @field_validator("email", mode="before")
            @classmethod
            def blank_email_to_none(cls, value: Any) -> Any:
                if value == "":
                    return None
                return value


        class TeacherCreate(TeacherBase):
            user_id: int | None = None


        class TeacherRead(TeacherBase, ResourceBase):
            user_id: int


        class DashboardStatistics(BaseModel):
            total_students: int
            total_teachers: int
            active_classes: int
            revenue_this_month: float
            attendance_rate: float
            fee_collection_rate: float
            pending_leaves: int
            open_issues: int
            total_tenants: int
            total_users: int
        """,
    )

    write(
        "preskool-erp/backend/app/services/base.py",
        """
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
        """,
    )

    write(
        "preskool-erp/backend/app/services/auth.py",
        """
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
        """,
    )

    write(
        "preskool-erp/backend/app/services/specialized.py",
        """
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
        """,
    )

    write(
        "preskool-erp/backend/app/api/v1/router.py",
        """
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


        @router.post("/teachers/", response_model=TeacherRead, dependencies=[Depends(require_roles("admin", "super_admin"))])
        async def create_teacher(payload: TeacherCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
            teacher = await teacher_service.create_teacher(db, current_user.tenant_id, payload)
            return TeacherRead.model_validate(teacher)


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
        """,
    )

    write(
        "preskool-erp/backend/app/main.py",
        """
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from sqlalchemy import text

        from app.api.v1.router import router as api_router
        from app.core.auth import get_password_hash
        from app.core.config import get_settings
        from app.core.database import AsyncSessionLocal
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
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
                await ensure_super_admin(
                    session,
                    settings.default_tenant_id,
                    settings.superadmin_email,
                    get_password_hash(settings.superadmin_password),
                    settings.superadmin_name,
                )
        """,
    )

    write(
        "preskool-erp/backend/alembic.ini",
        """
        [alembic]
        script_location = alembic
        sqlalchemy.url = postgresql+psycopg2://preskool:preskool@localhost:5432/preskool

        [loggers]
        keys = root,sqlalchemy,alembic
        [handlers]
        keys = console
        [formatters]
        keys = generic
        [logger_root]
        level = WARN
        handlers = console
        [logger_sqlalchemy]
        level = WARN
        handlers =
        qualname = sqlalchemy.engine
        [logger_alembic]
        level = INFO
        handlers =
        qualname = alembic
        [handler_console]
        class = StreamHandler
        args = (sys.stderr,)
        level = NOTSET
        formatter = generic
        [formatter_generic]
        format = %(levelname)-5.5s [%(name)s] %(message)s
        """,
    )

    write(
        "preskool-erp/backend/alembic/env.py",
        """
        from logging.config import fileConfig

        from alembic import context
        from sqlalchemy import create_engine, pool

        from app.core.config import get_settings
        from app.core.database import Base
        from app.models import *  # noqa: F401,F403

        config = context.config
        settings = get_settings()
        config.set_main_option("sqlalchemy.url", settings.sync_database_url)

        if config.config_file_name is not None:
            fileConfig(config.config_file_name)

        target_metadata = Base.metadata


        def run_migrations_offline() -> None:
            context.configure(url=settings.sync_database_url, target_metadata=target_metadata, literal_binds=True)
            with context.begin_transaction():
                context.run_migrations()


        def run_migrations_online() -> None:
            connectable = create_engine(settings.sync_database_url, poolclass=pool.NullPool)
            with connectable.connect() as connection:
                context.configure(connection=connection, target_metadata=target_metadata)
                with context.begin_transaction():
                    context.run_migrations()


        if context.is_offline_mode():
            run_migrations_offline()
        else:
            run_migrations_online()
        """,
    )

    write(
        "preskool-erp/backend/alembic/versions/001_initial.py",
        """
        from alembic import op
        import sqlalchemy as sa

        from app.core.database import Base
        from app.models import *  # noqa: F401,F403

        revision = "001_initial"
        down_revision = None
        branch_labels = None
        depends_on = None


        def _rls_sql(table_name: str) -> None:
            op.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;")
            op.execute(
                f\"\"\"
                CREATE POLICY tenant_isolation_{table_name}
                ON {table_name}
                USING (tenant_id = current_setting('app.current_tenant_id')::text);
                \"\"\"
            )
            op.execute(
                f\"\"\"
                CREATE POLICY superadmin_all_{table_name}
                ON {table_name}
                USING (current_setting('app.is_superadmin', true)::boolean = true);
                \"\"\"
            )


        def upgrade() -> None:
            bind = op.get_bind()
            Base.metadata.create_all(bind=bind)
            for table_name in Base.metadata.tables:
                if table_name != "tenants":
                    _rls_sql(table_name)


        def downgrade() -> None:
            Base.metadata.drop_all(bind=op.get_bind())
        """,
    )

    write(
        "preskool-erp/backend/e2e_test.py",
        """
        import pytest
        from httpx import AsyncClient, ASGITransport

        from app.main import app


        @pytest.mark.asyncio
        async def test_health_endpoint():
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/v1/health")
                assert response.status_code == 200
                assert response.json()["status"] == "healthy"
        """,
    )

    write(
        "preskool-erp/frontend/package.json",
        """
        {
          "name": "preskool-erp-frontend",
          "private": true,
          "version": "1.0.0",
          "type": "module",
          "scripts": {
            "dev": "vite",
            "build": "tsc -b && vite build",
            "preview": "vite preview"
          },
          "dependencies": {
            "@emotion/react": "^11.14.0",
            "@emotion/styled": "^11.14.1",
            "@mui/icons-material": "^7.3.2",
            "@mui/material": "^7.3.2",
            "@reduxjs/toolkit": "^2.9.0",
            "axios": "^1.11.0",
            "dayjs": "^1.11.13",
            "react": "^19.1.1",
            "react-dom": "^19.1.1",
            "react-redux": "^9.2.0",
            "react-router-dom": "^7.8.2"
          },
          "devDependencies": {
            "@types/react": "^19.1.10",
            "@types/react-dom": "^19.1.7",
            "@vitejs/plugin-react": "^5.0.0",
            "typescript": "~5.8.3",
            "vite": "^7.1.2"
          }
        }
        """,
    )

    write(
        "preskool-erp/frontend/tsconfig.json",
        """
        {
          "compilerOptions": {
            "target": "ES2022",
            "useDefineForClassFields": true,
            "lib": ["DOM", "DOM.Iterable", "ES2022"],
            "allowJs": false,
            "skipLibCheck": true,
            "esModuleInterop": true,
            "allowSyntheticDefaultImports": true,
            "strict": true,
            "forceConsistentCasingInFileNames": true,
            "module": "ESNext",
            "moduleResolution": "Bundler",
            "resolveJsonModule": true,
            "isolatedModules": true,
            "noEmit": true,
            "jsx": "react-jsx"
          },
          "include": ["src"],
          "references": []
        }
        """,
    )

    write(
        "preskool-erp/frontend/vite.config.ts",
        """
        import { defineConfig } from "vite";
        import react from "@vitejs/plugin-react";

        export default defineConfig({
          plugins: [react()],
          server: { port: 5173 },
        });
        """,
    )

    write(
        "preskool-erp/frontend/index.html",
        """
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <link rel="preconnect" href="https://fonts.googleapis.com" />
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
            <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
            <title>PreSkool ERP</title>
          </head>
          <body>
            <div id="root"></div>
            <script type="module" src="/src/main.tsx"></script>
          </body>
        </html>
        """,
    )

    write(
        "preskool-erp/frontend/vercel.json",
        """
        {
          "rewrites": [
            { "source": "/(.*)", "destination": "/" }
          ]
        }
        """,
    )

    write(
        "preskool-erp/frontend/src/services/api.ts",
        """
        import axios from "axios";

        const api = axios.create({
          baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1",
        });

        api.interceptors.request.use((config) => {
          const token = localStorage.getItem("access_token");
          if (token) {
            config.headers.Authorization = `Bearer ${token}`;
          }
          return config;
        });

        api.interceptors.response.use(
          (response) => response,
          async (error) => {
            const original = error.config;
            if (error.response?.status === 401 && !original._retry) {
              original._retry = true;
              const refreshToken = localStorage.getItem("refresh_token");
              if (refreshToken) {
                const response = await axios.post(`${api.defaults.baseURL}/auth/refresh`, { refresh_token: refreshToken });
                localStorage.setItem("access_token", response.data.access_token);
                localStorage.setItem("refresh_token", response.data.refresh_token);
                original.headers.Authorization = `Bearer ${response.data.access_token}`;
                return api(original);
              }
            }
            return Promise.reject(error);
          }
        );

        export default api;
        """,
    )

    write(
        "preskool-erp/frontend/src/store/store.ts",
        """
        import { configureStore } from "@reduxjs/toolkit";
        import authReducer from "./slices/authSlice";
        import dashboardReducer from "./slices/dashboardSlice";
        import resourcesReducer from "./slices/resourcesSlice";

        export const store = configureStore({
          reducer: {
            auth: authReducer,
            dashboard: dashboardReducer,
            resources: resourcesReducer,
          },
        });

        export type RootState = ReturnType<typeof store.getState>;
        export type AppDispatch = typeof store.dispatch;
        """,
    )

    write(
        "preskool-erp/frontend/src/store/slices/authSlice.ts",
        """
        import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
        import api from "../../services/api";

        export interface User {
          id: number;
          email: string;
          full_name: string;
          role: string;
          tenant_id: string;
        }

        interface AuthState {
          user: User | null;
          status: "idle" | "loading" | "failed";
          error: string | null;
        }

        const initialState: AuthState = {
          user: null,
          status: "idle",
          error: null,
        };

        export const login = createAsyncThunk("auth/login", async (payload: { email: string; password: string }) => {
          const response = await api.post("/auth/login", payload);
          localStorage.setItem("access_token", response.data.access_token);
          localStorage.setItem("refresh_token", response.data.refresh_token);
          localStorage.setItem("user", JSON.stringify(response.data.user));
          return response.data.user as User;
        });

        export const register = createAsyncThunk("auth/register", async (payload: Record<string, unknown>) => {
          const response = await api.post("/auth/register", payload);
          return response.data as User;
        });

        const authSlice = createSlice({
          name: "auth",
          initialState,
          reducers: {
            hydrateUser: (state) => {
              const raw = localStorage.getItem("user");
              state.user = raw ? JSON.parse(raw) : null;
            },
            logout: (state) => {
              localStorage.removeItem("access_token");
              localStorage.removeItem("refresh_token");
              localStorage.removeItem("user");
              state.user = null;
            },
          },
          extraReducers: (builder) => {
            builder
              .addCase(login.pending, (state) => {
                state.status = "loading";
              })
              .addCase(login.fulfilled, (state, action) => {
                state.status = "idle";
                state.user = action.payload;
              })
              .addCase(login.rejected, (state, action) => {
                state.status = "failed";
                state.error = action.error.message ?? "Login failed";
              });
          },
        });

        export const { hydrateUser, logout } = authSlice.actions;
        export default authSlice.reducer;
        """,
    )

    write(
        "preskool-erp/frontend/src/store/slices/dashboardSlice.ts",
        """
        import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
        import api from "../../services/api";

        export const fetchDashboardStatistics = createAsyncThunk("dashboard/fetchStatistics", async () => {
          const response = await api.get("/dashboard/statistics");
          return response.data;
        });

        const dashboardSlice = createSlice({
          name: "dashboard",
          initialState: { stats: null as Record<string, number> | null, status: "idle" as string },
          reducers: {},
          extraReducers: (builder) => {
            builder
              .addCase(fetchDashboardStatistics.pending, (state) => {
                state.status = "loading";
              })
              .addCase(fetchDashboardStatistics.fulfilled, (state, action) => {
                state.status = "idle";
                state.stats = action.payload;
              })
              .addCase(fetchDashboardStatistics.rejected, (state) => {
                state.status = "failed";
              });
          },
        });

        export default dashboardSlice.reducer;
        """,
    )

    write(
        "preskool-erp/frontend/src/store/slices/resourcesSlice.ts",
        """
        import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
        import api from "../../services/api";

        export const fetchResource = createAsyncThunk("resources/fetch", async (resource: string) => {
          const response = await api.get(`/${resource}/`);
          return { resource, items: response.data };
        });

        export const createResource = createAsyncThunk("resources/create", async ({ resource, payload }: { resource: string; payload: Record<string, unknown> }) => {
          const response = await api.post(`/${resource}/`, payload);
          return { resource, item: response.data };
        });

        export const updateResource = createAsyncThunk("resources/update", async ({ resource, id, payload }: { resource: string; id: number; payload: Record<string, unknown> }) => {
          const response = await api.put(`/${resource}/${id}`, payload);
          return { resource, item: response.data };
        });

        export const deleteResource = createAsyncThunk("resources/delete", async ({ resource, id }: { resource: string; id: number }) => {
          await api.delete(`/${resource}/${id}`);
          return { resource, id };
        });

        const resourcesSlice = createSlice({
          name: "resources",
          initialState: { byResource: {} as Record<string, unknown[]> },
          reducers: {},
          extraReducers: (builder) => {
            builder
              .addCase(fetchResource.fulfilled, (state, action) => {
                state.byResource[action.payload.resource] = action.payload.items;
              })
              .addCase(createResource.fulfilled, (state, action) => {
                const current = (state.byResource[action.payload.resource] ?? []) as unknown[];
                state.byResource[action.payload.resource] = [action.payload.item, ...current];
              })
              .addCase(updateResource.fulfilled, (state, action) => {
                const current = (state.byResource[action.payload.resource] ?? []) as Record<string, unknown>[];
                state.byResource[action.payload.resource] = current.map((item) => item.id === action.payload.item.id ? action.payload.item : item);
              })
              .addCase(deleteResource.fulfilled, (state, action) => {
                const current = (state.byResource[action.payload.resource] ?? []) as Record<string, unknown>[];
                state.byResource[action.payload.resource] = current.filter((item) => item.id !== action.payload.id);
              });
          },
        });

        export default resourcesSlice.reducer;
        """,
    )

    write(
        "preskool-erp/frontend/src/components/auth/RoleProtectedRoute.tsx",
        """
        import { Navigate, Outlet } from "react-router-dom";

        const dashboardByRole: Record<string, string> = {
          super_admin: "/super-admin-dashboard",
          superadmin: "/super-admin-dashboard",
          admin: "/admin-dashboard",
          teacher: "/teacher-dashboard",
          student: "/student-dashboard",
          parent: "/parent-dashboard",
        };

        export function RoleProtectedRoute({ allowedRoles, role }: { allowedRoles: string[]; role?: string }) {
          if (!role) {
            return <Navigate to="/login" replace />;
          }
          if (allowedRoles.includes(role)) {
            return <Outlet />;
          }
          return <Navigate to={dashboardByRole[role] ?? "/profile"} replace />;
        }

        export function roleDashboard(role?: string) {
          return (role && dashboardByRole[role]) || "/profile";
        }
        """,
    )

    write(
        "preskool-erp/frontend/src/layouts/DashboardLayout.tsx",
        """
        import { PropsWithChildren } from "react";
        import { AppBar, Box, CssBaseline, Drawer, List, ListItemButton, ListItemText, Toolbar, Typography } from "@mui/material";
        import { Link, useLocation } from "react-router-dom";

        export interface NavItem {
          label: string;
          path: string;
        }

        export default function DashboardLayout({ children, items, title }: PropsWithChildren<{ items: NavItem[]; title: string }>) {
          const location = useLocation();
          return (
            <Box sx={{ display: "flex", minHeight: "100vh", bgcolor: "#f4f7fb" }}>
              <CssBaseline />
              <AppBar position="fixed" sx={{ bgcolor: "#3D5EE1", backgroundImage: "linear-gradient(90deg, #3D5EE1, #10b981)" }}>
                <Toolbar>
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>{title}</Typography>
                </Toolbar>
              </AppBar>
              <Drawer
                variant="permanent"
                sx={{
                  width: 260,
                  flexShrink: 0,
                  [`& .MuiDrawer-paper`]: { width: 260, boxSizing: "border-box", mt: 8, borderRight: 0, bgcolor: "#0f172a", color: "#fff" },
                }}
              >
                <List>
                  {items.map((item) => (
                    <ListItemButton
                      component={Link}
                      to={item.path}
                      selected={location.pathname === item.path}
                      key={item.path}
                      sx={{ borderRadius: 2, mx: 1, my: 0.5 }}
                    >
                      <ListItemText primary={item.label} />
                    </ListItemButton>
                  ))}
                </List>
              </Drawer>
              <Box component="main" sx={{ flexGrow: 1, p: 4, mt: 8, ml: "260px" }}>
                {children}
              </Box>
            </Box>
          );
        }
        """,
    )

    write(
        "preskool-erp/frontend/src/pages/ResourcePage.tsx",
        """
        import { FormEvent, useEffect, useState } from "react";
        import { Alert, Box, Button, Card, CardContent, CircularProgress, Grid, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from "@mui/material";
        import { useDispatch, useSelector } from "react-redux";
        import { createResource, deleteResource, fetchResource } from "../store/slices/resourcesSlice";
        import type { AppDispatch, RootState } from "../store/store";

        export default function ResourcePage({ resource, title, fields }: { resource: string; title: string; fields: string[] }) {
          const dispatch = useDispatch<AppDispatch>();
          const items = useSelector((state: RootState) => state.resources.byResource[resource] as Record<string, unknown>[] | undefined) ?? [];
          const [form, setForm] = useState<Record<string, string>>({});
          const [loading, setLoading] = useState(false);

          useEffect(() => {
            void dispatch(fetchResource(resource));
          }, [dispatch, resource]);

          async function handleSubmit(event: FormEvent) {
            event.preventDefault();
            setLoading(true);
            const payload = Object.fromEntries(
              Object.entries(form)
                .map(([key, value]) => [key, value.trim() === "" ? undefined : value])
                .filter(([, value]) => value !== undefined)
            );
            await dispatch(createResource({ resource, payload }));
            setForm({});
            setLoading(false);
          }

          return (
            <Stack spacing={3}>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>{title}</Typography>
              <Grid container spacing={3}>
                <Grid size={{ xs: 12, md: 4 }}>
                  <Card sx={{ borderRadius: 3, boxShadow: "0 20px 45px rgba(15, 23, 42, 0.08)" }}>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>Add {title.slice(0, -1)}</Typography>
                      <Box component="form" onSubmit={handleSubmit}>
                        <Stack spacing={2}>
                          {fields.map((field) => (
                            <TextField
                              key={field}
                              label={field.replaceAll("_", " ")}
                              value={form[field] ?? ""}
                              onChange={(event) => setForm((current) => ({ ...current, [field]: event.target.value }))}
                              fullWidth
                              size="small"
                            />
                          ))}
                          <Button type="submit" variant="contained" disabled={loading}>
                            {loading ? <CircularProgress size={18} color="inherit" /> : "Save"}
                          </Button>
                        </Stack>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid size={{ xs: 12, md: 8 }}>
                  <Card sx={{ borderRadius: 3, boxShadow: "0 20px 45px rgba(15, 23, 42, 0.08)" }}>
                    <CardContent>
                      {items.length === 0 ? (
                        <Alert severity="info">No records found</Alert>
                      ) : (
                        <Table stickyHeader>
                          <TableHead>
                            <TableRow>
                              {fields.map((field) => <TableCell key={field}>{field}</TableCell>)}
                              <TableCell align="right">Actions</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {items.map((item, index) => (
                              <TableRow key={String(item.id ?? index)} sx={{ "&:nth-of-type(odd)": { bgcolor: "rgba(61,94,225,0.03)" } }}>
                                {fields.map((field) => <TableCell key={field}>{String(item[field] ?? "")}</TableCell>)}
                                <TableCell align="right">
                                  <Button color="error" onClick={() => void dispatch(deleteResource({ resource, id: Number(item.id) }))}>Delete</Button>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Stack>
          );
        }
        """,
    )

    write(
        "preskool-erp/frontend/src/pages/LoginPage.tsx",
        """
        import { FormEvent, useState } from "react";
        import { Alert, Box, Button, Card, CardContent, Stack, TextField, Typography } from "@mui/material";
        import { useDispatch, useSelector } from "react-redux";
        import { useNavigate } from "react-router-dom";
        import { roleDashboard } from "../components/auth/RoleProtectedRoute";
        import { login } from "../store/slices/authSlice";
        import type { AppDispatch, RootState } from "../store/store";

        export default function LoginPage() {
          const dispatch = useDispatch<AppDispatch>();
          const navigate = useNavigate();
          const [email, setEmail] = useState("admin@preskool.com");
          const [password, setPassword] = useState("Admin@1234");
          const auth = useSelector((state: RootState) => state.auth);

          async function handleSubmit(event: FormEvent) {
            event.preventDefault();
            const result = await dispatch(login({ email, password }));
            if (login.fulfilled.match(result)) {
              navigate(roleDashboard(result.payload.role));
            }
          }

          return (
            <Box sx={{ minHeight: "100vh", display: "grid", placeItems: "center", background: "radial-gradient(circle at top, #dbeafe, #f8fafc 55%)" }}>
              <Card sx={{ width: 420, borderRadius: 4, boxShadow: "0 25px 60px rgba(15,23,42,0.12)" }}>
                <CardContent sx={{ p: 4 }}>
                  <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>PreSkool ERP</Typography>
                  <Typography color="text.secondary" sx={{ mb: 3 }}>Production-ready multi-tenant school operations</Typography>
                  <Box component="form" onSubmit={handleSubmit}>
                    <Stack spacing={2}>
                      {auth.error && <Alert severity="error">{auth.error}</Alert>}
                      <TextField label="Email" value={email} onChange={(event) => setEmail(event.target.value)} />
                      <TextField label="Password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
                      <Button type="submit" variant="contained" size="large">Sign in</Button>
                    </Stack>
                  </Box>
                </CardContent>
              </Card>
            </Box>
          );
        }
        """,
    )

    write(
        "preskool-erp/frontend/src/pages/DashboardPage.tsx",
        """
        import { useEffect } from "react";
        import { Alert, Card, CardContent, Grid, Stack, Typography } from "@mui/material";
        import { useDispatch, useSelector } from "react-redux";
        import { fetchDashboardStatistics } from "../store/slices/dashboardSlice";
        import type { AppDispatch, RootState } from "../store/store";

        const statConfig = [
          ["total_students", "Total Students"],
          ["total_teachers", "Total Teachers"],
          ["active_classes", "Active Classes"],
          ["revenue_this_month", "Revenue This Month"],
          ["attendance_rate", "Attendance Rate"],
          ["fee_collection_rate", "Fee Collection Rate"],
          ["pending_leaves", "Pending Leaves"],
          ["open_issues", "Open Issues"],
        ];

        export default function DashboardPage({ title }: { title: string }) {
          const dispatch = useDispatch<AppDispatch>();
          const stats = useSelector((state: RootState) => state.dashboard.stats);

          useEffect(() => {
            void dispatch(fetchDashboardStatistics());
          }, [dispatch]);

          return (
            <Stack spacing={3}>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>{title}</Typography>
              {!stats ? (
                <Alert severity="info">Loading dashboard data...</Alert>
              ) : (
                <Grid container spacing={3}>
                  {statConfig.map(([key, label]) => (
                    <Grid size={{ xs: 12, sm: 6, xl: 3 }} key={key}>
                      <Card sx={{ borderRadius: 3, minHeight: 140, boxShadow: "0 18px 40px rgba(15,23,42,0.08)", transition: "transform 0.2s ease", "&:hover": { transform: "translateY(-4px)" } }}>
                        <CardContent>
                          <Typography color="text.secondary">{label}</Typography>
                          <Typography variant="h4" sx={{ mt: 2, fontWeight: 700 }}>{String(stats[key] ?? 0)}</Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              )}
            </Stack>
          );
        }
        """,
    )

    write(
        "preskool-erp/frontend/src/App.tsx",
        """
        import { useEffect } from "react";
        import { ThemeProvider, createTheme } from "@mui/material";
        import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
        import { useDispatch, useSelector } from "react-redux";
        import DashboardLayout, { NavItem } from "./layouts/DashboardLayout";
        import { RoleProtectedRoute, roleDashboard } from "./components/auth/RoleProtectedRoute";
        import DashboardPage from "./pages/DashboardPage";
        import LoginPage from "./pages/LoginPage";
        import ResourcePage from "./pages/ResourcePage";
        import { hydrateUser } from "./store/slices/authSlice";
        import type { AppDispatch, RootState } from "./store/store";

        const theme = createTheme({
          typography: { fontFamily: "Outfit, sans-serif" },
          shape: { borderRadius: 12 },
          palette: {
            primary: { main: "#3D5EE1" },
            success: { main: "#10b981" },
            warning: { main: "#f59e0b" },
            background: { default: "#f4f7fb" },
          },
        });

        const adminNav: NavItem[] = [
          { label: "Dashboard", path: "/admin-dashboard" },
          { label: "Students", path: "/students" },
          { label: "Teachers", path: "/teachers" },
          { label: "Classes", path: "/classes" },
          { label: "Subjects", path: "/subjects" },
          { label: "Departments", path: "/departments" },
          { label: "Timetable", path: "/timetable" },
          { label: "Attendance", path: "/attendance" },
          { label: "Exams", path: "/exams" },
          { label: "Grades", path: "/grades" },
          { label: "Fees", path: "/fees" },
          { label: "Payroll", path: "/payroll" },
          { label: "Leave", path: "/leave" },
          { label: "Library", path: "/library" },
          { label: "Hostel", path: "/hostel" },
          { label: "Transport", path: "/transport" },
          { label: "Sports", path: "/sports" },
          { label: "Rooms", path: "/rooms" },
          { label: "Guardians", path: "/guardians" },
          { label: "Reports", path: "/reports" },
          { label: "Notifications", path: "/notifications" },
          { label: "Files", path: "/files" },
          { label: "Payments", path: "/payments" },
          { label: "Settings", path: "/settings" },
          { label: "Plugins", path: "/plugins" }
        ];

        const teacherNav: NavItem[] = [
          { label: "Dashboard", path: "/teacher-dashboard" },
          { label: "Classes", path: "/classes" },
          { label: "Attendance", path: "/attendance" },
          { label: "Grades", path: "/grades" },
          { label: "Timetable", path: "/timetable" },
          { label: "Syllabus", path: "/syllabus" },
          { label: "Leave", path: "/leave" },
          { label: "Notifications", path: "/notifications" },
          { label: "Profile", path: "/profile" },
        ];

        const studentNav: NavItem[] = [
          { label: "Dashboard", path: "/student-dashboard" },
          { label: "Timetable", path: "/timetable" },
          { label: "Subjects", path: "/subjects" },
          { label: "Syllabus", path: "/syllabus" },
          { label: "Files", path: "/files" },
          { label: "Grades", path: "/grades" },
          { label: "Attendance", path: "/attendance" },
          { label: "Fees", path: "/fees" },
          { label: "Library", path: "/library" },
          { label: "Notifications", path: "/notifications" },
          { label: "Profile", path: "/profile" },
        ];

        const parentNav: NavItem[] = [
          { label: "Dashboard", path: "/parent-dashboard" },
          { label: "Children", path: "/guardians" },
          { label: "Attendance", path: "/attendance" },
          { label: "Grades", path: "/grades" },
          { label: "Fees", path: "/fees" },
          { label: "Notifications", path: "/notifications" },
          { label: "Profile", path: "/profile" },
        ];

        const superAdminNav: NavItem[] = [
          { label: "Super Admin Dashboard", path: "/super-admin-dashboard" },
          { label: "Admin Panel", path: "/admin-dashboard" },
          { label: "Settings", path: "/settings" },
          { label: "Plugins", path: "/plugins" },
          { label: "Students", path: "/students" },
          { label: "Teachers", path: "/teachers" },
          { label: "Departments", path: "/departments" },
          { label: "Fees", path: "/fees" },
          { label: "Payroll", path: "/payroll" },
          { label: "Payments", path: "/payments" },
          { label: "Reports", path: "/reports" },
        ];

        const resourceMap: Record<string, { title: string; fields: string[] }> = {
          students: { title: "Students", fields: ["student_id", "first_name", "last_name", "date_of_birth", "gender", "email", "enrollment_date"] },
          teachers: { title: "Teachers", fields: ["employee_id", "first_name", "last_name", "date_of_birth", "gender", "hire_date", "email"] },
          classes: { title: "Classes", fields: ["name", "grade_level", "section", "academic_year", "room_number", "capacity"] },
          subjects: { title: "Subjects", fields: ["name", "code", "description", "credits"] },
          departments: { title: "Departments", fields: ["name", "code", "description"] },
          timetable: { title: "Timetable", fields: ["class_id", "subject_id", "teacher_id", "day_of_week", "start_time", "end_time", "period_number", "academic_year"] },
          attendance: { title: "Attendance", fields: ["student_id", "class_id", "date", "status", "academic_year"] },
          exams: { title: "Exams", fields: ["name", "exam_type", "class_id", "subject_id", "date", "total_marks", "passing_marks", "academic_year"] },
          grades: { title: "Grades", fields: ["student_id", "exam_id", "subject_id", "marks_obtained", "grade", "academic_year"] },
          fees: { title: "Student Fee Assignments", fields: ["student_id", "fee_type_id", "amount", "discount", "net_amount", "paid_amount", "balance", "status"] },
          payroll: { title: "Salary Structures", fields: ["teacher_id", "basic_salary", "hra", "da", "ta", "net_salary", "effective_from"] },
          leave: { title: "Leave Requests", fields: ["user_id", "leave_type", "start_date", "end_date", "reason", "status"] },
          library: { title: "Books", fields: ["title", "isbn", "author", "publisher", "total_copies", "available_copies", "status"] },
          hostel: { title: "Hostels", fields: ["name", "code", "hostel_type", "total_rooms", "total_beds", "monthly_fee"] },
          transport: { title: "Transport Routes", fields: ["route_name", "route_code", "start_point", "end_point", "distance_km", "status"] },
          sports: { title: "Sports", fields: ["name", "code", "category", "coach_name", "venue", "status"] },
          rooms: { title: "Rooms", fields: ["name", "room_number", "building", "floor", "capacity", "room_type"] },
          guardians: { title: "Guardians", fields: ["user_id", "student_id", "relationship", "phone", "occupation"] },
          reports: { title: "Reports", fields: ["title", "report_type", "generated_by", "format", "file_path"] },
          notifications: { title: "Notifications", fields: ["title", "message", "notification_type", "priority", "sender_id"] },
          files: { title: "Files", fields: ["filename", "original_filename", "file_size", "file_path", "uploaded_by"] },
          payments: { title: "Payments", fields: ["student_id", "amount", "payment_method", "payment_date", "status", "transaction_id"] },
          settings: { title: "Settings", fields: ["key", "value", "category", "description"] },
          plugins: { title: "Plugins", fields: ["name", "version", "description", "is_enabled", "config"] },
          syllabus: { title: "Syllabus", fields: ["subject_id", "class_id", "title", "description", "topics", "academic_year", "completion_percentage"] },
          profile: { title: "Profile", fields: ["full_name", "email", "role"] },
        };

        function LayoutForRole({ role, children }: { role?: string; children: React.ReactNode }) {
          const items = role === "super_admin" ? superAdminNav : role === "admin" ? adminNav : role === "teacher" ? teacherNav : role === "student" ? studentNav : parentNav;
          return <DashboardLayout items={items} title="PreSkool ERP">{children}</DashboardLayout>;
        }

        export default function App() {
          const dispatch = useDispatch<AppDispatch>();
          const role = useSelector((state: RootState) => state.auth.user?.role);

          useEffect(() => {
            dispatch(hydrateUser());
          }, [dispatch]);

          return (
            <ThemeProvider theme={theme}>
              <BrowserRouter>
                <Routes>
                  <Route path="/login" element={<LoginPage />} />
                  <Route path="/" element={<Navigate to={roleDashboard(role)} replace />} />

                  <Route element={<RoleProtectedRoute allowedRoles={["admin", "super_admin", "superadmin"]} role={role} />}>
                    <Route path="/admin-dashboard" element={<LayoutForRole role={role}><DashboardPage title="Admin Dashboard" /></LayoutForRole>} />
                  </Route>
                  <Route element={<RoleProtectedRoute allowedRoles={["super_admin", "superadmin"]} role={role} />}>
                    <Route path="/super-admin-dashboard" element={<LayoutForRole role={role}><DashboardPage title="Super Admin Dashboard" /></LayoutForRole>} />
                  </Route>
                  <Route element={<RoleProtectedRoute allowedRoles={["teacher"]} role={role} />}>
                    <Route path="/teacher-dashboard" element={<LayoutForRole role={role}><DashboardPage title="Teacher Dashboard" /></LayoutForRole>} />
                  </Route>
                  <Route element={<RoleProtectedRoute allowedRoles={["student"]} role={role} />}>
                    <Route path="/student-dashboard" element={<LayoutForRole role={role}><DashboardPage title="Student Dashboard" /></LayoutForRole>} />
                  </Route>
                  <Route element={<RoleProtectedRoute allowedRoles={["parent"]} role={role} />}>
                    <Route path="/parent-dashboard" element={<LayoutForRole role={role}><DashboardPage title="Parent Dashboard" /></LayoutForRole>} />
                  </Route>

                  {Object.entries(resourceMap).map(([path, config]) => (
                    <Route
                      key={path}
                      path={`/${path}`}
                      element={<LayoutForRole role={role}><ResourcePage resource={path === "fees" ? "student-fee-assignments" : path === "payroll" ? "salary-structures" : path === "library" ? "books" : path === "hostel" ? "hostels" : path === "transport" ? "transport" : path} title={config.title} fields={config.fields} /></LayoutForRole>}
                    />
                  ))}

                  <Route path="*" element={<Navigate to={roleDashboard(role)} replace />} />
                </Routes>
              </BrowserRouter>
            </ThemeProvider>
          );
        }
        """,
    )

    write(
        "preskool-erp/frontend/src/main.tsx",
        """
        import React from "react";
        import ReactDOM from "react-dom/client";
        import { Provider } from "react-redux";
        import App from "./App";
        import { store } from "./store/store";

        ReactDOM.createRoot(document.getElementById("root")!).render(
          <React.StrictMode>
            <Provider store={store}>
              <App />
            </Provider>
          </React.StrictMode>
        );
        """,
    )

    write(
        ".github/workflows/deploy.yml",
        """
        name: Deploy PreSkool ERP

        on:
          push:
            branches: [main]

        jobs:
          test:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
              - uses: actions/setup-python@v5
                with:
                  python-version: "3.11"
              - uses: actions/setup-node@v4
                with:
                  node-version: "20"
              - run: pip install -r preskool-erp/backend/requirements.txt
              - run: pytest preskool-erp/backend/e2e_test.py
              - run: cd preskool-erp/frontend && npm install && npm run build

          deploy-backend:
            needs: test
            if: github.ref == 'refs/heads/main'
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
              - uses: azure/login@v2
                with:
                  creds: ${{ secrets.AZURE_CREDENTIALS }}
              - uses: azure/webapps-deploy@v3
                with:
                  app-name: preskool-api-v2
                  package: preskool-erp/backend
        """,
    )


if __name__ == "__main__":
    main()
