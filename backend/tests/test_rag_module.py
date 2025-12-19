"""
Unit tests for the RAG Module.
Tests basic functionality of vector database operations and retrieval.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import uuid

from backend.services.rag_module import (
    RAGModule,
    EmbeddingModel,
    ContentType,
    RetrievalContext,
    RetrievedDocument,
    RetrievalResult,
    IndexableContent,
)


class MockEmbeddingModel:
    """Mock embedding model for testing without loading actual model."""
    
    def __init__(self, model_name: str = "mock"):
        self.model_name = model_name
        self.dimension = 384  # Standard dimension
    
    def encode(self, texts):
        """Generate deterministic mock embeddings based on text content."""
        embeddings = []
        for text in texts:
            # Create a simple deterministic embedding based on text hash
            hash_val = hash(text)
            embedding = [(hash_val >> i) % 100 / 100.0 for i in range(self.dimension)]
            embeddings.append(embedding)
        return embeddings
    
    def encode_single(self, text):
        return self.encode([text])[0]


@pytest.fixture
def mock_embedding_model():
    """Fixture for mock embedding model."""
    return MockEmbeddingModel()


@pytest.fixture
def rag_module(mock_embedding_model):
    """Fixture for RAG module with in-memory storage."""
    module = RAGModule(
        persist_directory=None,  # In-memory
        embedding_model=mock_embedding_model,
        collection_name=f"test_collection_{uuid.uuid4().hex[:8]}"
    )
    yield module
    # Cleanup
    try:
        module.reset()
    except Exception:
        pass


class TestRAGModuleBasics:
    """Test basic RAG module functionality."""
    
    def test_initialization(self, rag_module):
        """Test RAG module initializes correctly."""
        assert rag_module is not None
        assert rag_module.collection is not None
    
    def test_index_single_content(self, rag_module):
        """Test indexing a single piece of content."""
        content = IndexableContent(
            id="test-1",
            content="解一元二次方程式 x² + 5x + 6 = 0",
            content_type=ContentType.QUESTION,
            metadata={"subject": "數學", "unit": "代數"}
        )
        
        rag_module.index(content)
        
        stats = rag_module.get_collection_stats()
        assert stats["count"] == 1
    
    def test_index_batch_content(self, rag_module):
        """Test batch indexing multiple pieces of content."""
        contents = [
            IndexableContent(
                id=f"test-{i}",
                content=f"測試題目 {i}",
                content_type=ContentType.QUESTION,
                metadata={"index": i}
            )
            for i in range(5)
        ]
        
        rag_module.index_batch(contents)
        
        stats = rag_module.get_collection_stats()
        assert stats["count"] == 5
    
    def test_retrieve_basic(self, rag_module):
        """Test basic retrieval functionality."""
        # Index some content
        contents = [
            IndexableContent(
                id="q1",
                content="解一元二次方程式 x² + 5x + 6 = 0",
                content_type=ContentType.QUESTION,
                metadata={"subject": "數學"}
            ),
            IndexableContent(
                id="q2",
                content="計算三角形面積",
                content_type=ContentType.QUESTION,
                metadata={"subject": "數學"}
            ),
        ]
        rag_module.index_batch(contents)
        
        # Retrieve
        result = rag_module.retrieve("方程式")
        
        assert isinstance(result, RetrievalResult)
        assert result.total_found >= 0
    
    def test_retrieve_with_context(self, rag_module):
        """Test retrieval with context filters."""
        # Index content with different metadata
        contents = [
            IndexableContent(
                id="q1",
                content="一元二次方程式",
                content_type=ContentType.QUESTION,
                metadata={"knowledge_node": "algebra"}
            ),
            IndexableContent(
                id="q2",
                content="三角形面積公式",
                content_type=ContentType.QUESTION,
                metadata={"knowledge_node": "geometry"}
            ),
        ]
        rag_module.index_batch(contents)
        
        # Retrieve with knowledge node filter
        context = RetrievalContext(
            knowledge_nodes=["algebra"],
            max_results=5,
            min_similarity=0.0
        )
        result = rag_module.retrieve("方程式", context)
        
        assert isinstance(result, RetrievalResult)
    
    def test_delete_content(self, rag_module):
        """Test deleting content from the index."""
        content = IndexableContent(
            id="to-delete",
            content="要刪除的內容",
            content_type=ContentType.QUESTION
        )
        rag_module.index(content)
        
        assert rag_module.get_collection_stats()["count"] == 1
        
        result = rag_module.delete("to-delete")
        assert result is True
        assert rag_module.get_collection_stats()["count"] == 0
    
    def test_delete_batch(self, rag_module):
        """Test batch deletion."""
        contents = [
            IndexableContent(id=f"del-{i}", content=f"內容 {i}", content_type=ContentType.QUESTION)
            for i in range(3)
        ]
        rag_module.index_batch(contents)
        
        assert rag_module.get_collection_stats()["count"] == 3
        
        deleted = rag_module.delete_batch(["del-0", "del-1"])
        assert deleted == 2
        assert rag_module.get_collection_stats()["count"] == 1


class TestRAGModuleRetrieval:
    """Test specialized retrieval methods."""
    
    def test_retrieve_misconceptions(self, rag_module):
        """Test retrieving misconceptions."""
        contents = [
            IndexableContent(
                id="m1",
                content="常見錯誤：忘記負號",
                content_type=ContentType.MISCONCEPTION,
                metadata={"question_id": "q1"}
            ),
            IndexableContent(
                id="q1",
                content="解方程式",
                content_type=ContentType.QUESTION
            ),
        ]
        rag_module.index_batch(contents)
        
        misconceptions = rag_module.retrieve_misconceptions("負號錯誤")
        
        # Should return misconception type documents
        for doc in misconceptions:
            assert doc.content_type == ContentType.MISCONCEPTION
    
    def test_retrieve_solutions(self, rag_module):
        """Test retrieving solutions."""
        contents = [
            IndexableContent(
                id="s1",
                content="解法：先移項再因式分解",
                content_type=ContentType.SOLUTION,
                metadata={"question_id": "q1"}
            ),
            IndexableContent(
                id="q1",
                content="解方程式 x² - 4 = 0",
                content_type=ContentType.QUESTION
            ),
        ]
        rag_module.index_batch(contents)
        
        solutions = rag_module.retrieve_solutions("因式分解")
        
        # Should return solution type documents
        for doc in solutions:
            assert doc.content_type == ContentType.SOLUTION
    
    def test_retrieve_similar_questions(self, rag_module):
        """Test retrieving similar questions."""
        contents = [
            IndexableContent(
                id="q1",
                content="解一元二次方程式 x² + 2x + 1 = 0",
                content_type=ContentType.QUESTION,
                metadata={"knowledge_node": "quadratic"}
            ),
            IndexableContent(
                id="q2",
                content="解一元二次方程式 x² - 4x + 4 = 0",
                content_type=ContentType.QUESTION,
                metadata={"knowledge_node": "quadratic"}
            ),
            IndexableContent(
                id="q3",
                content="計算圓的面積",
                content_type=ContentType.QUESTION,
                metadata={"knowledge_node": "geometry"}
            ),
        ]
        rag_module.index_batch(contents)
        
        similar = rag_module.retrieve_similar_questions("q1", count=2)
        
        # Should not include the original question
        for doc in similar:
            assert doc.id != "q1"
            assert doc.content_type == ContentType.QUESTION


class TestRetrievalContext:
    """Test RetrievalContext functionality."""
    
    def test_default_values(self):
        """Test default context values."""
        context = RetrievalContext()
        
        assert context.question_id is None
        assert context.knowledge_nodes is None
        assert context.max_results == 5
        assert context.min_similarity == 0.5
    
    def test_custom_values(self):
        """Test custom context values."""
        context = RetrievalContext(
            question_id="q1",
            knowledge_nodes=["node1", "node2"],
            max_results=10,
            min_similarity=0.7
        )
        
        assert context.question_id == "q1"
        assert context.knowledge_nodes == ["node1", "node2"]
        assert context.max_results == 10
        assert context.min_similarity == 0.7


class TestIndexableContent:
    """Test IndexableContent dataclass."""
    
    def test_creation(self):
        """Test creating indexable content."""
        content = IndexableContent(
            id="test-id",
            content="測試內容",
            content_type=ContentType.QUESTION,
            metadata={"key": "value"}
        )
        
        assert content.id == "test-id"
        assert content.content == "測試內容"
        assert content.content_type == ContentType.QUESTION
        assert content.metadata == {"key": "value"}
        assert content.embedding is None
    
    def test_with_embedding(self):
        """Test creating content with pre-computed embedding."""
        embedding = [0.1] * 384
        content = IndexableContent(
            id="test-id",
            content="測試內容",
            content_type=ContentType.QUESTION,
            embedding=embedding
        )
        
        assert content.embedding == embedding


class TestContentType:
    """Test ContentType enum."""
    
    def test_all_types(self):
        """Test all content types exist."""
        assert ContentType.QUESTION.value == "QUESTION"
        assert ContentType.SOLUTION.value == "SOLUTION"
        assert ContentType.MISCONCEPTION.value == "MISCONCEPTION"
        assert ContentType.CONCEPT.value == "CONCEPT"
        assert ContentType.HINT.value == "HINT"
