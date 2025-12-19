"""
AI 數學語音助教系統 - FastAPI Backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import (
    questions_router,
    sessions_router,
    errors_router,
    dashboard_router,
)

app = FastAPI(
    title="AI 數學語音助教",
    description="國中數學 AI 語音助教系統 API",
    version="0.1.0"
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(questions_router)
app.include_router(sessions_router)
app.include_router(errors_router)
app.include_router(dashboard_router)


@app.get("/")
async def root():
    return {"message": "AI 數學語音助教系統 API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
