"""
Unit tests for the Dialog Engine module.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from backend.services.dialog_engine import (
    DialogEngine,
    TutoringSession,
    StudentInput,
    TutorResponse,
    ResponseType,
    AudioFeatures,
    ConversationTurn,
    SessionState,
    SessionSummary,
)
from backend.services.fsm_controller import FSMController, FSMState, FSMEvent, FSMEventType
from backend.services.rag_module import RAGModule, RetrievalResult, RetrievedDocument, ContentType
from backend.services.llm_client import OllamaClient, LLMResponse
from backend.services.hint_controller import HintController, HintLevel


class TestTutoringSession:
    """Tests for TutoringSession class."""
    
    def test_session_creation(self):
        """Test creating a new tutoring session."""
        session = TutoringSession(
            session_id="test-session-1",
            question_id="q1",
            student_id="s1",
            question_content="What is 2+2?",
            standard_solution="4",
            required_concepts=["addition", "arithmetic"]
        )
        
        assert session.id == "test-session-1"
        assert session.question_id == "q1"
        assert session.student_id == "s1"
        assert session.question_content == "What is 2+2?"
        assert session.standard_solution == "4"
        assert session.required_concepts == ["addition", "arithmetic"]
        assert session.covered_concepts == []
        assert session.conversation_history == []
        assert session.is_active is True
        assert session.turn_count == 0
    
    def test_add_turn(self):
        """Test adding conversation turns."""
        session = TutoringSession(
            session_id="test-session-1",
            question_id="q1",
            student_id="s1"
        )
        
        turn = session.add_turn(
            speaker="STUDENT",
            content="I think the answer is 4",
            fsm_state=FSMState.LISTENING
        )
        
        assert turn.turn_number == 1
        assert turn.speaker == "STUDENT"
        assert turn.content == "I think the answer is 4"
        assert turn.fsm_state == FSMState.LISTENING
        assert session.turn_count == 1
        assert len(session.conversation_history) == 1
    
    def test_get_conversation_as_dicts(self):
        """Test getting conversation history as dictionaries."""
        session = TutoringSession(
            session_id="test-session-1",
            question_id="q1",
            student_id="s1"
        )
        
        session.add_turn("STUDENT", "Hello", FSMState.LISTENING)
        session.add_turn("TUTOR", "Hi there!", FSMState.LISTENING)
        
        history = session.get_conversation_as_dicts()
        
        assert len(history) == 2
        assert history[0] == {"speaker": "STUDENT", "content": "Hello"}
        assert history[1] == {"speaker": "TUTOR", "content": "Hi there!"}
    
    def test_update_covered_concepts(self):
        """Test updating covered concepts."""
        session = TutoringSession(
            session_id="test-session-1",
            question_id="q1",
            student_id="s1",
            required_concepts=["addition", "subtraction", "multiplication"]
        )
        
        session.update_covered_concepts(["addition"])
        assert session.covered_concepts == ["addition"]
        
        # Adding same concept again should not duplicate
        session.update_covered_concepts(["addition", "subtraction"])
        assert session.covered_concepts == ["addition", "subtraction"]
    
    def test_calculate_concept_coverage(self):
        """Test concept coverage calculation."""
        session = TutoringSession(
            session_id="test-session-1",
            question_id="q1",
            student_id="s1",
            required_concepts=["addition", "subtraction", "multiplication", "division"]
        )
        
        assert session.calculate_concept_coverage() == 0.0
        
        session.update_covered_concepts(["addition", "subtraction"])
        assert session.calculate_concept_coverage() == 0.5
        
        session.update_covered_concepts(["multiplication", "division"])
        assert session.calculate_concept_coverage() == 1.0
    
    def test_calculate_concept_coverage_no_required(self):
        """Test concept coverage when no concepts are required."""
        session = TutoringSession(
            session_id="test-session-1",
            question_id="q1",
            student_id="s1",
            required_concepts=[]
        )
        
        # No required concepts means full coverage
        assert session.calculate_concept_coverage() == 1.0
    
    def test_end_session(self):
        """Test ending a session."""
        session = TutoringSession(
            session_id="test-session-1",
            question_id="q1",
            student_id="s1"
        )
        
        assert session.is_active is True
        assert session.end_time is None
        
        session.end()
        
        assert session.is_active is False
        assert session.end_time is not None
    
    def test_session_duration(self):
        """Test session duration calculation."""
        session = TutoringSession(
            session_id="test-session-1",
            question_id="q1",
            student_id="s1"
        )
        
        # Duration should be positive
        assert session.duration >= 0
        
        session.end()
        duration = session.duration
        assert duration >= 0



class TestDialogEngine:
    """Tests for DialogEngine class."""
    
    @pytest.fixture
    def mock_fsm(self):
        """Create a mock FSM controller."""
        fsm = Mock(spec=FSMController)
        fsm.get_current_state.return_value = FSMState.LISTENING
        fsm.process_event.return_value = FSMState.LISTENING
        return fsm
    
    @pytest.fixture
    def mock_rag(self):
        """Create a mock RAG module."""
        rag = Mock(spec=RAGModule)
        rag.retrieve.return_value = RetrievalResult(documents=[], total_found=0)
        return rag
    
    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM client."""
        llm = Mock(spec=OllamaClient)
        llm.generate.return_value = LLMResponse(
            text='{"logic_complete": true, "logic_gap": false, "logic_error": false, "covered_concepts": ["addition"], "missing_concepts": [], "feedback": "Good job!"}',
            model="test",
            total_duration_ms=100
        )
        return llm
    
    @pytest.fixture
    def mock_hint_controller(self):
        """Create a mock hint controller."""
        hint = Mock(spec=HintController)
        hint.request_hint.return_value = HintLevel.LEVEL_1
        hint.get_hint_count.return_value = 0
        hint.get_session_hints.return_value = []
        return hint
    
    @pytest.fixture
    def dialog_engine(self, mock_fsm, mock_rag, mock_llm, mock_hint_controller):
        """Create a dialog engine with mocked dependencies."""
        return DialogEngine(
            fsm_controller=mock_fsm,
            rag_module=mock_rag,
            llm_client=mock_llm,
            hint_controller=mock_hint_controller
        )
    
    def test_start_session(self, dialog_engine, mock_fsm, mock_hint_controller):
        """Test starting a new session."""
        session = dialog_engine.start_session(
            question_id="q1",
            student_id="s1",
            question_content="What is 2+2?",
            standard_solution="4",
            required_concepts=["addition"]
        )
        
        assert session is not None
        assert session.question_id == "q1"
        assert session.student_id == "s1"
        assert session.is_active is True
        
        # Verify FSM was reset and started
        mock_fsm.reset.assert_called_once()
        mock_fsm.process_event.assert_called()
        
        # Verify hint controller was initialized
        mock_hint_controller.start_session.assert_called_once()
    
    def test_process_student_input(self, dialog_engine, mock_fsm, mock_llm):
        """Test processing student input."""
        # Start a session first
        session = dialog_engine.start_session(
            question_id="q1",
            student_id="s1",
            question_content="What is 2+2?",
            required_concepts=["addition"]
        )
        
        # Process student input
        input_data = StudentInput(
            session_id=session.id,
            text="I think the answer is 4 because 2 plus 2 equals 4"
        )
        
        response = dialog_engine.process_student_input(input_data)
        
        assert response is not None
        assert isinstance(response, TutorResponse)
        assert response.text is not None
        assert response.response_type is not None
    
    def test_process_student_input_invalid_session(self, dialog_engine):
        """Test processing input for non-existent session."""
        input_data = StudentInput(
            session_id="non-existent-session",
            text="Hello"
        )
        
        response = dialog_engine.process_student_input(input_data)
        
        assert response.response_type == ResponseType.ACKNOWLEDGE
        assert "找不到" in response.text
    
    def test_hint_request_detection(self, dialog_engine):
        """Test detection of hint requests."""
        # Test various hint request phrases
        assert dialog_engine._is_hint_request("給我提示") is True
        assert dialog_engine._is_hint_request("我不知道怎麼做") is True
        assert dialog_engine._is_hint_request("幫幫我") is True
        assert dialog_engine._is_hint_request("我卡住了") is True
        assert dialog_engine._is_hint_request("hint please") is True
        
        # Test non-hint requests
        assert dialog_engine._is_hint_request("答案是4") is False
        assert dialog_engine._is_hint_request("我覺得應該這樣做") is False
    
    def test_handle_hint_request(self, dialog_engine, mock_fsm, mock_hint_controller, mock_llm):
        """Test handling hint requests."""
        # Configure mock for hint response
        mock_llm.generate.return_value = LLMResponse(
            text="試著想想看，2加2等於什麼？",
            model="test",
            total_duration_ms=100
        )
        mock_fsm.process_event.return_value = FSMState.HINTING
        
        # Start a session
        session = dialog_engine.start_session(
            question_id="q1",
            student_id="s1",
            question_content="What is 2+2?",
            required_concepts=["addition"]
        )
        
        # Request a hint
        input_data = StudentInput(
            session_id=session.id,
            text="給我提示"
        )
        
        response = dialog_engine.process_student_input(input_data)
        
        assert response.response_type == ResponseType.HINT
        assert response.hint_level is not None
        mock_hint_controller.request_hint.assert_called()
    
    def test_end_session(self, dialog_engine, mock_fsm, mock_hint_controller):
        """Test ending a session."""
        # Start a session
        session = dialog_engine.start_session(
            question_id="q1",
            student_id="s1",
            required_concepts=["addition"]
        )
        
        # End the session
        summary = dialog_engine.end_session(session.id)
        
        assert summary is not None
        assert isinstance(summary, SessionSummary)
        assert summary.session_id == session.id
        assert summary.duration >= 0
        assert summary.total_turns >= 0
    
    def test_end_session_invalid(self, dialog_engine):
        """Test ending a non-existent session."""
        summary = dialog_engine.end_session("non-existent-session")
        
        assert summary.session_id == "non-existent-session"
        assert summary.duration == 0
        assert summary.total_turns == 0
    
    def test_get_session_state(self, dialog_engine, mock_fsm, mock_hint_controller):
        """Test getting session state."""
        mock_hint_controller.get_hint_count.return_value = 2
        
        # Start a session
        session = dialog_engine.start_session(
            question_id="q1",
            student_id="s1",
            required_concepts=["addition"]
        )
        
        state = dialog_engine.get_session_state(session.id)
        
        assert state is not None
        assert isinstance(state, SessionState)
        assert state.session_id == session.id
        assert state.question_id == "q1"
        assert state.student_id == "s1"
        assert state.is_active is True
    
    def test_get_session_state_invalid(self, dialog_engine):
        """Test getting state for non-existent session."""
        state = dialog_engine.get_session_state("non-existent-session")
        assert state is None
    
    def test_handle_silence(self, dialog_engine, mock_fsm, mock_llm):
        """Test handling silence detection."""
        # Configure FSM to transition to HINTING on silence
        mock_fsm.process_event.return_value = FSMState.HINTING
        mock_llm.generate.return_value = LLMResponse(
            text="需要一些提示嗎？",
            model="test",
            total_duration_ms=100
        )
        
        # Start a session
        session = dialog_engine.start_session(
            question_id="q1",
            student_id="s1"
        )
        
        # Simulate silence
        response = dialog_engine.handle_silence(session.id, silence_duration=10.0)
        
        # Should get a hint response
        assert response is not None
        assert response.response_type == ResponseType.HINT
    
    def test_handle_silence_no_transition(self, dialog_engine, mock_fsm):
        """Test silence handling when no transition occurs."""
        # Configure FSM to stay in LISTENING
        mock_fsm.process_event.return_value = FSMState.LISTENING
        
        # Start a session
        session = dialog_engine.start_session(
            question_id="q1",
            student_id="s1"
        )
        
        # Simulate short silence (below threshold)
        response = dialog_engine.handle_silence(session.id, silence_duration=2.0)
        
        # Should not get a response
        assert response is None
    
    def test_get_active_sessions(self, dialog_engine):
        """Test getting list of active sessions."""
        # Initially no sessions
        assert dialog_engine.get_active_sessions() == []
        
        # Start some sessions
        session1 = dialog_engine.start_session(question_id="q1", student_id="s1")
        session2 = dialog_engine.start_session(question_id="q2", student_id="s2")
        
        active = dialog_engine.get_active_sessions()
        assert len(active) == 2
        assert session1.id in active
        assert session2.id in active
    
    def test_cleanup_session(self, dialog_engine):
        """Test cleaning up a session."""
        # Start a session
        session = dialog_engine.start_session(question_id="q1", student_id="s1")
        
        # Cleanup
        result = dialog_engine.cleanup_session(session.id)
        assert result is True
        
        # Session should be gone
        assert dialog_engine.get_session_state(session.id) is None
        
        # Cleanup non-existent session
        result = dialog_engine.cleanup_session("non-existent")
        assert result is False


