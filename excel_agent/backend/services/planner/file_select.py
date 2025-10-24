"""
File and sheet selection using RAG
"""
from typing import List, Dict, Any
from backend.services.rag.retriever import RAGRetriever
from backend.services.intent.schema import Intent
from backend.utils.logging import setup_logger

logger = setup_logger(__name__)


class FileSelector:
    """Select best files/sheets for a query"""
    
    def __init__(self, retriever: RAGRetriever):
        """
        Initialize file selector
        
        Args:
            retriever: RAG retriever instance
        """
        self.retriever = retriever
    
    def select(self, intent: Intent, top_k: int = 3,
               allow_files: List[str] = None,
               disallow_files: List[str] = None) -> List[Dict[str, Any]]:
        """
        Select best files/sheets for the intent
        
        Args:
            intent: Parsed intent
            top_k: Number of candidates to return
            allow_files: Optional whitelist of file names
            disallow_files: Optional blacklist of file names
            
        Returns:
            List of candidate dicts with selection rationale
        """
        question = intent.original_question
        
        # Use RAG to search
        candidates = self.retriever.search(
            question=question,
            top_k=top_k,
            allow_files=allow_files,
            disallow_files=disallow_files
        )
        
        # Enhance rationale based on intent
        for candidate in candidates:
            rationale_parts = [candidate['rationale']]
            
            # Check for specific intent requirements
            columns = candidate['columns']
            types = candidate['types']
            
            # Trend analysis needs date column
            if intent.is_trend:
                date_cols = [col for col, t in types.items() if t == 'date']
                if date_cols:
                    rationale_parts.append(f"包含日期列: {', '.join(date_cols)}")
                else:
                    rationale_parts.append("警告: 缺少日期列")
            
            # Aggregation needs numeric columns
            if intent.is_aggregation:
                numeric_cols = [col for col, t in types.items() if t == 'numeric']
                if numeric_cols:
                    rationale_parts.append(f"包含数值列: {', '.join(numeric_cols[:3])}")
            
            # Text analysis needs text columns
            if intent.is_text_analysis:
                text_cols = [col for col, t in types.items() if t == 'text']
                if text_cols:
                    rationale_parts.append(f"包含文本列: {', '.join(text_cols)}")
            
            # Update rationale
            candidate['rationale'] = ' | '.join(rationale_parts)
        
        logger.info(f"Selected {len(candidates)} candidates for intent")
        return candidates

