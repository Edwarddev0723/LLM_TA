"""
Unit tests for FSM Controller.
"""
import pytest
from backend.services.fsm_controller import (
    FSMController,
    FSMState,
    FSMEvent,
    FSMEventType,
)


class TestFSMController:
    """Test cases for FSMController."""

    def test_initial_state_is_idle(self):
        """Test that FSM starts in IDLE state."""
        fsm = FSMController()
        assert fsm.get_current_state() == FSMState.IDLE

    def test_session_start_transitions_to_listening(self):
        """Test that SESSION_START transitions from IDLE to LISTENING."""
        fsm = FSMController()
        event = FSMEvent(type=FSMEventType.SESSION_START)
        new_state = fsm.process_event(event)
        assert new_state == FSMState.LISTENING

    def test_student_input_transitions_to_analyzing(self):
        """Test that STUDENT_INPUT transitions from LISTENING to ANALYZING."""
        fsm = FSMController()
        # First start session
        fsm.process_event(FSMEvent(type=FSMEventType.SESSION_START))
        # Then send student input
        event = FSMEvent(type=FSMEventType.STUDENT_INPUT, payload={'text': 'test'})
        new_state = fsm.process_event(event)
        assert new_state == FSMState.ANALYZING

    def test_silence_timeout_transitions_to_hinting(self):
        """Test that silence timeout transitions to HINTING."""
        fsm = FSMController(silence_threshold=5.0)
        fsm.process_event(FSMEvent(type=FSMEventType.SESSION_START))
        
        # Silence detected with duration >= threshold
        event = FSMEvent(
            type=FSMEventType.SILENCE_DETECTED,
            payload={'duration': 6.0}
        )
        new_state = fsm.process_event(event)
        assert new_state == FSMState.HINTING

    def test_silence_below_threshold_stays_listening(self):
        """Test that silence below threshold keeps LISTENING state."""
        fsm = FSMController(silence_threshold=5.0)
        fsm.process_event(FSMEvent(type=FSMEventType.SESSION_START))
        
        event = FSMEvent(
            type=FSMEventType.SILENCE_DETECTED,
            payload={'duration': 3.0}
        )
        new_state = fsm.process_event(event)
        assert new_state == FSMState.LISTENING

    def test_hint_request_transitions_to_hinting(self):
        """Test that HINT_REQUEST transitions to HINTING."""
        fsm = FSMController()
        fsm.process_event(FSMEvent(type=FSMEventType.SESSION_START))
        
        event = FSMEvent(type=FSMEventType.HINT_REQUEST)
        new_state = fsm.process_event(event)
        assert new_state == FSMState.HINTING

    def test_logic_gap_transitions_to_probing(self):
        """Test that logic gap in analysis transitions to PROBING."""
        fsm = FSMController()
        fsm.process_event(FSMEvent(type=FSMEventType.SESSION_START))
        fsm.process_event(FSMEvent(type=FSMEventType.STUDENT_INPUT))
        
        event = FSMEvent(
            type=FSMEventType.ANALYSIS_RESULT,
            payload={'logic_gap': True}
        )
        new_state = fsm.process_event(event)
        assert new_state == FSMState.PROBING

    def test_logic_error_transitions_to_repair(self):
        """Test that logic error in analysis transitions to REPAIR."""
        fsm = FSMController()
        fsm.process_event(FSMEvent(type=FSMEventType.SESSION_START))
        fsm.process_event(FSMEvent(type=FSMEventType.STUDENT_INPUT))
        
        event = FSMEvent(
            type=FSMEventType.ANALYSIS_RESULT,
            payload={'logic_error': True}
        )
        new_state = fsm.process_event(event)
        assert new_state == FSMState.REPAIR

    def test_coverage_threshold_transitions_to_consolidating(self):
        """Test that meeting coverage threshold transitions to CONSOLIDATING."""
        fsm = FSMController(coverage_threshold=0.9)
        fsm.process_event(FSMEvent(type=FSMEventType.SESSION_START))
        fsm.process_event(FSMEvent(type=FSMEventType.STUDENT_INPUT))
        
        event = FSMEvent(
            type=FSMEventType.ANALYSIS_RESULT,
            payload={'coverage': 0.95}
        )
        new_state = fsm.process_event(event)
        assert new_state == FSMState.CONSOLIDATING

    def test_reset_returns_to_idle(self):
        """Test that reset() returns FSM to IDLE state."""
        fsm = FSMController()
        fsm.process_event(FSMEvent(type=FSMEventType.SESSION_START))
        assert fsm.get_current_state() == FSMState.LISTENING
        
        fsm.reset()
        assert fsm.get_current_state() == FSMState.IDLE

    def test_state_history_is_recorded(self):
        """Test that state transitions are recorded in history."""
        fsm = FSMController()
        fsm.process_event(FSMEvent(type=FSMEventType.SESSION_START))
        
        history = fsm.get_state_history()
        assert len(history) == 1
        assert history[0].from_state == FSMState.IDLE
        assert history[0].to_state == FSMState.LISTENING

    def test_state_change_callback_is_called(self):
        """Test that state change callbacks are invoked."""
        fsm = FSMController()
        callback_results = []
        
        def callback(old_state, new_state):
            callback_results.append((old_state, new_state))
        
        fsm.on_state_change(callback)
        fsm.process_event(FSMEvent(type=FSMEventType.SESSION_START))
        
        assert len(callback_results) == 1
        assert callback_results[0] == (FSMState.IDLE, FSMState.LISTENING)

    def test_session_end_returns_to_idle(self):
        """Test that SESSION_END returns to IDLE from any state."""
        fsm = FSMController()
        fsm.process_event(FSMEvent(type=FSMEventType.SESSION_START))
        
        event = FSMEvent(type=FSMEventType.SESSION_END)
        new_state = fsm.process_event(event)
        assert new_state == FSMState.IDLE

    def test_logic_error_has_priority_over_logic_gap(self):
        """Test that logic_error takes priority when both are present."""
        fsm = FSMController()
        fsm.process_event(FSMEvent(type=FSMEventType.SESSION_START))
        fsm.process_event(FSMEvent(type=FSMEventType.STUDENT_INPUT))
        
        event = FSMEvent(
            type=FSMEventType.ANALYSIS_RESULT,
            payload={'logic_error': True, 'logic_gap': True}
        )
        new_state = fsm.process_event(event)
        assert new_state == FSMState.REPAIR

    def test_clear_history(self):
        """Test that clear_history() empties the history."""
        fsm = FSMController()
        fsm.process_event(FSMEvent(type=FSMEventType.SESSION_START))
        assert len(fsm.get_state_history()) > 0
        
        fsm.clear_history()
        assert len(fsm.get_state_history()) == 0
