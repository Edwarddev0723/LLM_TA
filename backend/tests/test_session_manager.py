"""
Unit tests for the Session Manager module.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch

from backend.services.session_manager import (
    SessionManager,
    SessionData,
    ConceptCoverageResult,
)
from backend.services.fsm_controller import FSMState
from backend.models.session import Session as SessionModel, ConversationTurn as ConversationTurnModel
from backend.models.question import Question
from backend.models.knowledge import KnowledgeNode


class TestConceptCoverageResult:
    """Tests for ConceptCoverageResult dataclass."""
    
    def test_creation(self):
        """Test creating ConceptCoverageResult."""
        result = ConceptCoverageResult(
            coverage_ratio=0.75,
            covered_concepts=["c1", "c2", "c3"],
            missing_concepts=["c4"],
            total_required=4,
            total_covered=3
        )
        
        assert result.coverage_ratio == 0.75
        assert len(result.covered_concepts) == 3
        assert len(result.missing_concepts) == 1
        assert result.total_required == 4
        assert result.total_covered == 3


class TestSessionData:
    """Tests for SessionData dataclass."""
    
    def test_creation(self):
        """Test creating SessionData."""
        now = datetime.now(timezone.utc)
        data = SessionData(
            id="session-1",
            student_id="student-1",
            question_id="question-1",
            start_time=now
        )
        
        assert data.id == "session-1"
        assert data.student_id == "student-1"
        assert data.question_id == "question-1"
        assert data.start_time == now
        assert data.end_time is None
        assert data.final_state is None
        assert data.concept_coverage == 0.0
        assert data.conversation_turns == []
    
    def test_with_all_fields(self):
        """Test SessionData with all fields."""
        now = datetime.now(timezone.utc)
        data = SessionData(
            id="session-1",
            student_id="student-1",
            question_id="question-1",
            start_time=now,
            end_time=now,
            final_state="CONSOLIDATING",
            concept_coverage=0.95,
            conversation_turns=[{"turn": 1}]
        )
        
        assert data.end_time == now
        assert data.final_state == "CONSOLIDATING"
        assert data.concept_coverage == 0.95
        assert len(data.conversation_turns) == 1


class TestSessionManager:
    """Tests for SessionManager class."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = MagicMock()
        return db
    
    @pytest.fixture
    def session_manager(self, mock_db):
        """Create a SessionManager with mock database."""
        return SessionManager(db=mock_db)
    
    def test_create_session(self, session_manager, mock_db):
        """Test creating a new session."""
        # Configure mock
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        
        session = session_manager.create_session(
            student_id="student-1",
            question_id="question-1"
        )
        
        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # Verify session properties
        assert session.student_id == "student-1"
        assert session.question_id == "question-1"
        assert session.concept_coverage == 0.0
    
    def test_create_session_with_custom_id(self, session_manager, mock_db):
        """Test creating a session with custom ID."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        
        session = session_manager.create_session(
            student_id="student-1",
            question_id="question-1",
            session_id="custom-session-id"
        )
        
        assert session.id == "custom-session-id"
    
    def test_get_session(self, session_manager, mock_db):
        """Test getting a session by ID."""
        mock_session = SessionModel(
            id="session-1",
            student_id="student-1",
            question_id="question-1",
            start_time=datetime.now(timezone.utc)
        )
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_session
        mock_db.query.return_value = mock_query
        
        session = session_manager.get_session("session-1")
        
        assert session is not None
        assert session.id == "session-1"
    
    def test_get_session_not_found(self, session_manager, mock_db):
        """Test getting a non-existent session."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        session = session_manager.get_session("non-existent")
        
        assert session is None
    
    def test_end_session(self, session_manager, mock_db):
        """Test ending a session."""
        mock_session = SessionModel(
            id="session-1",
            student_id="student-1",
            question_id="question-1",
            start_time=datetime.now(timezone.utc)
        )
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_session
        mock_db.query.return_value = mock_query
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        
        result = session_manager.end_session(
            session_id="session-1",
            final_state=FSMState.CONSOLIDATING,
            concept_coverage=0.95
        )
        
        assert result is not None
        assert result.final_state == "CONSOLIDATING"
        assert result.concept_coverage == 0.95
        assert result.end_time is not None
    
    def test_end_session_not_found(self, session_manager, mock_db):
        """Test ending a non-existent session."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        result = session_manager.end_session(
            session_id="non-existent",
            final_state=FSMState.IDLE,
            concept_coverage=0.0
        )
        
        assert result is None
    
    def test_add_conversation_turn(self, session_manager, mock_db):
        """Test adding a conversation turn."""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        
        turn = session_manager.add_conversation_turn(
            session_id="session-1",
            turn_number=1,
            speaker="STUDENT",
            content="Hello",
            fsm_state=FSMState.LISTENING
        )
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        assert turn.session_id == "session-1"
        assert turn.turn_number == 1
        assert turn.speaker == "STUDENT"
        assert turn.content == "Hello"
        assert turn.fsm_state == "LISTENING"
    
    def test_get_conversation_history(self, session_manager, mock_db):
        """Test getting conversation history."""
        mock_turns = [
            ConversationTurnModel(
                id="turn-1",
                session_id="session-1",
                turn_number=1,
                speaker="STUDENT",
                content="Hello",
                fsm_state="LISTENING",
                timestamp=datetime.now(timezone.utc)
            ),
            ConversationTurnModel(
                id="turn-2",
                session_id="session-1",
                turn_number=2,
                speaker="TUTOR",
                content="Hi there!",
                fsm_state="LISTENING",
                timestamp=datetime.now(timezone.utc)
            )
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = mock_turns
        mock_db.query.return_value = mock_query
        
        history = session_manager.get_conversation_history("session-1")
        
        assert len(history) == 2
        assert history[0].turn_number == 1
        assert history[1].turn_number == 2
    
    def test_calculate_concept_coverage_no_question(self, session_manager, mock_db):
        """Test coverage calculation when question not found."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        result = session_manager.calculate_concept_coverage(
            question_id="non-existent",
            covered_concepts=["c1", "c2"]
        )
        
        assert result.coverage_ratio == 1.0
        assert result.total_required == 0
    
    def test_calculate_concept_coverage_no_required_concepts(self, session_manager, mock_db):
        """Test coverage calculation when no concepts required."""
        mock_question = Question(
            id="q1",
            content="Test",
            type="CALCULATION",
            subject="Math",
            unit="Algebra",
            difficulty=1,
            standard_solution="Answer"
        )
        mock_question.knowledge_nodes = []
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_question
        mock_db.query.return_value = mock_query
        
        result = session_manager.calculate_concept_coverage(
            question_id="q1",
            covered_concepts=["c1"]
        )
        
        assert result.coverage_ratio == 1.0
        assert result.total_required == 0
    
    def test_calculate_concept_coverage_partial(self, session_manager, mock_db):
        """Test partial concept coverage calculation."""
        # Create mock knowledge nodes
        node1 = MagicMock()
        node1.id = "concept-1"
        node2 = MagicMock()
        node2.id = "concept-2"
        node3 = MagicMock()
        node3.id = "concept-3"
        node4 = MagicMock()
        node4.id = "concept-4"
        
        mock_question = Question(
            id="q1",
            content="Test",
            type="CALCULATION",
            subject="Math",
            unit="Algebra",
            difficulty=1,
            standard_solution="Answer"
        )
        mock_question.knowledge_nodes = [node1, node2, node3, node4]
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_question
        mock_db.query.return_value = mock_query
        
        result = session_manager.calculate_concept_coverage(
            question_id="q1",
            covered_concepts=["concept-1", "concept-2", "concept-5"]  # concept-5 is extra
        )
        
        assert result.coverage_ratio == 0.5  # 2 out of 4
        assert result.total_required == 4
        assert result.total_covered == 2
        assert "concept-3" in result.missing_concepts
        assert "concept-4" in result.missing_concepts
    
    def test_update_concept_coverage(self, session_manager, mock_db):
        """Test updating concept coverage."""
        mock_session = SessionModel(
            id="session-1",
            student_id="student-1",
            question_id="question-1",
            start_time=datetime.now(timezone.utc),
            concept_coverage=0.5
        )
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_session
        mock_db.query.return_value = mock_query
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        
        result = session_manager.update_concept_coverage(
            session_id="session-1",
            coverage=0.9
        )
        
        assert result is not None
        assert result.concept_coverage == 0.9
    
    def test_get_student_sessions(self, session_manager, mock_db):
        """Test getting sessions for a student."""
        mock_sessions = [
            SessionModel(
                id="session-1",
                student_id="student-1",
                question_id="q1",
                start_time=datetime.now(timezone.utc)
            ),
            SessionModel(
                id="session-2",
                student_id="student-1",
                question_id="q2",
                start_time=datetime.now(timezone.utc)
            )
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_sessions
        mock_db.query.return_value = mock_query
        
        sessions = session_manager.get_student_sessions("student-1")
        
        assert len(sessions) == 2
    
    def test_get_active_sessions(self, session_manager, mock_db):
        """Test getting active sessions."""
        mock_sessions = [
            SessionModel(
                id="session-1",
                student_id="student-1",
                question_id="q1",
                start_time=datetime.now(timezone.utc),
                end_time=None
            )
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_sessions
        mock_db.query.return_value = mock_query
        
        sessions = session_manager.get_active_sessions()
        
        assert len(sessions) == 1
    
    def test_delete_session(self, session_manager, mock_db):
        """Test deleting a session."""
        mock_session = SessionModel(
            id="session-1",
            student_id="student-1",
            question_id="q1",
            start_time=datetime.now(timezone.utc)
        )
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_session
        mock_query.filter.return_value.delete.return_value = None
        mock_db.query.return_value = mock_query
        mock_db.delete = MagicMock()
        mock_db.commit = MagicMock()
        
        result = session_manager.delete_session("session-1")
        
        assert result is True
        mock_db.delete.assert_called_once_with(mock_session)
    
    def test_delete_session_not_found(self, session_manager, mock_db):
        """Test deleting a non-existent session."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        result = session_manager.delete_session("non-existent")
        
        assert result is False
    
    def test_get_session_statistics_no_sessions(self, session_manager, mock_db):
        """Test getting statistics when no sessions exist."""
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        
        stats = session_manager.get_session_statistics("student-1")
        
        assert stats["total_sessions"] == 0
        assert stats["completed_sessions"] == 0
        assert stats["average_coverage"] == 0.0
        assert stats["total_duration_minutes"] == 0.0
    
    def test_get_session_statistics_with_sessions(self, session_manager, mock_db):
        """Test getting statistics with sessions."""
        now = datetime.now(timezone.utc)
        from datetime import timedelta
        
        mock_sessions = [
            SessionModel(
                id="session-1",
                student_id="student-1",
                question_id="q1",
                start_time=now - timedelta(minutes=30),
                end_time=now - timedelta(minutes=20),
                concept_coverage=0.8
            ),
            SessionModel(
                id="session-2",
                student_id="student-1",
                question_id="q2",
                start_time=now - timedelta(minutes=15),
                end_time=now - timedelta(minutes=5),
                concept_coverage=0.9
            ),
            SessionModel(
                id="session-3",
                student_id="student-1",
                question_id="q3",
                start_time=now,
                end_time=None,  # Active session
                concept_coverage=None
            )
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_sessions
        mock_db.query.return_value = mock_query
        
        stats = session_manager.get_session_statistics("student-1")
        
        assert stats["total_sessions"] == 3
        assert stats["completed_sessions"] == 2
        assert abs(stats["average_coverage"] - 0.85) < 0.001  # (0.8 + 0.9) / 2
        assert stats["total_duration_minutes"] == 20.0  # 10 + 10 minutes
