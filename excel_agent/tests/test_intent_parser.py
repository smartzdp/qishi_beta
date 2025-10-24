"""
Test intent parser
"""
import pytest
from backend.services.intent.parser import IntentParser


def test_parse_aggregation_cn():
    """Test aggregation intent parsing (Chinese)"""
    parser = IntentParser()
    
    question = "求各地区销售额总和"
    intent = parser.parse(question)
    
    assert intent.is_aggregation
    assert intent.language == 'zh'
    assert len(intent.aggregations) > 0


def test_parse_trend_cn():
    """Test trend intent parsing (Chinese)"""
    parser = IntentParser()
    
    question = "帮我分析各地区销售趋势（从2023年起、按月）"
    intent = parser.parse(question)
    
    assert intent.is_trend
    assert intent.trend is not None
    assert intent.trend.frequency.value == 'M'
    assert intent.date_range is not None


def test_parse_ranking_cn():
    """Test ranking intent parsing (Chinese)"""
    parser = IntentParser()
    
    question = "显示销售额前10名的地区"
    intent = parser.parse(question)
    
    assert intent.is_ranking
    assert intent.top_n == 10


def test_parse_growth_cn():
    """Test growth intent parsing (Chinese)"""
    parser = IntentParser()
    
    question = "分析销售额同比增长"
    intent = parser.parse(question)
    
    assert intent.is_growth
    assert intent.growth is not None
    assert intent.growth.growth_type == 'yoy'


def test_parse_text_analysis_cn():
    """Test text analysis intent parsing (Chinese)"""
    parser = IntentParser()
    
    question = "提取答辩意见中的关键词"
    intent = parser.parse(question)
    
    assert intent.is_text_analysis
    assert intent.text_analysis is not None


def test_parse_price_analysis_cn():
    """Test price analysis intent parsing (Chinese)"""
    parser = IntentParser()
    
    question = "比较清仓价和建议零售价"
    intent = parser.parse(question)
    
    assert intent.is_price_analysis


def test_parse_aggregation_en():
    """Test aggregation intent parsing (English)"""
    parser = IntentParser()
    
    question = "Show total sales by region"
    intent = parser.parse(question)
    
    assert intent.is_aggregation
    assert intent.language == 'en'


def test_parse_ranking_en():
    """Test ranking intent parsing (English)"""
    parser = IntentParser()
    
    question = "Show top 5 SKUs by clearance discount vs MSRP in 2024"
    intent = parser.parse(question)
    
    assert intent.is_ranking
    assert intent.top_n == 5
    assert intent.is_price_analysis

