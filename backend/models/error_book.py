"""
Error book model for the AI Math Tutor system.
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from backend.models.database import Base


class ErrorRecord(Base):
    """錯題本表"""
    __tablename__ = "error_records"

    id = Column(String, primary_key=True)
    student_id = Column(String, ForeignKey("students.id"))
    question_id = Column(String, ForeignKey("questions.id"))
    student_answer = Column(Text, nullable=False)
    correct_answer = Column(Text, nullable=False)
    error_type = Column(String, nullable=False)  # CALCULATION, CONCEPT, CARELESS
    error_tags = Column(Text)  # JSON array stored as text
    timestamp = Column(DateTime, nullable=False)
    repaired = Column(Boolean, default=False)
    repaired_at = Column(DateTime)

    # Relationships
    student = relationship("Student", back_populates="error_records")
    question = relationship("Question", back_populates="error_records")
