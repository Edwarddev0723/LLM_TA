"""
Embedding model for RAG vector storage.
"""
from datetime import datetime
from sqlalchemy import Column, String, LargeBinary, DateTime

from backend.models.database import Base


class Embedding(Base):
    """向量索引表 (用於 RAG)"""
    __tablename__ = "embeddings"

    id = Column(String, primary_key=True)
    content_id = Column(String, nullable=False)
    content_type = Column(String, nullable=False)  # QUESTION, SOLUTION, MISCONCEPTION, CONCEPT
    embedding = Column(LargeBinary, nullable=False)  # 儲存向量
    created_at = Column(DateTime, default=datetime.utcnow)
