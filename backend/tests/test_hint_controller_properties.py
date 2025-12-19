"""
Property-based tests for Hint Controller.

Feature: ai-math-tutor, Property 8: 提示層級遞增正確性
Validates: Requirements 7.1, 7.2, 7.3, 7.4

Property 8 states:
*For any* 連續的提示請求序列，提示層級應從 Level 1 開始，每次請求遞增一級，
最高至 Level 3，且每次提示都應被記錄。
"""
import pytest
from hypothesis import given, strategies as st, settings, assume

from backend.services.hint_controller import (
    HintController,
    HintLevel,
    HintRecord,
)


# Strategies for generating test data
session_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='-_'),
    min_size=1,
    max_size=50
)
concept_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'Zs'), whitelist_characters='-_'),
    min_size=1,
    max_size=100
)
hint_request_count_strategy = st.integers(min_value=1, max_value=20)


class TestHintLevelProgressionProperties:
    """
    Property-based tests for hint level progression correctness.
    
    Feature: ai-math-tutor, Property 8: 提示層級遞增正確性
    Validates: Requirements 7.1, 7.2, 7.3, 7.4
    """

    @settings(max_examples=100)
    @given(
        session_id=session_id_strategy,
        concept=concept_strategy,
        num_requests=hint_request_count_strategy
    )
    def test_hint_level_progression_from_level_1(
        self,
        session_id: str,
        concept: str,
        num_requests: int
    ):
        """
        Property 8 (Requirements 7.1, 7.2, 7.3): 提示層級遞增正確性
        
        For any sequence of hint requests:
        - First hint should be Level 1 (Requirement 7.1)
        - Second hint should be Level 2 (Requirement 7.2)
        - Third hint should be Level 3 (Requirement 7.3)
        - Subsequent hints should stay at Level 3
        
        Feature: ai-math-tutor, Property 8: 提示層級遞增正確性
        Validates: Requirements 7.1, 7.2, 7.3
        """
        controller = HintController()
        controller.start_session(session_id, concept)
        
        for i in range(num_requests):
            level = controller.request_hint()
            expected_level = min(i + 1, 3)  # Level 1, 2, 3, 3, 3, ...
            
            assert level == HintLevel(expected_level), (
                f"Request {i + 1}: Expected Level {expected_level}, but got Level {level}"
            )

    @settings(max_examples=100)
    @given(
        session_id=session_id_strategy,
        concept=concept_strategy,
        num_requests=hint_request_count_strategy
    )
    def test_all_hints_are_recorded(
        self,
        session_id: str,
        concept: str,
        num_requests: int
    ):
        """
        Property 8 (Requirement 7.4): 每次提示都應被記錄
        
        For any sequence of hint requests, all hints should be recorded
        in the hint history with correct levels.
        
        Feature: ai-math-tutor, Property 8: 提示層級遞增正確性
        Validates: Requirements 7.4
        """
        controller = HintController()
        controller.start_session(session_id, concept)
        
        # Request hints
        requested_levels = []
        for _ in range(num_requests):
            level = controller.request_hint()
            requested_levels.append(level)
        
        # Verify all hints are recorded
        history = controller.get_hint_history()
        assert len(history) == num_requests, (
            f"Expected {num_requests} hints in history, but got {len(history)}"
        )
        
        # Verify recorded levels match requested levels
        for i, (record, expected_level) in enumerate(zip(history, requested_levels)):
            assert record.level == expected_level, (
                f"History record {i}: Expected Level {expected_level}, but got Level {record.level}"
            )

    @settings(max_examples=100)
    @given(
        session_id=session_id_strategy,
        concept=concept_strategy,
        num_requests=hint_request_count_strategy
    )
    def test_hint_records_contain_session_and_concept(
        self,
        session_id: str,
        concept: str,
        num_requests: int
    ):
        """
        Property 8 (Requirement 7.4): 提示記錄應包含會話與概念資訊
        
        For any hint request, the recorded hint should contain
        the correct session ID and concept.
        
        Feature: ai-math-tutor, Property 8: 提示層級遞增正確性
        Validates: Requirements 7.4
        """
        controller = HintController()
        controller.start_session(session_id, concept)
        
        for _ in range(num_requests):
            controller.request_hint()
        
        history = controller.get_hint_history()
        for record in history:
            assert record.session_id == session_id, (
                f"Expected session_id '{session_id}', but got '{record.session_id}'"
            )
            assert record.concept == concept, (
                f"Expected concept '{concept}', but got '{record.concept}'"
            )

    @settings(max_examples=100)
    @given(
        session_id=session_id_strategy,
        concept=concept_strategy,
        num_requests=hint_request_count_strategy
    )
    def test_hint_records_have_increasing_timestamps(
        self,
        session_id: str,
        concept: str,
        num_requests: int
    ):
        """
        Property 8 (Requirement 7.4): 提示記錄時間戳應遞增
        
        For any sequence of hint requests, the timestamps in the
        recorded hints should be non-decreasing.
        
        Feature: ai-math-tutor, Property 8: 提示層級遞增正確性
        Validates: Requirements 7.4
        """
        controller = HintController()
        controller.start_session(session_id, concept)
        
        for _ in range(num_requests):
            controller.request_hint()
        
        history = controller.get_hint_history()
        for i in range(1, len(history)):
            assert history[i].timestamp >= history[i - 1].timestamp, (
                f"Timestamp at index {i} ({history[i].timestamp}) should be >= "
                f"timestamp at index {i - 1} ({history[i - 1].timestamp})"
            )

    @settings(max_examples=100)
    @given(
        session_id=session_id_strategy,
        concept1=concept_strategy,
        concept2=concept_strategy,
        requests_before_reset=st.integers(min_value=1, max_value=5),
        requests_after_reset=st.integers(min_value=1, max_value=5)
    )
    def test_reset_for_concept_restarts_level_progression(
        self,
        session_id: str,
        concept1: str,
        concept2: str,
        requests_before_reset: int,
        requests_after_reset: int
    ):
        """
        Property 8: 重置概念後，提示層級應從 Level 1 重新開始
        
        When reset_for_concept is called, the hint level should
        restart from Level 1 for the new concept.
        
        Feature: ai-math-tutor, Property 8: 提示層級遞增正確性
        Validates: Requirements 7.1, 7.2, 7.3
        """
        controller = HintController()
        controller.start_session(session_id, concept1)
        
        # Request hints for first concept
        for _ in range(requests_before_reset):
            controller.request_hint()
        
        # Reset for new concept
        controller.reset_for_concept(concept2)
        
        # Verify level restarts from Level 1
        for i in range(requests_after_reset):
            level = controller.request_hint(concept=concept2)
            expected_level = min(i + 1, 3)
            
            assert level == HintLevel(expected_level), (
                f"After reset, request {i + 1}: Expected Level {expected_level}, "
                f"but got Level {level}"
            )

    @settings(max_examples=100)
    @given(
        session_id=session_id_strategy,
        concept=concept_strategy,
        num_requests=st.integers(min_value=4, max_value=20)
    )
    def test_level_3_is_maximum(
        self,
        session_id: str,
        concept: str,
        num_requests: int
    ):
        """
        Property 8 (Requirement 7.3): Level 3 是最高層級
        
        For any number of hint requests beyond 3, the level
        should remain at Level 3.
        
        Feature: ai-math-tutor, Property 8: 提示層級遞增正確性
        Validates: Requirements 7.3
        """
        controller = HintController()
        controller.start_session(session_id, concept)
        
        # Request hints
        levels = []
        for _ in range(num_requests):
            level = controller.request_hint()
            levels.append(level)
        
        # Verify all levels from index 2 onwards are Level 3
        for i in range(2, num_requests):
            assert levels[i] == HintLevel.LEVEL_3, (
                f"Request {i + 1}: Expected Level 3, but got Level {levels[i]}"
            )

    @settings(max_examples=100)
    @given(
        session_id=session_id_strategy,
        concept=concept_strategy,
        num_requests=hint_request_count_strategy,
        total_turns=st.integers(min_value=1, max_value=100)
    )
    def test_hint_dependency_calculation_with_recorded_hints(
        self,
        session_id: str,
        concept: str,
        num_requests: int,
        total_turns: int
    ):
        """
        Property 8 (Requirement 7.4): 提示依賴度計算應基於記錄的提示
        
        The hint dependency calculation should use all recorded hints
        with their correct weights.
        
        Feature: ai-math-tutor, Property 8: 提示層級遞增正確性
        Validates: Requirements 7.4
        """
        assume(total_turns >= num_requests)  # Ensure valid calculation
        
        controller = HintController()
        controller.start_session(session_id, concept)
        
        # Request hints and track expected weights
        expected_weighted_sum = 0.0
        for i in range(num_requests):
            level = controller.request_hint()
            expected_weighted_sum += controller.HINT_WEIGHTS[level]
        
        # Calculate dependency
        dependency = controller.calculate_hint_dependency(total_turns)
        
        # Verify calculation
        expected_dependency = max(0.0, min(1.0, 1 - (expected_weighted_sum / total_turns)))
        assert abs(dependency - expected_dependency) < 0.001, (
            f"Expected dependency {expected_dependency}, but got {dependency}"
        )
