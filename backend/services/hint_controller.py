"""
Hint Controller for the AI Math Tutor system.
Manages hint levels and hint usage tracking.
"""
from enum import IntEnum
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import uuid

from sqlalchemy.orm import Session as DBSession

from backend.models.metrics import HintUsage


class HintLevel(IntEnum):
    """Hint levels for progressive assistance."""
    LEVEL_1 = 1  # 方向性暗示 (Directional hint)
    LEVEL_2 = 2  # 關鍵步驟提示 (Key step hint)
    LEVEL_3 = 3  # 具體解法框架 (Concrete solution framework)


@dataclass
class HintRecord:
    """Record of a hint provided to the student."""
    level: HintLevel
    concept: str
    timestamp: float
    session_id: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


class HintController:
    """
    Controller for managing hint levels and tracking hint usage.
    
    Implements progressive hint system:
    - Level 1: Directional hints (方向性暗示)
    - Level 2: Key step hints (關鍵步驟提示)
    - Level 3: Concrete solution framework (具體解法框架)
    """
    
    # Weights for hint dependency calculation
    HINT_WEIGHTS = {
        HintLevel.LEVEL_1: 0.2,
        HintLevel.LEVEL_2: 0.5,
        HintLevel.LEVEL_3: 1.0
    }

    def __init__(self, db: Optional[DBSession] = None):
        """
        Initialize the Hint Controller.
        
        Args:
            db: Optional SQLAlchemy database session for persistence
        """
        self._db = db
        self._current_level: HintLevel = HintLevel.LEVEL_1
        self._hint_history: List[HintRecord] = []
        self._current_concept: Optional[str] = None
        self._session_id: Optional[str] = None

    def start_session(self, session_id: str, concept: Optional[str] = None) -> None:
        """
        Start a new hint session for a concept.
        
        Args:
            session_id: The session ID
            concept: Optional concept being worked on
        """
        self._session_id = session_id
        self._current_concept = concept
        self._current_level = HintLevel.LEVEL_1
        # Don't clear history - keep for statistics

    def reset_for_concept(self, concept: str) -> None:
        """
        Reset hint level for a new concept.
        
        Args:
            concept: The new concept being worked on
        """
        self._current_concept = concept
        self._current_level = HintLevel.LEVEL_1

    def get_current_level(self) -> HintLevel:
        """
        Get the current hint level.
        
        Returns:
            Current HintLevel
        """
        return self._current_level

    def request_hint(self, concept: Optional[str] = None) -> HintLevel:
        """
        Request a hint and get the appropriate level.
        
        This method:
        1. Returns the current hint level
        2. Records the hint usage
        3. Increments the level for next request (up to LEVEL_3)
        
        Args:
            concept: Optional concept for the hint (uses current if not provided)
            
        Returns:
            The HintLevel to provide
        """
        # Use provided concept or current concept
        hint_concept = concept or self._current_concept or "unknown"
        
        # Get the level to return
        level_to_return = self._current_level
        
        # Record the hint usage
        hint_record = HintRecord(
            level=level_to_return,
            concept=hint_concept,
            timestamp=datetime.utcnow().timestamp(),
            session_id=self._session_id
        )
        self._hint_history.append(hint_record)
        
        # Persist to database if available
        if self._db and self._session_id:
            self._persist_hint_usage(hint_record)
        
        # Increment level for next request (max at LEVEL_3)
        if self._current_level < HintLevel.LEVEL_3:
            self._current_level = HintLevel(self._current_level + 1)
        
        return level_to_return

    def _persist_hint_usage(self, hint_record: HintRecord) -> None:
        """
        Persist hint usage to database.
        
        Args:
            hint_record: The hint record to persist
        """
        if not self._db or not self._session_id:
            return
        
        hint_usage = HintUsage(
            id=hint_record.id,
            session_id=self._session_id,
            hint_level=int(hint_record.level),
            concept=hint_record.concept,
            timestamp=datetime.fromtimestamp(hint_record.timestamp)
        )
        self._db.add(hint_usage)
        self._db.commit()

    def get_hint_history(self) -> List[HintRecord]:
        """
        Get the history of hints provided.
        
        Returns:
            List of HintRecord entries
        """
        return self._hint_history.copy()

    def get_session_hints(self, session_id: Optional[str] = None) -> List[HintRecord]:
        """
        Get hints for a specific session.
        
        Args:
            session_id: The session ID (uses current if not provided)
            
        Returns:
            List of HintRecord entries for the session
        """
        target_session = session_id or self._session_id
        return [h for h in self._hint_history if h.session_id == target_session]

    def get_hint_count(self, session_id: Optional[str] = None) -> int:
        """
        Get the number of hints provided in a session.
        
        Args:
            session_id: The session ID (uses current if not provided)
            
        Returns:
            Number of hints provided
        """
        return len(self.get_session_hints(session_id))

    def calculate_hint_dependency(
        self,
        total_turns: int,
        session_id: Optional[str] = None
    ) -> float:
        """
        Calculate hint dependency score for a session.
        
        Formula: 1 - Σ(hint_count × weight) / total_turns
        
        Args:
            total_turns: Total number of interaction turns
            session_id: The session ID (uses current if not provided)
            
        Returns:
            Hint dependency score (0-1, lower is more dependent)
        """
        if total_turns <= 0:
            return 1.0  # No turns means no dependency
        
        session_hints = self.get_session_hints(session_id)
        
        if not session_hints:
            return 1.0  # No hints means no dependency
        
        # Calculate weighted hint sum
        weighted_sum = sum(
            self.HINT_WEIGHTS.get(h.level, 1.0)
            for h in session_hints
        )
        
        # Calculate dependency (clamped to 0-1)
        dependency = 1 - (weighted_sum / total_turns)
        return max(0.0, min(1.0, dependency))

    def get_hints_by_level(
        self,
        session_id: Optional[str] = None
    ) -> dict[HintLevel, int]:
        """
        Get hint counts grouped by level.
        
        Args:
            session_id: The session ID (uses current if not provided)
            
        Returns:
            Dictionary mapping HintLevel to count
        """
        session_hints = self.get_session_hints(session_id)
        
        counts = {level: 0 for level in HintLevel}
        for hint in session_hints:
            counts[hint.level] += 1
        
        return counts

    def clear_history(self) -> None:
        """Clear all hint history."""
        self._hint_history.clear()

    def reset(self) -> None:
        """Reset the controller to initial state."""
        self._current_level = HintLevel.LEVEL_1
        self._current_concept = None
        self._session_id = None
        # Keep history for statistics
