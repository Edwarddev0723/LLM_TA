"""
Session Manager for the AI Math Tutor system.
Handles session persistence and concept coverage calculation.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from sqlalchemy.orm import Session as DBSession
from sqlalchemy import and_

from backend.models.session import Session as SessionModel, ConversationTurn as ConversationTurnModel
from backend.models.question import Question
from backend.models.knowledge import KnowledgeNode
from backend.services.fsm_controller import FSMState


@dataclass
class ConceptCoverageResult:
    """Result of concept coverage calculation."""
    coverage_ratio: float
    covered_concepts: List[str]
    missing_concepts: List[str]
    total_required: int
    total_covered: int


@dataclass
class SessionData:
    """Data transfer object for session information."""
    id: str
    student_id: str
    question_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    final_state: Optional[str] = None
    concept_coverage: float = 0.0
    conversation_turns: List[Dict[str, Any]] = field(default_factory=list)


class SessionManager:
    """
    Manager for session persistence and retrieval.
    
    Handles:
    - Creating and storing sessions in the database
    - Recording conversation turns
    - Calculating concept coverage
    - Retrieving session history
    
    Implements Requirements:
    - 6.8: WHEN 概念覆蓋率達到 90% 以上 THEN THE FSM_Controller SHALL 轉移至 CONSOLIDATING 狀態
    """
    
    def __init__(self, db: DBSession):
        """
        Initialize the Session Manager.
        
        Args:
            db: SQLAlchemy database session
        """
        self._db = db
    
    def create_session(
        self,
        student_id: str,
        question_id: str,
        session_id: Optional[str] = None
    ) -> SessionModel:
        """
        Create a new session in the database.
        
        Args:
            student_id: ID of the student
            question_id: ID of the question
            session_id: Optional custom session ID
            
        Returns:
            The created Session model
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        session = SessionModel(
            id=session_id,
            student_id=student_id,
            question_id=question_id,
            start_time=datetime.now(timezone.utc),
            concept_coverage=0.0
        )
        
        self._db.add(session)
        self._db.commit()
        self._db.refresh(session)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionModel]:
        """
        Get a session by ID.
        
        Args:
            session_id: The session ID
            
        Returns:
            Session model or None if not found
        """
        return self._db.query(SessionModel).filter(
            SessionModel.id == session_id
        ).first()
    
    def end_session(
        self,
        session_id: str,
        final_state: FSMState,
        concept_coverage: float
    ) -> Optional[SessionModel]:
        """
        End a session and update its final state.
        
        Args:
            session_id: The session ID
            final_state: The final FSM state
            concept_coverage: The final concept coverage ratio
            
        Returns:
            Updated Session model or None if not found
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        session.end_time = datetime.now(timezone.utc)
        session.final_state = final_state.value
        session.concept_coverage = concept_coverage
        
        self._db.commit()
        self._db.refresh(session)
        
        return session
    
    def add_conversation_turn(
        self,
        session_id: str,
        turn_number: int,
        speaker: str,
        content: str,
        fsm_state: FSMState
    ) -> ConversationTurnModel:
        """
        Add a conversation turn to a session.
        
        Args:
            session_id: The session ID
            turn_number: The turn number in the conversation
            speaker: "STUDENT" or "TUTOR"
            content: The content of the turn
            fsm_state: The FSM state at this turn
            
        Returns:
            The created ConversationTurn model
        """
        turn = ConversationTurnModel(
            id=str(uuid.uuid4()),
            session_id=session_id,
            turn_number=turn_number,
            speaker=speaker,
            content=content,
            fsm_state=fsm_state.value,
            timestamp=datetime.now(timezone.utc)
        )
        
        self._db.add(turn)
        self._db.commit()
        self._db.refresh(turn)
        
        return turn
    
    def get_conversation_history(
        self,
        session_id: str
    ) -> List[ConversationTurnModel]:
        """
        Get all conversation turns for a session.
        
        Args:
            session_id: The session ID
            
        Returns:
            List of ConversationTurn models ordered by turn number
        """
        return self._db.query(ConversationTurnModel).filter(
            ConversationTurnModel.session_id == session_id
        ).order_by(ConversationTurnModel.turn_number).all()
    
    def calculate_concept_coverage(
        self,
        question_id: str,
        covered_concepts: List[str]
    ) -> ConceptCoverageResult:
        """
        Calculate concept coverage for a question.
        
        Args:
            question_id: The question ID
            covered_concepts: List of concept IDs that have been covered
            
        Returns:
            ConceptCoverageResult with coverage details
        """
        # Get the question and its required knowledge nodes
        question = self._db.query(Question).filter(
            Question.id == question_id
        ).first()
        
        if not question:
            return ConceptCoverageResult(
                coverage_ratio=1.0,  # No question means full coverage
                covered_concepts=covered_concepts,
                missing_concepts=[],
                total_required=0,
                total_covered=len(covered_concepts)
            )
        
        # Get required concepts from the question's knowledge nodes
        required_concepts = [node.id for node in question.knowledge_nodes]
        
        if not required_concepts:
            return ConceptCoverageResult(
                coverage_ratio=1.0,  # No required concepts means full coverage
                covered_concepts=covered_concepts,
                missing_concepts=[],
                total_required=0,
                total_covered=len(covered_concepts)
            )
        
        # Calculate coverage
        covered_set = set(covered_concepts)
        required_set = set(required_concepts)
        
        covered_required = covered_set.intersection(required_set)
        missing = required_set - covered_set
        
        coverage_ratio = len(covered_required) / len(required_set)
        
        return ConceptCoverageResult(
            coverage_ratio=coverage_ratio,
            covered_concepts=list(covered_required),
            missing_concepts=list(missing),
            total_required=len(required_set),
            total_covered=len(covered_required)
        )
    
    def update_concept_coverage(
        self,
        session_id: str,
        coverage: float
    ) -> Optional[SessionModel]:
        """
        Update the concept coverage for a session.
        
        Args:
            session_id: The session ID
            coverage: The new coverage ratio (0-1)
            
        Returns:
            Updated Session model or None if not found
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        session.concept_coverage = coverage
        self._db.commit()
        self._db.refresh(session)
        
        return session
    
    def get_student_sessions(
        self,
        student_id: str,
        limit: int = 10
    ) -> List[SessionModel]:
        """
        Get recent sessions for a student.
        
        Args:
            student_id: The student ID
            limit: Maximum number of sessions to return
            
        Returns:
            List of Session models ordered by start time (newest first)
        """
        return self._db.query(SessionModel).filter(
            SessionModel.student_id == student_id
        ).order_by(SessionModel.start_time.desc()).limit(limit).all()
    
    def get_question_sessions(
        self,
        question_id: str,
        limit: int = 10
    ) -> List[SessionModel]:
        """
        Get recent sessions for a question.
        
        Args:
            question_id: The question ID
            limit: Maximum number of sessions to return
            
        Returns:
            List of Session models ordered by start time (newest first)
        """
        return self._db.query(SessionModel).filter(
            SessionModel.question_id == question_id
        ).order_by(SessionModel.start_time.desc()).limit(limit).all()
    
    def get_active_sessions(self) -> List[SessionModel]:
        """
        Get all active (not ended) sessions.
        
        Returns:
            List of active Session models
        """
        return self._db.query(SessionModel).filter(
            SessionModel.end_time.is_(None)
        ).all()
    
    def get_session_data(self, session_id: str) -> Optional[SessionData]:
        """
        Get session data as a DTO.
        
        Args:
            session_id: The session ID
            
        Returns:
            SessionData DTO or None if not found
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        turns = self.get_conversation_history(session_id)
        turn_data = [
            {
                "turn_number": t.turn_number,
                "speaker": t.speaker,
                "content": t.content,
                "fsm_state": t.fsm_state,
                "timestamp": t.timestamp.isoformat() if t.timestamp else None
            }
            for t in turns
        ]
        
        return SessionData(
            id=session.id,
            student_id=session.student_id,
            question_id=session.question_id,
            start_time=session.start_time,
            end_time=session.end_time,
            final_state=session.final_state,
            concept_coverage=session.concept_coverage or 0.0,
            conversation_turns=turn_data
        )
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its related data.
        
        Args:
            session_id: The session ID
            
        Returns:
            True if deleted, False if not found
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        # Delete conversation turns first
        self._db.query(ConversationTurnModel).filter(
            ConversationTurnModel.session_id == session_id
        ).delete()
        
        # Delete the session
        self._db.delete(session)
        self._db.commit()
        
        return True
    
    def get_session_statistics(
        self,
        student_id: str
    ) -> Dict[str, Any]:
        """
        Get statistics for a student's sessions.
        
        Args:
            student_id: The student ID
            
        Returns:
            Dictionary with session statistics
        """
        sessions = self._db.query(SessionModel).filter(
            SessionModel.student_id == student_id
        ).all()
        
        if not sessions:
            return {
                "total_sessions": 0,
                "completed_sessions": 0,
                "average_coverage": 0.0,
                "total_duration_minutes": 0.0
            }
        
        completed = [s for s in sessions if s.end_time is not None]
        
        # Calculate average coverage
        coverages = [s.concept_coverage for s in completed if s.concept_coverage is not None]
        avg_coverage = sum(coverages) / len(coverages) if coverages else 0.0
        
        # Calculate total duration
        total_duration = 0.0
        for s in completed:
            if s.start_time and s.end_time:
                duration = (s.end_time - s.start_time).total_seconds() / 60
                total_duration += duration
        
        return {
            "total_sessions": len(sessions),
            "completed_sessions": len(completed),
            "average_coverage": avg_coverage,
            "total_duration_minutes": total_duration
        }
