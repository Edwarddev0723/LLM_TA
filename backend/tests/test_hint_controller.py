"""
Unit tests for Hint Controller.
"""
import pytest
from backend.services.hint_controller import (
    HintController,
    HintLevel,
)


class TestHintController:
    """Test cases for HintController."""

    def test_initial_level_is_level_1(self):
        """Test that hint controller starts at Level 1."""
        controller = HintController()
        assert controller.get_current_level() == HintLevel.LEVEL_1

    def test_first_hint_returns_level_1(self):
        """Test that first hint request returns Level 1."""
        controller = HintController()
        controller.start_session("session-1", "algebra")
        
        level = controller.request_hint()
        assert level == HintLevel.LEVEL_1

    def test_second_hint_returns_level_2(self):
        """Test that second hint request returns Level 2."""
        controller = HintController()
        controller.start_session("session-1", "algebra")
        
        controller.request_hint()  # Level 1
        level = controller.request_hint()  # Level 2
        assert level == HintLevel.LEVEL_2

    def test_third_hint_returns_level_3(self):
        """Test that third hint request returns Level 3."""
        controller = HintController()
        controller.start_session("session-1", "algebra")
        
        controller.request_hint()  # Level 1
        controller.request_hint()  # Level 2
        level = controller.request_hint()  # Level 3
        assert level == HintLevel.LEVEL_3

    def test_fourth_hint_stays_at_level_3(self):
        """Test that hints stay at Level 3 after reaching max."""
        controller = HintController()
        controller.start_session("session-1", "algebra")
        
        controller.request_hint()  # Level 1
        controller.request_hint()  # Level 2
        controller.request_hint()  # Level 3
        level = controller.request_hint()  # Still Level 3
        assert level == HintLevel.LEVEL_3

    def test_hint_history_is_recorded(self):
        """Test that hint requests are recorded in history."""
        controller = HintController()
        controller.start_session("session-1", "algebra")
        
        controller.request_hint()
        controller.request_hint()
        
        history = controller.get_hint_history()
        assert len(history) == 2
        assert history[0].level == HintLevel.LEVEL_1
        assert history[1].level == HintLevel.LEVEL_2

    def test_reset_for_concept_resets_level(self):
        """Test that reset_for_concept resets hint level to 1."""
        controller = HintController()
        controller.start_session("session-1", "algebra")
        
        controller.request_hint()  # Level 1
        controller.request_hint()  # Level 2
        
        controller.reset_for_concept("geometry")
        level = controller.request_hint()
        assert level == HintLevel.LEVEL_1

    def test_get_session_hints(self):
        """Test getting hints for a specific session."""
        controller = HintController()
        
        controller.start_session("session-1", "algebra")
        controller.request_hint()
        
        controller.start_session("session-2", "geometry")
        controller.request_hint()
        controller.request_hint()
        
        session_1_hints = controller.get_session_hints("session-1")
        session_2_hints = controller.get_session_hints("session-2")
        
        assert len(session_1_hints) == 1
        assert len(session_2_hints) == 2

    def test_get_hint_count(self):
        """Test getting hint count for a session."""
        controller = HintController()
        controller.start_session("session-1", "algebra")
        
        controller.request_hint()
        controller.request_hint()
        controller.request_hint()
        
        assert controller.get_hint_count() == 3

    def test_calculate_hint_dependency_no_hints(self):
        """Test hint dependency calculation with no hints."""
        controller = HintController()
        controller.start_session("session-1", "algebra")
        
        dependency = controller.calculate_hint_dependency(total_turns=10)
        assert dependency == 1.0  # No dependency

    def test_calculate_hint_dependency_with_hints(self):
        """Test hint dependency calculation with hints."""
        controller = HintController()
        controller.start_session("session-1", "algebra")
        
        controller.request_hint()  # Level 1, weight 0.2
        controller.request_hint()  # Level 2, weight 0.5
        
        # Weighted sum = 0.2 + 0.5 = 0.7
        # Dependency = 1 - 0.7/10 = 0.93
        dependency = controller.calculate_hint_dependency(total_turns=10)
        assert abs(dependency - 0.93) < 0.01

    def test_calculate_hint_dependency_zero_turns(self):
        """Test hint dependency with zero turns returns 1.0."""
        controller = HintController()
        controller.start_session("session-1", "algebra")
        
        dependency = controller.calculate_hint_dependency(total_turns=0)
        assert dependency == 1.0

    def test_get_hints_by_level(self):
        """Test getting hint counts grouped by level."""
        controller = HintController()
        controller.start_session("session-1", "algebra")
        
        controller.request_hint()  # Level 1
        controller.request_hint()  # Level 2
        controller.request_hint()  # Level 3
        controller.request_hint()  # Level 3
        
        by_level = controller.get_hints_by_level()
        assert by_level[HintLevel.LEVEL_1] == 1
        assert by_level[HintLevel.LEVEL_2] == 1
        assert by_level[HintLevel.LEVEL_3] == 2

    def test_clear_history(self):
        """Test that clear_history empties all history."""
        controller = HintController()
        controller.start_session("session-1", "algebra")
        controller.request_hint()
        
        controller.clear_history()
        assert len(controller.get_hint_history()) == 0

    def test_reset_keeps_history(self):
        """Test that reset keeps history for statistics."""
        controller = HintController()
        controller.start_session("session-1", "algebra")
        controller.request_hint()
        
        controller.reset()
        assert len(controller.get_hint_history()) == 1
        assert controller.get_current_level() == HintLevel.LEVEL_1

    def test_hint_with_custom_concept(self):
        """Test requesting hint with custom concept."""
        controller = HintController()
        controller.start_session("session-1", "algebra")
        
        controller.request_hint(concept="quadratic equations")
        
        history = controller.get_hint_history()
        assert history[0].concept == "quadratic equations"
