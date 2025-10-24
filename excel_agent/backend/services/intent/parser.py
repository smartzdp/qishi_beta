"""
Intent parser: NL -> Intent using rules + LLM
"""
import re
from typing import Dict, Any, List, Optional
from backend.services.intent.schema import (
    Intent, AggregationType, TrendFrequency, VisualizationType,
    AggregationSpec, FilterCondition, SortSpec, TrendSpec, GrowthSpec, TextAnalysisSpec, SortOrder
)
from backend.utils.logging import setup_logger

logger = setup_logger(__name__)


class IntentParser:
    """Parse natural language into structured intent"""
    
    # Patterns for intent detection
    AGGREGATION_PATTERNS = {
        'sum': ['总', '求和', '合计', '累计', '总计', 'sum', 'total'],
        'mean': ['平均', '均值', 'average', 'mean'],
        'count': ['计数', '统计', '数量', '个数', 'count', 'number of'],
        'max': ['最大', '最高', '最多', 'max', 'maximum', 'highest'],
        'min': ['最小', '最低', '最少', 'min', 'minimum', 'lowest'],
    }
    
    GROUPBY_PATTERNS = ['按', '分组', '各', '每个', 'by', 'per', 'each', 'group by']
    
    TREND_PATTERNS = ['趋势', '变化', '走势', 'trend', 'change', 'over time']
    
    TIME_FREQ_PATTERNS = {
        'D': ['日', '天', 'day', 'daily'],
        'W': ['周', '星期', 'week', 'weekly'],
        'M': ['月', '月份', '月度', 'month', 'monthly'],
        'Q': ['季度', 'quarter', 'quarterly'],
        'Y': ['年', '年度', 'year', 'yearly', 'annual'],
    }
    
    RANKING_PATTERNS = ['排名', '前', '后', 'top', 'bottom', 'rank', '最']
    
    GROWTH_PATTERNS = {
        'yoy': ['同比', 'year-over-year', 'yoy'],
        'mom': ['环比', 'month-over-month', 'mom'],
        'general': ['增长', '增速', 'growth', 'increase'],
    }
    
    TEXT_PATTERNS = ['关键词', '意见', '评论', 'keyword', 'comment', 'text']
    
    PRICE_PATTERNS = ['价格', '成本', '折扣', '清仓', '零售价', 'price', 'cost', 'discount', 'clearance']
    
    def __init__(self):
        """Initialize intent parser"""
        pass
    
    def detect_language(self, question: str) -> str:
        """
        Detect language (zh or en)
        
        Args:
            question: User question
            
        Returns:
            Language code
        """
        # Simple heuristic: check for Chinese characters
        if re.search(r'[\u4e00-\u9fff]', question):
            return 'zh'
        return 'en'
    
    def extract_numbers(self, question: str) -> List[int]:
        """
        Extract numbers from question
        
        Args:
            question: User question
            
        Returns:
            List of numbers
        """
        numbers = re.findall(r'\d+', question)
        return [int(n) for n in numbers]
    
    def extract_date_range(self, question: str) -> Optional[Dict[str, str]]:
        """
        Extract date range from question
        
        Args:
            question: User question
            
        Returns:
            Dict with start/end dates if found
        """
        # Look for year patterns
        years = re.findall(r'20\d{2}', question)
        
        if len(years) >= 2:
            return {'start': f'{years[0]}-01-01', 'end': f'{years[1]}-12-31'}
        elif len(years) == 1:
            # "从2023年起" or "2024年"
            if '起' in question or 'since' in question.lower():
                return {'start': f'{years[0]}-01-01', 'end': None}
            else:
                return {'start': f'{years[0]}-01-01', 'end': f'{years[0]}-12-31'}
        
        return None
    
    def detect_aggregation(self, question: str) -> List[AggregationSpec]:
        """
        Detect aggregation operations
        
        Args:
            question: User question
            
        Returns:
            List of aggregation specs
        """
        aggregations = []
        
        for agg_type, patterns in self.AGGREGATION_PATTERNS.items():
            for pattern in patterns:
                if pattern in question:
                    # Try to extract column name (placeholder)
                    aggregations.append(AggregationSpec(
                        column='value',  # Will be resolved later
                        operation=agg_type
                    ))
                    break
        
        return aggregations
    
    def detect_groupby(self, question: str) -> List[str]:
        """
        Detect group-by columns
        
        Args:
            question: User question
            
        Returns:
            List of potential group-by keywords
        """
        groupby_keywords = []
        
        # Common dimension keywords
        dimensions = {
            'geography': ['地区', '城市', '省份', 'region', 'city', 'province'],
            'time': ['月', '年', 'month', 'year'],
            'product': ['产品', '商品', 'product', 'item', 'sku'],
            'category': ['类别', '品类', '分类', 'category', 'type'],
        }
        
        for dim, keywords in dimensions.items():
            for keyword in keywords:
                if keyword in question:
                    groupby_keywords.append(dim)
                    break
        
        return groupby_keywords
    
    def detect_trend_frequency(self, question: str) -> Optional[TrendFrequency]:
        """
        Detect trend analysis frequency
        
        Args:
            question: User question
            
        Returns:
            Trend frequency if detected
        """
        for freq, patterns in self.TIME_FREQ_PATTERNS.items():
            for pattern in patterns:
                if pattern in question:
                    return TrendFrequency(freq)
        
        return None
    
    def detect_visualization(self, question: str, intent_flags: Dict[str, bool]) -> VisualizationType:
        """
        Infer preferred visualization type
        
        Args:
            question: User question
            intent_flags: Dict of intent flags
            
        Returns:
            Visualization type
        """
        # Explicit mentions
        if '图' in question or '图表' in question or 'chart' in question:
            if '折线' in question or '趋势' in question or 'line' in question:
                return VisualizationType.LINE
            elif '柱状' in question or '条形' in question or 'bar' in question:
                return VisualizationType.BAR
            elif '饼图' in question or 'pie' in question:
                return VisualizationType.PIE
        
        # Infer from intent
        if intent_flags.get('is_trend'):
            return VisualizationType.LINE
        elif intent_flags.get('is_ranking') or intent_flags.get('is_groupby'):
            return VisualizationType.BAR
        elif '占比' in question or '比例' in question or 'proportion' in question:
            return VisualizationType.PIE
        
        return VisualizationType.TABLE
    
    def parse(self, question: str) -> Intent:
        """
        Parse natural language question into structured intent
        
        Args:
            question: User question
            
        Returns:
            Intent object
        """
        logger.info(f"Parsing question: {question}")
        
        # Detect language
        language = self.detect_language(question)
        
        # Initialize intent
        intent = Intent(
            original_question=question,
            language=language
        )
        
        # Detect aggregation
        aggregations = self.detect_aggregation(question)
        if aggregations:
            intent.is_aggregation = True
            intent.aggregations = aggregations
        
        # Detect group-by
        groupby_keywords = self.detect_groupby(question)
        if groupby_keywords:
            intent.is_groupby = True
            intent.mentioned_columns.extend(groupby_keywords)
        
        # Detect trend
        for pattern in self.TREND_PATTERNS:
            if pattern in question:
                intent.is_trend = True
                freq = self.detect_trend_frequency(question)
                intent.trend = TrendSpec(
                    date_column='date',  # Will be resolved later
                    frequency=freq or TrendFrequency.MONTH
                )
                break
        
        # Detect ranking/TopN
        for pattern in self.RANKING_PATTERNS:
            if pattern in question:
                intent.is_ranking = True
                # Extract number
                numbers = self.extract_numbers(question)
                if numbers:
                    intent.top_n = numbers[0]
                else:
                    intent.top_n = 10  # Default
                
                # Add sort spec
                if '最大' in question or '最高' in question or '最多' in question or 'top' in question.lower():
                    intent.sorts.append(SortSpec(column='value', order=SortOrder.DESC))
                elif '最小' in question or '最低' in question or '最少' in question or 'bottom' in question.lower():
                    intent.sorts.append(SortSpec(column='value', order=SortOrder.ASC))
                break
        
        # Detect growth analysis
        for growth_type, patterns in self.GROWTH_PATTERNS.items():
            for pattern in patterns:
                if pattern in question:
                    intent.is_growth = True
                    intent.growth = GrowthSpec(
                        date_column='date',
                        value_column='value',
                        growth_type=growth_type
                    )
                    break
        
        # Detect text analysis
        for pattern in self.TEXT_PATTERNS:
            if pattern in question:
                intent.is_text_analysis = True
                intent.text_analysis = TextAnalysisSpec(
                    text_column='text',
                    extract_keywords=True,
                    topk=20
                )
                break
        
        # Detect price analysis
        for pattern in self.PRICE_PATTERNS:
            if pattern in question:
                intent.is_price_analysis = True
                break
        
        # Extract date range
        date_range = self.extract_date_range(question)
        if date_range:
            intent.date_range = date_range
            # Add filter
            if date_range.get('start'):
                intent.filters.append(FilterCondition(
                    column='date',
                    operator='>=',
                    value=date_range['start']
                ))
            if date_range.get('end'):
                intent.filters.append(FilterCondition(
                    column='date',
                    operator='<=',
                    value=date_range['end']
                ))
        
        # Infer visualization
        intent_flags = {
            'is_trend': intent.is_trend,
            'is_ranking': intent.is_ranking,
            'is_groupby': intent.is_groupby,
        }
        intent.preferred_viz = self.detect_visualization(question, intent_flags)
        
        logger.info(f"Parsed intent: aggregation={intent.is_aggregation}, "
                   f"groupby={intent.is_groupby}, trend={intent.is_trend}, "
                   f"ranking={intent.is_ranking}, growth={intent.is_growth}, "
                   f"text={intent.is_text_analysis}, price={intent.is_price_analysis}")
        
        return intent

