"""
Student Metrics API routes for the AI Math Tutor system.
Provides comprehensive learning analytics with real data from database.

Implements:
- GET /api/student/metrics/summary - Get KPI summary
- GET /api/student/metrics/trends - Get historical trends
- GET /api/student/metrics/errors - Get error analysis
- GET /api/student/metrics/sessions - Get session history
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from backend.models.database import get_db
from backend.models.metrics import LearningMetrics, Pause, HintUsage
from backend.models.session import Session as SessionModel, ConversationTurn
from backend.models.error_book import ErrorRecord
from backend.models.knowledge import KnowledgeNode
from backend.models.question import Question


router = APIRouter(prefix="/api/student/metrics", tags=["student-metrics"])


# ============ Response Models ============

class DataConfidence(BaseModel):
    """Confidence level for metrics based on sample size."""
    sample_count: int
    is_sufficient: bool  # True if sample_count >= min_samples
    min_samples: int = 5
    message: str  # e.g., "尚無足夠數據" or "數據充足"


class KPIValue(BaseModel):
    """A single KPI value with metadata."""
    value: float
    unit: str
    trend: Optional[float] = None  # Percentage change from previous period
    trend_direction: Optional[str] = None  # "up", "down", "stable"
    confidence: DataConfidence


class MetricsSummaryResponse(BaseModel):
    """Summary of all KPI metrics."""
    student_id: str
    generated_at: datetime
    
    # Core KPIs
    accuracy_rate: KPIValue  # 正確率
    avg_wpm: KPIValue  # 平均語速
    error_recurrence_rate: KPIValue  # 錯題復發率
    focus_duration_today: KPIValue  # 今日專注時長
    
    # Additional metrics
    total_sessions: int
    total_practice_time_minutes: float
    streak_days: int
    hint_dependency: KPIValue
    pause_ratio: KPIValue
    concept_coverage: KPIValue


class TrendDataPoint(BaseModel):
    """A single data point for trend charts."""
    date: str  # ISO date string
    value: float
    label: Optional[str] = None


class TrendsResponse(BaseModel):
    """Historical trends for charts."""
    student_id: str
    period: str  # "week", "month", "all"
    
    # Line chart data
    accuracy_trend: List[TrendDataPoint]
    wpm_trend: List[TrendDataPoint]
    focus_trend: List[TrendDataPoint]
    
    # Bar chart data
    sessions_by_day: List[TrendDataPoint]
    errors_by_unit: List[TrendDataPoint]
    
    # Confidence
    confidence: DataConfidence


class ErrorAnalysisItem(BaseModel):
    """Analysis of a specific error type."""
    error_type: str
    count: int
    recurrence_count: int
    recurrence_rate: float
    related_concepts: List[str]
    last_occurrence: Optional[datetime]


class ErrorAnalysisResponse(BaseModel):
    """Error analysis for the student."""
    student_id: str
    total_errors: int
    repaired_errors: int
    repair_rate: float
    
    # Error breakdown
    errors_by_type: List[ErrorAnalysisItem]
    errors_by_unit: Dict[str, int]
    
    # Recurrence analysis
    recurring_errors: List[ErrorAnalysisItem]
    
    confidence: DataConfidence


class SessionHistoryItem(BaseModel):
    """A session in the history list."""
    session_id: str
    date: datetime
    unit: str
    subject: str
    mode: str  # "講題模式" or "練習模式"
    duration_minutes: float
    correct_rate: float
    wpm: Optional[float]
    pause_ratio: Optional[float]
    hint_used: int
    questions_count: int
    mistakes_count: int


class SessionHistoryResponse(BaseModel):
    """Session history with pagination."""
    student_id: str
    sessions: List[SessionHistoryItem]
    total_count: int
    page: int
    page_size: int
    has_more: bool


# ============ Helper Functions ============

def calculate_confidence(sample_count: int, min_samples: int = 5) -> DataConfidence:
    """Calculate data confidence based on sample size."""
    is_sufficient = sample_count >= min_samples
    if sample_count == 0:
        message = "尚無數據"
    elif sample_count < min_samples:
        message = f"樣本數過少 ({sample_count}/{min_samples})"
    else:
        message = "數據充足"
    
    return DataConfidence(
        sample_count=sample_count,
        is_sufficient=is_sufficient,
        min_samples=min_samples,
        message=message
    )


def calculate_trend(current: float, previous: float) -> tuple[float, str]:
    """Calculate trend percentage and direction."""
    if previous == 0:
        return 0.0, "stable"
    
    change = ((current - previous) / previous) * 100
    
    if abs(change) < 1:
        direction = "stable"
    elif change > 0:
        direction = "up"
    else:
        direction = "down"
    
    return round(change, 1), direction


def get_streak_days(db: Session, student_id: str) -> int:
    """Calculate consecutive learning days."""
    sessions = db.query(SessionModel).filter(
        SessionModel.student_id == student_id
    ).order_by(SessionModel.start_time.desc()).all()
    
    if not sessions:
        return 0
    
    streak = 0
    current_date = datetime.utcnow().date()
    
    # Get unique dates
    session_dates = set()
    for s in sessions:
        if s.start_time:
            session_dates.add(s.start_time.date())
    
    # Count consecutive days
    while current_date in session_dates or (current_date - timedelta(days=1)) in session_dates:
        if current_date in session_dates:
            streak += 1
        current_date -= timedelta(days=1)
        if current_date not in session_dates:
            break
    
    return streak


# ============ API Endpoints ============

@router.get("/summary", response_model=MetricsSummaryResponse)
async def get_metrics_summary(
    student_id: str = Query(..., description="Student ID"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive KPI summary for a student.
    All data comes from real database records.
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)
    
    # Get all sessions for this student
    all_sessions = db.query(SessionModel).filter(
        SessionModel.student_id == student_id
    ).all()
    
    # Get sessions from this week and last week for trend calculation
    this_week_sessions = [s for s in all_sessions if s.start_time and s.start_time >= week_ago]
    last_week_sessions = [s for s in all_sessions if s.start_time and two_weeks_ago <= s.start_time < week_ago]
    today_sessions = [s for s in all_sessions if s.start_time and s.start_time >= today_start]
    
    # Get metrics for sessions
    session_ids = [s.id for s in all_sessions]
    metrics_list = db.query(LearningMetrics).filter(
        LearningMetrics.session_id.in_(session_ids)
    ).all() if session_ids else []
    
    this_week_metrics = [m for m in metrics_list if m.session_id in [s.id for s in this_week_sessions]]
    last_week_metrics = [m for m in metrics_list if m.session_id in [s.id for s in last_week_sessions]]
    
    # Get error records
    errors = db.query(ErrorRecord).filter(
        ErrorRecord.student_id == student_id
    ).all()
    
    # Calculate accuracy rate
    total_questions = sum(1 for s in all_sessions if s.concept_coverage is not None)
    correct_questions = sum(1 for s in all_sessions if s.concept_coverage and s.concept_coverage >= 0.8)
    current_accuracy = correct_questions / total_questions if total_questions > 0 else 0.0
    
    # Previous period accuracy
    prev_total = len(last_week_sessions)
    prev_correct = sum(1 for s in last_week_sessions if s.concept_coverage and s.concept_coverage >= 0.8)
    prev_accuracy = prev_correct / prev_total if prev_total > 0 else 0.0
    
    accuracy_trend, accuracy_dir = calculate_trend(current_accuracy, prev_accuracy)
    
    # Calculate average WPM
    wpm_values = [m.wpm for m in metrics_list if m.wpm and m.wpm > 0]
    current_wpm = sum(wpm_values) / len(wpm_values) if wpm_values else 0.0
    
    prev_wpm_values = [m.wpm for m in last_week_metrics if m.wpm and m.wpm > 0]
    prev_wpm = sum(prev_wpm_values) / len(prev_wpm_values) if prev_wpm_values else 0.0
    
    wpm_trend, wpm_dir = calculate_trend(current_wpm, prev_wpm)
    
    # Calculate error recurrence rate
    total_errors = len(errors)
    recurring_errors = sum(1 for e in errors if e.recurrence_count and e.recurrence_count > 0)
    recurrence_rate = recurring_errors / total_errors if total_errors > 0 else 0.0
    
    # Calculate focus duration today
    focus_today = sum(m.focus_duration or 0 for m in metrics_list 
                      if m.session_id in [s.id for s in today_sessions])
    
    # Calculate hint dependency
    hint_deps = [m.hint_dependency for m in metrics_list if m.hint_dependency is not None]
    avg_hint_dep = sum(hint_deps) / len(hint_deps) if hint_deps else 0.0
    
    # Calculate pause ratio
    pause_rates = [m.pause_rate for m in metrics_list if m.pause_rate is not None]
    avg_pause = sum(pause_rates) / len(pause_rates) if pause_rates else 0.0
    
    # Calculate concept coverage
    coverages = [m.concept_coverage for m in metrics_list if m.concept_coverage is not None]
    avg_coverage = sum(coverages) / len(coverages) if coverages else 0.0
    
    # Calculate total practice time
    total_time = 0.0
    for s in all_sessions:
        if s.start_time and s.end_time:
            total_time += (s.end_time - s.start_time).total_seconds() / 60
    
    # Get streak days
    streak = get_streak_days(db, student_id)
    
    return MetricsSummaryResponse(
        student_id=student_id,
        generated_at=now,
        accuracy_rate=KPIValue(
            value=round(current_accuracy * 100, 1),
            unit="%",
            trend=accuracy_trend,
            trend_direction=accuracy_dir,
            confidence=calculate_confidence(total_questions)
        ),
        avg_wpm=KPIValue(
            value=round(current_wpm, 0),
            unit="字/分鐘",
            trend=wpm_trend,
            trend_direction=wpm_dir,
            confidence=calculate_confidence(len(wpm_values))
        ),
        error_recurrence_rate=KPIValue(
            value=round(recurrence_rate * 100, 1),
            unit="%",
            trend=None,
            trend_direction=None,
            confidence=calculate_confidence(total_errors)
        ),
        focus_duration_today=KPIValue(
            value=round(focus_today / 60, 0),  # Convert to minutes
            unit="分鐘",
            trend=None,
            trend_direction=None,
            confidence=calculate_confidence(len(today_sessions))
        ),
        total_sessions=len(all_sessions),
        total_practice_time_minutes=round(total_time, 0),
        streak_days=streak,
        hint_dependency=KPIValue(
            value=round(avg_hint_dep * 100, 1),
            unit="%",
            trend=None,
            trend_direction=None,
            confidence=calculate_confidence(len(hint_deps))
        ),
        pause_ratio=KPIValue(
            value=round(avg_pause * 100, 1),
            unit="%",
            trend=None,
            trend_direction=None,
            confidence=calculate_confidence(len(pause_rates))
        ),
        concept_coverage=KPIValue(
            value=round(avg_coverage * 100, 1),
            unit="%",
            trend=None,
            trend_direction=None,
            confidence=calculate_confidence(len(coverages))
        )
    )


@router.get("/trends", response_model=TrendsResponse)
async def get_metrics_trends(
    student_id: str = Query(..., description="Student ID"),
    period: str = Query("week", description="Period: week, month, all"),
    db: Session = Depends(get_db)
):
    """
    Get historical trend data for charts.
    Returns data points for line charts and bar charts.
    """
    now = datetime.utcnow()
    
    # Determine date range
    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    else:
        start_date = datetime.min
    
    # Get sessions in range
    sessions = db.query(SessionModel).filter(
        and_(
            SessionModel.student_id == student_id,
            SessionModel.start_time >= start_date
        )
    ).order_by(SessionModel.start_time).all()
    
    session_ids = [s.id for s in sessions]
    metrics_list = db.query(LearningMetrics).filter(
        LearningMetrics.session_id.in_(session_ids)
    ).all() if session_ids else []
    
    # Build metrics lookup
    metrics_by_session = {m.session_id: m for m in metrics_list}
    
    # Group by date
    daily_data: Dict[str, Dict[str, Any]] = {}
    
    for session in sessions:
        if not session.start_time:
            continue
        
        date_str = session.start_time.strftime("%Y-%m-%d")
        if date_str not in daily_data:
            daily_data[date_str] = {
                "accuracy_values": [],
                "wpm_values": [],
                "focus_values": [],
                "session_count": 0
            }
        
        daily_data[date_str]["session_count"] += 1
        
        if session.concept_coverage is not None:
            daily_data[date_str]["accuracy_values"].append(session.concept_coverage)
        
        metrics = metrics_by_session.get(session.id)
        if metrics:
            if metrics.wpm:
                daily_data[date_str]["wpm_values"].append(metrics.wpm)
            if metrics.focus_duration:
                daily_data[date_str]["focus_values"].append(metrics.focus_duration)
    
    # Build trend data points
    accuracy_trend = []
    wpm_trend = []
    focus_trend = []
    sessions_by_day = []
    
    for date_str in sorted(daily_data.keys()):
        data = daily_data[date_str]
        
        # Accuracy trend
        if data["accuracy_values"]:
            avg_acc = sum(data["accuracy_values"]) / len(data["accuracy_values"])
            accuracy_trend.append(TrendDataPoint(
                date=date_str,
                value=round(avg_acc * 100, 1)
            ))
        
        # WPM trend
        if data["wpm_values"]:
            avg_wpm = sum(data["wpm_values"]) / len(data["wpm_values"])
            wpm_trend.append(TrendDataPoint(
                date=date_str,
                value=round(avg_wpm, 0)
            ))
        
        # Focus trend
        if data["focus_values"]:
            total_focus = sum(data["focus_values"]) / 60  # Convert to minutes
            focus_trend.append(TrendDataPoint(
                date=date_str,
                value=round(total_focus, 0)
            ))
        
        # Sessions by day
        sessions_by_day.append(TrendDataPoint(
            date=date_str,
            value=data["session_count"]
        ))
    
    # Get errors by unit
    errors = db.query(ErrorRecord).filter(
        and_(
            ErrorRecord.student_id == student_id,
            ErrorRecord.created_at >= start_date
        )
    ).all()
    
    unit_errors: Dict[str, int] = {}
    for error in errors:
        unit = error.unit or "未分類"
        unit_errors[unit] = unit_errors.get(unit, 0) + 1
    
    errors_by_unit = [
        TrendDataPoint(date=unit, value=count, label=unit)
        for unit, count in sorted(unit_errors.items(), key=lambda x: -x[1])
    ]
    
    return TrendsResponse(
        student_id=student_id,
        period=period,
        accuracy_trend=accuracy_trend,
        wpm_trend=wpm_trend,
        focus_trend=focus_trend,
        sessions_by_day=sessions_by_day,
        errors_by_unit=errors_by_unit,
        confidence=calculate_confidence(len(sessions))
    )


@router.get("/errors", response_model=ErrorAnalysisResponse)
async def get_error_analysis(
    student_id: str = Query(..., description="Student ID"),
    db: Session = Depends(get_db)
):
    """
    Get detailed error analysis including recurrence rates.
    """
    errors = db.query(ErrorRecord).filter(
        ErrorRecord.student_id == student_id
    ).all()
    
    total_errors = len(errors)
    repaired_errors = sum(1 for e in errors if e.is_repaired)
    repair_rate = repaired_errors / total_errors if total_errors > 0 else 0.0
    
    # Group errors by type
    errors_by_type_dict: Dict[str, Dict[str, Any]] = {}
    for error in errors:
        error_type = error.error_type or "未分類"
        if error_type not in errors_by_type_dict:
            errors_by_type_dict[error_type] = {
                "count": 0,
                "recurrence_count": 0,
                "concepts": set(),
                "last_occurrence": None
            }
        
        errors_by_type_dict[error_type]["count"] += 1
        if error.recurrence_count and error.recurrence_count > 0:
            errors_by_type_dict[error_type]["recurrence_count"] += 1
        if error.concept:
            errors_by_type_dict[error_type]["concepts"].add(error.concept)
        if error.created_at:
            current_last = errors_by_type_dict[error_type]["last_occurrence"]
            if current_last is None or error.created_at > current_last:
                errors_by_type_dict[error_type]["last_occurrence"] = error.created_at
    
    errors_by_type = [
        ErrorAnalysisItem(
            error_type=error_type,
            count=data["count"],
            recurrence_count=data["recurrence_count"],
            recurrence_rate=data["recurrence_count"] / data["count"] if data["count"] > 0 else 0.0,
            related_concepts=list(data["concepts"]),
            last_occurrence=data["last_occurrence"]
        )
        for error_type, data in errors_by_type_dict.items()
    ]
    
    # Group errors by unit
    errors_by_unit: Dict[str, int] = {}
    for error in errors:
        unit = error.unit or "未分類"
        errors_by_unit[unit] = errors_by_unit.get(unit, 0) + 1
    
    # Get recurring errors
    recurring_errors = [e for e in errors_by_type if e.recurrence_rate > 0]
    recurring_errors.sort(key=lambda x: -x.recurrence_rate)
    
    return ErrorAnalysisResponse(
        student_id=student_id,
        total_errors=total_errors,
        repaired_errors=repaired_errors,
        repair_rate=repair_rate,
        errors_by_type=errors_by_type,
        errors_by_unit=errors_by_unit,
        recurring_errors=recurring_errors[:5],  # Top 5 recurring
        confidence=calculate_confidence(total_errors)
    )


@router.get("/sessions", response_model=SessionHistoryResponse)
async def get_session_history(
    student_id: str = Query(..., description="Student ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get paginated session history with detailed metrics.
    """
    # Get total count
    total_count = db.query(SessionModel).filter(
        SessionModel.student_id == student_id
    ).count()
    
    # Get paginated sessions
    offset = (page - 1) * page_size
    sessions = db.query(SessionModel).filter(
        SessionModel.student_id == student_id
    ).order_by(SessionModel.start_time.desc()).offset(offset).limit(page_size).all()
    
    # Get metrics for these sessions
    session_ids = [s.id for s in sessions]
    metrics_list = db.query(LearningMetrics).filter(
        LearningMetrics.session_id.in_(session_ids)
    ).all() if session_ids else []
    metrics_by_session = {m.session_id: m for m in metrics_list}
    
    # Get hint counts
    hint_counts = {}
    if session_ids:
        hint_results = db.query(
            HintUsage.session_id,
            func.count(HintUsage.id).label("count")
        ).filter(
            HintUsage.session_id.in_(session_ids)
        ).group_by(HintUsage.session_id).all()
        hint_counts = {r.session_id: r.count for r in hint_results}
    
    # Get error counts
    error_counts = {}
    if session_ids:
        error_results = db.query(
            ErrorRecord.session_id,
            func.count(ErrorRecord.id).label("count")
        ).filter(
            ErrorRecord.session_id.in_(session_ids)
        ).group_by(ErrorRecord.session_id).all()
        error_counts = {r.session_id: r.count for r in error_results}
    
    # Build response items
    items = []
    for session in sessions:
        # Get question info
        question = db.query(Question).filter(
            Question.id == session.question_id
        ).first()
        
        # Calculate duration
        duration = 0.0
        if session.start_time and session.end_time:
            duration = (session.end_time - session.start_time).total_seconds() / 60
        
        metrics = metrics_by_session.get(session.id)
        
        items.append(SessionHistoryItem(
            session_id=session.id,
            date=session.start_time or datetime.utcnow(),
            unit=question.unit if question else "未知",
            subject=question.subject if question else "數學",
            mode="講題模式",  # Default mode
            duration_minutes=round(duration, 1),
            correct_rate=session.concept_coverage or 0.0,
            wpm=metrics.wpm if metrics else None,
            pause_ratio=metrics.pause_rate if metrics else None,
            hint_used=hint_counts.get(session.id, 0),
            questions_count=1,  # One question per session
            mistakes_count=error_counts.get(session.id, 0)
        ))
    
    return SessionHistoryResponse(
        student_id=student_id,
        sessions=items,
        total_count=total_count,
        page=page,
        page_size=page_size,
        has_more=(offset + page_size) < total_count
    )
