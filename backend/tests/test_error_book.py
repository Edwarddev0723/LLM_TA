"""
Tests for Error Book Manager.
"""
import pytest
import json
import uuid
from datetime import datetime, timedelta

from backend.models.student import Student
from backend.models.question import Question, Misconception
from backend.models.error_book import ErrorRecord
from backend.services.error_book import (
    ErrorBookManager,
    ErrorCriteria,
    ErrorStatistics,
)


@pytest.fixture
def sample_student(test_db):
    """Create a sample student for testing."""
    student = Student(
        id=str(uuid.uuid4()),
        name="測試學生",
        grade=8
    )
    test_db.add(student)
    test_db.commit()
    return student


@pytest.fixture
def sample_question(test_db):
    """Create a sample question for testing."""
    question = Question(
        id=str(uuid.uuid4()),
        content="解方程式: 2x + 3 = 7",
        type="CALCULATION",
        subject="數學",
        unit="代數",
        difficulty=1,
        standard_solution="x = 2"
    )
    test_db.add(question)
    test_db.commit()
    return question


@pytest.fixture
def error_book_manager(test_db):
    """Create an ErrorBookManager instance."""
    return ErrorBookManager(test_db)


class TestAddError:
    """Tests for add_error method."""

    def test_add_error_basic(self, test_db, error_book_manager, sample_student, sample_question):
        """Test adding a basic error record."""
        error = error_book_manager.add_error(
            student_id=sample_student.id,
            question_id=sample_question.id,
            student_answer="x = 5",
            correct_answer="x = 2"
        )
        
        assert error.id is not None
        assert error.student_id == sample_student.id
        assert error.question_id == sample_question.id
        assert error.student_answer == "x = 5"
        assert error.correct_answer == "x = 2"
        assert error.repaired is False
        assert error.error_type is not None
        assert error.error_tags is not None

    def test_add_error_with_explicit_type(self, test_db, error_book_manager, sample_student, sample_question):
        """Test adding an error with explicit error type."""
        error = error_book_manager.add_error(
            student_id=sample_student.id,
            question_id=sample_question.id,
            student_answer="x = 5",
            correct_answer="x = 2",
            error_type="CONCEPT"
        )
        
        assert error.error_type == "CONCEPT"

    def test_add_error_with_explicit_tags(self, test_db, error_book_manager, sample_student, sample_question):
        """Test adding an error with explicit tags."""
        tags = ["計算錯誤", "代數"]
        error = error_book_manager.add_error(
            student_id=sample_student.id,
            question_id=sample_question.id,
            student_answer="x = 5",
            correct_answer="x = 2",
            error_tags=tags
        )
        
        stored_tags = json.loads(error.error_tags)
        assert "計算錯誤" in stored_tags
        assert "代數" in stored_tags

    def test_auto_detect_careless_error(self, test_db, error_book_manager, sample_student, sample_question):
        """Test auto-detection of careless errors (sign error)."""
        error = error_book_manager.add_error(
            student_id=sample_student.id,
            question_id=sample_question.id,
            student_answer="-2",
            correct_answer="2"
        )
        
        assert error.error_type == "CARELESS"


