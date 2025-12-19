"""
Question-related API routes for the AI Math Tutor system.

Implements:
- GET /api/questions - Filter questions
- GET /api/questions/{id} - Get question details
- POST /api/questions/validate - Validate answer

Requirements: 1.1, 1.2, 3.1
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.services.question_bank import (
    QuestionBankManager,
    QuestionCriteria,
)


router = APIRouter(prefix="/api/questions", tags=["questions"])


# Pydantic models for request/response
class QuestionResponse(BaseModel):
    """Response model for a question."""
    id: str
    content: str
    type: str
    subject: str
    unit: str
    difficulty: int
    standard_solution: Optional[str] = None
    knowledge_nodes: List[str] = []
    hints: List[dict] = []
    misconceptions: List[dict] = []

    model_config = {"from_attributes": True}


class QuestionListResponse(BaseModel):
    """Response model for question list."""
    questions: List[QuestionResponse]
    total: int


class ValidateAnswerRequest(BaseModel):
    """Request model for answer validation."""
    question_id: str
    answer: str


class ValidateAnswerResponse(BaseModel):
    """Response model for answer validation."""
    is_correct: bool
    correct_answer: str
    student_answer: str
    feedback: Optional[str] = None
    response_time_ms: Optional[int] = None


@router.get("", response_model=QuestionListResponse)
async def filter_questions(
    subject: Optional[str] = Query(None, description="Filter by subject"),
    unit: Optional[str] = Query(None, description="Filter by unit"),
    difficulty: Optional[int] = Query(None, ge=1, le=3, description="Filter by difficulty (1-3)"),
    question_type: Optional[str] = Query(None, description="Filter by question type"),
    knowledge_nodes: Optional[str] = Query(None, description="Comma-separated knowledge node IDs"),
    exclude_ids: Optional[str] = Query(None, description="Comma-separated question IDs to exclude"),
    db: Session = Depends(get_db)
):
    """
    Filter questions based on criteria.
    
    Requirements: 1.1, 1.2
    - WHEN 學生進入練習模組 THEN THE AI_Tutor SHALL 顯示科目、單元、難度的篩選介面
    - WHEN 學生選擇篩選條件並確認 THEN THE Question_Bank SHALL 返回符合條件的題目列表
    """
    manager = QuestionBankManager(db)
    
    # Parse comma-separated values
    node_list = knowledge_nodes.split(",") if knowledge_nodes else None
    exclude_list = exclude_ids.split(",") if exclude_ids else None
    
    criteria = QuestionCriteria(
        subject=subject,
        unit=unit,
        difficulty=difficulty,
        knowledge_nodes=node_list,
        exclude_ids=exclude_list,
        question_type=question_type
    )
    
    questions = manager.filter_questions(criteria)
    
    # Convert to response format
    question_responses = []
    for q in questions:
        question_responses.append(QuestionResponse(
            id=q.id,
            content=q.content,
            type=q.type,
            subject=q.subject,
            unit=q.unit,
            difficulty=q.difficulty,
            standard_solution=q.standard_solution,
            knowledge_nodes=[node.id for node in q.knowledge_nodes],
            hints=[{"level": h.level, "content": h.content} for h in q.hints],
            misconceptions=[
                {"id": m.id, "description": m.description, "error_type": m.error_type}
                for m in q.misconceptions
            ]
        ))
    
    return QuestionListResponse(
        questions=question_responses,
        total=len(question_responses)
    )


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: str,
    db: Session = Depends(get_db)
):
    """
    Get question details by ID.
    
    Requirements: 1.2
    """
    manager = QuestionBankManager(db)
    question = manager.get_question(question_id)
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return QuestionResponse(
        id=question.id,
        content=question.content,
        type=question.type,
        subject=question.subject,
        unit=question.unit,
        difficulty=question.difficulty,
        standard_solution=question.standard_solution,
        knowledge_nodes=[node.id for node in question.knowledge_nodes],
        hints=[{"level": h.level, "content": h.content} for h in question.hints],
        misconceptions=[
            {"id": m.id, "description": m.description, "error_type": m.error_type}
            for m in question.misconceptions
        ]
    )


@router.post("/validate", response_model=ValidateAnswerResponse)
async def validate_answer(
    request: ValidateAnswerRequest,
    db: Session = Depends(get_db)
):
    """
    Validate a student's answer.
    
    Requirements: 3.1
    - WHEN 學生提交答案 THEN THE AI_Tutor SHALL 於 2 秒內判定正誤並顯示結果
    """
    import time
    start_time = time.time()
    
    manager = QuestionBankManager(db)
    validation = manager.validate_answer(request.question_id, request.answer)
    
    if not validation:
        raise HTTPException(status_code=404, detail="Question not found")
    
    response_time_ms = int((time.time() - start_time) * 1000)
    
    return ValidateAnswerResponse(
        is_correct=validation.is_correct,
        correct_answer=validation.correct_answer,
        student_answer=validation.student_answer,
        feedback=validation.feedback,
        response_time_ms=response_time_ms
    )
