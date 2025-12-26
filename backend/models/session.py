"""
Session and conversation models for the AI Math Tutor system.
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from backend.models.database import Base


class Session(Base):
    """學習會話表"""
    __tablename__ = "sessions"

    id = Column(String, primary_key=True)
    student_id = Column(String, ForeignKey("students.id"))
    question_id = Column(String, ForeignKey("questions.id"))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    final_state = Column(String)  # FSM state
    concept_coverage = Column(Float)

    # Relationships
    student = relationship("Student", back_populates="sessions")
    question = relationship("Question", back_populates="sessions")
    conversation_turns = relationship("ConversationTurn", back_populates="session")
    learning_metrics = relationship("LearningMetrics", back_populates="session", uselist=False)
    pauses = relationship("Pause", back_populates="session")
    hint_usages = relationship("HintUsage", back_populates="session")
    error_records = relationship("ErrorRecord", back_populates="session")


class ConversationTurn(Base):
    """對話紀錄表"""
    __tablename__ = "conversation_turns"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    turn_number = Column(Integer, nullable=False)
    speaker = Column(String, nullable=False)  # STUDENT or TUTOR
    content = Column(Text, nullable=False)
    fsm_state = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)

    # Relationships
    session = relationship("Session", back_populates="conversation_turns")
