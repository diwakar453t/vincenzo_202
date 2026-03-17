from __future__ import annotations

from datetime import date, datetime
from typing import Optional

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
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    address: Mapped[Optional[str]] = mapped_column(Text)
    enrollment_date: Mapped[date] = mapped_column(Date, nullable=False)
    class_id: Mapped[Optional[int]] = mapped_column(ForeignKey("classes.id"))
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    photo_url: Mapped[Optional[str]] = mapped_column(String(500))
    emergency_contact: Mapped[Optional[str]] = mapped_column(String(20))
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(100))
    medical_info: Mapped[Optional[str]] = mapped_column(Text)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))


class Teacher(Base, BaseModelMixin):
    __tablename__ = "teachers"
    employee_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    address: Mapped[Optional[str]] = mapped_column(Text)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    qualification: Mapped[Optional[str]] = mapped_column(String(255))
    specialization: Mapped[Optional[str]] = mapped_column(String(255))
    salary: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    photo_url: Mapped[Optional[str]] = mapped_column(String(500))
    email: Mapped[Optional[str]] = mapped_column(String(255))


class ClassRoom(Base, BaseModelMixin):
    __tablename__ = "classes"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False)
    section: Mapped[str] = mapped_column(String(10), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    room_number: Mapped[Optional[str]] = mapped_column(String(20))
    capacity: Mapped[int] = mapped_column(Integer, default=40, nullable=False)
    class_teacher_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teachers.id"))


class Subject(Base, BaseModelMixin):
    __tablename__ = "subjects"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    credits: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class ClassSubject(Base, BaseModelMixin):
    __tablename__ = "class_subjects"
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)
    teacher_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teachers.id"))


class Department(Base, BaseModelMixin):
    __tablename__ = "departments"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    head_teacher_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teachers.id"))
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class SubjectGroup(Base, BaseModelMixin):
    __tablename__ = "subject_groups"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Syllabus(Base, BaseModelMixin):
    __tablename__ = "syllabus"
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    topics: Mapped[Optional[str]] = mapped_column(Text)
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
    room_number: Mapped[Optional[str]] = mapped_column(String(20))
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)


class StudentAttendance(Base, BaseModelMixin):
    __tablename__ = "student_attendance"
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    remarks: Mapped[Optional[str]] = mapped_column(Text)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)


class StaffAttendance(Base, BaseModelMixin):
    __tablename__ = "staff_attendance"
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    check_in: Mapped[Optional[str]] = mapped_column(String(10))
    check_out: Mapped[Optional[str]] = mapped_column(String(10))
    remarks: Mapped[Optional[str]] = mapped_column(Text)


class Exam(Base, BaseModelMixin):
    __tablename__ = "exams"
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    exam_type: Mapped[str] = mapped_column(String(50), nullable=False)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[Optional[str]] = mapped_column(String(10))
    end_time: Mapped[Optional[str]] = mapped_column(String(10))
    total_marks: Mapped[float] = mapped_column(Float, nullable=False)
    passing_marks: Mapped[float] = mapped_column(Float, nullable=False)
    room_number: Mapped[Optional[str]] = mapped_column(String(20))
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Grade(Base, BaseModelMixin):
    __tablename__ = "grades"
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)
    marks_obtained: Mapped[float] = mapped_column(Float, nullable=False)
    grade: Mapped[str] = mapped_column(String(5), nullable=False)
    remarks: Mapped[Optional[str]] = mapped_column(Text)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)


class FeeGroup(Base, BaseModelMixin):
    __tablename__ = "fee_groups"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class FeeType(Base, BaseModelMixin):
    __tablename__ = "fee_types"
    fee_group_id: Mapped[int] = mapped_column(ForeignKey("fee_groups.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    frequency: Mapped[Optional[str]] = mapped_column(String(20))
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    class_id: Mapped[Optional[int]] = mapped_column(ForeignKey("classes.id"))
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
    due_date: Mapped[Optional[date]] = mapped_column(Date)


class FeeCollection(Base, BaseModelMixin):
    __tablename__ = "fee_collections"
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    fee_type_id: Mapped[int] = mapped_column(ForeignKey("fee_types.id"), nullable=False)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("student_fee_assignments.id"), nullable=False)
    receipt_number: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    payment_method: Mapped[str] = mapped_column(String(20), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    transaction_id: Mapped[Optional[str]] = mapped_column(String(100))
    remarks: Mapped[Optional[str]] = mapped_column(Text)


class Leave(Base, BaseModelMixin):
    __tablename__ = "leaves"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    leave_type: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    approved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    remarks: Mapped[Optional[str]] = mapped_column(Text)


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
    payment_date: Mapped[Optional[date]] = mapped_column(Date)
    payment_method: Mapped[Optional[str]] = mapped_column(String(20))
    transaction_id: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), nullable=False)


