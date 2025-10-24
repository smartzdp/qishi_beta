"""
File utilities
"""
import hashlib
from pathlib import Path
from typing import Union


def compute_file_hash(file_path: Union[str, Path]) -> str:
    """
    Compute SHA256 hash of a file
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hex digest of the file hash
    """
    file_path = Path(file_path)
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()


def get_file_extension(file_path: Union[str, Path]) -> str:
    """
    Get file extension (lowercase, without dot)
    
    Args:
        file_path: Path to the file
        
    Returns:
        File extension
    """
    return Path(file_path).suffix.lower().lstrip('.')


def is_excel_file(file_path: Union[str, Path]) -> bool:
    """
    Check if file is an Excel file
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if Excel file
    """
    ext = get_file_extension(file_path)
    return ext in {'xlsx', 'xls', 'xlsm'}


def is_csv_file(file_path: Union[str, Path]) -> bool:
    """
    Check if file is a CSV file
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if CSV file
    """
    ext = get_file_extension(file_path)
    return ext == 'csv'

