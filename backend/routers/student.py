"""
Student router for the AI Math Tutor system.
Handles student-specific features like mistakes, teaching sessions, etc.
"""
import json
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func, distinct
from pydantic import BaseModel

from backend.models import (
    get_db, User, QuestionV2, MistakeReason, TeachingSession, 
    Unit, Subject
)

router = APIRouter(prefix="/student", tags=["Student"])


# ===== Pydantic Models =====

class SaveMistakeReasonRequest(BaseModel):
    question_id: int
    session_id: Optional[int] = None
    reason_type: str
    reason_description: Optional[str] = None


class SaveTeachingSessionRequest(BaseModel):
    question_id: int
    session_type: Optional[str] = "teaching"
    transcript: Optional[str] = None
    whiteboard_data: Optional[dict] = None
    duration_seconds: Optional[int] = 0
    audio_url: Optional[str] = None


# ===== Helper Functions =====

def get_current_user_id(user_id: Optional[str] = Header(None, alias="user-id")) -> Optional[int]:
    """Get current user ID from header."""
    if user_id:
        try:
            return int(user_id)
        except ValueError:
            return None
    return None


# ===== Routes =====

@router.post("/mistake-reasons")
async def save_mistake_reason(
    request: SaveMistakeReasonRequest,
    user_id: Optional[int] = Depends(get_current_user_id),
    db: DBSession = Depends(get_db)
):
    """Save a mistake reason for a question."""
    if not user_id:
        raise HTTPException(status_code=401, detail="未授權訪問")
    
    if not request.reason_type:
        raise HTTPException(status_code=400, detail="缺少必要參數")
    
    new_reason = MistakeReason(
        student_id=user_id,
        question_id=request.question_id,
        session_id=request.session_id,
        reason_type=request.reason_type,
        reason_description=request.reason_description
    )
    
    db.add(new_reason)
    db.commit()
    db.refresh(new_reason)
    
    return {
        "success": True,
        "id": new_reason.id,
        "message": "錯題原因已保存"
    }


@router.get("/mistake-reasons/{question_id}")
async def get_mistake_reasons(
    question_id: int,
    user_id: Optional[int] = Depends(get_current_user_id),
    db: DBSession = Depends(get_db)
):
    """Get mistake reasons for a specific question."""
    if not user_id:
        raise HTTPException(status_code=401, detail="未授權訪問")
    
    reasons = db.query(MistakeReason).filter(
        MistakeReason.student_id == user_id,
        MistakeReason.question_id == question_id
    ).order_by(MistakeReason.recorded_at.desc()).all()
    
    return {
        "reasons": [
            {
                "id": r.id,
                "reason_type": r.reason_type,
                "reason_description": r.reason_description,
                "recorded_at": r.recorded_at
            }
            for r in reasons
        ]
    }


@router.get("/mistakes")
async def get_student_mistakes(
    user_id: Optional[int] = Depends(get_current_user_id),
    db: DBSession = Depends(get_db)
):
    """Get all mistakes for a student."""
    if not user_id:
        raise HTTPException(status_code=401, detail="未授權訪問")
    
    # Get distinct questions with mistake reasons
    mistakes = db.query(
        QuestionV2,
        Unit,
        Subject,
        MistakeReason.reason_type,
        MistakeReason.reason_description,
        func.max(MistakeReason.recorded_at).label("last_recorded_at")
    ).join(
        MistakeReason, QuestionV2.id == MistakeReason.question_id
    ).join(
        Unit, QuestionV2.unit_id == Unit.id
    ).join(
        Subject, Unit.subject_id == Subject.id
    ).filter(
        MistakeReason.student_id == user_id
    ).group_by(
        MistakeReason.question_id
    ).order_by(
        func.max(MistakeReason.recorded_at).desc()
    ).all()
    
    result = []
    for q, u, s, reason_type, reason_desc, last_recorded in mistakes:
        result.append({
            "id": q.id,
            "question_text": q.question_text,
            "answer_text": q.answer_text,
            "solution_text": q.solution_text,
            "difficulty": q.difficulty.value if q.difficulty else "medium",
            "unit_name": u.unit_name,
            "subject_name": s.subject_name,
            "reason_type": reason_type,
            "reason_description": reason_desc,
            "last_recorded_at": last_recorded
        })
    
    return {"mistakes": result}


@router.get("/stats")
async def get_student_stats(
    user_id: Optional[int] = Depends(get_current_user_id),
    db: DBSession = Depends(get_db)
):
    """Get statistics for a student."""
    if not user_id:
        raise HTTPException(status_code=401, detail="未授權訪問")
    
    # Total mistakes
    total_mistakes = db.query(
        func.count(distinct(MistakeReason.question_id))
    ).filter(
        MistakeReason.student_id == user_id
    ).scalar() or 0
    
    # Weekly mistakes
    week_ago = datetime.utcnow() - timedelta(days=7)
    weekly_mistakes = db.query(
        func.count(distinct(MistakeReason.question_id))
    ).filter(
        MistakeReason.student_id == user_id,
        MistakeReason.recorded_at > week_ago
    ).scalar() or 0
    
    # Reason distribution
    reason_dist = db.query(
        MistakeReason.reason_type,
        func.count(MistakeReason.id).label("count")
    ).filter(
        MistakeReason.student_id == user_id
    ).group_by(
        MistakeReason.reason_type
    ).all()
    
    return {
        "totalMistakes": total_mistakes,
        "weeklyMistakes": weekly_mistakes,
        "reasonDistribution": [
            {"reason_type": r, "count": c}
            for r, c in reason_dist
        ]
    }


@router.post("/teaching-sessions")
async def save_teaching_session(
    request: SaveTeachingSessionRequest,
    user_id: Optional[int] = Depends(get_current_user_id),
    db: DBSession = Depends(get_db)
):
    """Save a teaching session."""
    if not user_id:
        raise HTTPException(status_code=401, detail="未授權訪問")
    
    whiteboard_json = None
    if request.whiteboard_data:
        whiteboard_json = json.dumps(request.whiteboard_data)
    
    new_session = TeachingSession(
        student_id=user_id,
        question_id=request.question_id,
        session_type=request.session_type or "teaching",
        transcript=request.transcript,
        whiteboard_data=whiteboard_json,
        duration_seconds=request.duration_seconds or 0,
        audio_url=request.audio_url
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return {
        "success": True,
        "sessionId": new_session.id,
        "message": "教學會話已保存"
    }


@router.get("/teaching-sessions/{session_id}")
async def get_teaching_session(
    session_id: int,
    user_id: Optional[int] = Depends(get_current_user_id),
    db: DBSession = Depends(get_db)
):
    """Get a specific teaching session."""
    if not user_id:
        raise HTTPException(status_code=401, detail="未授權訪問")
    
    session = db.query(TeachingSession).filter(
        TeachingSession.id == session_id,
        TeachingSession.student_id == user_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="會話不存在")
    
    whiteboard_data = None
    if session.whiteboard_data:
        try:
            whiteboard_data = json.loads(session.whiteboard_data)
        except json.JSONDecodeError:
            whiteboard_data = None
    
    return {
        "session": {
            "id": session.id,
            "question_id": session.question_id,
            "session_type": session.session_type,
            "transcript": session.transcript,
            "whiteboard_data": whiteboard_data,
            "audio_url": session.audio_url,
            "duration_seconds": session.duration_seconds,
            "started_at": session.started_at,
            "ended_at": session.ended_at
        }
    }