class TestGetErrors:
    """Tests for get_errors method."""

    def test_get_errors_basic(self, test_db, error_book_manager, sample_student, sample_question):
        """Test getting all errors for a student."""
        # Add multiple errors
        error_book_manager.add_error(
            student_id=sample_student.id,
            question_id=sample_question.id,
            student_answer="x = 5",
            correct_answer="x = 2"
        )
        error_book_manager.add_error(
            student_id=sample_student.id,
            question_id=sample_question.id,
            student_answer="x = 10",
            correct_answer="x = 2"
        )
        
        errors = error_book_manager.get_errors(sample_student.id)
        assert len(errors) == 2

    def test_get_errors_filter_by_type(self, test_db, error_book_manager, sample_student, sample_question):
        """Test filtering errors by type."""
        error_book_manager.add_error(
            student_id=sample_student.id,
            question_id=sample_question.id,
            student_answer="x = 5",
            correct_answer="x = 2",
            error_type="CALCULATION"
        )
        error_book_manager.add_error(
            student_id=sample_student.id,
            question_id=sample_question.id,
            student_answer="x = 10",
            correct_answer="x = 2",
            error_type="CONCEPT"
        )
        
        criteria = ErrorCriteria(error_type="CALCULATION")
        errors = error_book_manager.get_errors(sample_student.id, criteria)
        
        assert len(errors) == 1
        assert errors[0].error_type == "CALCULATION"

    def test_get_errors_filter_by_repaired_status(self, test_db, error_book_manager, sample_student, sample_question):
        """Test filtering errors by repaired status."""
        error1 = error_book_manager.add_error(
            student_id=sample_student.id,
            question_id=sample_question.id,
            student_answer="x = 5",
            correct_answer="x = 2"
        )
        error_book_manager.add_error(
            student_id=sample_student.id,
            question_id=sample_question.id,
            student_answer="x = 10",
            correct_answer="x = 2"
        )
        
        # Mark first error as repaired
        error_book_manager.mark_as_repaired(error1.id)
        
        # Get only unrepaired errors
        criteria = ErrorCriteria(repaired_status=False)
        errors = error_book_manager.get_errors(sample_student.id, criteria)
        
        assert len(errors) == 1
        assert errors[0].repaired is False

    def test_get_errors_filter_by_unit(self, test_db, error_book_manager, sample_student):
        """Test filtering errors by unit."""
        # Create questions in different units
        q1 = Question(
            id=str(uuid.uuid4()),
            content="Q1",
            type="CALCULATION",
            subject="數學",
            unit="代數",
            difficulty=1,
            standard_solution="1"
        )
        q2 = Question(
            id=str(uuid.uuid4()),
            content="Q2",
            type="CALCULATION",
            subject="數學",
            unit="幾何",
            difficulty=1,
            standard_solution="2"
        )
        test_db.add_all([q1, q2])
        test_db.commit()
        
        error_book_manager.add_error(
            student_id=sample_student.id,
            question_id=q1.id,
            student_answer="wrong",
            correct_answer="1"
        )
        error_book_manager.add_error(
            student_id=sample_student.id,
            question_id=q2.id,
            student_answer="wrong",
            correct_answer="2"
        )
        
        criteria = ErrorCriteria(unit="代數")
        errors = error_book_manager.get_errors(sample_student.id, criteria)
        
        assert len(errors) == 1


class TestMarkAsRepaired:
    """Tests for mark_as_repaired method."""

    def test_mark_as_repaired_success(self, test_db, error_book_manager, sample_student, sample_question):
        """Test marking an error as repaired."""
        error = error_book_manager.add_error(
            student_id=sample_student.id,
            question_id=sample_question.id,
            student_answer="x = 5",
            correct_answer="x = 2"
        )
        
        assert error.repaired is False
        assert error.repaired_at is None
        
        updated = error_book_manager.mark_as_repaired(error.id)
        
        assert updated.repaired is True
        assert updated.repaired_at is not None

    def test_mark_as_repaired_not_found(self, test_db, error_book_manager):
        """Test marking a non-existent error as repaired."""
        result = error_book_manager.mark_as_repaired("non-existent-id")
        assert result is None


class TestGetErrorStatistics:
    """Tests for get_error_statistics method."""

    def test_get_statistics_basic(self, test_db, error_book_manager, sample_student, sample_question):
        """Test getting error statistics."""
        # Add errors with different types
        error_book_manager.add_error(
            student_id=sample_student.id,
            question_id=sample_question.id,
            student_answer="x = 5",
            correct_answer="x = 2",
            error_type="CALCULATION"
        )
        error_book_manager.add_error(
            student_id=sample_student.id,
            question_id=sample_question.id,
            student_answer="x = 10",
            correct_answer="x = 2",
            error_type="CALCULATION"
        )
        error1 = error_book_manager.add_error(
            student_id=sample_student.id,
            question_id=sample_question.id,
            student_answer="wrong concept",
            correct_answer="x = 2",
            error_type="CONCEPT"
        )
        
        # Mark one as repaired
        error_book_manager.mark_as_repaired(error1.id)
        
        stats = error_book_manager.get_error_statistics(sample_student.id)
        
        assert stats.total_errors == 3
        assert stats.repaired_count == 1
        assert stats.errors_by_type.get("CALCULATION") == 2
        assert stats.errors_by_type.get("CONCEPT") == 1
        assert "代數" in stats.errors_by_unit


class TestAutoTagging:
    """Tests for auto-tagging functionality."""

    def test_sign_error_detection(self, test_db, error_book_manager, sample_student, sample_question):
        """Test detection of sign errors."""
        error = error_book_manager.add_error(
            student_id=sample_student.id,
            question_id=sample_question.id,
            student_answer="-5",
            correct_answer="5"
        )
        
        tags = json.loads(error.error_tags)
        assert "符號錯誤" in tags

    def test_unit_tag_added(self, test_db, error_book_manager, sample_student, sample_question):
        """Test that unit is added as a tag."""
        error = error_book_manager.add_error(
            student_id=sample_student.id,
            question_id=sample_question.id,
            student_answer="x = 5",
            correct_answer="x = 2"
        )
        
        tags = json.loads(error.error_tags)
        assert "代數" in tags
