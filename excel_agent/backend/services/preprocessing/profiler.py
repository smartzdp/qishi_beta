"""
DataFrame profiler: infer types, generate distributions, head/tail samples
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any
from backend.utils.df_utils import infer_column_type, get_distribution_summary
from backend.utils.logging import setup_logger

logger = setup_logger(__name__)


class DataFrameProfiler:
    """Profile DataFrames for RAG indexing and analysis"""
    
    def profile(self, df: pd.DataFrame, sheet_name: str = "") -> Dict[str, Any]:
        """
        Generate comprehensive profile for a DataFrame
        
        Args:
            df: Input DataFrame
            sheet_name: Sheet name
            
        Returns:
            Profile dict containing types, head, tail, distributions
        """
        logger.info(f"Profiling DataFrame: {sheet_name} {df.shape}")
        
        profile = {
            'types': {},
            'head10': [],
            'tail5': [],
            'distributions': {
                'categorical': {},
                'date': {},
                'numeric': {}
            }
        }
        
        # Infer column types
        for col in df.columns:
            col_type = infer_column_type(df[col])
            profile['types'][col] = col_type
        
        # Head 10 rows (convert datetime to string for JSON serialization)
        head_df = df.head(10).copy()
        for col in head_df.select_dtypes(include=['datetime64']).columns:
            head_df[col] = head_df[col].astype(str)
        profile['head10'] = head_df.to_dict(orient='records')
        
        # Tail 5 rows (convert datetime to string for JSON serialization)
        tail_df = df.tail(5).copy()
        for col in tail_df.select_dtypes(include=['datetime64']).columns:
            tail_df[col] = tail_df[col].astype(str)
        profile['tail5'] = tail_df.to_dict(orient='records')
        
        # Distribution summaries
        for col, col_type in profile['types'].items():
            try:
                dist = get_distribution_summary(df[col], col_type)
                profile['distributions'][col_type][col] = dist
            except Exception as e:
                logger.warning(f"Failed to get distribution for {col}: {e}")
        
        return profile
    
    def generate_field_description(self, col_name: str, col_type: str, 
                                   distribution: Any, head_samples: List[Any]) -> str:
        """
        Generate natural language description for a field
        
        Args:
            col_name: Column name
            col_type: Column type
            distribution: Distribution summary
            head_samples: Sample values from head
            
        Returns:
            Field description string
        """
        desc = f"字段名：{col_name}，类型：{col_type}"
        
        if col_type == "categorical":
            if distribution:
                top_values = [item[0] for item in distribution[:3]]
                desc += f"，常见值：{', '.join(map(str, top_values))}"
        
        elif col_type == "date":
            if distribution and 'min' in distribution:
                desc += f"，范围：{distribution['min']} 至 {distribution['max']}"
                desc += f"，粒度：{distribution.get('granularity', 'D')}"
        
        elif col_type == "numeric":
            if distribution and 'mean' in distribution:
                desc += f"，均值：{distribution['mean']:.2f}"
                desc += f"，范围：{distribution['min']:.2f} ~ {distribution['max']:.2f}"
        
        # Add sample values
        valid_samples = [s for s in head_samples if pd.notna(s)][:3]
        if valid_samples:
            desc += f"，示例：{', '.join(map(str, valid_samples))}"
        
        return desc
    
    def generate_summary(self, df: pd.DataFrame, profile: Dict[str, Any], 
                        sheet_name: str, file_name: str) -> Dict[str, Any]:
        """
        Generate complete summary for RAG indexing
        
        Args:
            df: DataFrame
            profile: Profile dict
            sheet_name: Sheet name
            file_name: File name
            
        Returns:
            Summary dict
        """
        summary = {
            'file_name': file_name,
            'sheet_name': sheet_name,
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': list(df.columns),
            'types': profile['types'],
            'profile': profile,
            'field_descriptions': []
        }
        
        # Generate field descriptions
        for col in df.columns:
            col_type = profile['types'].get(col, 'text')
            dist = profile['distributions'].get(col_type, {}).get(col, {})
            
            # Get head samples for this column
            head_samples = [row.get(col) for row in profile['head10']]
            
            desc = self.generate_field_description(col, col_type, dist, head_samples)
            summary['field_descriptions'].append(desc)
        
        # Detect date range if date columns exist
        date_cols = [col for col, t in profile['types'].items() if t == 'date']
        if date_cols:
            date_ranges = []
            for col in date_cols:
                dist = profile['distributions']['date'].get(col, {})
                if 'min' in dist and 'max' in dist:
                    date_ranges.append(f"{col}: {dist['min']} ~ {dist['max']}")
            if date_ranges:
                summary['date_range'] = ', '.join(date_ranges)
        
        # Generate text summary
        text_parts = [
            f"文件：{file_name}",
            f"工作表：{sheet_name}",
            f"行数：{len(df)}",
            f"列数：{len(df.columns)}",
            f"字段：{', '.join(df.columns[:10])}"
        ]
        if len(df.columns) > 10:
            text_parts[-1] += "..."
        
        summary['text_summary'] = '，'.join(text_parts)
        
        return summary

