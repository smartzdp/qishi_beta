"""
Data lineage tracking: static AST + runtime tracking
Enhanced to handle chained calls like df.groupby()['col'].sum()
"""
import ast
import re
from typing import List, Set, Dict, Any
import pandas as pd
from backend.utils.logging import setup_logger

logger = setup_logger(__name__)


class LineageTracker:
    """Track data lineage for analysis code"""
    
    @staticmethod
    def extract_columns_from_code_regex(code: str) -> Set[str]:
        """
        Extract column names using regex as a fallback/supplement to AST
        Handles patterns like df['col'], df["col"], ['col'], ["col"]
        
        Args:
            code: Python code string
            
        Returns:
            Set of column names
        """
        columns = set()
        
        # Pattern 1: df['column_name'] or df["column_name"]
        pattern1 = r"df\[['\"]([^'\"]+)['\"]\]"
        matches1 = re.findall(pattern1, code)
        columns.update(matches1)
        
        # Pattern 2: ['column_name'] or ["column_name"] in any context
        pattern2 = r"\[['\"]([^'\"]+)['\"]\]"
        matches2 = re.findall(pattern2, code)
        # Filter out common non-column strings
        for m in matches2:
            if len(m) > 1 and m not in ['x', 'y', 'name', 'title', 'text']:
                columns.add(m)
        
        # Pattern 3: result['column_name']
        pattern3 = r"result\[['\"]([^'\"]+)['\"]\]"
        matches3 = re.findall(pattern3, code)
        columns.update(matches3)
        
        # Pattern 4: grouped['column_name']
        pattern4 = r"grouped\[['\"]([^'\"]+)['\"]\]"
        matches4 = re.findall(pattern4, code)
        columns.update(matches4)
        
        return columns
    
    @staticmethod
    def extract_columns_from_ast(code: str) -> Set[str]:
        """
        Extract column references from code using AST
        Enhanced to handle chained calls like df.groupby()['col'].sum()
        
        Args:
            code: Python code string
            
        Returns:
            Set of referenced column names
        """
        columns = set()
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # df['col'] or df["col"] or any_result['col']
                if isinstance(node, ast.Subscript):
                    if isinstance(node.slice, ast.Constant):
                        if isinstance(node.slice.value, str):
                            # Check if it's a reasonable column name (not a dict key like 'col')
                            col_name = node.slice.value
                            # Add if it contains Chinese, is alphanumeric, or contains common separators
                            if col_name and (
                                any('\u4e00' <= c <= '\u9fff' for c in col_name) or  # Chinese
                                col_name.replace('_', '').replace('-', '').replace('.', '').isalnum() or
                                len(col_name) > 1
                            ):
                                columns.add(col_name)
                    
                    # Handle df[['col1', 'col2']] - multiple columns
                    elif isinstance(node.slice, ast.List):
                        for elt in node.slice.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                columns.add(elt.value)
                
                # groupby(['col1', 'col2']) or sort_values('col')
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        if node.func.attr in ['groupby', 'sort_values', 'drop', 'dropna', 'agg']:
                            for arg in node.args:
                                if isinstance(arg, ast.List):
                                    for elt in arg.elts:
                                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                            columns.add(elt.value)
                                elif isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                                    columns.add(arg.value)
                                # Handle dict for agg: {'col': 'sum'}
                                elif isinstance(arg, ast.Dict):
                                    for key in arg.keys:
                                        if isinstance(key, ast.Constant) and isinstance(key.value, str):
                                            columns.add(key.value)
        
        except Exception as e:
            logger.warning(f"Failed to parse AST: {e}")
        
        logger.info(f"Extracted {len(columns)} columns from AST: {columns}")
        return columns
    
    @staticmethod
    def create_tracking_df(df: pd.DataFrame) -> pd.DataFrame:
        """
        Wrap DataFrame with tracking capability
        
        Note: This is a simplified version. For full tracking,
        we'd need to subclass DataFrame and override methods.
        
        Args:
            df: Original DataFrame
            
        Returns:
            DataFrame (with tracking metadata attached)
        """
        # Attach metadata
        df._accessed_columns = set()
        
        # We can't easily intercept __getitem__ without subclassing,
        # so we'll rely mainly on AST analysis
        
        return df
    
    @staticmethod
    def merge_lineage(original_columns: List[str], 
                     expected_columns: List[str],
                     ast_columns: Set[str],
                     columns_map: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Merge lineage from multiple sources
        
        Args:
            original_columns: Original column names from file
            expected_columns: Expected columns from plan
            ast_columns: Columns extracted from AST
            columns_map: Original->normalized column mapping
            
        Returns:
            Lineage dict
        """
        # Combine expected and AST columns
        used_columns = set(expected_columns) | ast_columns
        
        # Map back to original if mapping exists
        if columns_map:
            original_used = set()
            reverse_map = {v: k for k, v in columns_map.items()}
            
            for col in used_columns:
                if col in reverse_map:
                    original_used.add(reverse_map[col])
                else:
                    original_used.add(col)
        else:
            original_used = used_columns
        
        # Filter to actual columns that exist
        final_columns = [col for col in original_columns if col in used_columns]
        
        lineage = {
            'used_columns': final_columns,
            'column_count': len(final_columns),
            'original_column_count': len(original_columns),
            'coverage': len(final_columns) / max(len(original_columns), 1),
            'mapping': []
        }
        
        # Add mapping details
        if columns_map:
            for col in final_columns:
                if col in reverse_map:
                    lineage['mapping'].append({
                        'original': reverse_map[col],
                        'used': col
                    })
                else:
                    lineage['mapping'].append({
                        'original': col,
                        'used': col
                    })
        else:
            for col in final_columns:
                lineage['mapping'].append({
                    'original': col,
                    'used': col
                })
        
        logger.info(f"Lineage: {len(final_columns)}/{len(original_columns)} columns used")
        
        return lineage


class TrackingDataFrame(pd.DataFrame):
    """
    DataFrame subclass with column access tracking
    
    Note: This is a simplified implementation. Full tracking
    would require overriding many more methods.
    """
    
    _metadata = ['_accessed_columns']
    
    @property
    def _constructor(self):
        return TrackingDataFrame
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._accessed_columns = set()
    
    def __getitem__(self, key):
        """Track column access"""
        result = super().__getitem__(key)
        
        if isinstance(key, str):
            self._accessed_columns.add(key)
        elif isinstance(key, list):
            self._accessed_columns.update(key)
        
        return result
    
    def get_accessed_columns(self) -> Set[str]:
        """Get set of accessed columns"""
        return self._accessed_columns

