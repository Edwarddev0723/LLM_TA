"""
Unit tests for the Metrics Calculator service.
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from backend.services.metrics_calculator import (
    MetricsCalculator,
    PauseData,
    HintUsageData,
    MetricsReport,
)


class TestPauseData:
    """Tests for PauseData dataclass."""

    def test_valid_pause_data(self):
        """Test creating valid pause data."""
        pause = PauseData(start_time=1.0, end_time=3.0, duration=2.0)
        assert pause.start_time == 1.0
        assert pause.end_time == 3.0
        assert pause.duration == 2.0
        assert pause.id is not None

    def test_negative_start_time_raises_error(self):
        """Test that negative start_time raises ValueError."""
        with pytest.raises(ValueError, match="start_time must be non-negative"):
            PauseData(start_time=-1.0, end_time=3.0, duration=2.0)

    def test_end_time_before_start_raises_error(self):
        """Test that end_time < start_time raises ValueError."""
        with pytest.raises(ValueError, match="end_time must be >= start_time"):
            PauseData(start_time=5.0, end_time=3.0, duration=2.0)

    def test_negative_duration_raises_error(self):
        """Test that negative duration raises ValueError."""
        with pytest.raises(ValueError, match="duration must be non-negative"):
            PauseData(start_time=1.0, end_time=3.0, duration=-1.0)


class TestHintUsageData:
    """Tests for HintUsageData dataclass."""

    def test_hint_weights(self):
        """Test hint weight calculation."""
        hint1 = HintUsageData(level=1, concept="algebra", timestamp=1.0)
        hint2 = HintUsageData(level=2, concept="algebra", timestamp=2.0)
        hint3 = HintUsageData(level=3, concept="algebra", timestamp=3.0)

        assert hint1.weight == 0.2
        assert hint2.weight == 0.5
        assert hint3.weight == 1.0

    def test_unknown_level_weight(self):
        """Test that unknown level defaults to weight 1.0."""
        hint = HintUsageData(level=99, concept="algebra", timestamp=1.0)
        assert hint.weight == 1.0


class TestMetricsCalculator:
    """Tests for MetricsCalculator class."""

    @pytest.fixture
    def calculator(self):
        """Create a MetricsCalculator instance."""
        return MetricsCalculator()

    # WPM Tests
    def test_calculate_wpm_basic(self, calculator):
        """Test basic WPM calculation."""
        wpm = calculator.calculate_wpm(word_count=150, duration_minutes=2.0)
        assert wpm == 75.0

    def test_calculate_wpm_zero_words(self, calculator):
        """Test WPM with zero words."""
        wpm = calculator.calculate_wpm(word_count=0, duration_minutes=1.0)
        assert wpm == 0.0

    def test_calculate_wpm_negative_words_raises_error(self, calculator):
        """Test that negative word count raises ValueError."""
        with pytest.raises(ValueError, match="word_count must be non-negative"):
            calculator.calculate_wpm(word_count=-10, duration_minutes=1.0)

    def test_calculate_wpm_zero_duration_raises_error(self, calculator):
        """Test that zero duration raises ValueError."""
        with pytest.raises(ValueError, match="duration_minutes must be positive"):
            calculator.calculate_wpm(word_count=100, duration_minutes=0)

    def test_calculate_wpm_negative_duration_raises_error(self, calculator):
        """Test that negative duration raises ValueError."""
        with pytest.raises(ValueError, match="duration_minutes must be positive"):
            calculator.calculate_wpm(word_count=100, duration_minutes=-1.0)

    # Pause Rate Tests
    def test_calculate_pause_rate_basic(self, calculator):
        """Test basic pause rate calculation."""
        pauses = [
            PauseData(start_time=0, end_time=2, duration=2.0),
            PauseData(start_time=5, end_time=8, duration=3.0),
        ]
        rate = calculator.calculate_pause_rate(pauses, total_duration=10.0)
        assert rate == 0.5  # 5 seconds of pause in 10 seconds

    def test_calculate_pause_rate_no_pauses(self, calculator):
        """Test pause rate with no pauses."""
        rate = calculator.calculate_pause_rate([], total_duration=10.0)
        assert rate == 0.0

    def test_calculate_pause_rate_clamped_to_one(self, calculator):
        """Test that pause rate is clamped to 1.0."""
        pauses = [PauseData(start_time=0, end_time=15, duration=15.0)]
        rate = calculator.calculate_pause_rate(pauses, total_duration=10.0)
        assert rate == 1.0

    def test_calculate_pause_rate_zero_duration_raises_error(self, calculator):
        """Test that zero duration raises ValueError."""
        with pytest.raises(ValueError, match="total_duration must be positive"):
            calculator.calculate_pause_rate([], total_duration=0)

    # Hint Dependency Tests
    def test_calculate_hint_dependency_no_hints(self, calculator):
        """Test hint dependency with no hints."""
        dependency = calculator.calculate_hint_dependency([], total_turns=10)
        assert dependency == 1.0

    def test_calculate_hint_dependency_no_turns(self, calculator):
        """Test hint dependency with no turns."""
        dependency = calculator.calculate_hint_dependency([], total_turns=0)
        assert dependency == 1.0

    def test_calculate_hint_dependency_basic(self, calculator):
        """Test basic hint dependency calculation."""
        hints = [
            HintUsageData(level=1, concept="algebra", timestamp=1.0),  # weight 0.2
            HintUsageData(level=2, concept="algebra", timestamp=2.0),  # weight 0.5
        ]
        # weighted_sum = 0.2 + 0.5 = 0.7
        # dependency = 1 - 0.7/10 = 0.93
        dependency = calculator.calculate_hint_dependency(hints, total_turns=10)
        assert abs(dependency - 0.93) < 0.001

    def test_calculate_hint_dependency_clamped_to_zero(self, calculator):
        """Test that hint dependency is clamped to 0.0."""
        hints = [
            HintUsageData(level=3, concept="algebra", timestamp=1.0),  # weight 1.0
            HintUsageData(level=3, concept="algebra", timestamp=2.0),  # weight 1.0
        ]
        # weighted_sum = 2.0, total_turns = 1
        # dependency = 1 - 2.0/1 = -1.0 -> clamped to 0.0
        dependency = calculator.calculate_hint_dependency(hints, total_turns=1)
        assert dependency == 0.0

    def test_calculate_hint_dependency_negative_turns_raises_error(self, calculator):
        """Test that negative turns raises ValueError."""
        with pytest.raises(ValueError, match="total_turns must be non-negative"):
            calculator.calculate_hint_dependency([], total_turns=-1)

    # Concept Coverage Tests
    def test_calculate_concept_coverage_full(self, calculator):
        """Test full concept coverage."""
        coverage = calculator.calculate_concept_coverage(
            covered_concepts=["algebra", "geometry", "calculus"],
            required_concepts=["algebra", "geometry"]
        )
        assert coverage == 1.0

    def test_calculate_concept_coverage_partial(self, calculator):
        """Test partial concept coverage."""
        coverage = calculator.calculate_concept_coverage(
            covered_concepts=["algebra"],
            required_concepts=["algebra", "geometry"]
        )
        assert coverage == 0.5

    def test_calculate_concept_coverage_none(self, calculator):
        """Test no concept coverage."""
        coverage = calculator.calculate_concept_coverage(
            covered_concepts=["calculus"],
            required_concepts=["algebra", "geometry"]
        )
        assert coverage == 0.0

    def test_calculate_concept_coverage_empty_required(self, calculator):
        """Test coverage with no required concepts."""
        coverage = calculator.calculate_concept_coverage(
            covered_concepts=["algebra"],
            required_concepts=[]
        )
        assert coverage == 1.0

    def test_calculate_concept_coverage_empty_covered(self, calculator):
        """Test coverage with no covered concepts."""
        coverage = calculator.calculate_concept_coverage(
            covered_concepts=[],
            required_concepts=["algebra", "geometry"]
        )
        assert coverage == 0.0

    # Generate Metrics Report Tests
    def test_generate_metrics_report(self, calculator):
        """Test generating a complete metrics report."""
        pauses = [PauseData(start_time=0, end_time=30, duration=30.0)]
        hints = [HintUsageData(level=1, concept="algebra", timestamp=1.0)]

        report = calculator.generate_metrics_report(
            session_id="session-123",
            word_count=150,
            duration_minutes=2.0,
            pauses=pauses,
            hints=hints,
            total_turns=10,
            covered_concepts=["algebra"],
            required_concepts=["algebra", "geometry"],
            focus_duration=100.0
        )

        assert report.session_id == "session-123"
        assert report.wpm == 75.0
        assert report.pause_rate == 0.25  # 30s pause in 120s
        assert abs(report.hint_dependency - 0.98) < 0.001  # 1 - 0.2/10
        assert report.concept_coverage == 0.5
        assert report.focus_duration == 100.0


class TestMetricsCalculatorPersistence:
    """Tests for MetricsCalculator persistence methods."""

    def test_save_metrics_without_db_raises_error(self):
        """Test that save_metrics raises error without database."""
        calculator = MetricsCalculator()
        metrics = MetricsReport(
            session_id="session-123",
            wpm=75.0,
            pause_rate=0.25,
            hint_dependency=0.98,
            concept_coverage=0.5,
            focus_duration=100.0
        )
        with pytest.raises(RuntimeError, match="No database session available"):
            calculator.save_metrics(metrics)

    def test_get_metrics_without_db_raises_error(self):
        """Test that get_metrics raises error without database."""
        calculator = MetricsCalculator()
        with pytest.raises(RuntimeError, match="No database session available"):
            calculator.get_metrics("session-123")

    def test_save_and_get_metrics_with_mock_db(self):
        """Test save and get metrics with mocked database."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        calculator = MetricsCalculator(db=mock_db)
        metrics = MetricsReport(
            session_id="session-123",
            wpm=75.0,
            pause_rate=0.25,
            hint_dependency=0.98,
            concept_coverage=0.5,
            focus_duration=100.0
        )

        # Test save
        result_id = calculator.save_metrics(metrics)
        assert result_id == metrics.id
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()



