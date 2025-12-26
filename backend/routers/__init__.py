# API Routers
# Legacy AI Tutor routers
from backend.routers.questions import router as questions_router
from backend.routers.sessions import router as sessions_router
from backend.routers.errors import router as errors_router
from backend.routers.dashboard import router as dashboard_router
from backend.routers.asr import router as asr_router

# New routers (User management, Teacher, Student)
from backend.routers.auth import router as auth_router
from backend.routers.teacher import router as teacher_router
from backend.routers.subjects import router as subjects_router
from backend.routers.student import router as student_router

__all__ = [
    # Legacy routers
    "questions_router",
    "sessions_router",
    "errors_router",
    "dashboard_router",
    "asr_router",
    # New routers
    "auth_router",
    "teacher_router",
    "subjects_router",
    "student_router",
]
