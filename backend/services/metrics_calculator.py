"""
Metrics Calculator for the AI Math Tutor system.
Calculates and persists learning metrics including WPM, pause rate,
hint dependency, and concept coverage.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Set
import uuid

from sqlalchemy.orm import Session as DBSession

from backend.models.metrics import LearningMetrics, Pause as PauseModel, HintUsage


@dataclass
class PauseData:
    """Data class representing a pause during speech."""
    start_time: float
    end_time: float
    duration: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """Validate pause data."""
        if self.start_time < 0:
            raise ValueError("start_time must be non-negative")
        if self.end_time < self.start_time:
            raise ValueError("end_time must be >= start_time")
        if self.duration < 0:
            raise ValueError("duration must be non-negative")


@dataclass
class HintUsageData:
    """Data class representing hint usage."""
    level: int  # 1, 2, or 3
    concept: str
    timestamp: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Weights for hint dependency calculation
    HINT_WEIGHTS = {
        1: 0.2,  # Level 1: Directional hint
        2: 0.5,  # Level 2: Key step hint
        3: 1.0   # Level 3: Concrete solution framework
    }

    @property
    def weight(self) -> float:
        """Get the weight for this hint level."""
        return self.HINT_WEIGHTS.get(self.level, 1.0)


@dataclass
class MetricsReport:
    """Complete metrics report for a session."""
    session_id: str
    wpm: float
    pause_rate: float
    hint_dependency: float
    concept_coverage: float
    focus_duration: float
    created_at: datetime = field(default_factory=datetime.utcnow)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


class MetricsCalculator:
    """
    Calculator for learning metrics.
    
    Implements calculations for:
    - WPM (Words Per Minute)
    - Pause Rate
    - Hint Dependency
    - Concept Coverage
    
    Also handles persistence of metrics to database.
    """

    def __init__(self, db: Optional[DBSession] = None):
        """
        Initialize the Metrics Calculator.
        
        Args:
            db: Optional SQLAlchemy database session for persistence
        """
        self._db = db

    def calculate_wpm(self, word_count: int, duration_minutes: float) -> float:
        """
        Calculate Words Per Minute (WPM).
        
        Formula: WPM = total_words / duration_minutes
        
        Args:
            word_count: Total number of words spoken
            duration_minutes: Duration in minutes
            
        Returns:
            Words per minute value
            
        Raises:
            ValueError: If word_count is negative or duration_minutes <= 0
        """
        if word_count < 0:
            raise ValueError("word_count must be non-negative")
        if duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        
        return word_count / duration_minutes

    def calculate_pause_rate(
        self,
        pauses: List[PauseData],
        total_duration: float
    ) -> float:
        """
        Calculate pause rate (ratio of pause time to total time).
        
        Formula: pause_rate = sum(pause_durations) / total_duration
        
        Args:
            pauses: List of PauseData objects
            total_duration: Total session duration in seconds
            
        Returns:
            Pause rate (0.0 to 1.0)
            
        Raises:
            ValueError: If total_duration <= 0
        """
        if total_duration <= 0:
            raise ValueError("total_duration must be positive")
        
        if not pauses:
            return 0.0
        
        total_pause_duration = sum(p.duration for p in pauses)
        
        # Clamp to 0-1 range (pause time shouldn't exceed total time)
        pause_rate = total_pause_duration / total_duration
        return max(0.0, min(1.0, pause_rate))

    def calculate_hint_dependency(
        self,
        hints: List[HintUsageData],
        total_turns: int
    ) -> float:
        """
        Calculate hint dependency score.
        
        Formula: hint_dependency = 1 - Σ(hint_count × weight) / total_turns
        
        Lower values indicate higher dependency on hints.
        
        Args:
            hints: List of HintUsageData objects
            total_turns: Total number of interaction turns
            
        Returns:
            Hint dependency score (0.0 to 1.0)
            
        Raises:
            ValueError: If total_turns < 0
        """
        if total_turns < 0:
            raise ValueError("total_turns must be non-negative")
        
        if total_turns == 0:
            return 1.0  # No turns means no dependency
        
        if not hints:
            return 1.0  # No hints means no dependency
        
        # Calculate weighted hint sum
        weighted_sum = sum(h.weight for h in hints)
        
        # Calculate dependency (clamped to 0-1)
        dependency = 1 - (weighted_sum / total_turns)
        return max(0.0, min(1.0, dependency))

    def calculate_concept_coverage(
        self,
        covered_concepts: List[str],
        required_concepts: List[str]
    ) -> float:
        """
        Calculate concept coverage rate.
        
        Formula: coverage = |covered ∩ required| / |required|
        
        Args:
            covered_concepts: List of concepts covered by the student
            required_concepts: List of concepts required for the question
            
        Returns:
            Concept coverage rate (0.0 to 1.0)
        """
        if not required_concepts:
            return 1.0  # No required concepts means full coverage
        
        # Use sets for efficient intersection
        covered_set: Set[str] = set(covered_concepts)
        required_set: Set[str] = set(required_concepts)
        
        # Calculate intersection
        covered_required = covered_set.intersection(required_set)
        
        return len(covered_required) / len(required_set)


    def generate_metrics_report(
        self,
        session_id: str,
        word_count: int,
        duration_minutes: float,
        pauses: List[PauseData],
        hints: List[HintUsageData],
        total_turns: int,
        covered_concepts: List[str],
        required_concepts: List[str],
        focus_duration: float = 0.0
    ) -> MetricsReport:
        """
        Generate a complete metrics report for a session.
        
        Args:
            session_id: The session ID
            word_count: Total words spoken
            duration_minutes: Duration in minutes
            pauses: List of pauses
            hints: List of hint usages
            total_turns: Total interaction turns
            covered_concepts: Concepts covered
            required_concepts: Required concepts
            focus_duration: Optional focus duration in seconds
            
        Returns:
            MetricsReport with all calculated metrics
        """
        # Calculate total duration in seconds for pause rate
        total_duration_seconds = duration_minutes * 60
        
        return MetricsReport(
            session_id=session_id,
            wpm=self.calculate_wpm(word_count, duration_minutes),
            pause_rate=self.calculate_pause_rate(pauses, total_duration_seconds),
            hint_dependency=self.calculate_hint_dependency(hints, total_turns),
            concept_coverage=self.calculate_concept_coverage(
                covered_concepts, required_concepts
            ),
            focus_duration=focus_duration
        )

    def save_metrics(self, metrics: MetricsReport) -> str:
        """
        Save metrics to the database.
        
        Args:
            metrics: MetricsReport to save
            
        Returns:
            The ID of the saved metrics record
            
        Raises:
            RuntimeError: If no database session is available
        """
        if not self._db:
            raise RuntimeError("No database session available for persistence")
        
        learning_metrics = LearningMetrics(
            id=metrics.id,
            session_id=metrics.session_id,
            wpm=metrics.wpm,
            pause_rate=metrics.pause_rate,
            hint_dependency=metrics.hint_dependency,
            concept_coverage=metrics.concept_coverage,
            focus_duration=metrics.focus_duration,
            created_at=metrics.created_at
        )
        
        self._db.add(learning_metrics)
        self._db.commit()
        
        return metrics.id

    def get_metrics(self, session_id: str) -> Optional[MetricsReport]:
        """
        Retrieve metrics for a session from the database.
        
        Args:
            session_id: The session ID to retrieve metrics for
            
        Returns:
            MetricsReport if found, None otherwise
            
        Raises:
            RuntimeError: If no database session is available
        """
        if not self._db:
            raise RuntimeError("No database session available for retrieval")
        
        learning_metrics = self._db.query(LearningMetrics).filter(
            LearningMetrics.session_id == session_id
        ).first()
        
        if not learning_metrics:
            return None
        
        return MetricsReport(
            id=learning_metrics.id,
            session_id=learning_metrics.session_id,
            wpm=learning_metrics.wpm or 0.0,
            pause_rate=learning_metrics.pause_rate or 0.0,
            hint_dependency=learning_metrics.hint_dependency or 0.0,
            concept_coverage=learning_metrics.concept_coverage or 0.0,
            focus_duration=learning_metrics.focus_duration or 0.0,
            created_at=learning_metrics.created_at or datetime.utcnow()
        )

    def get_metrics_by_id(self, metrics_id: str) -> Optional[MetricsReport]:
        """
        Retrieve metrics by ID from the database.
        
        Args:
            metrics_id: The metrics record ID
            
        Returns:
            MetricsReport if found, None otherwise
            
        Raises:
            RuntimeError: If no database session is available
        """
        if not self._db:
            raise RuntimeError("No database session available for retrieval")
        
        learning_metrics = self._db.query(LearningMetrics).filter(
            LearningMetrics.id == metrics_id
        ).first()
        
        if not learning_metrics:
            return None
        
        return MetricsReport(
            id=learning_metrics.id,
            session_id=learning_metrics.session_id,
            wpm=learning_metrics.wpm or 0.0,
            pause_rate=learning_metrics.pause_rate or 0.0,
            hint_dependency=learning_metrics.hint_dependency or 0.0,
            concept_coverage=learning_metrics.concept_coverage or 0.0,
            focus_duration=learning_metrics.focus_duration or 0.0,
            created_at=learning_metrics.created_at or datetime.utcnow()
        )

    def update_metrics(self, metrics: MetricsReport) -> bool:
        """
        Update existing metrics in the database.
        
        Args:
            metrics: MetricsReport with updated values
            
        Returns:
            True if updated successfully, False if not found
            
        Raises:
            RuntimeError: If no database session is available
        """
        if not self._db:
            raise RuntimeError("No database session available for update")
        
        learning_metrics = self._db.query(LearningMetrics).filter(
            LearningMetrics.id == metrics.id
        ).first()
        
        if not learning_metrics:
            return False
        
        learning_metrics.wpm = metrics.wpm
        learning_metrics.pause_rate = metrics.pause_rate
        learning_metrics.hint_dependency = metrics.hint_dependency
        learning_metrics.concept_coverage = metrics.concept_coverage
        learning_metrics.focus_duration = metrics.focus_duration
        
        self._db.commit()
        return True

    def delete_metrics(self, metrics_id: str) -> bool:
        """
        Delete metrics from the database.
        
        Args:
            metrics_id: The metrics record ID to delete
            
        Returns:
            True if deleted successfully, False if not found
            
        Raises:
            RuntimeError: If no database session is available
        """
        if not self._db:
            raise RuntimeError("No database session available for deletion")
        
        learning_metrics = self._db.query(LearningMetrics).filter(
            LearningMetrics.id == metrics_id
        ).first()
        
        if not learning_metrics:
            return False
        
        self._db.delete(learning_metrics)
        self._db.commit()
        return True

    def get_student_metrics_history(
        self,
        student_id: str,
        limit: int = 10
    ) -> List[MetricsReport]:
        """
        Get metrics history for a student across sessions.
        
        Args:
            student_id: The student ID
            limit: Maximum number of records to return
            
        Returns:
            List of MetricsReport ordered by creation date (newest first)
            
        Raises:
            RuntimeError: If no database session is available
        """
        if not self._db:
            raise RuntimeError("No database session available for retrieval")
        
        # Import Session model here to avoid circular imports
        from backend.models.session import Session
        
        # Join with sessions to filter by student
        metrics_list = (
            self._db.query(LearningMetrics)
            .join(Session, LearningMetrics.session_id == Session.id)
            .filter(Session.student_id == student_id)
            .order_by(LearningMetrics.created_at.desc())
            .limit(limit)
            .all()
        )
        
        return [
            MetricsReport(
                id=m.id,
                session_id=m.session_id,
                wpm=m.wpm or 0.0,
                pause_rate=m.pause_rate or 0.0,
                hint_dependency=m.hint_dependency or 0.0,
                concept_coverage=m.concept_coverage or 0.0,
                focus_duration=m.focus_duration or 0.0,
                created_at=m.created_at or datetime.utcnow()
            )
            for m in metrics_list
        ]
