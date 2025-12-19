"""
Property-based tests for Error Book Manager.

Feature: ai-math-tutor, Property 4: 錯題歸檔完整性
Validates: Requirements 4.1, 4.2

Feature: ai-math-tutor, Property 5: 錯題篩選正確性
Validates: Requirements 4.3
"""
import json
import uuid
from datetime import datetime, timedelta
import pytest
from hypothesis import given, strategies as st, settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.database import Base
from backend.models.student import Student
from backend.models.question import Question
from backend.models.error_book import ErrorRecord
from backend.services.error_book import ErrorBookManager


def create_test_db():
    """Create a fresh test database session."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return TestingSessionLocal()


# Strategies for generating test data
subject_strategy = st.sampled_from(['數學', '代數', '幾何', '統計', '微積分'])
unit_strategy = st.sampled_from([
    '一元一次方程式', '二元一次方程式', '三角函數', '畢氏定理', '圓的性質',
    '因式分解', '平方根', '比例', '機率', '統計圖表'
])
difficulty_strategy = st.integers(min_value=1, max_value=3)
question_type_strategy = st.sampled_from(['MULTIPLE_CHOICE', 'FILL_BLANK', 'CALCULATION', 'PROOF'])
error_type_strategy = st.sampled_from(['CALCULATION', 'CONCEPT', 'CARELESS'])

# Strategy for generating non-empty answer strings
answer_strategy = st.text(
    min_size=1,
    max_size=100,
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))
).filter(lambda x: x.strip())  # Ensure non-empty after stripping


@st.composite
def student_strategy(draw):
    """Generate a valid Student."""
    return Student(
        id=str(uuid.uuid4()),
        name=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L',)))),
        grade=draw(st.integers(min_value=7, max_value=9))
    )


@st.composite
def question_strategy(draw):
    """Generate a valid Question."""
    return Question(
        id=str(uuid.uuid4()),
        content=draw(st.text(min_size=5, max_size=200, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z')))),
        type=draw(question_type_strategy),
        subject=draw(subject_strategy),
        unit=draw(unit_strategy),
        difficulty=draw(difficulty_strategy),
        standard_solution=draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))))
    )



# =============================================================================
# Property 4: 錯題歸檔完整性
# =============================================================================

@settings(max_examples=100, deadline=5000)
@given(
    student=student_strategy(),
    question=question_strategy(),
    student_answer=answer_strategy,
    correct_answer=answer_strategy
)
def test_error_record_archiving_completeness(student, question, student_answer, correct_answer):
    """
    Feature: ai-math-tutor, Property 4: 錯題歸檔完整性
    Validates: Requirements 4.1, 4.2
    
    Property: For any student's incorrect answer, Error_Book should store a complete
    error record (question ID, student answer, correct answer, error type tags),
    and querying that error record should return the same data.
    """
    db = create_test_db()
    try:
        # Setup: Add student and question to database
        db.add(student)
        db.add(question)
        db.commit()
        
        manager = ErrorBookManager(db)
        
        # Add error record
        error_record = manager.add_error(
            student_id=student.id,
            question_id=question.id,
            student_answer=student_answer,
            correct_answer=correct_answer
        )
        
        # Verify the error record was created with all required fields
        assert error_record.id is not None, "Error record ID should not be None"
        assert error_record.student_id == student.id, \
            f"Student ID mismatch: expected {student.id}, got {error_record.student_id}"
        assert error_record.question_id == question.id, \
            f"Question ID mismatch: expected {question.id}, got {error_record.question_id}"
        assert error_record.student_answer == student_answer, \
            f"Student answer mismatch: expected '{student_answer}', got '{error_record.student_answer}'"
        assert error_record.correct_answer == correct_answer, \
            f"Correct answer mismatch: expected '{correct_answer}', got '{error_record.correct_answer}'"
        
        # Verify error type is auto-assigned (Requirement 4.2)
        assert error_record.error_type is not None, "Error type should be auto-assigned"
        assert error_record.error_type in ['CALCULATION', 'CONCEPT', 'CARELESS'], \
            f"Invalid error type: {error_record.error_type}"
        
        # Verify error tags are auto-generated (Requirement 4.2)
        assert error_record.error_tags is not None, "Error tags should be auto-generated"
        tags = json.loads(error_record.error_tags)
        assert isinstance(tags, list), "Error tags should be a list"
        assert len(tags) > 0, "Error tags should not be empty"
        
        # Verify timestamp is set
        assert error_record.timestamp is not None, "Timestamp should be set"
        
        # Verify repaired status is initialized to False
        assert error_record.repaired is False, "Repaired status should be False initially"
        
        # Query the error record back and verify data integrity
        retrieved_record = manager.get_error_by_id(error_record.id)
        assert retrieved_record is not None, "Should be able to retrieve the error record"
        
        # Verify retrieved data matches original
        assert retrieved_record.id == error_record.id
        assert retrieved_record.student_id == student.id
        assert retrieved_record.question_id == question.id
        assert retrieved_record.student_answer == student_answer
        assert retrieved_record.correct_answer == correct_answer
        assert retrieved_record.error_type == error_record.error_type
        assert retrieved_record.error_tags == error_record.error_tags
        
    finally:
        db.close()


@settings(max_examples=100, deadline=5000)
@given(
    student=student_strategy(),
    question=question_strategy(),
    student_answer=answer_strategy,
    correct_answer=answer_strategy,
    explicit_error_type=error_type_strategy
)
def test_error_record_with_explicit_type_completeness(
    student, question, student_answer, correct_answer, explicit_error_type
):
    """
    Feature: ai-math-tutor, Property 4: 錯題歸檔完整性
    Validates: Requirements 4.1, 4.2
    
    Property: When an explicit error type is provided, Error_Book should store
    the complete error record with the specified type, and querying should
    return the same data.
    """
    db = create_test_db()
    try:
        # Setup
        db.add(student)
        db.add(question)
        db.commit()
        
        manager = ErrorBookManager(db)
        
        # Add error record with explicit type
        error_record = manager.add_error(
            student_id=student.id,
            question_id=question.id,
            student_answer=student_answer,
            correct_answer=correct_answer,
            error_type=explicit_error_type
        )
        
        # Verify the explicit error type is preserved
        assert error_record.error_type == explicit_error_type, \
            f"Error type should be '{explicit_error_type}', got '{error_record.error_type}'"
        
        # Verify all other required fields are present
        assert error_record.id is not None
        assert error_record.student_id == student.id
        assert error_record.question_id == question.id
        assert error_record.student_answer == student_answer
        assert error_record.correct_answer == correct_answer
        assert error_record.error_tags is not None
        assert error_record.timestamp is not None
        
        # Query back and verify
        retrieved = manager.get_error_by_id(error_record.id)
        assert retrieved is not None
        assert retrieved.error_type == explicit_error_type
        
    finally:
        db.close()


@settings(max_examples=100, deadline=5000)
@given(
    student=student_strategy(),
    question=question_strategy(),
    student_answer=answer_strategy,
    correct_answer=answer_strategy,
    explicit_tags=st.lists(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L',))),
        min_size=1,
        max_size=5
    )
)
def test_error_record_with_explicit_tags_completeness(
    student, question, student_answer, correct_answer, explicit_tags
):
    """
    Feature: ai-math-tutor, Property 4: 錯題歸檔完整性
    Validates: Requirements 4.1, 4.2
    
    Property: When explicit error tags are provided, Error_Book should store
    the complete error record with the specified tags, and querying should
    return the same data.
    """
    db = create_test_db()
    try:
        # Setup
        db.add(student)
        db.add(question)
        db.commit()
        
        manager = ErrorBookManager(db)
        
        # Add error record with explicit tags
        error_record = manager.add_error(
            student_id=student.id,
            question_id=question.id,
            student_answer=student_answer,
            correct_answer=correct_answer,
            error_tags=explicit_tags
        )
        
        # Verify the explicit tags are preserved
        stored_tags = json.loads(error_record.error_tags)
        for tag in explicit_tags:
            assert tag in stored_tags, \
                f"Tag '{tag}' should be in stored tags {stored_tags}"
        
        # Verify all other required fields are present
        assert error_record.id is not None
        assert error_record.student_id == student.id
        assert error_record.question_id == question.id
        assert error_record.student_answer == student_answer
        assert error_record.correct_answer == correct_answer
        assert error_record.error_type is not None
        assert error_record.timestamp is not None
        
        # Query back and verify
        retrieved = manager.get_error_by_id(error_record.id)
        assert retrieved is not None
        retrieved_tags = json.loads(retrieved.error_tags)
        for tag in explicit_tags:
            assert tag in retrieved_tags
        
    finally:
        db.close()


@settings(max_examples=100, deadline=5000)
@given(
    student=student_strategy(),
    question=question_strategy(),
    num_errors=st.integers(min_value=1, max_value=10)
)
def test_multiple_error_records_archiving_completeness(student, question, num_errors):
    """
    Feature: ai-math-tutor, Property 4: 錯題歸檔完整性
    Validates: Requirements 4.1, 4.2
    
    Property: For multiple error records from the same student, Error_Book should
    store all records completely, and querying should return all records with
    correct data.
    """
    db = create_test_db()
    try:
        # Setup
        db.add(student)
        db.add(question)
        db.commit()
        
        manager = ErrorBookManager(db)
        
        # Add multiple error records
        created_records = []
        for i in range(num_errors):
            error_record = manager.add_error(
                student_id=student.id,
                question_id=question.id,
                student_answer=f"wrong_answer_{i}",
                correct_answer=f"correct_answer_{i}"
            )
            created_records.append(error_record)
        
        # Verify all records were created
        assert len(created_records) == num_errors
        
        # Query all errors for the student
        retrieved_errors = manager.get_errors(student.id)
        
        # Verify count matches
        assert len(retrieved_errors) == num_errors, \
            f"Expected {num_errors} errors, got {len(retrieved_errors)}"
        
        # Verify each created record can be retrieved
        created_ids = {r.id for r in created_records}
        retrieved_ids = {r.id for r in retrieved_errors}
        assert created_ids == retrieved_ids, \
            "All created error records should be retrievable"
        
        # Verify each record has complete data
        for record in retrieved_errors:
            assert record.student_id == student.id
            assert record.question_id == question.id
            assert record.student_answer is not None
            assert record.correct_answer is not None
            assert record.error_type is not None
            assert record.error_tags is not None
            assert record.timestamp is not None
        
    finally:
        db.close()


# =============================================================================
# Property 5: 錯題篩選正確性
# =============================================================================

@settings(max_examples=100, deadline=5000)
@given(
    student=student_strategy(),
    questions=st.lists(question_strategy(), min_size=2, max_size=5, unique_by=lambda q: q.id),
    filter_error_type=error_type_strategy
)
def test_error_filter_by_error_type_correctness(student, questions, filter_error_type):
    """
    Feature: ai-math-tutor, Property 5: 錯題篩選正確性
    Validates: Requirements 4.3
    
    Property: For any error type filter, Error_Book should return only error records
    that match the specified error type.
    """
    from backend.services.error_book import ErrorCriteria
    
    db = create_test_db()
    try:
        # Setup: Add student and questions
        db.add(student)
        for q in questions:
            db.add(q)
        db.commit()
        
        manager = ErrorBookManager(db)
        
        # Create error records with different error types
        error_types = ['CALCULATION', 'CONCEPT', 'CARELESS']
        created_records = []
        for i, q in enumerate(questions):
            error_type = error_types[i % len(error_types)]
            record = manager.add_error(
                student_id=student.id,
                question_id=q.id,
                student_answer=f"wrong_{i}",
                correct_answer=f"correct_{i}",
                error_type=error_type
            )
            created_records.append(record)
        
        # Filter by error type
        criteria = ErrorCriteria(error_type=filter_error_type)
        filtered_errors = manager.get_errors(student.id, criteria)
        
        # Verify all returned records match the filter criteria
        for error in filtered_errors:
            assert error.error_type == filter_error_type, \
                f"Error type mismatch: expected '{filter_error_type}', got '{error.error_type}'"
        
        # Verify we got all matching records
        expected_count = sum(1 for r in created_records if r.error_type == filter_error_type)
        assert len(filtered_errors) == expected_count, \
            f"Expected {expected_count} errors with type '{filter_error_type}', got {len(filtered_errors)}"
        
    finally:
        db.close()


@settings(max_examples=100, deadline=5000)
@given(
    student=student_strategy(),
    questions=st.lists(question_strategy(), min_size=2, max_size=5, unique_by=lambda q: q.id),
    filter_repaired=st.booleans()
)
def test_error_filter_by_repaired_status_correctness(student, questions, filter_repaired):
    """
    Feature: ai-math-tutor, Property 5: 錯題篩選正確性
    Validates: Requirements 4.3
    
    Property: For any repaired status filter, Error_Book should return only error
    records that match the specified repaired status.
    """
    from backend.services.error_book import ErrorCriteria
    
    db = create_test_db()
    try:
        # Setup
        db.add(student)
        for q in questions:
            db.add(q)
        db.commit()
        
        manager = ErrorBookManager(db)
        
        # Create error records and mark some as repaired
        created_records = []
        for i, q in enumerate(questions):
            record = manager.add_error(
                student_id=student.id,
                question_id=q.id,
                student_answer=f"wrong_{i}",
                correct_answer=f"correct_{i}"
            )
            # Mark every other record as repaired
            if i % 2 == 0:
                manager.mark_as_repaired(record.id)
                record.repaired = True
            created_records.append(record)
        
        # Filter by repaired status
        criteria = ErrorCriteria(repaired_status=filter_repaired)
        filtered_errors = manager.get_errors(student.id, criteria)
        
        # Verify all returned records match the filter criteria
        for error in filtered_errors:
            assert error.repaired == filter_repaired, \
                f"Repaired status mismatch: expected {filter_repaired}, got {error.repaired}"
        
        # Verify we got all matching records
        expected_count = sum(1 for r in created_records if r.repaired == filter_repaired)
        assert len(filtered_errors) == expected_count, \
            f"Expected {expected_count} errors with repaired={filter_repaired}, got {len(filtered_errors)}"
        
    finally:
        db.close()


@settings(max_examples=100, deadline=5000)
@given(
    student=student_strategy(),
    questions=st.lists(question_strategy(), min_size=2, max_size=5, unique_by=lambda q: q.id)
)
def test_error_filter_by_unit_correctness(student, questions):
    """
    Feature: ai-math-tutor, Property 5: 錯題篩選正確性
    Validates: Requirements 4.3
    
    Property: For any unit filter, Error_Book should return only error records
    whose associated questions belong to the specified unit.
    """
    from backend.services.error_book import ErrorCriteria
    
    db = create_test_db()
    try:
        # Setup
        db.add(student)
        for q in questions:
            db.add(q)
        db.commit()
        
        manager = ErrorBookManager(db)
        
        # Create error records for each question
        created_records = []
        for i, q in enumerate(questions):
            record = manager.add_error(
                student_id=student.id,
                question_id=q.id,
                student_answer=f"wrong_{i}",
                correct_answer=f"correct_{i}"
            )
            created_records.append((record, q))
        
        # Pick a unit to filter by (use the first question's unit)
        filter_unit = questions[0].unit
        
        # Filter by unit
        criteria = ErrorCriteria(unit=filter_unit)
        filtered_errors = manager.get_errors(student.id, criteria)
        
        # Verify all returned records are associated with questions in the specified unit
        for error in filtered_errors:
            # Get the associated question
            question = db.query(Question).filter(Question.id == error.question_id).first()
            assert question is not None, "Question should exist"
            assert question.unit == filter_unit, \
                f"Unit mismatch: expected '{filter_unit}', got '{question.unit}'"
        
        # Verify we got all matching records
        expected_count = sum(1 for _, q in created_records if q.unit == filter_unit)
        assert len(filtered_errors) == expected_count, \
            f"Expected {expected_count} errors in unit '{filter_unit}', got {len(filtered_errors)}"
        
    finally:
        db.close()


@settings(max_examples=100, deadline=5000)
@given(
    student=student_strategy(),
    question=question_strategy(),
    num_errors=st.integers(min_value=3, max_value=8)
)
def test_error_filter_by_date_range_correctness(student, question, num_errors):
    """
    Feature: ai-math-tutor, Property 5: 錯題篩選正確性
    Validates: Requirements 4.3
    
    Property: For any date range filter, Error_Book should return only error records
    whose timestamps fall within the specified date range.
    """
    from backend.services.error_book import ErrorCriteria
    
    db = create_test_db()
    try:
        # Setup
        db.add(student)
        db.add(question)
        db.commit()
        
        manager = ErrorBookManager(db)
        
        # Create error records with different timestamps
        base_time = datetime.utcnow()
        created_records = []
        for i in range(num_errors):
            record = manager.add_error(
                student_id=student.id,
                question_id=question.id,
                student_answer=f"wrong_{i}",
                correct_answer=f"correct_{i}"
            )
            # Manually adjust timestamp to spread across days
            record.timestamp = base_time - timedelta(days=i)
            db.commit()
            created_records.append(record)
        
        # Define date range (last 2 days)
        date_from = base_time - timedelta(days=2)
        date_to = base_time + timedelta(days=1)  # Include today
        
        # Filter by date range
        criteria = ErrorCriteria(date_from=date_from, date_to=date_to)
        filtered_errors = manager.get_errors(student.id, criteria)
        
        # Verify all returned records fall within the date range
        for error in filtered_errors:
            assert error.timestamp >= date_from, \
                f"Timestamp {error.timestamp} is before date_from {date_from}"
            assert error.timestamp <= date_to, \
                f"Timestamp {error.timestamp} is after date_to {date_to}"
        
        # Verify we got all matching records
        expected_count = sum(
            1 for r in created_records 
            if date_from <= r.timestamp <= date_to
        )
        assert len(filtered_errors) == expected_count, \
            f"Expected {expected_count} errors in date range, got {len(filtered_errors)}"
        
    finally:
        db.close()


@settings(max_examples=100, deadline=5000)
@given(
    student=student_strategy(),
    questions=st.lists(question_strategy(), min_size=3, max_size=6, unique_by=lambda q: q.id),
    filter_tag=st.sampled_from(['計算錯誤', '觀念錯誤', '粗心錯誤'])
)
def test_error_filter_by_tags_correctness(student, questions, filter_tag):
    """
    Feature: ai-math-tutor, Property 5: 錯題篩選正確性
    Validates: Requirements 4.3
    
    Property: For any tag filter, Error_Book should return only error records
    that contain the specified tag in their error_tags.
    """
    from backend.services.error_book import ErrorCriteria
    
    db = create_test_db()
    try:
        # Setup
        db.add(student)
        for q in questions:
            db.add(q)
        db.commit()
        
        manager = ErrorBookManager(db)
        
        # Create error records with specific tags
        tag_options = [['計算錯誤'], ['觀念錯誤'], ['粗心錯誤'], ['計算錯誤', '觀念錯誤']]
        created_records = []
        for i, q in enumerate(questions):
            tags = tag_options[i % len(tag_options)]
            record = manager.add_error(
                student_id=student.id,
                question_id=q.id,
                student_answer=f"wrong_{i}",
                correct_answer=f"correct_{i}",
                error_tags=tags
            )
            created_records.append((record, tags))
        
        # Filter by tag
        criteria = ErrorCriteria(tags=[filter_tag])
        filtered_errors = manager.get_errors(student.id, criteria)
        
        # Verify all returned records contain the specified tag
        for error in filtered_errors:
            stored_tags = json.loads(error.error_tags)
            assert filter_tag in stored_tags, \
                f"Tag '{filter_tag}' not found in error tags {stored_tags}"
        
        # Verify we got all matching records
        expected_count = sum(1 for _, tags in created_records if filter_tag in tags)
        assert len(filtered_errors) == expected_count, \
            f"Expected {expected_count} errors with tag '{filter_tag}', got {len(filtered_errors)}"
        
    finally:
        db.close()


@settings(max_examples=100, deadline=5000)
@given(
    student=student_strategy(),
    questions=st.lists(question_strategy(), min_size=4, max_size=8, unique_by=lambda q: q.id),
    filter_error_type=error_type_strategy,
    filter_repaired=st.booleans()
)
def test_error_filter_combined_criteria_correctness(student, questions, filter_error_type, filter_repaired):
    """
    Feature: ai-math-tutor, Property 5: 錯題篩選正確性
    Validates: Requirements 4.3
    
    Property: For any combination of filter criteria (error type + repaired status),
    Error_Book should return only error records that match ALL specified criteria.
    """
    from backend.services.error_book import ErrorCriteria
    
    db = create_test_db()
    try:
        # Setup
        db.add(student)
        for q in questions:
            db.add(q)
        db.commit()
        
        manager = ErrorBookManager(db)
        
        # Create error records with varied attributes
        error_types = ['CALCULATION', 'CONCEPT', 'CARELESS']
        created_records = []
        for i, q in enumerate(questions):
            error_type = error_types[i % len(error_types)]
            record = manager.add_error(
                student_id=student.id,
                question_id=q.id,
                student_answer=f"wrong_{i}",
                correct_answer=f"correct_{i}",
                error_type=error_type
            )
            # Mark some as repaired
            if i % 2 == 0:
                manager.mark_as_repaired(record.id)
                record.repaired = True
            created_records.append(record)
        
        # Filter by combined criteria
        criteria = ErrorCriteria(
            error_type=filter_error_type,
            repaired_status=filter_repaired
        )
        filtered_errors = manager.get_errors(student.id, criteria)
        
        # Verify all returned records match ALL filter criteria
        for error in filtered_errors:
            assert error.error_type == filter_error_type, \
                f"Error type mismatch: expected '{filter_error_type}', got '{error.error_type}'"
            assert error.repaired == filter_repaired, \
                f"Repaired status mismatch: expected {filter_repaired}, got {error.repaired}"
        
        # Verify we got all matching records
        expected_count = sum(
            1 for r in created_records 
            if r.error_type == filter_error_type and r.repaired == filter_repaired
        )
        assert len(filtered_errors) == expected_count, \
            f"Expected {expected_count} errors matching combined criteria, got {len(filtered_errors)}"
        
    finally:
        db.close()
