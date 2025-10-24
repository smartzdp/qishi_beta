"""
Query rewriter: Intent + Candidate -> Executable Plan
"""
from typing import Dict, Any, List, Optional
from backend.services.intent.schema import Intent
from backend.utils.logging import setup_logger
from backend.utils.df_utils import fuzzy_match_cols

logger = setup_logger(__name__)


class QueryRewriter:
    """Rewrite intent into executable plan JSON"""
    
    def __init__(self):
        """Initialize query rewriter"""
        pass
    
    def resolve_columns(self, keywords: List[str], available_columns: List[str],
                       column_types: Dict[str, str]) -> Dict[str, str]:
        """
        Resolve abstract column keywords to actual column names
        
        Args:
            keywords: List of keywords (e.g., ['geography', 'time', 'sales'])
            available_columns: Available column names
            column_types: Column types dict
            
        Returns:
            Dict mapping keyword -> actual column name
        """
        resolved = {}
        
        # Type-based matching
        type_mapping = {
            'geography': 'categorical',
            'time': 'date',
            'date': 'date',
            'value': 'numeric',
            'amount': 'numeric',
            'sales': 'numeric',
            'text': 'text',
        }
        
        # Keyword patterns
        keyword_patterns = {
            'geography': ['地区', '城市', '省份', '区域', 'region', 'city', 'province'],
            'time': ['日期', '时间', '月', '年', 'date', 'time', 'month', 'year'],
            'sales': ['销售', '销量', '金额', 'sales', 'amount', 'revenue'],
            'product': ['产品', '商品', 'product', 'item', 'name', '名称'],
            'price': ['价格', '成本', '清仓', '零售', 'price', 'cost', 'clearance'],
            'text': ['意见', '评论', '备注', 'comment', 'note', 'remark'],
        }
        
        for keyword in keywords:
            matched = False
            
            # Try pattern matching first
            if keyword in keyword_patterns:
                patterns = keyword_patterns[keyword]
                for col in available_columns:
                    col_lower = col.lower()
                    if any(pat in col_lower for pat in patterns):
                        resolved[keyword] = col
                        matched = True
                        logger.info(f"Resolved '{keyword}' -> '{col}' (pattern match)")
                        break
            
            # Try type-based matching
            if not matched and keyword in type_mapping:
                target_type = type_mapping[keyword]
                for col, col_type in column_types.items():
                    if col_type == target_type and col in available_columns:
                        resolved[keyword] = col
                        matched = True
                        logger.info(f"Resolved '{keyword}' -> '{col}' (type match: {target_type})")
                        break
            
            # Fuzzy matching
            if not matched:
                matches = fuzzy_match_cols(keyword, available_columns)
                if matches:
                    resolved[keyword] = matches[0]
                    logger.info(f"Resolved '{keyword}' -> '{matches[0]}' (fuzzy match)")
                else:
                    logger.warning(f"Failed to resolve keyword: {keyword}")
        
        return resolved
    
    def rewrite(self, intent: Intent, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rewrite intent into executable plan
        
        Args:
            intent: Parsed intent
            candidate: Selected file/sheet candidate
            
        Returns:
            Executable plan dict
        """
        logger.info(f"Rewriting intent for file: {candidate['file_name']}, sheet: {candidate['sheet_name']}")
        
        columns = candidate['columns']
        types = candidate['types']
        
        plan = {
            'file_name': candidate['file_name'],
            'sheet_name': candidate['sheet_name'],
            'filters': [],
            'groupby': [],
            'agg': [],
            'trend': None,
            'growth': None,
            'text_ops': None,
            'sort': [],
            'limit': None,
            'viz': intent.preferred_viz.value
        }
        
        # Build column resolution keywords
        resolution_keywords = []
        
        # Add keywords from group-by
        if intent.is_groupby:
            resolution_keywords.extend(intent.mentioned_columns)
        
        # Add keywords for time/date
        if intent.is_trend or intent.growth:
            resolution_keywords.append('time')
            resolution_keywords.append('date')
        
        # Add keywords for values
        if intent.is_aggregation or intent.is_ranking:
            resolution_keywords.append('sales')
            resolution_keywords.append('value')
            resolution_keywords.append('amount')
            resolution_keywords.append('price')
            resolution_keywords.append('清仓价')
            resolution_keywords.append('价格')
        
        # Add keywords for text
        if intent.is_text_analysis:
            resolution_keywords.append('text')
        
        # Resolve columns
        resolved_cols = self.resolve_columns(resolution_keywords, columns, types)
        logger.info(f"Resolution keywords: {resolution_keywords}")
        logger.info(f"Resolved columns: {resolved_cols}")
        
        # Build filters
        for filter_cond in intent.filters:
            # Resolve column name
            col_name = resolved_cols.get(filter_cond.column, filter_cond.column)
            if col_name in columns:
                plan['filters'].append({
                    'col': col_name,
                    'op': filter_cond.operator,
                    'value': filter_cond.value
                })
        
        # Build group-by
        if intent.is_groupby:
            for keyword in intent.mentioned_columns:
                col_name = resolved_cols.get(keyword)
                if col_name and col_name in columns:
                    plan['groupby'].append(col_name)
        
        # Build aggregations
        if intent.is_aggregation:
            for agg_spec in intent.aggregations:
                # Find numeric columns
                numeric_cols = [col for col, t in types.items() if t == 'numeric']
                if numeric_cols:
                    for num_col in numeric_cols[:3]:  # Use first few numeric columns
                        plan['agg'].append({
                            'col': num_col,
                            'op': agg_spec.operation.value
                        })
        
        # Build trend
        if intent.is_trend and intent.trend:
            date_col = resolved_cols.get('date') or resolved_cols.get('time')
            if not date_col:
                # Fallback: find any date column
                date_cols = [col for col, t in types.items() if t == 'date']
                if date_cols:
                    date_col = date_cols[0]
            
            if date_col:
                plan['trend'] = {
                    'date_col': date_col,
                    'freq': intent.trend.frequency.value
                }
                
                # Add value columns
                value_cols = []
                if plan['agg']:
                    value_cols = [a['col'] for a in plan['agg']]
                else:
                    # Use numeric columns
                    numeric_cols = [col for col, t in types.items() if t == 'numeric']
                    value_cols = numeric_cols[:2]
                
                plan['trend']['value_cols'] = value_cols
        
        # Build growth
        if intent.is_growth and intent.growth:
            date_col = resolved_cols.get('date') or resolved_cols.get('time')
            value_col = resolved_cols.get('value') or resolved_cols.get('sales')
            
            if not date_col:
                date_cols = [col for col, t in types.items() if t == 'date']
                if date_cols:
                    date_col = date_cols[0]
            
            if not value_col:
                numeric_cols = [col for col, t in types.items() if t == 'numeric']
                if numeric_cols:
                    value_col = numeric_cols[0]
            
            if date_col and value_col:
                plan['growth'] = {
                    'date_col': date_col,
                    'value_col': value_col,
                    'growth_type': intent.growth.growth_type
                }
        
        # Build text operations
        if intent.is_text_analysis and intent.text_analysis:
            text_col = resolved_cols.get('text')
            if not text_col:
                text_cols = [col for col, t in types.items() if t == 'text']
                if text_cols:
                    text_col = text_cols[0]
            
            if text_col:
                plan['text_ops'] = {
                    'text_col': text_col,
                    'keywords': True,
                    'tokenizer': 'simple_zh' if intent.language == 'zh' else 'simple_en',
                    'topk': intent.text_analysis.topk
                }
        
        # Build sort
        if intent.is_ranking:
            for sort_spec in intent.sorts:
                # Resolve value column
                value_col = resolved_cols.get('value') or resolved_cols.get('sales')
                if not value_col:
                    # Look for price-related columns first (even if marked as 'date')
                    price_cols = [col for col in columns if '价格' in col or '清仓价' in col or 'price' in col.lower()]
                    if price_cols:
                        value_col = price_cols[0]
                    else:
                        # Fallback: look for numeric columns
                        numeric_cols = [col for col, t in types.items() if t == 'numeric']
                        if numeric_cols:
                            value_col = numeric_cols[0]
                
                if value_col:
                    plan['sort'].append({
                        'col': value_col,
                        'order': sort_spec.order.value
                    })
            
            # Set limit
            if intent.top_n:
                plan['limit'] = intent.top_n
        
        logger.info(f"Generated plan: groupby={plan['groupby']}, "
                   f"agg={len(plan['agg'])}, filters={len(plan['filters'])}, "
                   f"trend={plan['trend'] is not None}, sort={len(plan['sort'])}")
        
        return plan

