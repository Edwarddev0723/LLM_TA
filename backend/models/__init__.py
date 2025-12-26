# Database Models
from backend.models.database import Base, engine, SessionLocal, get_db

# Legacy models (AI Tutor core)
from backend.models.student import Student
from backend.models.knowledge import KnowledgeNode, KnowledgeRelation
from backend.models.question import Question, Misconception, Hint, question_knowledge_nodes
from backend.models.session import Session, ConversationTurn
from backend.models.metrics import LearningMetrics, Pause, HintUsage
from backend.models.error_book import ErrorRecord
from backend.models.embedding import Embedding

# New models (User management, Classes, etc.)
from backend.models.user import User, UserRole, VerificationStatus, Class, ClassStudent, ParentStudent
from backend.models.subject import Subject, Unit
from backend.models.question_v2 import QuestionV2, Difficulty, MistakeReason, TeachingSession

__all__ = [
    # Database
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    # Legacy models
    "Student",
    "KnowledgeNode",
    "KnowledgeRelation",
    "Question",
    "Misconception",
    "Hint",
    "question_knowledge_nodes",
    "Session",
    "ConversationTurn",
    "LearningMetrics",
    "Pause",
    "HintUsage",
    "ErrorRecord",
    "Embedding",
    # New models
    "User",
    "UserRole",
    "VerificationStatus",
    "Class",
    "ClassStudent",
    "ParentStudent",
    "Subject",
    "Unit",
    "QuestionV2",
    "Difficulty",
    "MistakeReason",
    "TeachingSession",
]
