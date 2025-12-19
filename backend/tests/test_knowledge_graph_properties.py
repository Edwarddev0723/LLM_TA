"""
Property-based tests for Knowledge Graph Manager.

Feature: ai-math-tutor, Property 14: 知識圖譜模組化擴充
Validates: Requirements 13.1
"""
import uuid
import pytest
from hypothesis import given, strategies as st, settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.database import Base
from backend.models.knowledge import KnowledgeNode, KnowledgeRelation
from backend.services.knowledge_graph import KnowledgeGraphManager


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
relation_type_strategy = st.sampled_from(['PREREQUISITE', 'RELATED', 'EXTENDS', 'SIMILAR'])
name_strategy = st.sampled_from([
    '基礎概念', '進階應用', '綜合練習', '公式推導', '實例演練',
    '定理證明', '計算技巧', '圖形分析', '數據處理', '邏輯推理'
])


@st.composite
def knowledge_node_strategy(draw):
    """Generate a valid KnowledgeNode."""
    return KnowledgeNode(
        id=str(uuid.uuid4()),
        name=draw(name_strategy),
        subject=draw(subject_strategy),
        unit=draw(unit_strategy),
        difficulty=draw(difficulty_strategy),
        description=draw(st.text(min_size=0, max_size=100) | st.none())
    )


@settings(max_examples=100, deadline=5000)
@given(node=knowledge_node_strategy())
def test_knowledge_graph_add_node_stores_correctly(node):
    """
    Feature: ai-math-tutor, Property 14: 知識圖譜模組化擴充
    Validates: Requirements 13.1
    
    Property: For any new subject or unit node, the Knowledge_Graph should
    correctly store it and the stored node should be retrievable with the same data.
    """
    db = create_test_db()
    try:
        manager = KnowledgeGraphManager(db)
        
        # Add the node
        added_node = manager.add_node(node)
        
        # Retrieve the node
        retrieved_node = manager.get_node(added_node.id)
        
        # Verify the node was stored correctly
        assert retrieved_node is not None
        assert retrieved_node.id == added_node.id
        assert retrieved_node.name == node.name
        assert retrieved_node.subject == node.subject
        assert retrieved_node.unit == node.unit
        assert retrieved_node.difficulty == node.difficulty
    finally:
        db.close()


@settings(max_examples=100, deadline=5000)
@given(
    node1=knowledge_node_strategy(),
    node2=knowledge_node_strategy(),
    relation_type=relation_type_strategy,
    weight=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False)
)
def test_knowledge_graph_add_relation_establishes_connection(node1, node2, relation_type, weight):
    """
    Feature: ai-math-tutor, Property 14: 知識圖譜模組化擴充
    Validates: Requirements 13.1
    
    Property: For any two nodes and a valid relation type, the Knowledge_Graph
    should correctly establish the relation and the relation should be queryable.
    """
    db = create_test_db()
    try:
        manager = KnowledgeGraphManager(db)
        
        # Add both nodes first
        added_node1 = manager.add_node(node1)
        added_node2 = manager.add_node(node2)
        
        # Create and add relation
        relation = KnowledgeRelation(
            from_id=added_node1.id,
            to_id=added_node2.id,
            relation_type=relation_type,
            weight=weight
        )
        added_relation = manager.add_relation(relation)
        
        # Verify relation was established
        related_nodes = manager.get_related_nodes(added_node1.id)
        assert len(related_nodes) >= 1
        assert any(n.id == added_node2.id for n in related_nodes)
        
        # Verify relation can be filtered by type
        filtered_related = manager.get_related_nodes(added_node1.id, relation_types=[relation_type])
        assert any(n.id == added_node2.id for n in filtered_related)
    finally:
        db.close()


@settings(max_examples=100, deadline=5000)
@given(
    nodes=st.lists(knowledge_node_strategy(), min_size=2, max_size=5, unique_by=lambda n: n.id)
)
def test_knowledge_graph_modular_extension_multiple_nodes(nodes):
    """
    Feature: ai-math-tutor, Property 14: 知識圖譜模組化擴充
    Validates: Requirements 13.1
    
    Property: For any list of new nodes (representing new subjects/units),
    the Knowledge_Graph should store all of them and they should all be retrievable.
    """
    db = create_test_db()
    try:
        manager = KnowledgeGraphManager(db)
        
        added_nodes = []
        for node in nodes:
            added_node = manager.add_node(node)
            added_nodes.append(added_node)
        
        # Verify all nodes were stored
        for original, added in zip(nodes, added_nodes):
            retrieved = manager.get_node(added.id)
            assert retrieved is not None
            assert retrieved.name == original.name
            assert retrieved.subject == original.subject
            assert retrieved.unit == original.unit
    finally:
        db.close()


@settings(max_examples=100, deadline=5000)
@given(
    subject=subject_strategy,
    units=st.lists(unit_strategy, min_size=1, max_size=5, unique=True)
)
def test_knowledge_graph_filter_by_subject_and_unit(subject, units):
    """
    Feature: ai-math-tutor, Property 14: 知識圖譜模組化擴充
    Validates: Requirements 13.1
    
    Property: For any subject with multiple units, the Knowledge_Graph should
    support filtering nodes by subject and unit correctly.
    """
    db = create_test_db()
    try:
        manager = KnowledgeGraphManager(db)
        
        # Add nodes for each unit under the same subject
        added_nodes = []
        for unit in units:
            node = KnowledgeNode(
                id=str(uuid.uuid4()),
                name=f"{subject}-{unit}",
                subject=subject,
                unit=unit,
                difficulty=1,
                description=None
            )
            added_nodes.append(manager.add_node(node))
        
        # Filter by subject
        subject_nodes = manager.get_all_nodes(subject=subject)
        assert len(subject_nodes) == len(units)
        
        # Filter by subject and specific unit
        for unit in units:
            unit_nodes = manager.get_all_nodes(subject=subject, unit=unit)
            assert len(unit_nodes) == 1
            assert unit_nodes[0].unit == unit
    finally:
        db.close()
