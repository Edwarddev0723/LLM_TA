"""
Property-based tests for Question Bank Manager.

Feature: ai-math-tutor, Property 1: 題目篩選結果正確性
Validates: Requirements 1.2
"""
import uuid
import pytest
from hypothesis import given, strategies as st, settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.database import Base
from backend.models.question import Question
from backend.models.knowledge import KnowledgeNode
from backend.services.question_bank import QuestionBankManager, QuestionCriteria


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


@st.composite
def question_list_strategy(draw, min_size=1, max_size=20):
    """Generate a list of questions with unique IDs."""
    questions = draw(st.lists(question_strategy(), min_size=min_size, max_size=max_size))
    # Ensure unique IDs
    for i, q in enumerate(questions):
        q.id = str(uuid.uuid4())
    return questions


@settings(max_examples=100, deadline=5000)
@given(
    questions=question_list_strategy(min_size=1, max_size=20),
    filter_subject=subject_strategy
)
def test_question_filter_by_subject_correctness(questions, filter_subject):
    """
    Feature: ai-math-tutor, Property 1: 題目篩選結果正確性
    Validates: Requirements 1.2
    
    Property: For any filter criteria (subject), all returned questions
    from Question_Bank should match the specified subject.
    """
    db = create_test_db()
    try:
        manager = QuestionBankManager(db)
        
        # Add all questions to the database
        for q in questions:
            db.add(q)
        db.commit()
        
        # Filter by subject
        criteria = QuestionCriteria(subject=filter_subject)
        results = manager.filter_questions(criteria)
        
        # Verify all returned questions match the filter criteria
        for question in results:
            assert question.subject == filter_subject, \
                f"Question subject '{question.subject}' does not match filter '{filter_subject}'"
    finally:
        db.close()


@settings(max_examples=100, deadline=5000)
@given(
    questions=question_list_strategy(min_size=1, max_size=20),
    filter_unit=unit_strategy
)
def test_question_filter_by_unit_correctness(questions, filter_unit):
    """
    Feature: ai-math-tutor, Property 1: 題目篩選結果正確性
    Validates: Requirements 1.2
    
    Property: For any filter criteria (unit), all returned questions
    from Question_Bank should match the specified unit.
    """
    db = create_test_db()
    try:
        manager = QuestionBankManager(db)
        
        # Add all questions to the database
        for q in questions:
            db.add(q)
        db.commit()
        
        # Filter by unit
        criteria = QuestionCriteria(unit=filter_unit)
        results = manager.filter_questions(criteria)
        
        # Verify all returned questions match the filter criteria
        for question in results:
            assert question.unit == filter_unit, \
                f"Question unit '{question.unit}' does not match filter '{filter_unit}'"
    finally:
        db.close()


@settings(max_examples=100, deadline=5000)
@given(
    questions=question_list_strategy(min_size=1, max_size=20),
    filter_difficulty=difficulty_strategy
)
def test_question_filter_by_difficulty_correctness(questions, filter_difficulty):
    """
    Feature: ai-math-tutor, Property 1: 題目篩選結果正確性
    Validates: Requirements 1.2
    
    Property: For any filter criteria (difficulty), all returned questions
    from Question_Bank should match the specified difficulty level.
    """
    db = create_test_db()
    try:
        manager = QuestionBankManager(db)
        
        # Add all questions to the database
        for q in questions:
            db.add(q)
        db.commit()
        
        # Filter by difficulty
        criteria = QuestionCriteria(difficulty=filter_difficulty)
        results = manager.filter_questions(criteria)
        
        # Verify all returned questions match the filter criteria
        for question in results:
            assert question.difficulty == filter_difficulty, \
                f"Question difficulty '{question.difficulty}' does not match filter '{filter_difficulty}'"
    finally:
        db.close()


