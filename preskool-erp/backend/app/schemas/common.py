from __future__ import annotations

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
    tenant_id: str | None = None
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
