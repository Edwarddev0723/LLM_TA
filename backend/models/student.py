"""
Student model for the AI Math Tutor system.
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship

from backend.models.database import Base


class Student(Base):
    """學生資料表"""
    __tablename__ = "students"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    grade = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    sessions = relationship("Session", back_populates="student")
    error_records = relationship("ErrorRecord", back_populates="student")
