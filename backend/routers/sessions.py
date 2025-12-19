"""
Session-related API routes for the AI Math Tutor system.

Implements:
- POST /api/sessions - Start new session
- POST /api/sessions/{id}/input - Process student input
- POST /api/sessions/{id}/end - End session

Requirements: 6.1
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.services.dialog_engine import (
    DialogEngine,
    StudentInput,
    AudioFeatures,
    ResponseType,
)
from backend.services.fsm_controller import FSMState
from backend.services.question_bank import QuestionBankManager


router = APIRouter(prefix="/api/sessions", tags=["sessions"])

# Global dialog engine instance (in production, use dependency injection)
_dialog_engine: Optional[DialogEngine] = None


def get_dialog_engine(db: Session = Depends(get_db)) -> DialogEngine:
    """Get or create the dialog engine instance."""
    global _dialog_engine
    if _dialog_engine is None:
        _dialog_engine = DialogEngine(db=db)
    return _dialog_engine


# Pydantic models for request/response
class StartSessionRequest(BaseModel):
    """Request model for starting a session."""
    question_id: str
    student_id: str


class StartSessionResponse(BaseModel):
    """Response model for session start."""
    session_id: str
    question_id: str
    student_id: str
    question_content: str
    fsm_state: str
    message: str


class StudentInputRequest(BaseModel):
    """Request model for student input."""
    text: str
    audio_duration: Optional[float] = None
    word_count: Optional[int] = None
    pause_count: Optional[int] = None
    total_pause_duration: Optional[float] = None


class TutorResponseModel(BaseModel):
    """Response model for tutor response."""
    text: str
    response_type: str
    hint_level: Optional[int] = None
    related_concepts: List[str] = []
    suggested_next_step: Optional[str] = None
    fsm_state: str


class EndSessionResponse(BaseModel):
    """Response model for session end."""
    session_id: str
    duration: float
    concepts_covered: List[str]
    concept_coverage: float
    hints_used: List[dict]
    total_turns: int
    final_state: str


class SessionStateResponse(BaseModel):
    """Response model for session state."""
    session_id: str
    question_id: str
    student_id: str
    fsm_state: str
    concept_coverage: float
    hints_used: int
    turn_count: int
    is_active: bool


@router.post("", response_model=StartSessionResponse)
async def start_session(
    request: StartSessionRequest,
    db: Session = Depends(get_db)
):
    """
    Start a new tutoring session.
    
    Requirements: 6.1
    - WHEN 學生開始口語講題 THEN THE FSM_Controller SHALL 初始化為 LISTENING 狀態並開始記錄
    """
    # Get question details
    question_manager = QuestionBankManager(db)
    question = question_manager.get_question(request.question_id)
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Get required concepts from knowledge nodes
    required_concepts = [node.id for node in question.knowledge_nodes]
    
    # Create dialog engine and start session
    dialog_engine = get_dialog_engine(db)
    session = dialog_engine.start_session(
        question_id=request.question_id,
        student_id=request.student_id,
        question_content=question.content,
        standard_solution=question.standard_solution,
        required_concepts=required_concepts
    )
    
    return StartSessionResponse(
        session_id=session.id,
        question_id=session.question_id,
        student_id=session.student_id,
        question_content=question.content,
        fsm_state=FSMState.LISTENING.value,
        message="會話已開始，請開始講解你的解題思路。"
    )


@router.post("/{session_id}/input", response_model=TutorResponseModel)
async def process_input(
    session_id: str,
    request: StudentInputRequest,
    db: Session = Depends(get_db)
):
    """
    Process student input and get tutor response.
    
    Requirements: 6.1
    - Processes student input through FSM and generates appropriate response
    """
    dialog_engine = get_dialog_engine(db)
    
    # Check if session exists
    session_state = dialog_engine.get_session_state(session_id)
    if not session_state:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session_state.is_active:
        raise HTTPException(status_code=400, detail="Session has ended")
    
    # Create audio features if provided
    audio_features = None
    if request.audio_duration is not None:
        audio_features = AudioFeatures(
            duration=request.audio_duration,
            word_count=request.word_count or 0,
            pause_count=request.pause_count or 0,
            total_pause_duration=request.total_pause_duration or 0.0
        )
    
    # Create student input
    student_input = StudentInput(
        session_id=session_id,
        text=request.text,
        audio_features=audio_features
    )
    
    # Process input and get response
    response = dialog_engine.process_student_input(student_input)
    
    return TutorResponseModel(
        text=response.text,
        response_type=response.response_type.value,
        hint_level=response.hint_level.value if response.hint_level else None,
        related_concepts=response.related_concepts,
        suggested_next_step=response.suggested_next_step,
        fsm_state=response.fsm_state.value if response.fsm_state else FSMState.LISTENING.value
    )


@router.post("/{session_id}/end", response_model=EndSessionResponse)
async def end_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    End a tutoring session and get summary.
    
    Requirements: 6.1
    """
    dialog_engine = get_dialog_engine(db)
    
    # Check if session exists
    session_state = dialog_engine.get_session_state(session_id)
    if not session_state:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # End session and get summary
    summary = dialog_engine.end_session(session_id)
    
    return EndSessionResponse(
        session_id=summary.session_id,
        duration=summary.duration,
        concepts_covered=summary.concepts_covered,
        concept_coverage=summary.concept_coverage,
        hints_used=summary.hints_used,
        total_turns=summary.total_turns,
        final_state=summary.final_state.value
    )


@router.get("/{session_id}", response_model=SessionStateResponse)
async def get_session_state(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get current session state.
    """
    dialog_engine = get_dialog_engine(db)
    
    session_state = dialog_engine.get_session_state(session_id)
    if not session_state:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionStateResponse(
        session_id=session_state.session_id,
        question_id=session_state.question_id,
        student_id=session_state.student_id,
        fsm_state=session_state.fsm_state.value,
        concept_coverage=session_state.concept_coverage,
        hints_used=session_state.hints_used,
        turn_count=session_state.turn_count,
        is_active=session_state.is_active
    )
