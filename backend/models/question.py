"""
Question and related models for the AI Math Tutor system.
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Table
from sqlalchemy.orm import relationship

from backend.models.database import Base


# Association table for Question-KnowledgeNode many-to-many relationship
question_knowledge_nodes = Table(
    "question_knowledge_nodes",
    Base.metadata,
    Column("question_id", String, ForeignKey("questions.id"), primary_key=True),
    Column("node_id", String, ForeignKey("knowledge_nodes.id"), primary_key=True)
)


class Question(Base):
    """題目資料表"""
    __tablename__ = "questions"

    id = Column(String, primary_key=True)
    content = Column(Text, nullable=False)
    type = Column(String, nullable=False)  # MULTIPLE_CHOICE, FILL_BLANK, CALCULATION, PROOF
    subject = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    difficulty = Column(Integer, nullable=False)  # 1=EASY, 2=MEDIUM, 3=HARD
    standard_solution = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    knowledge_nodes = relationship(
        "KnowledgeNode",
        secondary=question_knowledge_nodes,
        back_populates="questions"
    )
    misconceptions = relationship("Misconception", back_populates="question")
    hints = relationship("Hint", back_populates="question")
    sessions = relationship("Session", back_populates="question")
    error_records = relationship("ErrorRecord", back_populates="question")


class Misconception(Base):
    """常見迷思概念表"""
    __tablename__ = "misconceptions"

    id = Column(String, primary_key=True)
    question_id = Column(String, ForeignKey("questions.id"))
    description = Column(Text, nullable=False)
    error_type = Column(String, nullable=False)  # CALCULATION, CONCEPT, CARELESS
    correction = Column(Text, nullable=False)

    # Relationships
    question = relationship("Question", back_populates="misconceptions")


class Hint(Base):
    """提示內容表"""
    __tablename__ = "hints"

    id = Column(String, primary_key=True)
    question_id = Column(String, ForeignKey("questions.id"))
    level = Column(Integer, nullable=False)  # 1, 2, or 3
    content = Column(Text, nullable=False)

    # Relationships
    question = relationship("Question", back_populates="hints")
