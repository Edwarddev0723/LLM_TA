"""
Dialog Engine for the AI Math Tutor system.
Integrates FSM Controller, RAG Module, LLM Client, and Hint Controller
to provide a complete tutoring dialog experience.
"""
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from sqlalchemy.orm import Session as DBSession

from backend.services.fsm_controller import (
    FSMController,
    FSMState,
    FSMEvent,
    FSMEventType,
)
from backend.services.rag_module import RAGModule, RetrievalContext, ContentType
from backend.services.llm_client import OllamaClient, LLMConfig
from backend.services.hint_controller import HintController, HintLevel
from backend.services.prompt_builder import PromptBuilder, PromptContext


class ResponseType(str, Enum):
    """Types of tutor responses."""
    PROBE = "PROBE"           # 追問 (Probing question)
    HINT = "HINT"             # 提示
    REPAIR = "REPAIR"         # 修正建議
    CONSOLIDATE = "CONSOLIDATE"  # 總結
    ACKNOWLEDGE = "ACKNOWLEDGE"  # 確認/鼓勵


@dataclass
class AudioFeatures:
    """Audio features from ASR analysis."""
    duration: float = 0.0
    word_count: int = 0
    pause_count: int = 0
    total_pause_duration: float = 0.0


@dataclass
class StudentInput:
    """Input from the student."""
    session_id: str
    text: str
    audio_features: Optional[AudioFeatures] = None
    timestamp: float = field(default_factory=lambda: datetime.utcnow().timestamp())


@dataclass
class TutorResponse:
    """Response from the tutor."""
    text: str
    response_type: ResponseType
    hint_level: Optional[HintLevel] = None
    related_concepts: List[str] = field(default_factory=list)
    suggested_next_step: Optional[str] = None
    fsm_state: Optional[FSMState] = None


@dataclass
class ConversationTurn:
    """A single turn in the conversation."""
    turn_number: int
    speaker: str  # "STUDENT" or "TUTOR"
    content: str
    fsm_state: FSMState
    timestamp: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class SessionState:
    """Current state of a tutoring session."""
    session_id: str
    question_id: str
    student_id: str
    fsm_state: FSMState
    concept_coverage: float
    hints_used: int
    turn_count: int
    start_time: float
    is_active: bool = True


@dataclass
class SessionSummary:
    """Summary of a completed tutoring session."""
    session_id: str
    duration: float
    concepts_covered: List[str]
    concept_coverage: float
    hints_used: List[Dict[str, Any]]
    total_turns: int
    final_state: FSMState



class TutoringSession:
    """
    Represents an active tutoring session.
    Manages conversation history and session state.
    """
    
    def __init__(
        self,
        session_id: str,
        question_id: str,
        student_id: str,
        question_content: str = "",
        standard_solution: str = "",
        required_concepts: Optional[List[str]] = None
    ):
        """
        Initialize a tutoring session.
        
        Args:
            session_id: Unique session identifier
            question_id: ID of the question being worked on
            student_id: ID of the student
            question_content: The question text
            standard_solution: The standard solution for reference
            required_concepts: List of concepts required for this question
        """
        self.id = session_id
        self.question_id = question_id
        self.student_id = student_id
        self.question_content = question_content
        self.standard_solution = standard_solution
        self.required_concepts = required_concepts or []
        self.covered_concepts: List[str] = []
        self.conversation_history: List[ConversationTurn] = []
        self.start_time = datetime.utcnow().timestamp()
        self.end_time: Optional[float] = None
        self.is_active = True
        self._turn_counter = 0
    
    def add_turn(
        self,
        speaker: str,
        content: str,
        fsm_state: FSMState
    ) -> ConversationTurn:
        """
        Add a conversation turn.
        
        Args:
            speaker: "STUDENT" or "TUTOR"
            content: The content of the turn
            fsm_state: Current FSM state
            
        Returns:
            The created ConversationTurn
        """
        self._turn_counter += 1
        turn = ConversationTurn(
            turn_number=self._turn_counter,
            speaker=speaker,
            content=content,
            fsm_state=fsm_state,
            timestamp=datetime.utcnow().timestamp()
        )
        self.conversation_history.append(turn)
        return turn
    
    def get_conversation_as_dicts(self) -> List[Dict[str, str]]:
        """
        Get conversation history as list of dicts for prompt building.
        
        Returns:
            List of conversation turn dictionaries
        """
        return [
            {"speaker": turn.speaker, "content": turn.content}
            for turn in self.conversation_history
        ]
    
    def update_covered_concepts(self, concepts: List[str]) -> None:
        """
        Update the list of covered concepts.
        
        Args:
            concepts: List of newly covered concepts
        """
        for concept in concepts:
            if concept not in self.covered_concepts:
                self.covered_concepts.append(concept)
    
    def calculate_concept_coverage(self) -> float:
        """
        Calculate the concept coverage ratio.
        
        Returns:
            Coverage ratio (0-1)
        """
        if not self.required_concepts:
            return 1.0  # No required concepts means full coverage
        
        covered_count = sum(
            1 for c in self.required_concepts
            if c in self.covered_concepts
        )
        return covered_count / len(self.required_concepts)
    
    @property
    def turn_count(self) -> int:
        """Get the total number of turns."""
        return self._turn_counter
    
    def end(self) -> None:
        """End the session."""
        self.end_time = datetime.utcnow().timestamp()
        self.is_active = False
    
    @property
    def duration(self) -> float:
        """Get session duration in seconds."""
        end = self.end_time or datetime.utcnow().timestamp()
        return end - self.start_time



