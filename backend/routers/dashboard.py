"""
Dashboard API routes for the AI Math Tutor system.

Implements:
- GET /api/dashboard/metrics - Get learning metrics
- GET /api/dashboard/heatmap - Get weakness heatmap

Requirements: 10.1, 10.2
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.metrics import LearningMetrics
from backend.models.session import Session as SessionModel
from backend.models.error_book import ErrorRecord
from backend.models.knowledge import KnowledgeNode
from backend.models.question import Question, question_knowledge_nodes
from backend.services.metrics_calculator import MetricsCalculator
from backend.services.knowledge_graph import KnowledgeGraphManager
from backend.services.error_book import ErrorBookManager


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


# Pydantic models for request/response
class MetricsDataPoint(BaseModel):
    """A single metrics data point."""
    session_id: str
    timestamp: datetime
    wpm: float
    pause_rate: float
    hint_dependency: float
    concept_coverage: float
    focus_duration: float


class MetricsResponse(BaseModel):
    """Response model for learning metrics."""
    student_id: str
    metrics_history: List[MetricsDataPoint]
    average_wpm: float
    average_pause_rate: float
    average_hint_dependency: float
    average_concept_coverage: float
    total_sessions: int
    total_focus_duration: float


class KnowledgeNodeMastery(BaseModel):
    """Mastery level for a knowledge node."""
    node_id: str
    node_name: str
    subject: str
    unit: str
    mastery_level: str  # "red", "yellow", "green"
    mastery_score: float  # 0.0 to 1.0
    error_count: int
    total_attempts: int
    concept_coverage: float


class HeatmapResponse(BaseModel):
    """Response model for weakness heatmap."""
    student_id: str
    nodes: List[KnowledgeNodeMastery]
    weak_areas: List[str]  # Node IDs with low mastery
    strong_areas: List[str]  # Node IDs with high mastery


class SessionSummaryResponse(BaseModel):
    """Summary of a session for dashboard."""
    session_id: str
    question_id: str
    start_time: datetime
    end_time: Optional[datetime]
    concept_coverage: float
    final_state: Optional[str]


class DashboardOverviewResponse(BaseModel):
    """Overview response for dashboard."""
    student_id: str
    total_sessions: int
    completed_sessions: int
    average_coverage: float
    total_duration_minutes: float
    recent_sessions: List[SessionSummaryResponse]
    error_statistics: Dict[str, Any]


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    student_id: str = Query(..., description="Student ID (required)"),
    limit: int = Query(10, ge=1, le=100, description="Number of recent sessions"),
    db: Session = Depends(get_db)
):
    """
    Get learning metrics for a student.
    
    Requirements: 10.1
    - WHEN 教師/家長登入儀表板 THEN THE Dashboard SHALL 顯示 WPM 趨勢圖、停頓比例分佈、提示依賴度統計
    """
    calculator = MetricsCalculator(db)
    
    # Get metrics history
    metrics_list = calculator.get_student_metrics_history(student_id, limit)
    
    if not metrics_list:
        return MetricsResponse(
            student_id=student_id,
            metrics_history=[],
            average_wpm=0.0,
            average_pause_rate=0.0,
            average_hint_dependency=0.0,
            average_concept_coverage=0.0,
            total_sessions=0,
            total_focus_duration=0.0
        )
    
    # Convert to response format
    data_points = [
        MetricsDataPoint(
            session_id=m.session_id,
            timestamp=m.created_at,
            wpm=m.wpm,
            pause_rate=m.pause_rate,
            hint_dependency=m.hint_dependency,
            concept_coverage=m.concept_coverage,
            focus_duration=m.focus_duration
        )
        for m in metrics_list
    ]
    
    # Calculate averages
    total = len(metrics_list)
    avg_wpm = sum(m.wpm for m in metrics_list) / total
    avg_pause_rate = sum(m.pause_rate for m in metrics_list) / total
    avg_hint_dependency = sum(m.hint_dependency for m in metrics_list) / total
    avg_concept_coverage = sum(m.concept_coverage for m in metrics_list) / total
    total_focus = sum(m.focus_duration for m in metrics_list)
    
    return MetricsResponse(
        student_id=student_id,
        metrics_history=data_points,
        average_wpm=avg_wpm,
        average_pause_rate=avg_pause_rate,
        average_hint_dependency=avg_hint_dependency,
        average_concept_coverage=avg_concept_coverage,
        total_sessions=total,
        total_focus_duration=total_focus
    )


@router.get("/heatmap", response_model=HeatmapResponse)
async def get_heatmap(
    student_id: str = Query(..., description="Student ID (required)"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    db: Session = Depends(get_db)
):
    """
    Get weakness heatmap based on knowledge graph.
    
    Requirements: 10.2
    - THE Dashboard SHALL 依據知識圖譜節點顯示弱點熱力圖 (紅黃綠燈)
    """
    knowledge_manager = KnowledgeGraphManager(db)
    error_manager = ErrorBookManager(db)
    
    # Get all knowledge nodes
    nodes = knowledge_manager.get_all_nodes(subject=subject)
    
    # Get error statistics
    error_stats = error_manager.get_error_statistics(student_id)
    
    # Get all errors for the student
    errors = error_manager.get_errors(student_id)
    
    # Get all sessions for the student to calculate concept coverage
    sessions = db.query(SessionModel).filter(
        SessionModel.student_id == student_id
    ).all()
    
    # Build mastery data for each node
    node_mastery_list = []
    weak_areas = []
    strong_areas = []
    
    for node in nodes:
        # Count errors related to this node
        node_errors = 0
        total_attempts = 0
        
        for error in errors:
            # Check if the error's question is related to this node
            question = db.query(Question).filter(
                Question.id == error.question_id
            ).first()
            if question:
                node_ids = [n.id for n in question.knowledge_nodes]
                if node.id in node_ids:
                    node_errors += 1
                    total_attempts += 1
        
        # Count successful attempts (sessions with this concept covered)
        for session in sessions:
            if session.concept_coverage and session.concept_coverage > 0:
                # Check if session's question relates to this node
                question = db.query(Question).filter(
                    Question.id == session.question_id
                ).first()
                if question:
                    node_ids = [n.id for n in question.knowledge_nodes]
                    if node.id in node_ids:
                        total_attempts += 1
        
        # Calculate mastery score
        if total_attempts > 0:
            error_rate = node_errors / total_attempts
            mastery_score = 1.0 - error_rate
        else:
            mastery_score = 0.5  # Unknown mastery
        
        # Determine mastery level (red/yellow/green)
        if mastery_score >= 0.8:
            mastery_level = "green"
            strong_areas.append(node.id)
        elif mastery_score >= 0.5:
            mastery_level = "yellow"
        else:
            mastery_level = "red"
            weak_areas.append(node.id)
        
        # Calculate average concept coverage for this node
        node_coverage = 0.0
        coverage_count = 0
        for session in sessions:
            question = db.query(Question).filter(
                Question.id == session.question_id
            ).first()
            if question:
                node_ids = [n.id for n in question.knowledge_nodes]
                if node.id in node_ids and session.concept_coverage:
                    node_coverage += session.concept_coverage
                    coverage_count += 1
        
        avg_coverage = node_coverage / coverage_count if coverage_count > 0 else 0.0
        
        node_mastery_list.append(KnowledgeNodeMastery(
            node_id=node.id,
            node_name=node.name,
            subject=node.subject,
            unit=node.unit,
            mastery_level=mastery_level,
            mastery_score=mastery_score,
            error_count=node_errors,
            total_attempts=total_attempts,
            concept_coverage=avg_coverage
        ))
    
    return HeatmapResponse(
        student_id=student_id,
        nodes=node_mastery_list,
        weak_areas=weak_areas,
        strong_areas=strong_areas
    )


class PauseRecord(BaseModel):
    """A pause/distraction record."""
    start_time: float
    end_time: float
    duration: float


class SessionDetailResponse(BaseModel):
    """Detailed session information including pauses."""
    session_id: str
    question_id: str
    student_id: str
    start_time: datetime
    end_time: Optional[datetime]
    final_state: Optional[str]
    concept_coverage: float
    wpm: Optional[float]
    pause_rate: Optional[float]
    hint_dependency: Optional[float]
    focus_duration: Optional[float]
    pauses: List[PauseRecord]
    total_pause_duration: float
    hint_count: int


@router.get("/session/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information for a specific session.
    
    Requirements: 10.3, 10.4
    - THE Dashboard SHALL 顯示學生專注時長、分心時段及疲勞週期分析
    - WHEN 點擊特定知識點 THEN THE Dashboard SHALL 展開該知識點的詳細學習歷程
    """
    from backend.models.metrics import Pause, HintUsage
    
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get pauses for this session
    pauses = db.query(Pause).filter(Pause.session_id == session_id).all()
    pause_records = [
        PauseRecord(
            start_time=p.start_time,
            end_time=p.end_time,
            duration=p.duration
        )
        for p in pauses
    ]
    total_pause_duration = sum(p.duration for p in pauses)
    
    # Get hint count
    hint_count = db.query(HintUsage).filter(HintUsage.session_id == session_id).count()
    
    # Get metrics if available
    metrics = db.query(LearningMetrics).filter(LearningMetrics.session_id == session_id).first()
    
    return SessionDetailResponse(
        session_id=session.id,
        question_id=session.question_id,
        student_id=session.student_id,
        start_time=session.start_time,
        end_time=session.end_time,
        final_state=session.final_state,
        concept_coverage=session.concept_coverage or 0.0,
        wpm=metrics.wpm if metrics else None,
        pause_rate=metrics.pause_rate if metrics else None,
        hint_dependency=metrics.hint_dependency if metrics else None,
        focus_duration=metrics.focus_duration if metrics else None,
        pauses=pause_records,
        total_pause_duration=total_pause_duration,
        hint_count=hint_count
    )


