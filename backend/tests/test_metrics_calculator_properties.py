"""
Property-based tests for the Metrics Calculator service.

Feature: ai-math-tutor, Property 10: 學習指標計算正確性
Validates: Requirements 9.1, 9.3, 9.4

Tests that learning metrics calculations are correct:
- WPM = 總字數 / 發話時間(分鐘)
- 停頓比例 = 停頓總時長 / 總時長
- 提示依賴度 = 1 - Σ(提示次數 × 權重) / 總互動輪數

Feature: ai-math-tutor, Property 11: 學習指標持久化完整性
Validates: Requirements 9.5

Tests that learning metrics persistence is complete:
- 儲存至資料庫後查詢應返回相同的指標值
"""
import uuid
from datetime import datetime

import pytest
from hypothesis import given, strategies as st, settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.database import Base
from backend.services.metrics_calculator import (
    MetricsCalculator,
    MetricsReport,
    PauseData,
    HintUsageData,
)


# Strategy for generating valid pause data
@st.composite
def valid_pause_strategy(draw):
    """Generate valid PauseData with end_time >= start_time."""
    start_time = draw(st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False))
    duration = draw(st.floats(min_value=0.0, max_value=500.0, allow_nan=False, allow_infinity=False))
    end_time = start_time + duration
    return PauseData(start_time=start_time, end_time=end_time, duration=duration)


# Strategy for generating valid hint usage data
hint_strategy = st.builds(
    HintUsageData,
    level=st.integers(min_value=1, max_value=3),
    concept=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))),
    timestamp=st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
)


