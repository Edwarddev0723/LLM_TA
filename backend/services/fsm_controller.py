"""
FSM Controller for the AI Math Tutor system.
Manages the finite state machine for dialog flow control.
"""
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Callable, Dict, Any


class FSMState(Enum):
    """FSM states for the tutoring dialog flow."""
    IDLE = 'IDLE'
    LISTENING = 'LISTENING'
    ANALYZING = 'ANALYZING'
    PROBING = 'PROBING'
    HINTING = 'HINTING'
    REPAIR = 'REPAIR'
    CONSOLIDATING = 'CONSOLIDATING'


class FSMEventType(Enum):
    """Types of events that can trigger state transitions."""
    STUDENT_INPUT = 'STUDENT_INPUT'
    SILENCE_DETECTED = 'SILENCE_DETECTED'
    HINT_REQUEST = 'HINT_REQUEST'
    ANALYSIS_RESULT = 'ANALYSIS_RESULT'
    SESSION_START = 'SESSION_START'
    SESSION_END = 'SESSION_END'


class TransitionConditionType(Enum):
    """Types of conditions for state transitions."""
    SILENCE_TIMEOUT = 'SILENCE_TIMEOUT'
    LOGIC_GAP = 'LOGIC_GAP'
    LOGIC_ERROR = 'LOGIC_ERROR'
    COVERAGE_THRESHOLD = 'COVERAGE_THRESHOLD'
    USER_REQUEST = 'USER_REQUEST'
    ANALYSIS_COMPLETE = 'ANALYSIS_COMPLETE'


@dataclass
class FSMEvent:
    """Event that can trigger FSM state transitions."""
    type: FSMEventType
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: datetime.utcnow().timestamp())


@dataclass
class TransitionCondition:
    """Condition for a state transition."""
    type: TransitionConditionType
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FSMTransition:
    """Definition of a state transition."""
    from_state: FSMState
    to_state: FSMState
    condition: TransitionCondition
    action: Optional[Callable[[], None]] = None


@dataclass
class StateTransitionLog:
    """Log entry for a state transition."""
    from_state: FSMState
    to_state: FSMState
    trigger: FSMEvent
    timestamp: float


