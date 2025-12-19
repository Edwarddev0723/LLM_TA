"""
Error Book API routes for the AI Math Tutor system.

Implements:
- GET /api/errors - Get error list
- POST /api/errors/{id}/repair - Mark as repaired

Requirements: 4.3, 8.3
"""
import json
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.services.error_book import (
    ErrorBookManager,
    ErrorCriteria,
)


router = APIRouter(prefix="/api/errors", tags=["errors"])


# Pydantic models for request/response
class ErrorRecordResponse(BaseModel):
    """Response model for an error record."""
    id: str
    student_id: str
    question_id: str
    student_answer: str
    correct_answer: str
    error_type: str
    error_tags: List[str]
    timestamp: datetime
    repaired: bool
    repaired_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ErrorListResponse(BaseModel):
    """Response model for error list."""
    errors: List[ErrorRecordResponse]
    total: int


class ErrorStatisticsResponse(BaseModel):
    """Response model for error statistics."""
    total_errors: int
    repaired_count: int
    errors_by_type: dict
    errors_by_unit: dict
    most_frequent_misconceptions: List[str]


class RepairResponse(BaseModel):
    """Response model for repair action."""
    id: str
    repaired: bool
    repaired_at: datetime
    message: str


@router.get("", response_model=ErrorListResponse)
async def get_errors(
    student_id: str = Query(..., description="Student ID (required)"),
    error_type: Optional[str] = Query(None, description="Filter by error type"),
    unit: Optional[str] = Query(None, description="Filter by unit"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter"),
    repaired: Optional[bool] = Query(None, description="Filter by repaired status"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    db: Session = Depends(get_db)
):
    """
    Get error records for a student with optional filtering.
    
    Requirements: 4.3
    - THE Error_Book SHALL 支援依標籤、日期、單元篩選錯題
    """
    manager = ErrorBookManager(db)
    
    # Parse tags
    tag_list = tags.split(",") if tags else None
    
    criteria = ErrorCriteria(
        error_type=error_type,
        tags=tag_list,
        unit=unit,
        date_from=date_from,
        date_to=date_to,
        repaired_status=repaired
    )
    
    errors = manager.get_errors(student_id, criteria)
    
    # Convert to response format
    error_responses = []
    for e in errors:
        # Parse error_tags from JSON string
        try:
            tags_list = json.loads(e.error_tags) if e.error_tags else []
        except json.JSONDecodeError:
            tags_list = []
        
        error_responses.append(ErrorRecordResponse(
            id=e.id,
            student_id=e.student_id,
            question_id=e.question_id,
            student_answer=e.student_answer,
            correct_answer=e.correct_answer,
            error_type=e.error_type,
            error_tags=tags_list,
            timestamp=e.timestamp,
            repaired=e.repaired,
            repaired_at=e.repaired_at
        ))
    
    return ErrorListResponse(
        errors=error_responses,
        total=len(error_responses)
    )


@router.get("/{error_id}", response_model=ErrorRecordResponse)
async def get_error(
    error_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific error record by ID.
    """
    manager = ErrorBookManager(db)
    error = manager.get_error_by_id(error_id)
    
    if not error:
        raise HTTPException(status_code=404, detail="Error record not found")
    
    # Parse error_tags from JSON string
    try:
        tags_list = json.loads(error.error_tags) if error.error_tags else []
    except json.JSONDecodeError:
        tags_list = []
    
    return ErrorRecordResponse(
        id=error.id,
        student_id=error.student_id,
        question_id=error.question_id,
        student_answer=error.student_answer,
        correct_answer=error.correct_answer,
        error_type=error.error_type,
        error_tags=tags_list,
        timestamp=error.timestamp,
        repaired=error.repaired,
        repaired_at=error.repaired_at
    )


@router.post("/{error_id}/repair", response_model=RepairResponse)
async def mark_as_repaired(
    error_id: str,
    db: Session = Depends(get_db)
):
    """
    Mark an error record as repaired.
    
    Requirements: 8.3
    - WHEN 學生通過變題測試 THEN THE Error_Book SHALL 將該錯題標記為「已修復」
    """
    manager = ErrorBookManager(db)
    
    error = manager.mark_as_repaired(error_id)
    
    if not error:
        raise HTTPException(status_code=404, detail="Error record not found")
    
    return RepairResponse(
        id=error.id,
        repaired=error.repaired,
        repaired_at=error.repaired_at,
        message="錯題已標記為已修復"
    )


@router.get("/statistics/{student_id}", response_model=ErrorStatisticsResponse)
async def get_error_statistics(
    student_id: str,
    db: Session = Depends(get_db)
):
    """
    Get error statistics for a student.
    """
    manager = ErrorBookManager(db)
    stats = manager.get_error_statistics(student_id)
    
    return ErrorStatisticsResponse(
        total_errors=stats.total_errors,
        repaired_count=stats.repaired_count,
        errors_by_type=stats.errors_by_type,
        errors_by_unit=stats.errors_by_unit,
        most_frequent_misconceptions=stats.most_frequent_misconceptions
    )
