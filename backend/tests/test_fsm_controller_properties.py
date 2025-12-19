"""
Property-based tests for FSM Controller.

Feature: ai-math-tutor, Property 7: FSM 狀態轉移正確性
Validates: Requirements 6.3, 6.4, 6.7, 6.8

Property 7 states:
*For any* FSM 事件序列，狀態轉移應遵循以下規則：
- 靜默超時 → 轉移至 HINTING
- 邏輯缺漏 → 轉移至 PROBING
- 邏輯謬誤 → 轉移至 REPAIR
- 概念覆蓋率 ≥ 90% → 轉移至 CONSOLIDATING
"""
import pytest
from hypothesis import given, strategies as st, settings, assume

from backend.services.fsm_controller import (
    FSMController,
    FSMState,
    FSMEvent,
    FSMEventType,
)


# Strategies for generating test data
silence_duration_strategy = st.floats(min_value=0.0, max_value=60.0, allow_nan=False, allow_infinity=False)
coverage_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
silence_threshold_strategy = st.floats(min_value=0.1, max_value=30.0, allow_nan=False, allow_infinity=False)
coverage_threshold_strategy = st.floats(min_value=0.1, max_value=1.0, allow_nan=False, allow_infinity=False)


def setup_fsm_in_listening_state(
    silence_threshold: float = 5.0,
    coverage_threshold: float = 0.9
) -> FSMController:
    """Helper to create FSM and transition to LISTENING state."""
    fsm = FSMController(
        silence_threshold=silence_threshold,
        coverage_threshold=coverage_threshold
    )
    fsm.process_event(FSMEvent(type=FSMEventType.SESSION_START))
    return fsm


def setup_fsm_in_analyzing_state(
    silence_threshold: float = 5.0,
    coverage_threshold: float = 0.9
) -> FSMController:
    """Helper to create FSM and transition to ANALYZING state."""
    fsm = setup_fsm_in_listening_state(silence_threshold, coverage_threshold)
    fsm.process_event(FSMEvent(type=FSMEventType.STUDENT_INPUT, payload={'text': 'test'}))
    return fsm