class TestMetricsCalculatorProperties:
    """
    Property-based tests for MetricsCalculator.
    
    Feature: ai-math-tutor, Property 10: 學習指標計算正確性
    Validates: Requirements 9.1, 9.3, 9.4
    """

    @settings(max_examples=100)
    @given(
        word_count=st.integers(min_value=0, max_value=100000),
        duration_minutes=st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False),
    )
    def test_wpm_calculation_correctness(self, word_count, duration_minutes):
        """
        Property 10 (Part 1): WPM 計算正確性
        
        *For any* valid word count and duration, WPM should equal word_count / duration_minutes.
        
        Feature: ai-math-tutor, Property 10: 學習指標計算正確性
        Validates: Requirements 9.1
        """
        calculator = MetricsCalculator()
        wpm = calculator.calculate_wpm(word_count, duration_minutes)
        expected_wpm = word_count / duration_minutes
        
        # Allow small floating point tolerance
        assert abs(wpm - expected_wpm) < 0.0001, (
            f"WPM calculation incorrect: got {wpm}, expected {expected_wpm}"
        )

    @settings(max_examples=100)
    @given(
        pauses=st.lists(valid_pause_strategy(), min_size=0, max_size=20),
        total_duration=st.floats(min_value=0.1, max_value=10000.0, allow_nan=False, allow_infinity=False),
    )
    def test_pause_rate_calculation_correctness(self, pauses, total_duration):
        """
        Property 10 (Part 2): 停頓比例計算正確性
        
        *For any* list of pauses and total duration, pause_rate should equal
        sum(pause_durations) / total_duration, clamped to [0, 1].
        
        Feature: ai-math-tutor, Property 10: 學習指標計算正確性
        Validates: Requirements 9.3
        """
        calculator = MetricsCalculator()
        pause_rate = calculator.calculate_pause_rate(pauses, total_duration)
        
        # Calculate expected pause rate
        total_pause_duration = sum(p.duration for p in pauses)
        expected_rate = total_pause_duration / total_duration
        expected_rate_clamped = max(0.0, min(1.0, expected_rate))
        
        # Allow small floating point tolerance
        assert abs(pause_rate - expected_rate_clamped) < 0.0001, (
            f"Pause rate calculation incorrect: got {pause_rate}, expected {expected_rate_clamped}"
        )

    @settings(max_examples=100)
    @given(
        pauses=st.lists(valid_pause_strategy(), min_size=0, max_size=20),
        total_duration=st.floats(min_value=0.1, max_value=10000.0, allow_nan=False, allow_infinity=False),
    )
    def test_pause_rate_bounded(self, pauses, total_duration):
        """
        Property 10 (Part 2b): 停頓比例範圍正確性
        
        *For any* input, pause_rate should always be in [0, 1].
        
        Feature: ai-math-tutor, Property 10: 學習指標計算正確性
        Validates: Requirements 9.3
        """
        calculator = MetricsCalculator()
        pause_rate = calculator.calculate_pause_rate(pauses, total_duration)
        
        assert 0.0 <= pause_rate <= 1.0, (
            f"Pause rate out of bounds: {pause_rate}"
        )

    @settings(max_examples=100)
    @given(
        hints=st.lists(hint_strategy, min_size=0, max_size=20),
        total_turns=st.integers(min_value=1, max_value=1000),
    )
    def test_hint_dependency_calculation_correctness(self, hints, total_turns):
        """
        Property 10 (Part 3): 提示依賴度計算正確性
        
        *For any* list of hints and total turns, hint_dependency should equal
        1 - Σ(hint_weight) / total_turns, clamped to [0, 1].
        
        Feature: ai-math-tutor, Property 10: 學習指標計算正確性
        Validates: Requirements 9.4
        """
        calculator = MetricsCalculator()
        hint_dependency = calculator.calculate_hint_dependency(hints, total_turns)
        
        # Calculate expected hint dependency
        weighted_sum = sum(h.weight for h in hints)
        expected_dependency = 1 - (weighted_sum / total_turns)
        expected_dependency_clamped = max(0.0, min(1.0, expected_dependency))
        
        # Allow small floating point tolerance
        assert abs(hint_dependency - expected_dependency_clamped) < 0.0001, (
            f"Hint dependency calculation incorrect: got {hint_dependency}, expected {expected_dependency_clamped}"
        )

    @settings(max_examples=100)
    @given(
        hints=st.lists(hint_strategy, min_size=0, max_size=20),
        total_turns=st.integers(min_value=0, max_value=1000),
    )
    def test_hint_dependency_bounded(self, hints, total_turns):
        """
        Property 10 (Part 3b): 提示依賴度範圍正確性
        
        *For any* input, hint_dependency should always be in [0, 1].
        
        Feature: ai-math-tutor, Property 10: 學習指標計算正確性
        Validates: Requirements 9.4
        """
        calculator = MetricsCalculator()
        hint_dependency = calculator.calculate_hint_dependency(hints, total_turns)
        
        assert 0.0 <= hint_dependency <= 1.0, (
            f"Hint dependency out of bounds: {hint_dependency}"
        )

    @settings(max_examples=100)
    @given(
        hints=st.lists(hint_strategy, min_size=0, max_size=10),
        total_turns=st.integers(min_value=1, max_value=100),
    )
    def test_hint_dependency_monotonic(self, hints, total_turns):
        """
        Property 10 (Part 3c): 提示依賴度單調性
        
        *For any* hint list, adding more hints should not increase hint_dependency
        (i.e., more hints = lower independence score).
        
        Feature: ai-math-tutor, Property 10: 學習指標計算正確性
        Validates: Requirements 9.4
        """
        calculator = MetricsCalculator()
        
        # Calculate dependency with current hints
        dependency_before = calculator.calculate_hint_dependency(hints, total_turns)
        
        # Add one more hint
        new_hint = HintUsageData(level=2, concept="test", timestamp=0.0)
        hints_with_extra = hints + [new_hint]
        dependency_after = calculator.calculate_hint_dependency(hints_with_extra, total_turns)
        
        # More hints should result in lower or equal dependency
        assert dependency_after <= dependency_before + 0.0001, (
            f"Hint dependency should not increase with more hints: "
            f"before={dependency_before}, after={dependency_after}"
        )

    @settings(max_examples=100)
    @given(
        word_count=st.integers(min_value=1, max_value=10000),
        duration_minutes=st.floats(min_value=0.1, max_value=60.0, allow_nan=False, allow_infinity=False),
        pauses=st.lists(valid_pause_strategy(), min_size=0, max_size=10),
        hints=st.lists(hint_strategy, min_size=0, max_size=10),
        total_turns=st.integers(min_value=1, max_value=100),
    )
    def test_metrics_report_consistency(
        self, word_count, duration_minutes, pauses, hints, total_turns
    ):
        """
        Property 10 (Combined): 完整指標報告一致性
        
        *For any* valid session data, the metrics report should contain
        values consistent with individual calculations.
        
        Feature: ai-math-tutor, Property 10: 學習指標計算正確性
        Validates: Requirements 9.1, 9.3, 9.4
        """
        calculator = MetricsCalculator()
        
        # Generate metrics report
        report = calculator.generate_metrics_report(
            session_id="test-session",
            word_count=word_count,
            duration_minutes=duration_minutes,
            pauses=pauses,
            hints=hints,
            total_turns=total_turns,
            covered_concepts=["concept1"],
            required_concepts=["concept1", "concept2"],
        )
        
        # Calculate expected values individually
        expected_wpm = word_count / duration_minutes
        total_duration_seconds = duration_minutes * 60
        total_pause_duration = sum(p.duration for p in pauses)
        expected_pause_rate = max(0.0, min(1.0, total_pause_duration / total_duration_seconds))
        weighted_hints = sum(h.weight for h in hints)
        expected_hint_dependency = max(0.0, min(1.0, 1 - (weighted_hints / total_turns)))
        
        # Verify consistency
        assert abs(report.wpm - expected_wpm) < 0.0001, (
            f"Report WPM inconsistent: got {report.wpm}, expected {expected_wpm}"
        )
        assert abs(report.pause_rate - expected_pause_rate) < 0.0001, (
            f"Report pause_rate inconsistent: got {report.pause_rate}, expected {expected_pause_rate}"
        )
        assert abs(report.hint_dependency - expected_hint_dependency) < 0.0001, (
            f"Report hint_dependency inconsistent: got {report.hint_dependency}, expected {expected_hint_dependency}"
        )