class TestResponseType:
    """Tests for ResponseType enum."""
    
    def test_response_types(self):
        """Test all response types exist."""
        assert ResponseType.PROBE == "PROBE"
        assert ResponseType.HINT == "HINT"
        assert ResponseType.REPAIR == "REPAIR"
        assert ResponseType.CONSOLIDATE == "CONSOLIDATE"
        assert ResponseType.ACKNOWLEDGE == "ACKNOWLEDGE"


class TestAudioFeatures:
    """Tests for AudioFeatures dataclass."""
    
    def test_default_values(self):
        """Test default values for AudioFeatures."""
        features = AudioFeatures()
        
        assert features.duration == 0.0
        assert features.word_count == 0
        assert features.pause_count == 0
        assert features.total_pause_duration == 0.0
    
    def test_custom_values(self):
        """Test custom values for AudioFeatures."""
        features = AudioFeatures(
            duration=60.0,
            word_count=100,
            pause_count=5,
            total_pause_duration=10.0
        )
        
        assert features.duration == 60.0
        assert features.word_count == 100
        assert features.pause_count == 5
        assert features.total_pause_duration == 10.0


class TestStudentInput:
    """Tests for StudentInput dataclass."""
    
    def test_creation(self):
        """Test creating StudentInput."""
        input_data = StudentInput(
            session_id="test-session",
            text="Hello, I need help"
        )
        
        assert input_data.session_id == "test-session"
        assert input_data.text == "Hello, I need help"
        assert input_data.audio_features is None
        assert input_data.timestamp > 0
    
    def test_with_audio_features(self):
        """Test StudentInput with audio features."""
        features = AudioFeatures(duration=30.0, word_count=50)
        input_data = StudentInput(
            session_id="test-session",
            text="My explanation",
            audio_features=features
        )
        
        assert input_data.audio_features is not None
        assert input_data.audio_features.duration == 30.0


class TestTutorResponse:
    """Tests for TutorResponse dataclass."""
    
    def test_creation(self):
        """Test creating TutorResponse."""
        response = TutorResponse(
            text="Good thinking!",
            response_type=ResponseType.ACKNOWLEDGE
        )
        
        assert response.text == "Good thinking!"
        assert response.response_type == ResponseType.ACKNOWLEDGE
        assert response.hint_level is None
        assert response.related_concepts == []
        assert response.suggested_next_step is None
    
    def test_with_all_fields(self):
        """Test TutorResponse with all fields."""
        response = TutorResponse(
            text="Here's a hint...",
            response_type=ResponseType.HINT,
            hint_level=HintLevel.LEVEL_2,
            related_concepts=["addition", "arithmetic"],
            suggested_next_step="Think about the basic operation",
            fsm_state=FSMState.HINTING
        )
        
        assert response.hint_level == HintLevel.LEVEL_2
        assert len(response.related_concepts) == 2
        assert response.suggested_next_step is not None
        assert response.fsm_state == FSMState.HINTING
