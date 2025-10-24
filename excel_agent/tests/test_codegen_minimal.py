"""
Test code generation (minimal)
"""
import pytest
from backend.services.codegen.generator import CodeGenerator


def test_generate_template_code():
    """Test template-based code generation"""
    generator = CodeGenerator()
    
    plan = {
        'file_name': 'test.xlsx',
        'sheet_name': 'Sheet1',
        'groupby': ['地区'],
        'agg': [{'col': '销售额', 'op': 'sum'}],
        'sort': [{'col': '销售额', 'order': 'desc'}],
        'limit': 10,
        'viz': 'bar',
        'filters': []
    }
    
    question = "按地区统计销售额，降序排列，取前10名"
    
    code, expected_cols = generator.generate(
        plan, question, ['地区', '销售额', '日期'], 
        {'地区': 'categorical', '销售额': 'numeric', '日期': 'date'}
    )
    
    assert 'import pandas as pd' in code
    assert 'groupby' in code
    assert '地区' in expected_cols
    assert '销售额' in expected_cols


def test_generate_trend_code():
    """Test trend analysis code generation"""
    generator = CodeGenerator()
    
    plan = {
        'file_name': 'test.xlsx',
        'sheet_name': 'Sheet1',
        'trend': {
            'date_col': '日期',
            'freq': 'M',
            'value_cols': ['销售额']
        },
        'groupby': [],
        'agg': [],
        'sort': [],
        'viz': 'line',
        'filters': []
    }
    
    question = "按月分析销售额趋势"
    
    code, expected_cols = generator.generate(
        plan, question, ['日期', '销售额'], 
        {'日期': 'date', '销售额': 'numeric'}
    )
    
    assert 'import pandas as pd' in code
    assert '日期' in code
    assert 'period' in code or 'trend' in code.lower()

