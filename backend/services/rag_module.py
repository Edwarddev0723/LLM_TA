"""
RAG (Retrieval-Augmented Generation) Module for the AI Math Tutor system.
Handles vector database operations, embedding generation, and content retrieval.
"""
import os
import uuid
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

import chromadb
from chromadb.config import Settings


class ContentType(str, Enum):
    """Types of content that can be indexed and retrieved."""
    QUESTION = "QUESTION"
    SOLUTION = "SOLUTION"
    MISCONCEPTION = "MISCONCEPTION"
    CONCEPT = "CONCEPT"
    HINT = "HINT"


@dataclass
class RetrievalContext:
    """Context for retrieval operations."""
    question_id: Optional[str] = None
    knowledge_nodes: Optional[List[str]] = None
    max_results: int = 5
    min_similarity: float = 0.5


@dataclass
class RetrievedDocument:
    """A document retrieved from the vector database."""
    id: str
    content: str
    content_type: ContentType
    similarity: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalResult:
    """Result of a retrieval operation."""
    documents: List[RetrievedDocument]
    total_found: int


@dataclass
class IndexableContent:
    """Content that can be indexed in the vector database."""
    id: str
    content: str
    content_type: ContentType
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None


class EmbeddingModel:
    """
    Wrapper for the sentence-transformers embedding model.
    Uses a lightweight model suitable for local deployment.
    """
    
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Initialize the embedding model.
        
        Args:
            model_name: Name of the sentence-transformers model to use.
                       Default is a multilingual model good for Chinese text.
        """
        self.model_name = model_name
        self._model = None
    
    @property
    def model(self):
        """Lazy load the model to avoid import overhead."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required. "
                    "Install with: pip install sentence-transformers"
                )
        return self._model
    
    def encode(self, texts: List[str]) -> List[List[float]]:
        """
        Encode texts into embeddings.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def encode_single(self, text: str) -> List[float]:
        """
        Encode a single text into an embedding.
        
        Args:
            text: Text to encode
            
        Returns:
            Embedding vector
        """
        return self.encode([text])[0]


class RAGModule:
    """
    RAG Module for retrieval-augmented generation.
    Manages vector database operations and content retrieval.
    """
    
    # Default collection name
    DEFAULT_COLLECTION = "math_tutor_content"
    
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        embedding_model: Optional[EmbeddingModel] = None,
        collection_name: str = DEFAULT_COLLECTION
    ):
        """
        Initialize the RAG Module.
        
        Args:
            persist_directory: Directory to persist ChromaDB data.
                             If None, uses in-memory storage.
            embedding_model: Custom embedding model. If None, uses default.
            collection_name: Name of the ChromaDB collection.
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize embedding model
        self.embedding_model = embedding_model or EmbeddingModel()
        
        # Initialize ChromaDB client
        self._client = None
        self._collection = None
    
    @property
    def client(self) -> chromadb.Client:
        """Get or create the ChromaDB client."""
        if self._client is None:
            if self.persist_directory:
                # Persistent storage
                self._client = chromadb.PersistentClient(
                    path=self.persist_directory,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
            else:
                # In-memory storage (for testing)
                self._client = chromadb.Client(
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
        return self._client
    
    @property
    def collection(self) -> chromadb.Collection:
        """Get or create the ChromaDB collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )
        return self._collection

    def index(self, content: IndexableContent) -> None:
        """
        Index a single piece of content in the vector database.
        
        Args:
            content: The content to index
        """
        # Generate embedding if not provided
        if content.embedding is None:
            embedding = self.embedding_model.encode_single(content.content)
        else:
            embedding = content.embedding
        
        # Prepare metadata
        metadata = {
            "content_type": content.content_type.value,
            **content.metadata
        }
        
        # Add to collection
        self.collection.upsert(
            ids=[content.id],
            embeddings=[embedding],
            documents=[content.content],
            metadatas=[metadata]
        )
    
    def index_batch(self, contents: List[IndexableContent]) -> None:
        """
        Index multiple pieces of content in batch.
        
        Args:
            contents: List of content to index
        """
        if not contents:
            return
        
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        # Collect texts that need embedding
        texts_to_embed = []
        embed_indices = []
        
        for i, content in enumerate(contents):
            ids.append(content.id)
            documents.append(content.content)
            metadatas.append({
                "content_type": content.content_type.value,
                **content.metadata
            })
            
            if content.embedding is not None:
                embeddings.append(content.embedding)
            else:
                texts_to_embed.append(content.content)
                embed_indices.append(i)
                embeddings.append(None)  # Placeholder
        
        # Generate embeddings for texts that need them
        if texts_to_embed:
            generated_embeddings = self.embedding_model.encode(texts_to_embed)
            for idx, embedding in zip(embed_indices, generated_embeddings):
                embeddings[idx] = embedding
        
        # Add to collection
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
    
    def retrieve(
        self,
        query: str,
        context: Optional[RetrievalContext] = None
    ) -> RetrievalResult:
        """
        Retrieve relevant content based on a query.
        
        Args:
            query: The search query
            context: Optional retrieval context with filters
            
        Returns:
            RetrievalResult containing matching documents
        """
        if context is None:
            context = RetrievalContext()
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode_single(query)
        
        # Build where filter
        where_filter = self._build_where_filter(context)
        
        # Query the collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=context.max_results,
            where=where_filter if where_filter else None,
            include=["documents", "metadatas", "distances"]
        )
        
        # Convert results to RetrievedDocument objects
        documents = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                # ChromaDB returns distances, convert to similarity
                # For cosine distance: similarity = 1 - distance
                distance = results["distances"][0][i] if results["distances"] else 0
                similarity = 1 - distance
                
                # Skip documents below similarity threshold
                if similarity < context.min_similarity:
                    continue
                
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                content_type_str = metadata.pop("content_type", "CONCEPT")
                
                try:
                    content_type = ContentType(content_type_str)
                except ValueError:
                    content_type = ContentType.CONCEPT
                
                documents.append(RetrievedDocument(
                    id=doc_id,
                    content=results["documents"][0][i] if results["documents"] else "",
                    content_type=content_type,
                    similarity=similarity,
                    metadata=metadata
                ))
        
        return RetrievalResult(
            documents=documents,
            total_found=len(documents)
        )
    
    def _build_where_filter(
        self,
        context: RetrievalContext
    ) -> Optional[Dict[str, Any]]:
        """
        Build a ChromaDB where filter from retrieval context.
        
        Args:
            context: The retrieval context
            
        Returns:
            Where filter dict or None
        """
        conditions = []
        
        if context.question_id:
            conditions.append({"question_id": context.question_id})
        
        if context.knowledge_nodes:
            # Filter by any of the knowledge nodes
            if len(context.knowledge_nodes) == 1:
                conditions.append({"knowledge_node": context.knowledge_nodes[0]})
            else:
                conditions.append({
                    "$or": [
                        {"knowledge_node": node}
                        for node in context.knowledge_nodes
                    ]
                })
        
        if not conditions:
            return None
        
        if len(conditions) == 1:
            return conditions[0]
        
        return {"$and": conditions}

    def retrieve_similar_questions(
        self,
        question_id: str,
        count: int = 2
    ) -> List[RetrievedDocument]:
        """
        Retrieve similar questions for extension practice.
        Used when a student answers incorrectly.
        
        Args:
            question_id: The ID of the original question
            count: Number of similar questions to retrieve
            
        Returns:
            List of similar question documents
        """
        # First, get the original question content
        results = self.collection.get(
            ids=[question_id],
            include=["documents", "metadatas"]
        )
        
        if not results["documents"]:
            return []
        
        original_content = results["documents"][0]
        original_metadata = results["metadatas"][0] if results["metadatas"] else {}
        
        # Get knowledge nodes from the original question
        knowledge_nodes = []
        if "knowledge_node" in original_metadata:
            knowledge_nodes = [original_metadata["knowledge_node"]]
        
        # Retrieve similar questions
        context = RetrievalContext(
            knowledge_nodes=knowledge_nodes if knowledge_nodes else None,
            max_results=count + 1,  # +1 to exclude the original
            min_similarity=0.3
        )
        
        result = self.retrieve(original_content, context)
        
        # Filter out the original question and questions that aren't QUESTION type
        similar = [
            doc for doc in result.documents
            if doc.id != question_id and doc.content_type == ContentType.QUESTION
        ]
        
        return similar[:count]
    
    def retrieve_misconceptions(
        self,
        query: str,
        question_id: Optional[str] = None,
        max_results: int = 3
    ) -> List[RetrievedDocument]:
        """
        Retrieve relevant misconceptions for a query.
        
        Args:
            query: The search query (e.g., student's answer or explanation)
            question_id: Optional question ID to filter by
            max_results: Maximum number of misconceptions to return
            
        Returns:
            List of misconception documents
        """
        # Build context
        context = RetrievalContext(
            question_id=question_id,
            max_results=max_results * 2,  # Get more to filter
            min_similarity=0.4
        )
        
        result = self.retrieve(query, context)
        
        # Filter to only misconceptions
        misconceptions = [
            doc for doc in result.documents
            if doc.content_type == ContentType.MISCONCEPTION
        ]
        
        return misconceptions[:max_results]
    
    def retrieve_solutions(
        self,
        query: str,
        question_id: Optional[str] = None,
        max_results: int = 3
    ) -> List[RetrievedDocument]:
        """
        Retrieve relevant solutions for a query.
        
        Args:
            query: The search query
            question_id: Optional question ID to filter by
            max_results: Maximum number of solutions to return
            
        Returns:
            List of solution documents
        """
        context = RetrievalContext(
            question_id=question_id,
            max_results=max_results * 2,
            min_similarity=0.4
        )
        
        result = self.retrieve(query, context)
        
        # Filter to only solutions
        solutions = [
            doc for doc in result.documents
            if doc.content_type == ContentType.SOLUTION
        ]
        
        return solutions[:max_results]
    
    def delete(self, content_id: str) -> bool:
        """
        Delete content from the vector database.
        
        Args:
            content_id: The ID of the content to delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            self.collection.delete(ids=[content_id])
            return True
        except Exception:
            return False
    
    def delete_batch(self, content_ids: List[str]) -> int:
        """
        Delete multiple pieces of content.
        
        Args:
            content_ids: List of content IDs to delete
            
        Returns:
            Number of items deleted
        """
        if not content_ids:
            return 0
        
        try:
            self.collection.delete(ids=content_ids)
            return len(content_ids)
        except Exception:
            return 0
    
    def update_index(self) -> None:
        """
        Update the vector index.
        ChromaDB handles this automatically, but this method
        is provided for interface compatibility.
        """
        # ChromaDB automatically updates the index
        pass
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection.
        
        Returns:
            Dictionary with collection statistics
        """
        return {
            "name": self.collection_name,
            "count": self.collection.count(),
            "persist_directory": self.persist_directory
        }
    
    def reset(self) -> None:
        """
        Reset the collection (delete all data).
        Use with caution!
        """
        self.client.delete_collection(self.collection_name)
        self._collection = None
