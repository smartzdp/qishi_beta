"""
Test code execution runner
"""
import pytest
import pandas as pd
from backend.services.exec.runner import CodeRunner


def test_execute_simple_code():
    """Test simple code execution"""
    runner = CodeRunner(timeout=5)
    
    code = """
print("Hello from code execution")
print(f"DataFrame shape: {df.shape}")
"""
    
    df = pd.DataFrame({
        '地区': ['北京', '上海', '广州'],
        '销售额': [100, 200, 150]
    })
    
    result = runner.execute(code, df, 'test.xlsx', 'Sheet1')
    
    assert 'stdout' in result
    assert 'Hello from code execution' in result['stdout']


def test_execute_with_error():
    """Test code execution with error"""
    runner = CodeRunner(timeout=5)
    
    code = """
# This will cause an error
result = 1 / 0
"""
    
    df = pd.DataFrame({'col': [1, 2, 3]})
    
    result = runner.execute(code, df, 'test.xlsx', 'Sheet1')
    
    # Should have stderr
    assert result['stderr'] or not result['success']


def test_execute_timeout():
    """Test execution timeout"""
    runner = CodeRunner(timeout=1)
    
    code = """
import time
time.sleep(10)  # Sleep longer than timeout
"""
    
    df = pd.DataFrame({'col': [1, 2, 3]})
    
    result = runner.execute(code, df, 'test.xlsx', 'Sheet1')
    
    assert not result['success']
    assert 'timeout' in result['stderr'].lower()

