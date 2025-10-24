"""
RAG Retriever: Semantic search with field coverage scoring
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors
from backend.utils.logging import setup_logger

logger = setup_logger(__name__)


class RAGRetriever:
    """Retrieve relevant files/sheets using RAG"""
    
    def __init__(self, knowledge_base_dir: Path, embedding_model: str):
        """
        Initialize RAG retriever
        
        Args:
            knowledge_base_dir: Directory containing index
            embedding_model: Sentence transformer model name
        """
        self.knowledge_base_dir = Path(knowledge_base_dir)
        
        # Load embedding model
        logger.info(f"Loading embedding model: {embedding_model}")
        self.model = SentenceTransformer(embedding_model)
        
        # Storage paths
        self.doc_embeddings_path = self.knowledge_base_dir / "doc_embeddings.npy"
        self.col_embeddings_path = self.knowledge_base_dir / "col_embeddings.npy"
        self.doc_metadata_path = self.knowledge_base_dir / "doc_metadata.json"
        self.col_metadata_path = self.knowledge_base_dir / "col_metadata.json"
        
        # Load index
        self.doc_embeddings = None
        self.col_embeddings = None
        self.doc_metadata = None
        self.col_metadata = None
        self.doc_nn = None
        self.col_nn = None
        
        self._load_index()
    
    def _load_index(self) -> None:
        """Load index from disk"""
        if not self.doc_embeddings_path.exists():
            logger.warning("Index not found, please build index first")
            return
        
        logger.info("Loading RAG index")
        
        # Load embeddings
        self.doc_embeddings = np.load(self.doc_embeddings_path)
        self.col_embeddings = np.load(self.col_embeddings_path)
        
        # Load metadata
        with open(self.doc_metadata_path, 'r', encoding='utf-8') as f:
            self.doc_metadata = json.load(f)
        
        with open(self.col_metadata_path, 'r', encoding='utf-8') as f:
            self.col_metadata = json.load(f)
        
        # Build nearest neighbors index
        # Ensure n_neighbors doesn't exceed number of samples
        doc_n_neighbors = min(10, len(self.doc_metadata))
        col_n_neighbors = max(1, min(20, len(self.col_metadata)))
        
        self.doc_nn = NearestNeighbors(n_neighbors=doc_n_neighbors, metric='cosine')
        self.doc_nn.fit(self.doc_embeddings)
        
        # Only fit column NN if we have column data
        if len(self.col_metadata) > 0 and self.col_embeddings.shape[0] > 0:
            self.col_nn = NearestNeighbors(n_neighbors=col_n_neighbors, metric='cosine')
            self.col_nn.fit(self.col_embeddings)
        else:
            self.col_nn = None
        
        logger.info(f"Loaded index: {len(self.doc_metadata)} documents, {len(self.col_metadata)} columns")
    
    def extract_keywords(self, question: str) -> List[str]:
        """
        Extract potential column keywords from question
        
        Args:
            question: User question
            
        Returns:
            List of keywords
        """
        keywords = []
        
        # Common patterns
        patterns = {
            'geography': ['地区', '城市', '省份', '区域', 'region', 'city'],
            'time': ['日期', '时间', '月', '年', 'date', 'time', 'month', 'year'],
            'sales': ['销售', '销量', '金额', 'sales', 'amount', 'revenue'],
            'product': ['产品', '商品', 'SKU', 'product', 'item'],
            'price': ['价格', '成本', '折扣', '清仓', 'price', 'cost', 'discount'],
            'growth': ['增长', '同比', '环比', '趋势', 'growth', 'trend', 'yoy'],
            'aggregation': ['总', '平均', '最大', '最小', 'sum', 'average', 'total', 'max', 'min'],
            'ranking': ['排名', '前', 'top', 'bottom', 'rank'],
        }
        
        for category, terms in patterns.items():
            for term in terms:
                if term in question:
                    keywords.append(category)
                    break
        
        return keywords
    
    def compute_field_coverage(self, question: str, columns: List[str]) -> float:
        """
        Compute field coverage score
        
        Args:
            question: User question
            columns: Available columns
            
        Returns:
            Coverage score (0-1)
        """
        keywords = self.extract_keywords(question)
        
        # Check how many keywords can be matched
        matches = 0
        for keyword in keywords:
            # Check if any column name contains related terms
            for col in columns:
                col_lower = col.lower()
                if keyword in col_lower:
                    matches += 1
                    break
        
        if not keywords:
            return 0.5  # Neutral score
        
        return matches / len(keywords)
    
    def search(self, question: str, top_k: int = 3, 
              allow_files: List[str] = None,
              disallow_files: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search for relevant files/sheets
        
        Args:
            question: User question
            top_k: Number of results to return
            allow_files: Optional list of allowed file names
            disallow_files: Optional list of disallowed file names
            
        Returns:
            List of candidate dicts with scores and rationale
        """
        if self.doc_nn is None:
            logger.error("Index not loaded")
            return []
        
        # Ensure top_k doesn't exceed available documents
        actual_top_k = min(top_k, len(self.doc_metadata))
        
        logger.info(f"Searching for: {question} (top_k: {actual_top_k})")
        
        # Generate query embedding
        query_embedding = self.model.encode([question])[0]
        
        # Search document-level index
        distances, indices = self.doc_nn.kneighbors([query_embedding])
        
        # Score and rank candidates
        candidates = []
        for dist, idx in zip(distances[0], indices[0]):
            metadata = self.doc_metadata[idx]
            
            # Apply filters
            file_name = metadata['file_name']
            if allow_files and file_name not in allow_files:
                continue
            if disallow_files and file_name in disallow_files:
                continue
            
            # Semantic similarity (1 - cosine distance)
            semantic_score = 1 - dist
            
            # Field coverage
            columns = metadata['columns']
            coverage_score = self.compute_field_coverage(question, columns)
            
            # Date range relevance
            date_score = 1.0
            if '2023' in question or '2024' in question or '2025' in question:
                date_range = metadata.get('date_range', '')
                if date_range:
                    if '2023' in question and '2023' in date_range:
                        date_score = 1.2
                    elif '2024' in question and '2024' in date_range:
                        date_score = 1.2
                    elif '2025' in question and '2025' in date_range:
                        date_score = 1.2
            
            # Numeric column bonus for aggregation questions
            numeric_bonus = 1.0
            if any(kw in question for kw in ['总', '平均', '求和', '统计', 'sum', 'average', 'total']):
                types = metadata['types']
                numeric_cols = [col for col, t in types.items() if t == 'numeric']
                if numeric_cols:
                    numeric_bonus = 1 + (len(numeric_cols) / len(types)) * 0.5
            
            # Final score
            final_score = semantic_score * (1 + coverage_score) * date_score * numeric_bonus
            
            # Generate rationale
            rationale_parts = []
            rationale_parts.append(f"语义相似度: {semantic_score:.3f}")
            rationale_parts.append(f"字段覆盖度: {coverage_score:.3f}")
            
            if date_score > 1.0:
                rationale_parts.append(f"日期范围匹配")
            if numeric_bonus > 1.0:
                rationale_parts.append(f"包含数值字段")
            
            # Add matched columns
            matched_cols = []
            keywords = self.extract_keywords(question)
            for col in columns:
                col_lower = col.lower()
                for kw in keywords:
                    if kw in col_lower:
                        matched_cols.append(col)
                        break
            
            if matched_cols:
                rationale_parts.append(f"匹配字段: {', '.join(matched_cols[:5])}")
            
            candidates.append({
                'file_name': file_name,
                'sheet_name': metadata['sheet_name'],
                'score': float(final_score),
                'semantic_score': float(semantic_score),
                'coverage_score': float(coverage_score),
                'columns': columns,
                'types': metadata['types'],
                'row_count': int(metadata['row_count']),
                'column_count': len(columns),
                'date_range': metadata.get('date_range', ''),
                'rationale': ' | '.join(rationale_parts),
                'summary': metadata['summary']
            })
        
        # Sort by final score
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top_k (use actual_top_k to ensure we don't exceed available candidates)
        result = candidates[:actual_top_k]
        logger.info(f"Found {len(result)} candidates")
        
        return result
    
    def search_columns(self, question: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for relevant columns
        
        Args:
            question: User question
            top_k: Number of results to return
            
        Returns:
            List of column metadata dicts
        """
        if self.col_nn is None:
            logger.error("Column index not loaded")
            return []
        
        # Ensure top_k doesn't exceed available columns
        actual_top_k = min(top_k, len(self.col_metadata))
        
        # Generate query embedding
        query_embedding = self.model.encode([question])[0]
        
        # Search column-level index
        distances, indices = self.col_nn.kneighbors([query_embedding])
        
        results = []
        for dist, idx in zip(distances[0][:actual_top_k], indices[0][:actual_top_k]):
            metadata = self.col_metadata[idx].copy()
            metadata['similarity'] = float(1 - dist)
            results.append(metadata)
        
        return results

