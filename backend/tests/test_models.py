"""
Tests for database models.
"""
import pytest
from datetime import datetime
import uuid

from backend.models import (
    Student,
    KnowledgeNode,
    KnowledgeRelation,
    Question,
    Misconception,
    Hint,
    Session,
    ConversationTurn,
    LearningMetrics,
    Pause,
    HintUsage,
    ErrorRecord,
)


def test_student_creation(test_db):
    """Test creating a student record."""
    student = Student(
        id=str(uuid.uuid4()),
        name="測試學生",
        grade=8
    )
    test_db.add(student)
    test_db.commit()

    result = test_db.query(Student).first()
    assert result.name == "測試學生"
    assert result.grade == 8


def test_knowledge_node_creation(test_db):
    """Test creating a knowledge node."""
    node = KnowledgeNode(
        id=str(uuid.uuid4()),
        name="一元一次方程式",
        subject="數學",
        unit="代數",
        difficulty=2,
        description="學習一元一次方程式的解法"
    )
    test_db.add(node)
    test_db.commit()

    result = test_db.query(KnowledgeNode).first()
    assert result.name == "一元一次方程式"
    assert result.difficulty == 2


def test_question_creation(test_db):
    """Test creating a question."""
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

    result = test_db.query(Question).first()
    assert result.content == "解方程式: 2x + 3 = 7"
    assert result.type == "CALCULATION"


def test_session_with_metrics(test_db):
    """Test creating a session with learning metrics."""
    student = Student(id=str(uuid.uuid4()), name="學生A", grade=7)
    question = Question(
        id=str(uuid.uuid4()),
        content="計算 3 + 5",
        type="CALCULATION",
        subject="數學",
        unit="算術",
        difficulty=1,
        standard_solution="8"
    )
    test_db.add_all([student, question])
    test_db.commit()

    session = Session(
        id=str(uuid.uuid4()),
        student_id=student.id,
        question_id=question.id,
        start_time=datetime.utcnow()
    )
    test_db.add(session)
    test_db.commit()

    metrics = LearningMetrics(
        id=str(uuid.uuid4()),
        session_id=session.id,
        wpm=45.5,
        pause_rate=0.15,
        hint_dependency=0.8,
        concept_coverage=0.95
    )
    test_db.add(metrics)
    test_db.commit()

    result = test_db.query(Session).first()
    assert result.learning_metrics.wpm == 45.5
    assert result.learning_metrics.concept_coverage == 0.95


def test_error_record_creation(test_db):
    """Test creating an error record."""
    student = Student(id=str(uuid.uuid4()), name="學生B", grade=8)
    question = Question(
        id=str(uuid.uuid4()),
        content="解方程式: x + 5 = 10",
        type="CALCULATION",
        subject="數學",
        unit="代數",
        difficulty=1,
        standard_solution="x = 5"
    )
    test_db.add_all([student, question])
    test_db.commit()

    error = ErrorRecord(
        id=str(uuid.uuid4()),
        student_id=student.id,
        question_id=question.id,
        student_answer="x = 15",
        correct_answer="x = 5",
        error_type="CALCULATION",
        error_tags='["計算錯誤"]',
        timestamp=datetime.utcnow()
    )
    test_db.add(error)
    test_db.commit()

    result = test_db.query(ErrorRecord).first()
    assert result.error_type == "CALCULATION"
    assert result.repaired is False