class DialogEngine:
    """
    Main Dialog Engine for the AI Math Tutor.
    
    Integrates:
    - FSM Controller for dialog flow management
    - RAG Module for knowledge retrieval
    - LLM Client for response generation
    - Hint Controller for progressive hints
    - Prompt Builder for prompt construction
    
    Implements Requirements:
    - 6.2: WHILE FSM 處於 LISTENING 狀態 WHEN 學生完成一段陳述 THEN THE AI_Tutor SHALL 分析邏輯完整性
    - 6.6: WHILE FSM 處於 HINTING 狀態 THEN THE AI_Tutor SHALL 提供最小充分提示
    - 6.9: WHILE FSM 處於 CONSOLIDATING 狀態 THEN THE AI_Tutor SHALL 生成觀念總結與遷移練習建議
    """
    
    def __init__(
        self,
        fsm_controller: Optional[FSMController] = None,
        rag_module: Optional[RAGModule] = None,
        llm_client: Optional[OllamaClient] = None,
        hint_controller: Optional[HintController] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        db: Optional[DBSession] = None
    ):
        """
        Initialize the Dialog Engine.
        
        Args:
            fsm_controller: FSM Controller instance (creates default if None)
            rag_module: RAG Module instance (creates default if None)
            llm_client: LLM Client instance (creates default if None)
            hint_controller: Hint Controller instance (creates default if None)
            prompt_builder: Prompt Builder instance (creates default if None)
            db: Optional database session for persistence
        """
        self._fsm = fsm_controller or FSMController()
        self._rag = rag_module or RAGModule()
        self._llm = llm_client or OllamaClient()
        self._hint_controller = hint_controller or HintController(db=db)
        self._prompt_builder = prompt_builder or PromptBuilder()
        self._db = db
        
        # Active sessions storage
        self._sessions: Dict[str, TutoringSession] = {}
    
    def start_session(
        self,
        question_id: str,
        student_id: str,
        question_content: str = "",
        standard_solution: str = "",
        required_concepts: Optional[List[str]] = None
    ) -> TutoringSession:
        """
        Start a new tutoring session.
        
        Args:
            question_id: ID of the question to work on
            student_id: ID of the student
            question_content: The question text
            standard_solution: The standard solution
            required_concepts: List of concepts required for this question
            
        Returns:
            The created TutoringSession
        """
        session_id = str(uuid.uuid4())
        
        # Create session
        session = TutoringSession(
            session_id=session_id,
            question_id=question_id,
            student_id=student_id,
            question_content=question_content,
            standard_solution=standard_solution,
            required_concepts=required_concepts
        )
        
        # Store session
        self._sessions[session_id] = session
        
        # Initialize FSM
        self._fsm.reset()
        start_event = FSMEvent(
            type=FSMEventType.SESSION_START,
            payload={"session_id": session_id}
        )
        self._fsm.process_event(start_event)
        
        # Initialize hint controller for this session
        self._hint_controller.start_session(
            session_id=session_id,
            concept=required_concepts[0] if required_concepts else None
        )
        
        return session
    
    def process_student_input(self, input_data: StudentInput) -> TutorResponse:
        """
        Process student input and generate a tutor response.
        
        This method:
        1. Records the student input
        2. Retrieves relevant context via RAG
        3. Analyzes the input using LLM
        4. Updates FSM state based on analysis
        5. Generates appropriate response based on FSM state
        
        Args:
            input_data: The student's input
            
        Returns:
            TutorResponse with the tutor's response
        """
        session = self._sessions.get(input_data.session_id)
        if not session:
            return TutorResponse(
                text="抱歉，找不到此會話。請重新開始。",
                response_type=ResponseType.ACKNOWLEDGE,
                fsm_state=FSMState.IDLE
            )
        
        # Record student input
        session.add_turn(
            speaker="STUDENT",
            content=input_data.text,
            fsm_state=self._fsm.get_current_state()
        )
        
        # Check for hint request
        if self._is_hint_request(input_data.text):
            return self._handle_hint_request(session, input_data)
        
        # Process through FSM
        student_event = FSMEvent(
            type=FSMEventType.STUDENT_INPUT,
            payload={"text": input_data.text}
        )
        self._fsm.process_event(student_event)
        
        # Retrieve RAG context
        rag_result = self._retrieve_context(
            query=input_data.text,
            session=session
        )
        
        # Analyze student input
        analysis = self._analyze_student_input(
            input_data=input_data,
            session=session,
            rag_documents=rag_result
        )
        
        # Update FSM based on analysis
        analysis_event = FSMEvent(
            type=FSMEventType.ANALYSIS_RESULT,
            payload=analysis
        )
        new_state = self._fsm.process_event(analysis_event)
        
        # Update covered concepts
        if analysis.get("covered_concepts"):
            session.update_covered_concepts(analysis["covered_concepts"])
        
        # Generate response based on new state
        response = self._generate_response(
            session=session,
            analysis=analysis,
            rag_documents=rag_result
        )
        
        # Record tutor response
        session.add_turn(
            speaker="TUTOR",
            content=response.text,
            fsm_state=new_state
        )
        
        return response
    
    def end_session(self, session_id: str) -> SessionSummary:
        """
        End a tutoring session and generate summary.
        
        Args:
            session_id: The session ID to end
            
        Returns:
            SessionSummary with session statistics
        """
        session = self._sessions.get(session_id)
        if not session:
            return SessionSummary(
                session_id=session_id,
                duration=0,
                concepts_covered=[],
                concept_coverage=0,
                hints_used=[],
                total_turns=0,
                final_state=FSMState.IDLE
            )
        
        # End the session
        session.end()
        
        # Reset FSM
        end_event = FSMEvent(
            type=FSMEventType.SESSION_END,
            payload={"session_id": session_id}
        )
        final_state = self._fsm.process_event(end_event)
        
        # Get hint usage
        hint_records = self._hint_controller.get_session_hints(session_id)
        hints_used = [
            {
                "level": h.level.value,
                "concept": h.concept,
                "timestamp": h.timestamp
            }
            for h in hint_records
        ]
        
        # Create summary
        summary = SessionSummary(
            session_id=session_id,
            duration=session.duration,
            concepts_covered=session.covered_concepts.copy(),
            concept_coverage=session.calculate_concept_coverage(),
            hints_used=hints_used,
            total_turns=session.turn_count,
            final_state=final_state
        )
        
        return summary
    
    def get_session_state(self, session_id: str) -> Optional[SessionState]:
        """
        Get the current state of a session.
        
        Args:
            session_id: The session ID
            
        Returns:
            SessionState or None if session not found
        """
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        hint_count = self._hint_controller.get_hint_count(session_id)
        
        return SessionState(
            session_id=session_id,
            question_id=session.question_id,
            student_id=session.student_id,
            fsm_state=self._fsm.get_current_state(),
            concept_coverage=session.calculate_concept_coverage(),
            hints_used=hint_count,
            turn_count=session.turn_count,
            start_time=session.start_time,
            is_active=session.is_active
        )
    
    def _is_hint_request(self, text: str) -> bool:
        """
        Check if the student is requesting a hint.
        
        Args:
            text: Student's input text
            
        Returns:
            True if this is a hint request
        """
        hint_keywords = [
            "給我提示", "提示", "幫幫我", "不知道", "不會",
            "hint", "help", "卡住", "想不出來"
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in hint_keywords)
    
    def _handle_hint_request(
        self,
        session: TutoringSession,
        input_data: StudentInput
    ) -> TutorResponse:
        """
        Handle a hint request from the student.
        
        Args:
            session: The current session
            input_data: The student's input
            
        Returns:
            TutorResponse with the hint
        """
        # Transition FSM to HINTING state
        hint_event = FSMEvent(
            type=FSMEventType.HINT_REQUEST,
            payload={"text": input_data.text}
        )
        self._fsm.process_event(hint_event)
        
        # Get hint level
        hint_level = self._hint_controller.request_hint(
            concept=session.required_concepts[0] if session.required_concepts else None
        )
        
        # Retrieve RAG context for hints
        rag_result = self._retrieve_context(
            query=session.question_content,
            session=session
        )
        
        # Build prompt context
        prompt_context = PromptContext(
            question_content=session.question_content,
            student_input=input_data.text,
            conversation_history=session.get_conversation_as_dicts(),
            rag_documents=rag_result,
            current_concept=session.required_concepts[0] if session.required_concepts else None,
            hint_level=hint_level,
            concept_coverage=session.calculate_concept_coverage()
        )
        
        # Generate hint response
        system_prompt, user_prompt = self._prompt_builder.build_full_prompt(
            state=FSMState.HINTING,
            context=prompt_context
        )
        
        llm_response = self._llm.generate(
            prompt=user_prompt,
            system=system_prompt
        )
        
        # Transition back to LISTENING
        analysis_event = FSMEvent(
            type=FSMEventType.ANALYSIS_RESULT,
            payload={"continue_listening": True}
        )
        new_state = self._fsm.process_event(analysis_event)
        
        response = TutorResponse(
            text=llm_response.text,
            response_type=ResponseType.HINT,
            hint_level=hint_level,
            related_concepts=session.required_concepts[:3] if session.required_concepts else [],
            fsm_state=new_state
        )
        
        # Record tutor response
        session.add_turn(
            speaker="TUTOR",
            content=response.text,
            fsm_state=new_state
        )
        
        return response
    
    def _retrieve_context(
        self,
        query: str,
        session: TutoringSession
    ) -> List:
        """
        Retrieve relevant context using RAG.
        
        Args:
            query: The search query
            session: The current session
            
        Returns:
            List of retrieved documents
        """
        context = RetrievalContext(
            question_id=session.question_id,
            knowledge_nodes=session.required_concepts,
            max_results=5,
            min_similarity=0.3
        )
        
        result = self._rag.retrieve(query, context)
        return result.documents
    
    def _analyze_student_input(
        self,
        input_data: StudentInput,
        session: TutoringSession,
        rag_documents: List
    ) -> Dict[str, Any]:
        """
        Analyze student input using LLM.
        
        Args:
            input_data: The student's input
            session: The current session
            rag_documents: Retrieved RAG documents
            
        Returns:
            Analysis result dictionary
        """
        # Build analysis prompt
        system_prompt, user_prompt = self._prompt_builder.get_analysis_prompt(
            student_input=input_data.text,
            question_content=session.question_content,
            standard_solution=session.standard_solution
        )
        
        # Get LLM analysis
        llm_response = self._llm.generate(
            prompt=user_prompt,
            system=system_prompt
        )
        
        # Parse JSON response
        try:
            analysis = json.loads(llm_response.text)
        except json.JSONDecodeError:
            # Default analysis if parsing fails
            analysis = {
                "logic_complete": False,
                "logic_gap": False,
                "logic_error": False,
                "error_type": None,
                "missing_concepts": [],
                "covered_concepts": [],
                "feedback": llm_response.text
            }
        
        # Calculate coverage
        covered = analysis.get("covered_concepts", [])
        session.update_covered_concepts(covered)
        analysis["coverage"] = session.calculate_concept_coverage()
        
        return analysis
    
    def _generate_response(
        self,
        session: TutoringSession,
        analysis: Dict[str, Any],
        rag_documents: List
    ) -> TutorResponse:
        """
        Generate tutor response based on FSM state and analysis.
        
        Args:
            session: The current session
            analysis: The analysis result
            rag_documents: Retrieved RAG documents
            
        Returns:
            TutorResponse
        """
        current_state = self._fsm.get_current_state()
        
        # Determine response type based on state
        response_type_map = {
            FSMState.PROBING: ResponseType.PROBE,
            FSMState.HINTING: ResponseType.HINT,
            FSMState.REPAIR: ResponseType.REPAIR,
            FSMState.CONSOLIDATING: ResponseType.CONSOLIDATE,
            FSMState.LISTENING: ResponseType.ACKNOWLEDGE,
            FSMState.ANALYZING: ResponseType.ACKNOWLEDGE,
            FSMState.IDLE: ResponseType.ACKNOWLEDGE,
        }
        response_type = response_type_map.get(current_state, ResponseType.ACKNOWLEDGE)
        
        # Build prompt context
        prompt_context = PromptContext(
            question_content=session.question_content,
            student_input=session.conversation_history[-1].content if session.conversation_history else "",
            conversation_history=session.get_conversation_as_dicts(),
            rag_documents=rag_documents,
            current_concept=session.required_concepts[0] if session.required_concepts else None,
            concept_coverage=session.calculate_concept_coverage()
        )
        
        # Generate response using LLM
        system_prompt, user_prompt = self._prompt_builder.build_full_prompt(
            state=current_state,
            context=prompt_context
        )
        
        llm_response = self._llm.generate(
            prompt=user_prompt,
            system=system_prompt
        )
        
        # Build suggested next step
        suggested_next = None
        if current_state == FSMState.CONSOLIDATING:
            suggested_next = "嘗試相關的延伸題目來鞏固學習"
        elif analysis.get("logic_gap"):
            suggested_next = "思考一下剛才的問題"
        
        return TutorResponse(
            text=llm_response.text,
            response_type=response_type,
            related_concepts=analysis.get("covered_concepts", []),
            suggested_next_step=suggested_next,
            fsm_state=current_state
        )
    
    def handle_silence(
        self,
        session_id: str,
        silence_duration: float
    ) -> Optional[TutorResponse]:
        """
        Handle silence detection during a session.
        
        Args:
            session_id: The session ID
            silence_duration: Duration of silence in seconds
            
        Returns:
            TutorResponse if action needed, None otherwise
        """
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        # Send silence event to FSM
        silence_event = FSMEvent(
            type=FSMEventType.SILENCE_DETECTED,
            payload={"duration": silence_duration}
        )
        new_state = self._fsm.process_event(silence_event)
        
        # If transitioned to HINTING, generate a prompt
        if new_state == FSMState.HINTING:
            # Create a synthetic input for hint handling
            synthetic_input = StudentInput(
                session_id=session_id,
                text="(沉默)"
            )
            return self._handle_hint_request(session, synthetic_input)
        
        return None
    
    def get_active_sessions(self) -> List[str]:
        """
        Get list of active session IDs.
        
        Returns:
            List of active session IDs
        """
        return [
            sid for sid, session in self._sessions.items()
            if session.is_active
        ]
    
    def cleanup_session(self, session_id: str) -> bool:
        """
        Remove a session from memory.
        
        Args:
            session_id: The session ID to remove
            
        Returns:
            True if removed, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