class Book(Base, BaseModelMixin):
    __tablename__ = "books"
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    isbn: Mapped[Optional[str]] = mapped_column(String(50))
    author: Mapped[Optional[str]] = mapped_column(String(255))
    publisher: Mapped[Optional[str]] = mapped_column(String(255))
    edition: Mapped[Optional[str]] = mapped_column(String(50))
    category: Mapped[Optional[str]] = mapped_column(String(100))
    subject: Mapped[Optional[str]] = mapped_column(String(100))
    language: Mapped[Optional[str]] = mapped_column(String(50))
    pages: Mapped[Optional[int]] = mapped_column(Integer)
    price: Mapped[Optional[float]] = mapped_column(Float)
    rack_number: Mapped[Optional[str]] = mapped_column(String(50))
    total_copies: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    available_copies: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)


class LibraryMember(Base, BaseModelMixin):
    __tablename__ = "library_members"
    member_code: Mapped[str] = mapped_column(String(50), nullable=False)
    member_type: Mapped[str] = mapped_column(String(20), nullable=False)
    student_id: Mapped[Optional[int]] = mapped_column(ForeignKey("students.id"))
    teacher_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teachers.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    max_books_allowed: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)


class IssueReturn(Base, BaseModelMixin):
    __tablename__ = "issue_returns"
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False)
    member_id: Mapped[int] = mapped_column(ForeignKey("library_members.id"), nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    return_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    fine_amount: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    fine_per_day: Mapped[float] = mapped_column(Float, default=0, nullable=False)


class Hostel(Base, BaseModelMixin):
    __tablename__ = "hostels"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    hostel_type: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text)
    warden_name: Mapped[Optional[str]] = mapped_column(String(100))
    warden_phone: Mapped[Optional[str]] = mapped_column(String(20))
    warden_email: Mapped[Optional[str]] = mapped_column(String(255))
    total_rooms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_beds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    occupied_beds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    monthly_fee: Mapped[Optional[float]] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class HostelRoom(Base, BaseModelMixin):
    __tablename__ = "hostel_rooms"
    hostel_id: Mapped[int] = mapped_column(ForeignKey("hostels.id"), nullable=False)
    room_number: Mapped[str] = mapped_column(String(20), nullable=False)
    floor: Mapped[Optional[int]] = mapped_column(Integer)
    room_type: Mapped[str] = mapped_column(String(20), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    occupied: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    has_attached_bathroom: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_ac: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    monthly_rent: Mapped[Optional[float]] = mapped_column(Float)


class RoomAllocation(Base, BaseModelMixin):
    __tablename__ = "room_allocations"
    hostel_id: Mapped[int] = mapped_column(ForeignKey("hostels.id"), nullable=False)
    room_id: Mapped[int] = mapped_column(ForeignKey("hostel_rooms.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    bed_number: Mapped[Optional[str]] = mapped_column(String(20))
    allocation_date: Mapped[date] = mapped_column(Date, nullable=False)
    vacating_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    monthly_fee: Mapped[Optional[float]] = mapped_column(Float)


class TransportRoute(Base, BaseModelMixin):
    __tablename__ = "transport_routes"
    route_name: Mapped[str] = mapped_column(String(100), nullable=False)
    route_code: Mapped[str] = mapped_column(String(20), nullable=False)
    start_point: Mapped[str] = mapped_column(String(100), nullable=False)
    end_point: Mapped[str] = mapped_column(String(100), nullable=False)
    stops: Mapped[Optional[str]] = mapped_column(Text)
    distance_km: Mapped[Optional[float]] = mapped_column(Float)
    morning_departure: Mapped[Optional[str]] = mapped_column(String(10))
    evening_departure: Mapped[Optional[str]] = mapped_column(String(10))
    monthly_fee: Mapped[Optional[float]] = mapped_column(Float)
    max_capacity: Mapped[Optional[int]] = mapped_column(Integer)
    vehicle_id: Mapped[Optional[int]] = mapped_column(ForeignKey("vehicles.id"))
    status: Mapped[str] = mapped_column(String(20), nullable=False)


class Vehicle(Base, BaseModelMixin):
    __tablename__ = "vehicles"
    vehicle_number: Mapped[str] = mapped_column(String(20), nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(20), nullable=False)
    make: Mapped[Optional[str]] = mapped_column(String(50))
    model: Mapped[Optional[str]] = mapped_column(String(50))
    year: Mapped[Optional[int]] = mapped_column(Integer)
    capacity: Mapped[Optional[int]] = mapped_column(Integer)
    driver_name: Mapped[Optional[str]] = mapped_column(String(100))
    driver_phone: Mapped[Optional[str]] = mapped_column(String(20))
    license: Mapped[Optional[str]] = mapped_column(String(100))
    conductor_name: Mapped[Optional[str]] = mapped_column(String(100))
    conductor_phone: Mapped[Optional[str]] = mapped_column(String(20))
    insurance_expiry: Mapped[Optional[date]] = mapped_column(Date)
    fitness_expiry: Mapped[Optional[date]] = mapped_column(Date)
    gps_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)


class TransportAssignment(Base, BaseModelMixin):
    __tablename__ = "transport_assignments"
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    route_id: Mapped[int] = mapped_column(ForeignKey("transport_routes.id"), nullable=False)
    pickup_stop: Mapped[Optional[str]] = mapped_column(String(100))
    drop_stop: Mapped[Optional[str]] = mapped_column(String(100))
    assignment_date: Mapped[date] = mapped_column(Date, nullable=False)
    monthly_fee: Mapped[Optional[float]] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), nullable=False)