class TestMetricsCalculatorDatabaseIntegration:
    """Integration tests for MetricsCalculator with real database."""

    @pytest.fixture
    def db_session(self):
        """Create a test database session."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.models.database import Base
        from backend.models.metrics import LearningMetrics
        from backend.models.session import Session
        from backend.models.student import Student
        from backend.models.question import Question

        # Create in-memory SQLite database
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        TestSession = sessionmaker(bind=engine)
        session = TestSession()

        # Create test student
        student = Student(id="student-1", name="Test Student", grade=8)
        session.add(student)

        # Create test question
        question = Question(
            id="question-1",
            content="Test question",
            type="CALCULATION",
            subject="數學",
            unit="代數",
            difficulty=2,
            standard_solution="x = 5"
        )
        session.add(question)

        # Create test session
        test_session = Session(
            id="session-1",
            student_id="student-1",
            question_id="question-1",
            start_time=datetime.utcnow()
        )
        session.add(test_session)
        session.commit()

        yield session

        session.close()

    def test_save_and_retrieve_metrics(self, db_session):
        """Test saving and retrieving metrics from database."""
        calculator = MetricsCalculator(db=db_session)

        metrics = MetricsReport(
            session_id="session-1",
            wpm=75.0,
            pause_rate=0.25,
            hint_dependency=0.98,
            concept_coverage=0.5,
            focus_duration=100.0
        )

        # Save metrics
        saved_id = calculator.save_metrics(metrics)
        assert saved_id == metrics.id

        # Retrieve metrics
        retrieved = calculator.get_metrics("session-1")
        assert retrieved is not None
        assert retrieved.session_id == "session-1"
        assert retrieved.wpm == 75.0
        assert retrieved.pause_rate == 0.25
        assert retrieved.hint_dependency == 0.98
        assert retrieved.concept_coverage == 0.5
        assert retrieved.focus_duration == 100.0

    def test_get_metrics_not_found(self, db_session):
        """Test retrieving non-existent metrics."""
        calculator = MetricsCalculator(db=db_session)
        result = calculator.get_metrics("non-existent-session")
        assert result is None

    def test_get_metrics_by_id(self, db_session):
        """Test retrieving metrics by ID."""
        calculator = MetricsCalculator(db=db_session)

        metrics = MetricsReport(
            session_id="session-1",
            wpm=75.0,
            pause_rate=0.25,
            hint_dependency=0.98,
            concept_coverage=0.5,
            focus_duration=100.0
        )

        saved_id = calculator.save_metrics(metrics)
        retrieved = calculator.get_metrics_by_id(saved_id)

        assert retrieved is not None
        assert retrieved.id == saved_id

    def test_update_metrics(self, db_session):
        """Test updating existing metrics."""
        calculator = MetricsCalculator(db=db_session)

        # Save initial metrics
        metrics = MetricsReport(
            session_id="session-1",
            wpm=75.0,
            pause_rate=0.25,
            hint_dependency=0.98,
            concept_coverage=0.5,
            focus_duration=100.0
        )
        calculator.save_metrics(metrics)

        # Update metrics
        metrics.wpm = 100.0
        metrics.concept_coverage = 0.8
        result = calculator.update_metrics(metrics)
        assert result is True

        # Verify update
        retrieved = calculator.get_metrics("session-1")
        assert retrieved.wpm == 100.0
        assert retrieved.concept_coverage == 0.8

    def test_update_metrics_not_found(self, db_session):
        """Test updating non-existent metrics."""
        calculator = MetricsCalculator(db=db_session)

        metrics = MetricsReport(
            id="non-existent-id",
            session_id="session-1",
            wpm=75.0,
            pause_rate=0.25,
            hint_dependency=0.98,
            concept_coverage=0.5,
            focus_duration=100.0
        )

        result = calculator.update_metrics(metrics)
        assert result is False

    def test_delete_metrics(self, db_session):
        """Test deleting metrics."""
        calculator = MetricsCalculator(db=db_session)

        metrics = MetricsReport(
            session_id="session-1",
            wpm=75.0,
            pause_rate=0.25,
            hint_dependency=0.98,
            concept_coverage=0.5,
            focus_duration=100.0
        )
        saved_id = calculator.save_metrics(metrics)

        # Delete metrics
        result = calculator.delete_metrics(saved_id)
        assert result is True

        # Verify deletion
        retrieved = calculator.get_metrics_by_id(saved_id)
        assert retrieved is None

    def test_delete_metrics_not_found(self, db_session):
        """Test deleting non-existent metrics."""
        calculator = MetricsCalculator(db=db_session)
        result = calculator.delete_metrics("non-existent-id")
        assert result is False
