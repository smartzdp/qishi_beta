"""
Intent schema definitions
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class AggregationType(str, Enum):
    """Aggregation types"""
    SUM = "sum"
    MEAN = "mean"
    COUNT = "count"
    MAX = "max"
    MIN = "min"
    MEDIAN = "median"


class TrendFrequency(str, Enum):
    """Trend analysis frequency"""
    DAY = "D"
    WEEK = "W"
    MONTH = "M"
    QUARTER = "Q"
    YEAR = "Y"


class VisualizationType(str, Enum):
    """Visualization types"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    TABLE = "table"


class SortOrder(str, Enum):
    """Sort order"""
    ASC = "asc"
    DESC = "desc"


class FilterCondition(BaseModel):
    """Filter condition"""
    column: str
    operator: str = Field(description="Comparison operator: =, !=, >, <, >=, <=, in, not in, contains")
    value: Any


class AggregationSpec(BaseModel):
    """Aggregation specification"""
    column: str
    operation: AggregationType


class SortSpec(BaseModel):
    """Sort specification"""
    column: str
    order: SortOrder = SortOrder.DESC


class TrendSpec(BaseModel):
    """Trend analysis specification"""
    date_column: str
    frequency: TrendFrequency = TrendFrequency.MONTH
    value_columns: List[str] = []


class GrowthSpec(BaseModel):
    """Growth analysis specification (YoY, MoM, etc.)"""
    date_column: str
    value_column: str
    growth_type: str = Field(description="yoy (year-over-year), mom (month-over-month), or general")


class TextAnalysisSpec(BaseModel):
    """Text analysis specification"""
    text_column: str
    extract_keywords: bool = True
    topk: int = 20


class Intent(BaseModel):
    """Parsed user intent"""
    original_question: str
    language: str = "zh"  # zh or en
    
    # Analysis type flags
    is_aggregation: bool = False
    is_groupby: bool = False
    is_trend: bool = False
    is_ranking: bool = False
    is_filtering: bool = False
    is_growth: bool = False
    is_text_analysis: bool = False
    is_price_analysis: bool = False
    
    # Specifications
    filters: List[FilterCondition] = []
    groupby_columns: List[str] = []
    aggregations: List[AggregationSpec] = []
    sorts: List[SortSpec] = []
    trend: Optional[TrendSpec] = None
    growth: Optional[GrowthSpec] = None
    text_analysis: Optional[TextAnalysisSpec] = None
    
    # Limits
    top_n: Optional[int] = None
    limit: Optional[int] = None
    
    # Visualization
    preferred_viz: VisualizationType = VisualizationType.TABLE
    
    # Extracted entities
    mentioned_columns: List[str] = []
    mentioned_values: List[str] = []
    date_range: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.model_dump()