@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_overview(
    student_id: str = Query(..., description="Student ID (required)"),
    db: Session = Depends(get_db)
):
    """
    Get dashboard overview for a student.
    
    Requirements: 10.1, 10.3
    """
    error_manager = ErrorBookManager(db)
    
    # Get sessions
    sessions = db.query(SessionModel).filter(
        SessionModel.student_id == student_id
    ).order_by(SessionModel.start_time.desc()).all()
    
    total_sessions = len(sessions)
    completed_sessions = len([s for s in sessions if s.end_time is not None])
    
    # Calculate average coverage
    coverages = [s.concept_coverage for s in sessions if s.concept_coverage is not None]
    avg_coverage = sum(coverages) / len(coverages) if coverages else 0.0
    
    # Calculate total duration
    total_duration = 0.0
    for s in sessions:
        if s.start_time and s.end_time:
            duration = (s.end_time - s.start_time).total_seconds() / 60
            total_duration += duration
    
    # Get recent sessions (top 5)
    recent_sessions = [
        SessionSummaryResponse(
            session_id=s.id,
            question_id=s.question_id,
            start_time=s.start_time,
            end_time=s.end_time,
            concept_coverage=s.concept_coverage or 0.0,
            final_state=s.final_state
        )
        for s in sessions[:5]
    ]
    
    # Get error statistics
    error_stats = error_manager.get_error_statistics(student_id)
    
    return DashboardOverviewResponse(
        student_id=student_id,
        total_sessions=total_sessions,
        completed_sessions=completed_sessions,
        average_coverage=avg_coverage,
        total_duration_minutes=total_duration,
        recent_sessions=recent_sessions,
        error_statistics={
            "total_errors": error_stats.total_errors,
            "repaired_count": error_stats.repaired_count,
            "errors_by_type": error_stats.errors_by_type,
            "errors_by_unit": error_stats.errors_by_unit,
            "most_frequent_misconceptions": error_stats.most_frequent_misconceptions
        }
    )