# Strategy for generating valid MetricsReport
@st.composite
def valid_metrics_report_strategy(draw):
    """Generate valid MetricsReport with realistic values."""
    session_id = draw(st.text(min_size=1, max_size=36, alphabet=st.characters(whitelist_categories=('L', 'N', 'Pd'))))
    wpm = draw(st.floats(min_value=0.0, max_value=500.0, allow_nan=False, allow_infinity=False))
    pause_rate = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    hint_dependency = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    concept_coverage = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    focus_duration = draw(st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False))
    
    return MetricsReport(
        id=str(uuid.uuid4()),
        session_id=session_id,
        wpm=wpm,
        pause_rate=pause_rate,
        hint_dependency=hint_dependency,
        concept_coverage=concept_coverage,
        focus_duration=focus_duration,
        created_at=datetime.utcnow()
    )


class TestMetricsPersistenceProperties:
    """
    Property-based tests for MetricsCalculator persistence.
    
    Feature: ai-math-tutor, Property 11: 學習指標持久化完整性
    Validates: Requirements 9.5
    """

    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Create a fresh in-memory database for each test."""
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=self.engine)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = TestingSessionLocal()
        yield
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    @settings(max_examples=100)
    @given(
        wpm=st.floats(min_value=0.0, max_value=500.0, allow_nan=False, allow_infinity=False),
        pause_rate=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        hint_dependency=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        concept_coverage=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        focus_duration=st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
    )
    def test_metrics_persistence_round_trip(
        self, wpm, pause_rate, hint_dependency, concept_coverage, focus_duration
    ):
        """
        Property 11: 學習指標持久化完整性
        
        *For any* 計算完成的學習指標，儲存至資料庫後查詢應返回相同的指標值。
        
        Feature: ai-math-tutor, Property 11: 學習指標持久化完整性
        Validates: Requirements 9.5
        """
        # Create a unique session_id for this test
        session_id = str(uuid.uuid4())
        metrics_id = str(uuid.uuid4())
        
        # Create metrics report
        original_metrics = MetricsReport(
            id=metrics_id,
            session_id=session_id,
            wpm=wpm,
            pause_rate=pause_rate,
            hint_dependency=hint_dependency,
            concept_coverage=concept_coverage,
            focus_duration=focus_duration,
            created_at=datetime.utcnow()
        )
        
        # Create calculator with database session
        calculator = MetricsCalculator(db=self.db)
        
        # Save metrics
        saved_id = calculator.save_metrics(original_metrics)
        assert saved_id == metrics_id, "Saved ID should match original ID"
        
        # Retrieve metrics by ID
        retrieved_metrics = calculator.get_metrics_by_id(metrics_id)
        
        # Verify round-trip: retrieved values should match original
        assert retrieved_metrics is not None, "Retrieved metrics should not be None"
        assert retrieved_metrics.id == original_metrics.id, (
            f"ID mismatch: got {retrieved_metrics.id}, expected {original_metrics.id}"
        )
        assert retrieved_metrics.session_id == original_metrics.session_id, (
            f"session_id mismatch: got {retrieved_metrics.session_id}, expected {original_metrics.session_id}"
        )
        assert abs(retrieved_metrics.wpm - original_metrics.wpm) < 0.0001, (
            f"wpm mismatch: got {retrieved_metrics.wpm}, expected {original_metrics.wpm}"
        )
        assert abs(retrieved_metrics.pause_rate - original_metrics.pause_rate) < 0.0001, (
            f"pause_rate mismatch: got {retrieved_metrics.pause_rate}, expected {original_metrics.pause_rate}"
        )
        assert abs(retrieved_metrics.hint_dependency - original_metrics.hint_dependency) < 0.0001, (
            f"hint_dependency mismatch: got {retrieved_metrics.hint_dependency}, expected {original_metrics.hint_dependency}"
        )
        assert abs(retrieved_metrics.concept_coverage - original_metrics.concept_coverage) < 0.0001, (
            f"concept_coverage mismatch: got {retrieved_metrics.concept_coverage}, expected {original_metrics.concept_coverage}"
        )
        assert abs(retrieved_metrics.focus_duration - original_metrics.focus_duration) < 0.0001, (
            f"focus_duration mismatch: got {retrieved_metrics.focus_duration}, expected {original_metrics.focus_duration}"
        )

    @settings(max_examples=100)
    @given(
        wpm=st.floats(min_value=0.0, max_value=500.0, allow_nan=False, allow_infinity=False),
        pause_rate=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        hint_dependency=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        concept_coverage=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        focus_duration=st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
    )
    def test_metrics_persistence_by_session_id(
        self, wpm, pause_rate, hint_dependency, concept_coverage, focus_duration
    ):
        """
        Property 11 (Part 2): 透過 session_id 查詢持久化完整性
        
        *For any* 計算完成的學習指標，透過 session_id 查詢應返回相同的指標值。
        
        Feature: ai-math-tutor, Property 11: 學習指標持久化完整性
        Validates: Requirements 9.5
        """
        # Create a unique session_id for this test
        session_id = str(uuid.uuid4())
        metrics_id = str(uuid.uuid4())
        
        # Create metrics report
        original_metrics = MetricsReport(
            id=metrics_id,
            session_id=session_id,
            wpm=wpm,
            pause_rate=pause_rate,
            hint_dependency=hint_dependency,
            concept_coverage=concept_coverage,
            focus_duration=focus_duration,
            created_at=datetime.utcnow()
        )
        
        # Create calculator with database session
        calculator = MetricsCalculator(db=self.db)
        
        # Save metrics
        calculator.save_metrics(original_metrics)
        
        # Retrieve metrics by session_id
        retrieved_metrics = calculator.get_metrics(session_id)
        
        # Verify round-trip: retrieved values should match original
        assert retrieved_metrics is not None, "Retrieved metrics should not be None"
        assert retrieved_metrics.session_id == original_metrics.session_id, (
            f"session_id mismatch: got {retrieved_metrics.session_id}, expected {original_metrics.session_id}"
        )
        assert abs(retrieved_metrics.wpm - original_metrics.wpm) < 0.0001, (
            f"wpm mismatch: got {retrieved_metrics.wpm}, expected {original_metrics.wpm}"
        )
        assert abs(retrieved_metrics.pause_rate - original_metrics.pause_rate) < 0.0001, (
            f"pause_rate mismatch: got {retrieved_metrics.pause_rate}, expected {original_metrics.pause_rate}"
        )
        assert abs(retrieved_metrics.hint_dependency - original_metrics.hint_dependency) < 0.0001, (
            f"hint_dependency mismatch: got {retrieved_metrics.hint_dependency}, expected {original_metrics.hint_dependency}"
        )
        assert abs(retrieved_metrics.concept_coverage - original_metrics.concept_coverage) < 0.0001, (
            f"concept_coverage mismatch: got {retrieved_metrics.concept_coverage}, expected {original_metrics.concept_coverage}"
        )
        assert abs(retrieved_metrics.focus_duration - original_metrics.focus_duration) < 0.0001, (
            f"focus_duration mismatch: got {retrieved_metrics.focus_duration}, expected {original_metrics.focus_duration}"
        )
