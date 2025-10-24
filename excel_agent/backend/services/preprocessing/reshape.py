"""
Excel reshape: detect headers, flatten multi-level headers, clean data
Wraps and extends examples/dismantle_excel.py
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import re
from backend.utils.df_utils import normalize_numeric, coerce_dates
from backend.utils.logging import setup_logger

logger = setup_logger(__name__)


class ExcelReshaper:
    """Reshape complex Excel sheets into clean 2D tables"""
    
    # Keywords for header detection
    HEADER_KEYWORDS = [
        '日期', '时间', '月份', '年度', '城市', '地区', '省份', '县', '区',
        '产品', '商品', '品类', '品牌', '规格', '单位', '编号', '条形码',
        '销售', '销量', '数量', '金额', '价格', '成本', '单价', '售价',
        '发电', '运行', '故障', '可利用率', '小时',
        '预算', '支出', '经费', '增长', '同比', '环比',
        '班级', '学号', '导师', '组别', '题目', '意见', '姓名', '学生',
        'Date', 'Time', 'City', 'Region', 'Product', 'Sales', 'Amount', 'Price'
    ]
    
    # Keywords for title/annotation rows to remove
    TITLE_KEYWORDS = ['单位', '表一', '表二', '表三', '表四', '编制', '审核', '填表日期']
    
    def detect_header_row(self, df: pd.DataFrame, max_search_rows: int = 12) -> Tuple[int, float]:
        """
        Auto-detect header row within first max_search_rows
        
        Args:
            df: Input DataFrame
            max_search_rows: Maximum rows to search
            
        Returns:
            Tuple of (header_row_index, confidence_score)
        """
        best_row = 0
        best_score = 0.0
        
        for i in range(min(max_search_rows, len(df))):
            row = df.iloc[i]
            score = 0.0
            
            # Non-empty ratio
            non_empty = row.notna().sum() / len(row)
            score += non_empty * 10
            
            # Keyword hits
            row_str = ' '.join([str(v) for v in row if pd.notna(v)])
            keyword_hits = sum(1 for kw in self.HEADER_KEYWORDS if kw in row_str)
            score += keyword_hits * 5
            
            # Lower numeric ratio is better for headers
            try:
                numeric_ratio = pd.to_numeric(row, errors='coerce').notna().sum() / len(row)
                score += (1 - numeric_ratio) * 3
            except:
                pass
            
            if score > best_score:
                best_score = score
                best_row = i
        
        logger.info(f"Detected header at row {best_row} (score: {best_score:.2f})")
        return best_row, best_score
    
    def detect_title_rows(self, df: pd.DataFrame, header_row: int) -> List[int]:
        """
        Detect title/annotation rows above header
        
        Args:
            df: Input DataFrame
            header_row: Detected header row index
            
        Returns:
            List of row indices to remove
        """
        rows_to_remove = []
        
        for i in range(header_row):
            row = df.iloc[i]
            row_str = ' '.join([str(v) for v in row if pd.notna(v)])
            
            # Check for title keywords
            for keyword in self.TITLE_KEYWORDS:
                if keyword in row_str:
                    rows_to_remove.append(i)
                    logger.info(f"Removing title row {i}: contains '{keyword}'")
                    break
        
        return rows_to_remove
    
    def flatten_multi_level_header(self, df: pd.DataFrame, header_row: int) -> Tuple[List[str], Dict[str, str]]:
        """
        Flatten multi-level headers
        
        Args:
            df: Input DataFrame
            header_row: Header start row
            
        Returns:
            Tuple of (flattened column names, original->normalized mapping)
        """
        # Check if there are multiple header rows (look 1-2 rows below)
        possible_header_rows = []
        for i in range(header_row, min(header_row + 3, len(df))):
            possible_header_rows.append(df.iloc[i])
        
        if len(possible_header_rows) == 1:
            # Single level header
            cols = [str(c) if pd.notna(c) else f'Unnamed_{i}' 
                   for i, c in enumerate(possible_header_rows[0])]
            mapping = {c: c for c in cols}
            return cols, mapping
        
        # Multi-level header: forward fill and concatenate
        flattened = []
        mapping = {}
        
        for col_idx in range(len(possible_header_rows[0])):
            parts = []
            for row in possible_header_rows:
                val = row.iloc[col_idx] if col_idx < len(row) else None
                if pd.notna(val):
                    val_str = str(val).strip()
                    if val_str and val_str not in parts:
                        parts.append(val_str)
            
            # Prefer rightmost part if multi-level
            if len(parts) > 1:
                flattened_name = parts[-1]  # Use rightmost (most specific)
                original_name = '.'.join(parts)
            elif len(parts) == 1:
                flattened_name = parts[0]
                original_name = parts[0]
            else:
                flattened_name = f'Unnamed_{col_idx}'
                original_name = flattened_name
            
            flattened.append(flattened_name)
            mapping[original_name] = flattened_name
        
        logger.info(f"Flattened {len(mapping)} columns from multi-level header")
        return flattened, mapping
    
    def handle_duplicate_columns(self, columns: List[str]) -> List[str]:
        """
        Handle duplicate column names by appending _1, _2, etc.
        
        Args:
            columns: List of column names
            
        Returns:
            List of unique column names
        """
        seen = {}
        result = []
        
        for col in columns:
            if col not in seen:
                seen[col] = 0
                result.append(col)
            else:
                seen[col] += 1
                result.append(f"{col}_{seen[col]}")
        
        return result
    
    def clean_numeric_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean numeric columns (prices, percentages, etc.)
        
        Args:
            df: Input DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        df = df.copy()
        
        for col in df.columns:
            col_lower = str(col).lower()
            
            # Price/amount columns
            if any(kw in col_lower for kw in ['价', '金额', '成本', '清仓', '零售', '单价', '售价', '采购']):
                logger.info(f"Cleaning price column: {col}")
                df[col] = normalize_numeric(df[col])
            
            # Percentage columns
            elif any(kw in col_lower for kw in ['增长', '增速', '同比', '环比', '%', '％', '可利用率', '率']):
                logger.info(f"Cleaning percentage column: {col}")
                df[col] = normalize_numeric(df[col])
            
            # Date columns
            elif any(kw in col_lower for kw in ['日期', '时间', 'date', 'time']):
                logger.info(f"Cleaning date column: {col}")
                df[col] = coerce_dates(df[col])
        
        return df
    
    def remove_empty_columns(self, df: pd.DataFrame, threshold: float = 0.98) -> pd.DataFrame:
        """
        Remove columns with high null ratio
        
        Args:
            df: Input DataFrame
            threshold: Null ratio threshold
            
        Returns:
            DataFrame with empty columns removed
        """
        null_ratios = df.isna().sum() / len(df)
        cols_to_keep = [col for col, ratio in null_ratios.items() if ratio < threshold]
        
        removed = len(df.columns) - len(cols_to_keep)
        if removed > 0:
            logger.info(f"Removed {removed} empty columns")
        
        return df[cols_to_keep]
    
    def reshape_sheet(self, df: pd.DataFrame, sheet_name: str) -> Dict[str, Any]:
        """
        Complete reshape pipeline for one sheet
        
        Args:
            df: Input DataFrame (raw)
            sheet_name: Sheet name
            
        Returns:
            Dict containing:
                - df: Cleaned DataFrame
                - columns_map: Original->normalized column mapping
                - log: Processing steps
                - issues: Issues encountered
        """
        log = []
        issues = []
        
        log.append(f"Processing sheet: {sheet_name}")
        log.append(f"Original shape: {df.shape}")
        
        # Step 1: Detect header row
        header_row, score = self.detect_header_row(df)
        log.append(f"Detected header at row {header_row} (score: {score:.2f})")
        
        # Step 2: Detect and remove title rows
        title_rows = self.detect_title_rows(df, header_row)
        if title_rows:
            log.append(f"Removing title rows: {title_rows}")
        
        # Step 3: Flatten multi-level header
        columns, columns_map = self.flatten_multi_level_header(df, header_row)
        
        # Step 4: Extract data rows (skip header and title rows)
        data_start_row = header_row + 1
        df_data = df.iloc[data_start_row:].reset_index(drop=True)
        
        # Step 5: Set column names
        df_data.columns = columns[:len(df_data.columns)]
        
        # Step 6: Handle duplicate columns
        df_data.columns = self.handle_duplicate_columns(list(df_data.columns))
        
        # Step 7: Remove empty columns
        df_data = self.remove_empty_columns(df_data)
        
        # Step 8: Clean numeric and date columns
        df_data = self.clean_numeric_columns(df_data)
        
        # Step 9: Remove completely empty rows
        df_data = df_data.dropna(how='all')
        
        log.append(f"Final shape: {df_data.shape}")
        
        # Check for issues
        if df_data.empty:
            issues.append("DataFrame is empty after cleaning")
        
        null_ratio = df_data.isna().sum().sum() / (df_data.shape[0] * df_data.shape[1])
        if null_ratio > 0.5:
            issues.append(f"High null ratio: {null_ratio:.2%}")
        
        return {
            'df': df_data,
            'columns_map': columns_map,
            'log': log,
            'issues': issues
        }
    
    def select_best_sheets(self, sheets_results: Dict[str, Dict], top_k: int = 3) -> List[str]:
        """
        Select best sheets based on quality metrics
        
        Args:
            sheets_results: Dict of sheet_name -> reshape result
            top_k: Number of sheets to select
            
        Returns:
            List of selected sheet names
        """
        scores = {}
        
        for sheet_name, result in sheets_results.items():
            df = result['df']
            if df.empty:
                scores[sheet_name] = 0
                continue
            
            score = 0.0
            
            # Shape score
            score += min(df.shape[0] / 100, 10)  # More rows is better
            score += df.shape[1]  # More columns is better
            
            # Completeness score
            null_ratio = df.isna().sum().sum() / (df.shape[0] * df.shape[1])
            score += (1 - null_ratio) * 10
            
            # Numeric column ratio
            numeric_cols = df.select_dtypes(include=[np.number]).shape[1]
            score += (numeric_cols / max(df.shape[1], 1)) * 5
            
            scores[sheet_name] = score
        
        # Sort by score
        sorted_sheets = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        selected = [name for name, score in sorted_sheets[:top_k]]
        
        logger.info(f"Selected sheets: {selected}")
        return selected

