"""
Dependency injection for FastAPI
"""
from backend.config import settings
from backend.services.rag.indexer import RAGIndexer
from backend.services.rag.retriever import RAGRetriever

# Singleton instances
_rag_indexer = None
_rag_retriever = None


def get_settings():
    """Get application settings"""
    return settings


def get_rag_indexer() -> RAGIndexer:
    """Get RAG indexer instance (singleton)"""
    global _rag_indexer
    if _rag_indexer is None:
        _rag_indexer = RAGIndexer(
            knowledge_base_dir=settings.knowledge_base_dir,
            embedding_model=settings.embedding_model
        )
    return _rag_indexer


def get_rag_retriever() -> RAGRetriever:
    """Get RAG retriever instance (singleton)"""
    global _rag_retriever
    if _rag_retriever is None:
        _rag_retriever = RAGRetriever(
            knowledge_base_dir=settings.knowledge_base_dir,
            embedding_model=settings.embedding_model
        )
    return _rag_retriever

