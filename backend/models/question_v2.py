"""
Question model V2 for the AI Math Tutor system.
Compatible with apps/backend schema.
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship

from backend.models.database import Base


class Difficulty(str, Enum):
    """Difficulty level enumeration."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionV2(Base):
    """題目資料表 V2 - 與 apps/backend 相容"""
    __tablename__ = "questions_v2"

    id = Column(Integer, primary_key=True, autoincrement=True)
    unit_id = Column(Integer, ForeignKey("units.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    question_image = Column(String(255), nullable=True)
    difficulty = Column(SQLEnum(Difficulty), default=Difficulty.MEDIUM, index=True)
    answer_text = Column(Text, nullable=True)
    solution_text = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    unit = relationship("Unit", back_populates="questions")
    mistake_reasons = relationship("MistakeReason", back_populates="question")
    teaching_sessions = relationship("TeachingSession", back_populates="question")


class MistakeReason(Base):
    """錯題原因表"""
    __tablename__ = "mistake_reasons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions_v2.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(Integer, nullable=True)  # Optional link to teaching session
    reason_type = Column(String(50), nullable=True)
    reason_description = Column(Text, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("User", back_populates="mistake_reasons")
    question = relationship("QuestionV2", back_populates="mistake_reasons")


class TeachingSession(Base):
    """講題會話表"""
    __tablename__ = "teaching_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions_v2.id", ondelete="SET NULL"), nullable=True)
    session_type = Column(String(20), default="teaching")  # teaching, review
    whiteboard_data = Column(Text, nullable=True)  # JSON string
    transcript = Column(Text, nullable=True)
    audio_url = Column(String(255), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("User", back_populates="teaching_sessions")
    question = relationship("QuestionV2", back_populates="teaching_sessions")
