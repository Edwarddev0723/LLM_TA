"""
AI 數學語音助教系統 - FastAPI Backend
Unified backend integrating AI Tutor core + User/Class management
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from backend.models.database import Base, engine
# Import all models to ensure they are registered with Base
from backend.models import (
    # Legacy AI Tutor models
    Student, KnowledgeNode, KnowledgeRelation,
    Question, Misconception, Hint,
    Session, ConversationTurn,
    LearningMetrics, Pause, HintUsage,
    ErrorRecord, Embedding,
    # New models (User management, Classes, etc.)
    User, UserRole, VerificationStatus, Class, ClassStudent, ParentStudent,
    Subject, Unit, QuestionV2, Difficulty, MistakeReason, TeachingSession,
)
from backend.routers import (
    # Legacy AI Tutor routers
    questions_router,
    sessions_router,
    errors_router,
    dashboard_router,
    asr_router,
    # New routers
    auth_router,
    teacher_router,
    subjects_router,
    student_router,
)
from backend.routers.student_metrics import router as student_metrics_router
from backend.routers.practice import router as practice_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - create database tables on startup."""
    import threading
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Start ASR model warmup in background thread
    def warmup_asr():
        try:
            from backend.routers.asr import get_asr_module
            logger.info("Starting ASR model warmup in background...")
            get_asr_module()
            logger.info("ASR model warmup completed")
        except Exception as e:
            logger.warning(f"ASR warmup failed (will retry on first request): {e}")
    
    # Run warmup in background thread to not block startup
    warmup_thread = threading.Thread(target=warmup_asr, daemon=True)
    warmup_thread.start()
    
    yield
    # Cleanup (if needed)


app = FastAPI(
    title="AI 數學語音助教",
    description="國中數學 AI 語音助教系統 API",
    version="0.1.0",
    lifespan=lifespan
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server (frontend & apps/teacher-web)
        "http://localhost:3000",  # Alternative port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# Legacy AI Tutor routers (already have /api prefix in their definition)
app.include_router(questions_router)
app.include_router(sessions_router)
app.include_router(errors_router)
app.include_router(dashboard_router)
app.include_router(asr_router)

# New routers (User management, Teacher, Student) - add /api prefix
app.include_router(auth_router, prefix="/api")
app.include_router(teacher_router, prefix="/api")
app.include_router(subjects_router, prefix="/api")
app.include_router(student_router, prefix="/api")
app.include_router(student_metrics_router)  # Already has /api prefix
app.include_router(practice_router)  # Already has /api prefix

# Serve uploaded files (teacher ID documents, etc.)
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/")
async def root():
    return {"message": "AI 數學語音助教系統 API"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