class FSMController:
    """
    Finite State Machine Controller for managing dialog flow.
    
    Implements the five-stage guidance cycle:
    IDLE -> LISTENING -> ANALYZING -> PROBING/HINTING/REPAIR -> CONSOLIDATING
    """
    
    # Default silence timeout threshold in seconds
    DEFAULT_SILENCE_THRESHOLD = 5.0
    
    # Default concept coverage threshold for consolidation
    DEFAULT_COVERAGE_THRESHOLD = 0.9

    def __init__(
        self,
        silence_threshold: float = DEFAULT_SILENCE_THRESHOLD,
        coverage_threshold: float = DEFAULT_COVERAGE_THRESHOLD
    ):
        """
        Initialize the FSM Controller.
        
        Args:
            silence_threshold: Seconds of silence before transitioning to HINTING
            coverage_threshold: Concept coverage ratio (0-1) for CONSOLIDATING
        """
        self._current_state = FSMState.IDLE
        self._state_history: List[StateTransitionLog] = []
        self._state_change_callbacks: List[Callable[[FSMState, FSMState], None]] = []
        self._silence_threshold = silence_threshold
        self._coverage_threshold = coverage_threshold
        self._transitions = self._build_transitions()

    def _build_transitions(self) -> List[FSMTransition]:
        """Build the list of valid state transitions."""
        return [
            # IDLE -> LISTENING (session start)
            FSMTransition(
                from_state=FSMState.IDLE,
                to_state=FSMState.LISTENING,
                condition=TransitionCondition(
                    type=TransitionConditionType.USER_REQUEST
                )
            ),
            # LISTENING -> ANALYZING (student input received)
            FSMTransition(
                from_state=FSMState.LISTENING,
                to_state=FSMState.ANALYZING,
                condition=TransitionCondition(
                    type=TransitionConditionType.ANALYSIS_COMPLETE
                )
            ),
            # LISTENING -> HINTING (silence timeout)
            FSMTransition(
                from_state=FSMState.LISTENING,
                to_state=FSMState.HINTING,
                condition=TransitionCondition(
                    type=TransitionConditionType.SILENCE_TIMEOUT,
                    params={'threshold': self._silence_threshold}
                )
            ),
            # LISTENING -> HINTING (user requests hint)
            FSMTransition(
                from_state=FSMState.LISTENING,
                to_state=FSMState.HINTING,
                condition=TransitionCondition(
                    type=TransitionConditionType.USER_REQUEST
                )
            ),
            # ANALYZING -> PROBING (logic gap detected)
            FSMTransition(
                from_state=FSMState.ANALYZING,
                to_state=FSMState.PROBING,
                condition=TransitionCondition(
                    type=TransitionConditionType.LOGIC_GAP
                )
            ),
            # ANALYZING -> REPAIR (logic error detected)
            FSMTransition(
                from_state=FSMState.ANALYZING,
                to_state=FSMState.REPAIR,
                condition=TransitionCondition(
                    type=TransitionConditionType.LOGIC_ERROR
                )
            ),
            # ANALYZING -> CONSOLIDATING (coverage threshold met)
            FSMTransition(
                from_state=FSMState.ANALYZING,
                to_state=FSMState.CONSOLIDATING,
                condition=TransitionCondition(
                    type=TransitionConditionType.COVERAGE_THRESHOLD,
                    params={'threshold': self._coverage_threshold}
                )
            ),
            # ANALYZING -> LISTENING (continue listening)
            FSMTransition(
                from_state=FSMState.ANALYZING,
                to_state=FSMState.LISTENING,
                condition=TransitionCondition(
                    type=TransitionConditionType.ANALYSIS_COMPLETE
                )
            ),
            # PROBING -> LISTENING (after probe question)
            FSMTransition(
                from_state=FSMState.PROBING,
                to_state=FSMState.LISTENING,
                condition=TransitionCondition(
                    type=TransitionConditionType.ANALYSIS_COMPLETE
                )
            ),
            # HINTING -> LISTENING (after hint provided)
            FSMTransition(
                from_state=FSMState.HINTING,
                to_state=FSMState.LISTENING,
                condition=TransitionCondition(
                    type=TransitionConditionType.ANALYSIS_COMPLETE
                )
            ),
            # REPAIR -> LISTENING (after repair suggestion)
            FSMTransition(
                from_state=FSMState.REPAIR,
                to_state=FSMState.LISTENING,
                condition=TransitionCondition(
                    type=TransitionConditionType.ANALYSIS_COMPLETE
                )
            ),
            # CONSOLIDATING -> IDLE (session end)
            FSMTransition(
                from_state=FSMState.CONSOLIDATING,
                to_state=FSMState.IDLE,
                condition=TransitionCondition(
                    type=TransitionConditionType.ANALYSIS_COMPLETE
                )
            ),
        ]

    def get_current_state(self) -> FSMState:
        """
        Get the current FSM state.
        
        Returns:
            Current FSMState
        """
        return self._current_state

    def process_event(self, event: FSMEvent) -> FSMState:
        """
        Process an event and potentially transition to a new state.
        
        Args:
            event: The FSMEvent to process
            
        Returns:
            The new FSMState after processing
        """
        new_state = self._determine_next_state(event)
        
        if new_state != self._current_state:
            self._transition_to(new_state, event)
        
        return self._current_state

    def _determine_next_state(self, event: FSMEvent) -> FSMState:
        """
        Determine the next state based on the event.
        
        Args:
            event: The FSMEvent to process
            
        Returns:
            The determined next FSMState
        """
        # Handle session start
        if event.type == FSMEventType.SESSION_START:
            if self._current_state == FSMState.IDLE:
                return FSMState.LISTENING
            return self._current_state
        
        # Handle session end
        if event.type == FSMEventType.SESSION_END:
            return FSMState.IDLE
        
        # Handle silence detection
        if event.type == FSMEventType.SILENCE_DETECTED:
            duration = event.payload.get('duration', 0)
            if duration >= self._silence_threshold:
                if self._current_state == FSMState.LISTENING:
                    return FSMState.HINTING
            return self._current_state
        
        # Handle hint request
        if event.type == FSMEventType.HINT_REQUEST:
            if self._current_state in [FSMState.LISTENING, FSMState.ANALYZING]:
                return FSMState.HINTING
            return self._current_state
        
        # Handle student input
        if event.type == FSMEventType.STUDENT_INPUT:
            if self._current_state == FSMState.LISTENING:
                return FSMState.ANALYZING
            return self._current_state
        
        # Handle analysis result
        if event.type == FSMEventType.ANALYSIS_RESULT:
            return self._handle_analysis_result(event)
        
        return self._current_state

    def _handle_analysis_result(self, event: FSMEvent) -> FSMState:
        """
        Handle analysis result event and determine next state.
        
        Args:
            event: The analysis result event
            
        Returns:
            The next FSMState based on analysis
        """
        payload = event.payload
        
        # Check for logic error first (highest priority)
        if payload.get('logic_error', False):
            return FSMState.REPAIR
        
        # Check for logic gap
        if payload.get('logic_gap', False):
            return FSMState.PROBING
        
        # Check for coverage threshold
        coverage = payload.get('coverage', 0)
        if coverage >= self._coverage_threshold:
            return FSMState.CONSOLIDATING
        
        # Default: return to listening
        if self._current_state in [
            FSMState.ANALYZING, FSMState.PROBING,
            FSMState.HINTING, FSMState.REPAIR
        ]:
            return FSMState.LISTENING
        
        # From CONSOLIDATING, go to IDLE
        if self._current_state == FSMState.CONSOLIDATING:
            return FSMState.IDLE
        
        return self._current_state

    def _transition_to(self, new_state: FSMState, trigger: FSMEvent) -> None:
        """
        Perform the state transition.
        
        Args:
            new_state: The state to transition to
            trigger: The event that triggered the transition
        """
        old_state = self._current_state
        
        # Log the transition
        log_entry = StateTransitionLog(
            from_state=old_state,
            to_state=new_state,
            trigger=trigger,
            timestamp=datetime.utcnow().timestamp()
        )
        self._state_history.append(log_entry)
        
        # Update state
        self._current_state = new_state
        
        # Notify callbacks
        for callback in self._state_change_callbacks:
            callback(old_state, new_state)

    def on_state_change(
        self,
        callback: Callable[[FSMState, FSMState], None]
    ) -> None:
        """
        Register a callback for state changes.
        
        Args:
            callback: Function to call with (old_state, new_state)
        """
        self._state_change_callbacks.append(callback)

    def reset(self) -> None:
        """Reset the FSM to initial state."""
        if self._current_state != FSMState.IDLE:
            reset_event = FSMEvent(
                type=FSMEventType.SESSION_END,
                payload={'reason': 'reset'}
            )
            self._transition_to(FSMState.IDLE, reset_event)

    def get_state_history(self) -> List[StateTransitionLog]:
        """
        Get the history of state transitions.
        
        Returns:
            List of StateTransitionLog entries
        """
        return self._state_history.copy()

    def clear_history(self) -> None:
        """Clear the state transition history."""
        self._state_history.clear()

    @property
    def silence_threshold(self) -> float:
        """Get the silence threshold."""
        return self._silence_threshold

    @silence_threshold.setter
    def silence_threshold(self, value: float) -> None:
        """Set the silence threshold."""
        if value <= 0:
            raise ValueError("Silence threshold must be positive")
        self._silence_threshold = value

    @property
    def coverage_threshold(self) -> float:
        """Get the coverage threshold."""
        return self._coverage_threshold

    @coverage_threshold.setter
    def coverage_threshold(self, value: float) -> None:
        """Set the coverage threshold."""
        if not 0 <= value <= 1:
            raise ValueError("Coverage threshold must be between 0 and 1")
        self._coverage_threshold = value
