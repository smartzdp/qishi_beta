"""
Excel and CSV file loader
"""
import pandas as pd
from pathlib import Path
from typing import Dict, List, Union, Optional
import openpyxl
from backend.utils.logging import setup_logger

logger = setup_logger(__name__)


class FileLoader:
    """Load Excel and CSV files"""
    
    @staticmethod
    def load_excel_sheets(file_path: Union[str, Path]) -> Dict[str, pd.DataFrame]:
        """
        Load all sheets from an Excel file
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            Dictionary mapping sheet names to DataFrames
        """
        file_path = Path(file_path)
        logger.info(f"Loading Excel file: {file_path}")
        
        sheets = {}
        
        try:
            # Load with openpyxl for .xlsx files
            if file_path.suffix.lower() == '.xlsx':
                excel_file = pd.ExcelFile(file_path, engine='openpyxl')
            else:
                # Use xlrd for .xls files
                excel_file = pd.ExcelFile(file_path, engine='xlrd')
            
            for sheet_name in excel_file.sheet_names:
                try:
                    # Read without header first to analyze structure
                    df = pd.read_excel(
                        excel_file,
                        sheet_name=sheet_name,
                        header=None
                    )
                    sheets[sheet_name] = df
                    logger.info(f"  Loaded sheet '{sheet_name}': {df.shape}")
                except Exception as e:
                    logger.warning(f"  Failed to load sheet '{sheet_name}': {e}")
            
            excel_file.close()
            
        except Exception as e:
            logger.error(f"Failed to load Excel file: {e}")
            raise
        
        return sheets
    
    @staticmethod
    def load_csv(file_path: Union[str, Path], encoding: str = 'utf-8') -> pd.DataFrame:
        """
        Load CSV file
        
        Args:
            file_path: Path to CSV file
            encoding: File encoding
            
        Returns:
            DataFrame
        """
        file_path = Path(file_path)
        logger.info(f"Loading CSV file: {file_path}")
        
        try:
            # Try UTF-8 first
            df = pd.read_csv(file_path, encoding=encoding)
            logger.info(f"  Loaded CSV: {df.shape}")
            return df
        except UnicodeDecodeError:
            # Try GB18030 for Chinese files
            logger.warning("UTF-8 failed, trying GB18030")
            df = pd.read_csv(file_path, encoding='gb18030')
            logger.info(f"  Loaded CSV: {df.shape}")
            return df
        except Exception as e:
            logger.error(f"Failed to load CSV file: {e}")
            raise
    
    @staticmethod
    def get_sheet_preview(df: pd.DataFrame, n_rows: int = 15) -> List[List]:
        """
        Get preview of first n rows for sheet analysis
        
        Args:
            df: Input DataFrame
            n_rows: Number of rows to preview
            
        Returns:
            List of lists representing rows
        """
        preview = df.head(n_rows).values.tolist()
        # Convert to strings and handle NaN
        return [
            [str(cell) if pd.notna(cell) else '' for cell in row]
            for row in preview
        ]

