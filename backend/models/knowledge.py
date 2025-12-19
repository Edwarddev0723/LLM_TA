"""
Knowledge graph models for the AI Math Tutor system.
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from backend.models.database import Base


class KnowledgeNode(Base):
    """知識圖譜節點表"""
    __tablename__ = "knowledge_nodes"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    difficulty = Column(Integer, nullable=False)  # 1=EASY, 2=MEDIUM, 3=HARD
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    questions = relationship(
        "Question",
        secondary="question_knowledge_nodes",
        back_populates="knowledge_nodes"
    )
    relations_from = relationship(
        "KnowledgeRelation",
        foreign_keys="KnowledgeRelation.from_id",
        back_populates="from_node"
    )
    relations_to = relationship(
        "KnowledgeRelation",
        foreign_keys="KnowledgeRelation.to_id",
        back_populates="to_node"
    )


class KnowledgeRelation(Base):
    """知識圖譜關聯表"""
    __tablename__ = "knowledge_relations"

    from_id = Column(String, ForeignKey("knowledge_nodes.id"), primary_key=True)
    to_id = Column(String, ForeignKey("knowledge_nodes.id"), primary_key=True)
    relation_type = Column(String, primary_key=True, nullable=False)
    weight = Column(Float, default=1.0)

    # Relationships
    from_node = relationship(
        "KnowledgeNode",
        foreign_keys=[from_id],
        back_populates="relations_from"
    )
    to_node = relationship(
        "KnowledgeNode",
        foreign_keys=[to_id],
        back_populates="relations_to"
    )