@settings(max_examples=100, deadline=5000)
@given(
    questions=question_list_strategy(min_size=1, max_size=20),
    filter_subject=subject_strategy,
    filter_unit=unit_strategy,
    filter_difficulty=difficulty_strategy
)
def test_question_filter_combined_criteria_correctness(questions, filter_subject, filter_unit, filter_difficulty):
    """
    Feature: ai-math-tutor, Property 1: 題目篩選結果正確性
    Validates: Requirements 1.2
    
    Property: For any combination of filter criteria (subject, unit, difficulty),
    all returned questions from Question_Bank should match ALL specified criteria.
    """
    db = create_test_db()
    try:
        manager = QuestionBankManager(db)
        
        # Add all questions to the database
        for q in questions:
            db.add(q)
        db.commit()
        
        # Filter by combined criteria
        criteria = QuestionCriteria(
            subject=filter_subject,
            unit=filter_unit,
            difficulty=filter_difficulty
        )
        results = manager.filter_questions(criteria)
        
        # Verify all returned questions match ALL filter criteria
        for question in results:
            assert question.subject == filter_subject, \
                f"Question subject '{question.subject}' does not match filter '{filter_subject}'"
            assert question.unit == filter_unit, \
                f"Question unit '{question.unit}' does not match filter '{filter_unit}'"
            assert question.difficulty == filter_difficulty, \
                f"Question difficulty '{question.difficulty}' does not match filter '{filter_difficulty}'"
    finally:
        db.close()


@settings(max_examples=100, deadline=5000)
@given(
    questions=question_list_strategy(min_size=1, max_size=20),
    filter_subject=subject_strategy,
    filter_unit=unit_strategy,
    filter_difficulty=difficulty_strategy
)
def test_question_filter_returns_all_matching_questions(questions, filter_subject, filter_unit, filter_difficulty):
    """
    Feature: ai-math-tutor, Property 1: 題目篩選結果正確性
    Validates: Requirements 1.2
    
    Property: For any filter criteria, the Question_Bank should return ALL questions
    that match the criteria (completeness check).
    """
    db = create_test_db()
    try:
        manager = QuestionBankManager(db)
        
        # Add all questions to the database
        for q in questions:
            db.add(q)
        db.commit()
        
        # Filter by combined criteria
        criteria = QuestionCriteria(
            subject=filter_subject,
            unit=filter_unit,
            difficulty=filter_difficulty
        )
        results = manager.filter_questions(criteria)
        result_ids = {q.id for q in results}
        
        # Count expected matches manually
        expected_matches = [
            q for q in questions
            if q.subject == filter_subject
            and q.unit == filter_unit
            and q.difficulty == filter_difficulty
        ]
        expected_ids = {q.id for q in expected_matches}
        
        # Verify completeness: all matching questions should be returned
        assert result_ids == expected_ids, \
            f"Filter did not return all matching questions. Expected {len(expected_ids)}, got {len(result_ids)}"
    finally:
        db.close()


# =============================================================================
# Property 15: 題庫匯入匯出 Round-Trip
# =============================================================================

