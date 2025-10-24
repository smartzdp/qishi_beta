"""
RAG Indexer: Build embeddings and index for file summaries
"""
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
import pandas as pd
from datetime import datetime, date
from sentence_transformers import SentenceTransformer
from backend.utils.logging import setup_logger

logger = setup_logger(__name__)


def json_serializable(obj):
    """Convert non-JSON serializable objects to serializable format"""
    if isinstance(obj, (datetime, date, pd.Timestamp)):
        return str(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [json_serializable(item) for item in obj]
    elif pd.isna(obj):
        return None
    return obj


class RAGIndexer:
    """Build and manage RAG index for Excel files"""
    
    # Bilingual synonym table
    SYNONYMS = {
        'geography': ['地区', '城市', '省份', '地市', '区域', '县', '区', 'region', 'city', 'province'],
        'time': ['日期', '时间', '月份', '月度', '年度', '学年', '学期', 'date', 'time', 'month', 'year'],
        'sales': ['销售额', '净销售额', '销量', '销售数量', '单价', '售价', '价格', '成本', 
                 '清仓价', '建议零售价', 'sales', 'amount', 'price', 'cost'],
        'product': ['产品名称', '商品名称', '品类', '品牌', '规格', '箱规', '单位', 
                   '条形码', '商品编码', 'product', 'item', 'sku', 'brand'],
        'energy': ['发电量', '发电小时数', '运行时间', '故障小时数', '可利用率', 
                  'power', 'generation', 'runtime', 'availability'],
        'fiscal': ['小学', '初中', '高中', '普通高中', '中职', '生均经费', '预算', 
                  '增长', '同比', '环比', 'budget', 'expenditure', 'growth'],
        'academic': ['班级', '学号', '导师', '组别', '题目', '意见', '是否通过', 
                    'class', 'student', 'advisor', 'group', 'topic', 'comment']
    }
    
    def __init__(self, knowledge_base_dir: Path, embedding_model: str):
        """
        Initialize RAG indexer
        
        Args:
            knowledge_base_dir: Directory to store index
            embedding_model: Sentence transformer model name
        """
        self.knowledge_base_dir = Path(knowledge_base_dir)
        self.knowledge_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Load embedding model
        logger.info(f"Loading embedding model: {embedding_model}")
        self.model = SentenceTransformer(embedding_model)
        
        # Storage paths
        self.doc_embeddings_path = self.knowledge_base_dir / "doc_embeddings.npy"
        self.col_embeddings_path = self.knowledge_base_dir / "col_embeddings.npy"
        self.doc_metadata_path = self.knowledge_base_dir / "doc_metadata.json"
        self.col_metadata_path = self.knowledge_base_dir / "col_metadata.json"
    
    def expand_with_synonyms(self, text: str) -> str:
        """
        Expand text with synonyms
        
        Args:
            text: Input text
            
        Returns:
            Expanded text
        """
        expanded = text
        
        for category, synonyms in self.SYNONYMS.items():
            for synonym in synonyms:
                if synonym in text:
                    # Add other synonyms from the same category
                    other_synonyms = [s for s in synonyms if s != synonym]
                    expanded += " " + " ".join(other_synonyms[:3])
                    break
        
        return expanded
    
    def build_index(self, summaries: List[Dict[str, Any]]) -> None:
        """
        Build RAG index from file summaries
        
        Args:
            summaries: List of file/sheet summaries
        """
        logger.info(f"Building index from {len(summaries)} summaries")
        
        # Document-level index
        doc_texts = []
        doc_metadata = []
        
        # Column-level index
        col_texts = []
        col_metadata = []
        
        for summary in summaries:
            # Document-level text
            doc_text = summary.get('text_summary', '')
            
            # Add field descriptions
            field_descs = summary.get('field_descriptions', [])
            if field_descs:
                doc_text += " " + " ".join(field_descs[:20])
            
            # Add profile snippets
            profile = summary.get('profile', {})
            if profile:
                # Add column names
                columns = summary.get('columns', [])
                doc_text += " " + " ".join(columns)
                
                # Add sample values from head
                head = profile.get('head10', [])
                if head:
                    # Sample values from first row
                    first_row = head[0]
                    sample_values = [str(v) for v in first_row.values() if v][:10]
                    doc_text += " " + " ".join(sample_values)
            
            # Expand with synonyms
            doc_text = self.expand_with_synonyms(doc_text)
            
            doc_texts.append(doc_text)
            doc_metadata.append({
                'file_name': summary.get('file_name', ''),
                'sheet_name': summary.get('sheet_name', ''),
                'row_count': summary.get('row_count', 0),
                'column_count': summary.get('column_count', 0),
                'columns': summary.get('columns', []),
                'types': summary.get('types', {}),
                'date_range': summary.get('date_range', ''),
                'summary': summary
            })
            
            # Column-level index
            for i, field_desc in enumerate(field_descs):
                col_text = field_desc + " " + doc_text[:200]  # Add context
                col_text = self.expand_with_synonyms(col_text)
                
                col_texts.append(col_text)
                col_metadata.append({
                    'file_name': summary.get('file_name', ''),
                    'sheet_name': summary.get('sheet_name', ''),
                    'column_name': summary.get('columns', [])[i] if i < len(summary.get('columns', [])) else '',
                    'field_description': field_desc,
                    'column_type': summary.get('types', {}).get(
                        summary.get('columns', [])[i] if i < len(summary.get('columns', [])) else '',
                        'text'
                    )
                })
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(doc_texts)} documents")
        doc_embeddings = self.model.encode(doc_texts, show_progress_bar=True)
        
        logger.info(f"Generating embeddings for {len(col_texts)} columns")
        col_embeddings = self.model.encode(col_texts, show_progress_bar=True)
        
        # Save to disk
        np.save(self.doc_embeddings_path, doc_embeddings)
        np.save(self.col_embeddings_path, col_embeddings)
        
        # Convert to JSON serializable format
        doc_metadata = json_serializable(doc_metadata)
        col_metadata = json_serializable(col_metadata)
        
        with open(self.doc_metadata_path, 'w', encoding='utf-8') as f:
            json.dump(doc_metadata, f, ensure_ascii=False, indent=2)
        
        with open(self.col_metadata_path, 'w', encoding='utf-8') as f:
            json.dump(col_metadata, f, ensure_ascii=False, indent=2)
        
        logger.info("Index built successfully")
    
    def index_exists(self) -> bool:
        """Check if index exists"""
        return (
            self.doc_embeddings_path.exists() and
            self.doc_metadata_path.exists()
        )

