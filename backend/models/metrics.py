"""
Learning metrics models for the AI Math Tutor system.
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from backend.models.database import Base


class LearningMetrics(Base):
    """學習指標表"""
    __tablename__ = "learning_metrics"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    wpm = Column(Float)  # Words per minute
    pause_rate = Column(Float)  # 停頓比例
    hint_dependency = Column(Float)  # 提示依賴度
    concept_coverage = Column(Float)  # 概念覆蓋率
    focus_duration = Column(Float)  # 專注時長
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("Session", back_populates="learning_metrics")


class Pause(Base):
    """停頓紀錄表"""
    __tablename__ = "pauses"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)

    # Relationships
    session = relationship("Session", back_populates="pauses")


class HintUsage(Base):
    """提示使用紀錄表"""
    __tablename__ = "hint_usages"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    hint_level = Column(Integer, nullable=False)  # 1, 2, or 3
    concept = Column(String)
    timestamp = Column(DateTime, nullable=False)

    # Relationships
    session = relationship("Session", back_populates="hint_usages")
