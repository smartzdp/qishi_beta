"""
Test data lineage tracking
"""
import pytest
from backend.services.codegen.lineage import LineageTracker


def test_extract_columns_from_ast():
    """Test column extraction from AST"""
    tracker = LineageTracker()
    
    code = """
df['销售额'].sum()
df.groupby(['地区', '日期']).agg({'销售额': 'sum'})
result = df[df['日期'] >= '2023-01-01']
"""
    
    columns = tracker.extract_columns_from_ast(code)
    
    assert '销售额' in columns
    assert '地区' in columns
    assert '日期' in columns


def test_merge_lineage():
    """Test lineage merging"""
    tracker = LineageTracker()
    
    original_columns = ['地区', '销售额', '日期', '产品名称']
    expected_columns = ['地区', '销售额']
    ast_columns = {'销售额', '地区', '日期'}
    
    lineage = tracker.merge_lineage(
        original_columns,
        expected_columns,
        ast_columns
    )
    
    assert lineage['column_count'] >= 2
    assert '地区' in lineage['used_columns']
    assert '销售额' in lineage['used_columns']


def test_merge_lineage_with_mapping():
    """Test lineage merging with column mapping"""
    tracker = LineageTracker()
    
    original_columns = ['地区', '销售额', '日期']
    expected_columns = ['region', 'sales']
    ast_columns = {'region', 'sales'}
    columns_map = {'地区': 'region', '销售额': 'sales'}
    
    lineage = tracker.merge_lineage(
        original_columns,
        expected_columns,
        ast_columns,
        columns_map
    )
    
    assert len(lineage['mapping']) > 0