class TestFSMStateTransitionProperties:
    """
    Property-based tests for FSM state transition correctness.
    
    Feature: ai-math-tutor, Property 7: FSM 狀態轉移正確性
    Validates: Requirements 6.3, 6.4, 6.7, 6.8
    """

    @settings(max_examples=100)
    @given(
        silence_duration=silence_duration_strategy,
        silence_threshold=silence_threshold_strategy
    )
    def test_silence_timeout_transitions_to_hinting(
        self,
        silence_duration: float,
        silence_threshold: float
    ):
        """
        Property 7 (Requirement 6.4): 靜默超時 → 轉移至 HINTING
        
        For any silence duration and threshold, when silence duration >= threshold
        and FSM is in LISTENING state, it should transition to HINTING.
        
        Feature: ai-math-tutor, Property 7: FSM 狀態轉移正確性
        Validates: Requirements 6.4
        """
        fsm = setup_fsm_in_listening_state(silence_threshold=silence_threshold)
        
        event = FSMEvent(
            type=FSMEventType.SILENCE_DETECTED,
            payload={'duration': silence_duration}
        )
        new_state = fsm.process_event(event)
        
        if silence_duration >= silence_threshold:
            assert new_state == FSMState.HINTING, (
                f"Expected HINTING when silence ({silence_duration}s) >= threshold ({silence_threshold}s), "
                f"but got {new_state}"
            )
        else:
            assert new_state == FSMState.LISTENING, (
                f"Expected LISTENING when silence ({silence_duration}s) < threshold ({silence_threshold}s), "
                f"but got {new_state}"
            )

    @settings(max_examples=100)
    @given(
        logic_gap=st.booleans(),
        logic_error=st.booleans(),
        coverage=coverage_strategy,
        coverage_threshold=coverage_threshold_strategy
    )
    def test_logic_gap_transitions_to_probing(
        self,
        logic_gap: bool,
        logic_error: bool,
        coverage: float,
        coverage_threshold: float
    ):
        """
        Property 7 (Requirement 6.3): 邏輯缺漏 → 轉移至 PROBING
        
        For any analysis result with logic_gap=True (and no logic_error),
        FSM should transition to PROBING state.
        
        Feature: ai-math-tutor, Property 7: FSM 狀態轉移正確性
        Validates: Requirements 6.3
        """
        # Only test when logic_gap is True and logic_error is False
        # (logic_error has higher priority)
        assume(logic_gap and not logic_error)
        assume(coverage < coverage_threshold)  # Coverage below threshold
        
        fsm = setup_fsm_in_analyzing_state(coverage_threshold=coverage_threshold)
        
        event = FSMEvent(
            type=FSMEventType.ANALYSIS_RESULT,
            payload={
                'logic_gap': logic_gap,
                'logic_error': logic_error,
                'coverage': coverage
            }
        )
        new_state = fsm.process_event(event)
        
        assert new_state == FSMState.PROBING, (
            f"Expected PROBING when logic_gap=True and logic_error=False, "
            f"but got {new_state}"
        )

    @settings(max_examples=100)
    @given(
        logic_gap=st.booleans(),
        coverage=coverage_strategy
    )
    def test_logic_error_transitions_to_repair(
        self,
        logic_gap: bool,
        coverage: float
    ):
        """
        Property 7 (Requirement 6.7): 邏輯謬誤 → 轉移至 REPAIR
        
        For any analysis result with logic_error=True,
        FSM should transition to REPAIR state (regardless of logic_gap).
        
        Feature: ai-math-tutor, Property 7: FSM 狀態轉移正確性
        Validates: Requirements 6.7
        """
        fsm = setup_fsm_in_analyzing_state()
        
        event = FSMEvent(
            type=FSMEventType.ANALYSIS_RESULT,
            payload={
                'logic_error': True,
                'logic_gap': logic_gap,
                'coverage': coverage
            }
        )
        new_state = fsm.process_event(event)
        
        assert new_state == FSMState.REPAIR, (
            f"Expected REPAIR when logic_error=True, but got {new_state}"
        )

    @settings(max_examples=100)
    @given(
        coverage_threshold=coverage_threshold_strategy,
        coverage_delta=st.floats(min_value=0.0, max_value=0.5, allow_nan=False, allow_infinity=False)
    )
    def test_coverage_threshold_transitions_to_consolidating(
        self,
        coverage_threshold: float,
        coverage_delta: float
    ):
        """
        Property 7 (Requirement 6.8): 概念覆蓋率 ≥ 90% → 轉移至 CONSOLIDATING
        
        For any coverage value >= threshold (and no logic errors/gaps),
        FSM should transition to CONSOLIDATING state.
        
        Feature: ai-math-tutor, Property 7: FSM 狀態轉移正確性
        Validates: Requirements 6.8
        """
        # Generate coverage that is >= threshold (capped at 1.0)
        coverage = min(coverage_threshold + coverage_delta, 1.0)
        
        fsm = setup_fsm_in_analyzing_state(coverage_threshold=coverage_threshold)
        
        event = FSMEvent(
            type=FSMEventType.ANALYSIS_RESULT,
            payload={
                'logic_error': False,
                'logic_gap': False,
                'coverage': coverage
            }
        )
        new_state = fsm.process_event(event)
        
        assert new_state == FSMState.CONSOLIDATING, (
            f"Expected CONSOLIDATING when coverage ({coverage}) >= threshold ({coverage_threshold}), "
            f"but got {new_state}"
        )

    @settings(max_examples=100)
    @given(
        coverage_threshold=coverage_threshold_strategy,
        coverage_ratio=st.floats(min_value=0.0, max_value=0.99, allow_nan=False, allow_infinity=False)
    )
    def test_coverage_below_threshold_returns_to_listening(
        self,
        coverage_threshold: float,
        coverage_ratio: float
    ):
        """
        Property 7 complement: When coverage < threshold and no errors/gaps,
        FSM should return to LISTENING state.
        
        Feature: ai-math-tutor, Property 7: FSM 狀態轉移正確性
        Validates: Requirements 6.8
        """
        # Generate coverage that is < threshold
        coverage = coverage_threshold * coverage_ratio
        
        fsm = setup_fsm_in_analyzing_state(coverage_threshold=coverage_threshold)
        
        event = FSMEvent(
            type=FSMEventType.ANALYSIS_RESULT,
            payload={
                'logic_error': False,
                'logic_gap': False,
                'coverage': coverage
            }
        )
        new_state = fsm.process_event(event)
        
        assert new_state == FSMState.LISTENING, (
            f"Expected LISTENING when coverage ({coverage}) < threshold ({coverage_threshold}) "
            f"and no errors/gaps, but got {new_state}"
        )

    @settings(max_examples=100)
    @given(
        logic_error=st.booleans(),
        logic_gap=st.booleans(),
        coverage=coverage_strategy,
        coverage_threshold=coverage_threshold_strategy
    )
    def test_logic_error_has_highest_priority(
        self,
        logic_error: bool,
        logic_gap: bool,
        coverage: float,
        coverage_threshold: float
    ):
        """
        Property 7: Logic error should have highest priority over other conditions.
        
        When logic_error=True, FSM should always transition to REPAIR,
        regardless of logic_gap or coverage values.
        
        Feature: ai-math-tutor, Property 7: FSM 狀態轉移正確性
        Validates: Requirements 6.7
        """
        assume(logic_error)  # Only test when logic_error is True
        
        fsm = setup_fsm_in_analyzing_state(coverage_threshold=coverage_threshold)
        
        event = FSMEvent(
            type=FSMEventType.ANALYSIS_RESULT,
            payload={
                'logic_error': logic_error,
                'logic_gap': logic_gap,
                'coverage': coverage
            }
        )
        new_state = fsm.process_event(event)
        
        assert new_state == FSMState.REPAIR, (
            f"Expected REPAIR when logic_error=True (logic_gap={logic_gap}, "
            f"coverage={coverage}), but got {new_state}"
        )

    @settings(max_examples=100)
    @given(st.data())
    def test_hint_request_from_listening_transitions_to_hinting(self, data):
        """
        Property 7 (Requirement 6.4): User hint request → HINTING
        
        When user explicitly requests a hint from LISTENING state,
        FSM should transition to HINTING.
        
        Feature: ai-math-tutor, Property 7: FSM 狀態轉移正確性
        Validates: Requirements 6.4
        """
        fsm = setup_fsm_in_listening_state()
        
        event = FSMEvent(type=FSMEventType.HINT_REQUEST)
        new_state = fsm.process_event(event)
        
        assert new_state == FSMState.HINTING, (
            f"Expected HINTING when hint requested from LISTENING, but got {new_state}"
        )
