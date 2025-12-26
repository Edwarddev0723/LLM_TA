"""
User model for the AI Math Tutor system.
Supports multiple roles: admin, teacher, student, parent.
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.orm import relationship

from backend.models.database import Base


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    PARENT = "parent"


class VerificationStatus(str, Enum):
    """Verification status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base):
    """用戶資料表 - 支援多角色"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.STUDENT)
    full_name = Column(String(255), nullable=False)
    
    # Optional profile fields
    grade = Column(String(50), nullable=True)
    class_name = Column(String(100), nullable=True)  # 'class' is reserved
    phone = Column(String(20), nullable=True)
    student_name = Column(String(255), nullable=True)  # For parent linking
    relationship_type = Column(String(50), nullable=True)  # For parent-student relationship
    
    # Teacher verification
    id_document_path = Column(String(500), nullable=True)
    verification_status = Column(
        SQLEnum(VerificationStatus), 
        default=VerificationStatus.APPROVED
    )
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    classes_taught = relationship("Class", back_populates="teacher", foreign_keys="Class.teacher_id")
    class_enrollments = relationship("ClassStudent", back_populates="student")
    mistake_reasons = relationship("MistakeReason", back_populates="student")
    teaching_sessions = relationship("TeachingSession", back_populates="student")


class Class(Base):
    """班級資料表"""
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    teacher = relationship("User", back_populates="classes_taught", foreign_keys=[teacher_id])
    students = relationship("ClassStudent", back_populates="class_")


class ClassStudent(Base):
    """班級學生關聯表"""
    __tablename__ = "class_students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    class_ = relationship("Class", back_populates="students")
    student = relationship("User", back_populates="class_enrollments")


class ParentStudent(Base):
    """家長-學生關聯表"""
    __tablename__ = "parent_students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