class Sport(Base, BaseModelMixin):
    __tablename__ = "sports"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    coach_name: Mapped[Optional[str]] = mapped_column(String(100))
    coach_phone: Mapped[Optional[str]] = mapped_column(String(20))
    venue: Mapped[Optional[str]] = mapped_column(String(100))
    practice_schedule: Mapped[Optional[str]] = mapped_column(Text)
    max_participants: Mapped[Optional[int]] = mapped_column(Integer)
    registration_fee: Mapped[Optional[float]] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), nullable=False)


class SportParticipation(Base, BaseModelMixin):
    __tablename__ = "sport_participation"
    sport_id: Mapped[int] = mapped_column(ForeignKey("sports.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    registration_date: Mapped[date] = mapped_column(Date, nullable=False)
    position: Mapped[Optional[str]] = mapped_column(String(50))
    jersey_number: Mapped[Optional[str]] = mapped_column(String(20))
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
    building: Mapped[Optional[str]] = mapped_column(String(100))
    floor: Mapped[Optional[int]] = mapped_column(Integer)
    capacity: Mapped[Optional[int]] = mapped_column(Integer)
    room_type: Mapped[Optional[str]] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Notification(Base, BaseModelMixin):
    __tablename__ = "notifications"
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    recipient_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    recipient_role: Mapped[Optional[str]] = mapped_column(String(20))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class UploadedFile(Base, BaseModelMixin):
    __tablename__ = "uploaded_files"
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[Optional[str]] = mapped_column(String(50))
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(50))


class Payment(Base, BaseModelMixin):
    __tablename__ = "payments"
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    transaction_id: Mapped[Optional[str]] = mapped_column(String(100))
    receipt_number: Mapped[Optional[str]] = mapped_column(String(50))


class Guardian(Base, BaseModelMixin):
    __tablename__ = "guardians"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    relationship: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    occupation: Mapped[Optional[str]] = mapped_column(String(100))
    address: Mapped[Optional[str]] = mapped_column(Text)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Setting(Base, BaseModelMixin):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(50))
    description: Mapped[Optional[str]] = mapped_column(Text)


class Plugin(Base, BaseModelMixin):
    __tablename__ = "plugins"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    config: Mapped[Optional[str]] = mapped_column(Text)


class Report(Base, BaseModelMixin):
    __tablename__ = "reports"
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    generated_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    format: Mapped[str] = mapped_column(String(20), nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    parameters: Mapped[Optional[str]] = mapped_column(Text)


class AuditLog(Base, BaseModelMixin):
    __tablename__ = "audit_logs"
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(50), nullable=False)
    old_values: Mapped[Optional[str]] = mapped_column(Text)
    new_values: Mapped[Optional[str]] = mapped_column(Text)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))