@st.composite
def question_data_dict_strategy(draw):
    """Generate a valid question data dictionary for import/export testing."""
    return {
        'id': str(uuid.uuid4()),
        'content': draw(st.text(min_size=5, max_size=200, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z')))),
        'type': draw(question_type_strategy),
        'subject': draw(subject_strategy),
        'unit': draw(unit_strategy),
        'difficulty': draw(difficulty_strategy),
        'standard_solution': draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z')))),
        'knowledge_nodes': []  # Empty for simplicity in round-trip test
    }


@st.composite
def question_data_list_strategy(draw, min_size=1, max_size=10):
    """Generate a list of question data dictionaries with unique IDs."""
    questions = draw(st.lists(question_data_dict_strategy(), min_size=min_size, max_size=max_size))
    # Ensure unique IDs
    for q in questions:
        q['id'] = str(uuid.uuid4())
    return questions


@settings(max_examples=100, deadline=10000)
@given(questions_data=question_data_list_strategy(min_size=1, max_size=10))
def test_question_bank_json_round_trip(questions_data):
    """
    Feature: ai-math-tutor, Property 15: 題庫匯入匯出 Round-Trip
    Validates: Requirements 13.2
    
    Property: For any valid question data in JSON format, importing then exporting
    should produce an equivalent data structure.
    """
    import json
    
    db = create_test_db()
    try:
        manager = QuestionBankManager(db)
        
        # Export original data to JSON string
        original_json = json.dumps(questions_data, ensure_ascii=False, indent=2)
        
        # Import questions from JSON
        import_result = manager.import_questions(original_json, format='JSON')
        
        # Verify import succeeded
        assert import_result.success_count == len(questions_data), \
            f"Import failed: {import_result.errors}"
        assert import_result.error_count == 0, \
            f"Import had errors: {import_result.errors}"
        
        # Export all questions back to JSON
        exported_json = manager.export_questions(format='JSON')
        exported_data = json.loads(exported_json)
        
        # Verify round-trip: exported data should match original
        assert len(exported_data) == len(questions_data), \
            f"Round-trip count mismatch: expected {len(questions_data)}, got {len(exported_data)}"
        
        # Create lookup by ID for comparison
        original_by_id = {q['id']: q for q in questions_data}
        exported_by_id = {q['id']: q for q in exported_data}
        
        # Verify each question's core fields match
        for qid, original in original_by_id.items():
            assert qid in exported_by_id, f"Question {qid} missing after round-trip"
            exported = exported_by_id[qid]
            
            assert exported['content'] == original['content'], \
                f"Content mismatch for {qid}"
            assert exported['type'] == original['type'], \
                f"Type mismatch for {qid}"
            assert exported['subject'] == original['subject'], \
                f"Subject mismatch for {qid}"
            assert exported['unit'] == original['unit'], \
                f"Unit mismatch for {qid}"
            assert exported['difficulty'] == original['difficulty'], \
                f"Difficulty mismatch for {qid}"
            assert exported['standard_solution'] == original['standard_solution'], \
                f"Standard solution mismatch for {qid}"
    finally:
        db.close()


# =============================================================================
# Property 16: 題目知識點自動關聯
# =============================================================================

@st.composite
def knowledge_node_strategy(draw):
    """Generate a valid KnowledgeNode."""
    return KnowledgeNode(
        id=str(uuid.uuid4()),
        name=draw(st.sampled_from([
            '基礎概念', '進階應用', '綜合練習', '公式推導', '實例演練',
            '定理證明', '計算技巧', '圖形分析', '數據處理', '邏輯推理'
        ])),
        subject=draw(subject_strategy),
        unit=draw(unit_strategy),
        difficulty=draw(difficulty_strategy),
        description=draw(st.text(min_size=0, max_size=100) | st.none())
    )


@settings(max_examples=100, deadline=10000)
@given(
    question=question_strategy(),
    nodes=st.lists(knowledge_node_strategy(), min_size=1, max_size=5)
)
def test_question_knowledge_node_auto_association(question, nodes):
    """
    Feature: ai-math-tutor, Property 16: 題目知識點自動關聯
    Validates: Requirements 13.3
    
    Property: For any newly added question, the system should automatically
    associate it with the corresponding knowledge graph nodes, and the
    association relationship should be queryable.
    """
    db = create_test_db()
    try:
        manager = QuestionBankManager(db)
        
        # First, add knowledge nodes to the database
        added_node_ids = []
        for node in nodes:
            node.id = str(uuid.uuid4())  # Ensure unique IDs
            db.add(node)
            added_node_ids.append(node.id)
        db.commit()
        
        # Add the question
        question.id = str(uuid.uuid4())
        added_question = manager.add_question(question)
        
        # Link question to all knowledge nodes
        for node_id in added_node_ids:
            result = manager.link_question_to_knowledge_node(added_question.id, node_id)
            assert result is True, f"Failed to link question to node {node_id}"
        
        # Refresh the question to get updated relationships
        db.refresh(added_question)
        
        # Verify the associations are queryable
        retrieved_question = manager.get_question(added_question.id)
        assert retrieved_question is not None
        
        # Verify all knowledge nodes are associated
        associated_node_ids = {node.id for node in retrieved_question.knowledge_nodes}
        expected_node_ids = set(added_node_ids)
        
        assert associated_node_ids == expected_node_ids, \
            f"Association mismatch: expected {expected_node_ids}, got {associated_node_ids}"
        
        # Verify we can filter questions by knowledge nodes
        criteria = QuestionCriteria(knowledge_nodes=added_node_ids[:1])  # Filter by first node
        filtered_questions = manager.filter_questions(criteria)
        
        assert any(q.id == added_question.id for q in filtered_questions), \
            "Question not found when filtering by associated knowledge node"
    finally:
        db.close()


@settings(max_examples=100, deadline=10000)
@given(
    questions_data=question_data_list_strategy(min_size=1, max_size=5),
    nodes=st.lists(knowledge_node_strategy(), min_size=1, max_size=3)
)
def test_question_import_with_knowledge_nodes_association(questions_data, nodes):
    """
    Feature: ai-math-tutor, Property 16: 題目知識點自動關聯
    Validates: Requirements 13.3
    
    Property: When importing questions with knowledge node references,
    the system should automatically establish the associations, and
    these associations should be queryable.
    """
    import json
    
    db = create_test_db()
    try:
        manager = QuestionBankManager(db)
        
        # First, add knowledge nodes to the database
        added_node_ids = []
        for node in nodes:
            node.id = str(uuid.uuid4())
            db.add(node)
            added_node_ids.append(node.id)
        db.commit()
        
        # Update questions_data to include knowledge node references
        for q_data in questions_data:
            q_data['knowledge_nodes'] = added_node_ids
        
        # Import questions with knowledge node references
        json_data = json.dumps(questions_data, ensure_ascii=False)
        import_result = manager.import_questions(json_data, format='JSON')
        
        assert import_result.success_count == len(questions_data), \
            f"Import failed: {import_result.errors}"
        
        # Verify each imported question has the correct associations
        for q_data in questions_data:
            retrieved_question = manager.get_question(q_data['id'])
            assert retrieved_question is not None, \
                f"Question {q_data['id']} not found after import"
            
            # Verify knowledge node associations
            associated_node_ids = {node.id for node in retrieved_question.knowledge_nodes}
            expected_node_ids = set(added_node_ids)
            
            assert associated_node_ids == expected_node_ids, \
                f"Association mismatch for question {q_data['id']}: expected {expected_node_ids}, got {associated_node_ids}"
    finally:
        db.close()


@settings(max_examples=100, deadline=10000)
@given(questions_data=question_data_list_strategy(min_size=1, max_size=10))
def test_question_bank_csv_round_trip(questions_data):
    """
    Feature: ai-math-tutor, Property 15: 題庫匯入匯出 Round-Trip
    Validates: Requirements 13.2
    
    Property: For any valid question data in CSV format, importing then exporting
    should produce an equivalent data structure.
    """
    import json
    
    db = create_test_db()
    try:
        manager = QuestionBankManager(db)
        
        # First, add questions directly to get a valid CSV export format
        for q_data in questions_data:
            question = Question(
                id=q_data['id'],
                content=q_data['content'],
                type=q_data['type'],
                subject=q_data['subject'],
                unit=q_data['unit'],
                difficulty=q_data['difficulty'],
                standard_solution=q_data['standard_solution']
            )
            db.add(question)
        db.commit()
        
        # Export to CSV
        exported_csv = manager.export_questions(format='CSV')
        
        # Clear database and re-import from CSV
        db.query(Question).delete()
        db.commit()
        
        # Import from CSV
        import_result = manager.import_questions(exported_csv, format='CSV')
        
        # Verify import succeeded
        assert import_result.success_count == len(questions_data), \
            f"CSV Import failed: {import_result.errors}"
        
        # Export again to JSON for comparison
        final_export = manager.export_questions(format='JSON')
        final_data = json.loads(final_export)
        
        # Verify round-trip
        assert len(final_data) == len(questions_data), \
            f"CSV Round-trip count mismatch: expected {len(questions_data)}, got {len(final_data)}"
        
        # Create lookup by ID for comparison
        original_by_id = {q['id']: q for q in questions_data}
        final_by_id = {q['id']: q for q in final_data}
        
        # Verify each question's core fields match
        for qid, original in original_by_id.items():
            assert qid in final_by_id, f"Question {qid} missing after CSV round-trip"
            final = final_by_id[qid]
            
            assert final['content'] == original['content'], \
                f"Content mismatch for {qid}"
            assert final['type'] == original['type'], \
                f"Type mismatch for {qid}"
            assert final['subject'] == original['subject'], \
                f"Subject mismatch for {qid}"
            assert final['unit'] == original['unit'], \
                f"Unit mismatch for {qid}"
            assert final['difficulty'] == original['difficulty'], \
                f"Difficulty mismatch for {qid}"
            assert final['standard_solution'] == original['standard_solution'], \
                f"Standard solution mismatch for {qid}"
    finally:
        db.close()
