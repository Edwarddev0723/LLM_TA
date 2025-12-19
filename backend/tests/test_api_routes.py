"""
Tests for API routes in the AI Math Tutor system.

Tests:
- Question API routes (14.1)
- Session API routes (14.2)
- Error Book API routes (14.3)
- Dashboard API routes (14.5)
"""
import pytest
import httpx
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.models.database import Base, get_db
from backend.models.question import Question, Hint, Misconception
from backend.models.knowledge import KnowledgeNode
from backend.models.student import Student
from backend.models.error_book import ErrorRecord
from backend.models.session import Session as SessionModel
from backend.models.metrics import LearningMetrics


# Test database setup
@pytest.fixture(scope="function")
def test_db():
    """Create a fresh test database for each test."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def override_get_db(test_db):
    """Override the get_db dependency."""
    def _override():
        try:
            yield test_db
        finally:
            pass
    return _override


@pytest.fixture
async def client(override_get_db):
    """Create test client with overridden database."""
    app.dependency_overrides[get_db] = override_get_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_knowledge_node(test_db):
    """Create a sample knowledge node."""
    node = KnowledgeNode(
        id="node-1",
        name="一元一次方程式",
        subject="數學",
        unit="代數",
        difficulty=1,
        description="基礎代數概念"
    )
    test_db.add(node)
    test_db.commit()
    return node


@pytest.fixture
def sample_question(test_db, sample_knowledge_node):
    """Create a sample question."""
    question = Question(
        id="q-1",
        content="解方程式: 2x + 3 = 7",
        type="CALCULATION",
        subject="數學",
        unit="代數",
        difficulty=1,
        standard_solution="x = 2"
    )
    question.knowledge_nodes.append(sample_knowledge_node)
    test_db.add(question)
    test_db.commit()
    return question


@pytest.fixture
def sample_student(test_db):
    """Create a sample student."""
    student = Student(
        id="student-1",
        name="測試學生",
        grade=7
    )
    test_db.add(student)
    test_db.commit()
    return student


@pytest.fixture
def sample_error_record(test_db, sample_student, sample_question):
    """Create a sample error record."""
    error = ErrorRecord(
        id="error-1",
        student_id=sample_student.id,
        question_id=sample_question.id,
        student_answer="x = 3",
        correct_answer="x = 2",
        error_type="CALCULATION",
        error_tags='["計算錯誤", "代數"]',
        timestamp=datetime.utcnow(),
        repaired=False
    )
    test_db.add(error)
    test_db.commit()
    return error


# ============== Question API Tests (14.1) ==============

@pytest.mark.asyncio
async def test_filter_questions_empty(client):
    """Test filtering questions when database is empty."""
    response = await client.get("/api/questions")
    assert response.status_code == 200
    data = response.json()
    assert data["questions"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_filter_questions_with_data(client, sample_question):
    """Test filtering questions with data."""
    response = await client.get("/api/questions")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["questions"][0]["id"] == "q-1"
    assert data["questions"][0]["subject"] == "數學"


@pytest.mark.asyncio
async def test_filter_questions_by_subject(client, sample_question):
    """Test filtering questions by subject."""
    response = await client.get("/api/questions?subject=數學")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    
    # Filter by non-existent subject
    response = await client.get("/api/questions?subject=英文")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_filter_questions_by_difficulty(client, sample_question):
    """Test filtering questions by difficulty."""
    response = await client.get("/api/questions?difficulty=1")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    
    response = await client.get("/api/questions?difficulty=3")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_get_question_by_id(client, sample_question):
    """Test getting a question by ID."""
    response = await client.get("/api/questions/q-1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "q-1"
    assert data["content"] == "解方程式: 2x + 3 = 7"
    assert data["standard_solution"] == "x = 2"


@pytest.mark.asyncio
async def test_get_question_not_found(client):
    """Test getting a non-existent question."""
    response = await client.get("/api/questions/non-existent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_validate_answer_correct(client, sample_question):
    """Test validating a correct answer."""
    response = await client.post(
        "/api/questions/validate",
        json={"question_id": "q-1", "answer": "x = 2"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_correct"] is True
    assert data["response_time_ms"] is not None


@pytest.mark.asyncio
async def test_validate_answer_incorrect(client, sample_question):
    """Test validating an incorrect answer."""
    response = await client.post(
        "/api/questions/validate",
        json={"question_id": "q-1", "answer": "x = 3"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_correct"] is False


@pytest.mark.asyncio
async def test_validate_answer_question_not_found(client):
    """Test validating answer for non-existent question."""
    response = await client.post(
        "/api/questions/validate",
        json={"question_id": "non-existent", "answer": "x = 2"}
    )
    assert response.status_code == 404


# ============== Error Book API Tests (14.3) ==============

@pytest.mark.asyncio
async def test_get_errors_empty(client, sample_student):
    """Test getting errors when none exist."""
    response = await client.get(f"/api/errors?student_id={sample_student.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["errors"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_get_errors_with_data(client, sample_error_record):
    """Test getting errors with data."""
    response = await client.get("/api/errors?student_id=student-1")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["errors"][0]["id"] == "error-1"
    assert data["errors"][0]["error_type"] == "CALCULATION"


@pytest.mark.asyncio
async def test_get_errors_filter_by_type(client, sample_error_record):
    """Test filtering errors by type."""
    response = await client.get("/api/errors?student_id=student-1&error_type=CALCULATION")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    
    response = await client.get("/api/errors?student_id=student-1&error_type=CONCEPT")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_get_error_by_id(client, sample_error_record):
    """Test getting a specific error by ID."""
    response = await client.get("/api/errors/error-1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "error-1"
    assert data["student_answer"] == "x = 3"


@pytest.mark.asyncio
async def test_get_error_not_found(client):
    """Test getting a non-existent error."""
    response = await client.get("/api/errors/non-existent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_mark_error_as_repaired(client, sample_error_record):
    """Test marking an error as repaired."""
    response = await client.post("/api/errors/error-1/repair")
    assert response.status_code == 200
    data = response.json()
    assert data["repaired"] is True
    assert data["repaired_at"] is not None


@pytest.mark.asyncio
async def test_mark_error_as_repaired_not_found(client):
    """Test marking a non-existent error as repaired."""
    response = await client.post("/api/errors/non-existent/repair")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_error_statistics(client, sample_error_record):
    """Test getting error statistics."""
    response = await client.get("/api/errors/statistics/student-1")
    assert response.status_code == 200
    data = response.json()
    assert data["total_errors"] == 1
    assert data["repaired_count"] == 0
    assert "CALCULATION" in data["errors_by_type"]


# ============== Dashboard API Tests (14.5) ==============

@pytest.mark.asyncio
async def test_get_metrics_empty(client, sample_student):
    """Test getting metrics when none exist."""
    response = await client.get(f"/api/dashboard/metrics?student_id={sample_student.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["metrics_history"] == []
    assert data["total_sessions"] == 0


@pytest.mark.asyncio
async def test_get_heatmap_empty(client, sample_student):
    """Test getting heatmap when no data exists."""
    response = await client.get(f"/api/dashboard/heatmap?student_id={sample_student.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["nodes"] == []


@pytest.mark.asyncio
async def test_get_heatmap_with_nodes(client, sample_student, sample_knowledge_node):
    """Test getting heatmap with knowledge nodes."""
    response = await client.get(f"/api/dashboard/heatmap?student_id={sample_student.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) == 1
    assert data["nodes"][0]["node_id"] == "node-1"
    assert data["nodes"][0]["mastery_level"] in ["red", "yellow", "green"]


@pytest.mark.asyncio
async def test_get_overview(client, sample_student):
    """Test getting dashboard overview."""
    response = await client.get(f"/api/dashboard/overview?student_id={sample_student.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == "student-1"
    assert data["total_sessions"] == 0
    assert "error_statistics" in data
