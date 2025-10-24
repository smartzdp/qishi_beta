"""
DataFrame utilities
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import difflib


def normalize_numeric(series: pd.Series) -> pd.Series:
    """
    Normalize numeric series by removing Chinese punctuation, spaces, etc.
    
    Args:
        series: Input series
        
    Returns:
        Normalized numeric series
    """
    if series.dtype in [np.float64, np.int64]:
        return series
    
    # Convert to string
    s = series.astype(str)
    
    # Remove thousands separators, spaces, Chinese punctuation
    s = s.str.replace(',', '', regex=False)
    s = s.str.replace('，', '', regex=False)
    s = s.str.replace(' ', '', regex=False)
    s = s.str.replace('　', '', regex=False)  # Full-width space
    
    # Remove currency symbols
    s = s.str.replace('¥', '', regex=False)
    s = s.str.replace('$', '', regex=False)
    s = s.str.replace('元', '', regex=False)
    
    # Remove percentage symbols (but keep the number)
    s = s.str.replace('%', '', regex=False)
    s = s.str.replace('％', '', regex=False)
    
    # Convert to numeric
    return pd.to_numeric(s, errors='coerce')


def coerce_dates(series: pd.Series) -> pd.Series:
    """
    Coerce series to datetime, supporting multiple formats
    
    Args:
        series: Input series
        
    Returns:
        DateTime series
    """
    # Try standard formats first
    result = pd.to_datetime(series, errors='coerce')
    
    # If many NaT, try Chinese format YYYY.M.D
    if result.isna().sum() > len(series) * 0.5:
        # Try replacing . with -
        if series.dtype == object:
            s = series.astype(str).str.replace('.', '-', regex=False)
            result = pd.to_datetime(s, errors='coerce')
    
    return result


def fuzzy_match_cols(need: str, cols: List[str], cutoff: float = 0.6) -> List[str]:
    """
    Fuzzy match column names
    
    Args:
        need: Column name to find
        cols: Available column names
        cutoff: Similarity threshold
        
    Returns:
        List of matching column names
    """
    return difflib.get_close_matches(need, cols, n=5, cutoff=cutoff)


def infer_column_type(series: pd.Series) -> str:
    """
    Infer column type: categorical, date, numeric, or text
    
    Args:
        series: Input series
        
    Returns:
        Column type string
    """
    # Remove nulls for analysis
    s = series.dropna()
    if len(s) == 0:
        return "text"
    
    # Check if numeric
    if pd.api.types.is_numeric_dtype(s):
        return "numeric"
    
    # Check if datetime
    if pd.api.types.is_datetime64_any_dtype(s):
        return "date"
    
    # Try to convert to datetime (but only for string-like data)
    if s.dtype == object:
        try:
            dt = pd.to_datetime(s, errors='coerce')
            if dt.notna().sum() > len(s) * 0.7:
                return "date"
        except:
            pass
    
    # Check if categorical (few unique values)
    unique_ratio = len(s.unique()) / len(s)
    if unique_ratio < 0.1 and len(s.unique()) < 50:
        return "categorical"
    
    # Check average string length
    avg_len = s.astype(str).str.len().mean()
    if avg_len > 100:
        return "text"
    
    # Default to categorical
    return "categorical"


def get_distribution_summary(series: pd.Series, col_type: str) -> Dict[str, Any]:
    """
    Get distribution summary for a column
    
    Args:
        series: Input series
        col_type: Column type (from infer_column_type)
        
    Returns:
        Distribution summary dict
    """
    s = series.dropna()
    
    if col_type == "categorical":
        # Top value counts
        value_counts = s.value_counts().head(10)
        total = len(s)
        return [
            [str(val), int(count), round(count / total * 100, 2)]
            for val, count in value_counts.items()
        ]
    
    elif col_type == "date":
        # Date range and granularity
        try:
            dt = pd.to_datetime(s, errors='coerce').dropna()
            if len(dt) == 0:
                return {}
            
            date_range = (dt.max() - dt.min()).days
            if date_range < 7:
                granularity = "D"
            elif date_range < 60:
                granularity = "W"
            elif date_range < 730:
                granularity = "M"
            else:
                granularity = "Y"
            
            result = {
                "min": str(dt.min().date()),
                "max": str(dt.max().date()),
                "granularity": granularity
            }
            
            # Monthly histogram
            if granularity in ["M", "Y"]:
                monthly = dt.dt.to_period('M').value_counts().sort_index().head(24)
                result["hist"] = [
                    [str(period), int(count)]
                    for period, count in monthly.items()
                ]
            
            return result
        except Exception as e:
            return {}
    
    elif col_type == "numeric":
        # Numeric statistics
        try:
            desc = s.describe()
            result = {
                "count": int(desc.get("count", 0)),
                "mean": round(float(desc.get("mean", 0)), 2),
                "std": round(float(desc.get("std", 0)), 2),
                "min": round(float(desc.get("min", 0)), 2),
                "25%": round(float(desc.get("25%", 0)), 2),
                "50%": round(float(desc.get("50%", 0)), 2),
                "75%": round(float(desc.get("75%", 0)), 2),
                "max": round(float(desc.get("max", 0)), 2),
            }
            
            # Simple histogram (10 bins)
            try:
                hist, bins = np.histogram(s, bins=10)
                result["hist"] = [
                    [round(float(bins[i]), 2), round(float(bins[i+1]), 2), int(hist[i])]
                    for i in range(len(hist))
                ]
            except:
                pass
            
            return result
        except:
            return {}
    
    return {}


def melt_wide_to_long(df: pd.DataFrame, id_vars: List[str], 
                      value_vars: List[str], 
                      var_name: str = "variable",
                      value_name: str = "value") -> pd.DataFrame:
    """
    Convert wide format to long format
    
    Args:
        df: Input DataFrame
        id_vars: ID columns
        value_vars: Value columns to melt
        var_name: Name for variable column
        value_name: Name for value column
        
    Returns:
        Melted DataFrame
    """
    return pd.melt(
        df,
        id_vars=id_vars,
        value_vars=value_vars,
        var_name=var_name,
        value_name=value_name
    )

