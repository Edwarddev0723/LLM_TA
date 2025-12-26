"""
Error book model for the AI Math Tutor system.
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship

from backend.models.database import Base


class ErrorRecord(Base):
    """錯題本表"""
    __tablename__ = "error_records"

    id = Column(String, primary_key=True)
    student_id = Column(String, ForeignKey("students.id"))
    question_id = Column(String, ForeignKey("questions.id"))
    session_id = Column(String, ForeignKey("sessions.id"), nullable=True)
    student_answer = Column(Text, nullable=False)
    correct_answer = Column(Text, nullable=False)
    error_type = Column(String, nullable=False)  # CALCULATION, CONCEPT, CARELESS
    error_tags = Column(Text)  # JSON array stored as text
    concept = Column(String, nullable=True)  # Related concept/knowledge node
    unit = Column(String, nullable=True)  # Related unit
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    repaired = Column(Boolean, default=False)
    is_repaired = Column(Boolean, default=False)  # Alias for repaired
    repaired_at = Column(DateTime)
    recurrence_count = Column(Integer, default=0)  # Number of times this error recurred

    # Relationships
    student = relationship("Student", back_populates="error_records")
    question = relationship("Question", back_populates="error_records")
    session = relationship("Session", back_populates="error_records")
