"""
Code execution runner: execute Python code in subprocess with timeout
Wraps examples/execute_python.py
"""
import subprocess
import tempfile
import json
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
from backend.utils.logging import setup_logger

logger = setup_logger(__name__)


class CodeRunner:
    """Execute Python code safely in subprocess"""
    
    def __init__(self, timeout: int = 10):
        """
        Initialize code runner
        
        Args:
            timeout: Execution timeout in seconds
        """
        self.timeout = timeout
    
    def execute(self, code: str, df: pd.DataFrame = None,
               file_name: str = "", sheet_name: str = "",
               excel_path: str = None) -> Dict[str, Any]:
        """
        Execute Python code with data context
        
        Args:
            code: Python code to execute
            df: DataFrame to provide as context (optional if excel_path provided)
            file_name: Original file name (for logging)
            sheet_name: Sheet name (for logging)
            excel_path: Path to clean Excel file (preferred method)
            
        Returns:
            Execution result dict with stdout, stderr, tables, figures
        """
        logger.info(f"Executing code for {file_name} - {sheet_name}")
        
        # Create temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Prepare code with data loading
            if excel_path and Path(excel_path).exists():
                # Load from Excel file (better for column name consistency)
                # Use absolute path for subprocess
                abs_excel_path = Path(excel_path).absolute()
                data_load_code = f"df = pd.read_excel('{abs_excel_path}')"
                logger.info(f"Loading from clean Excel: {abs_excel_path}")
            else:
                # Fallback to pickle
                df_path = tmpdir_path / "data.pkl"
                df.to_pickle(df_path)
                data_load_code = f"df = pd.read_pickle('{df_path}')"
                logger.info(f"Loading from pickle")
            
            full_code = f"""
import pandas as pd
import numpy as np
import sys
import traceback

# Load data
{data_load_code}

# User code
try:
{chr(10).join('    ' + line for line in code.split(chr(10)))}
except Exception as e:
    print(f'ERROR: {{e}}', file=sys.stderr)
    traceback.print_exc()
"""
            
            # Write code to temp file
            code_path = tmpdir_path / "script.py"
            with open(code_path, 'w', encoding='utf-8') as f:
                f.write(full_code)
            
            # Execute with subprocess
            try:
                result = subprocess.run(
                    ['python', str(code_path)],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=tmpdir
                )
                
                stdout = result.stdout
                stderr = result.stderr
                returncode = result.returncode
                
            except subprocess.TimeoutExpired:
                logger.error(f"Execution timeout ({self.timeout}s)")
                return {
                    'success': False,
                    'stdout': '',
                    'stderr': f'Execution timeout ({self.timeout}s)',
                    'tables': [],
                    'figures': [],
                    'used_files': [{'file': file_name, 'sheet': sheet_name}]
                }
            
            except Exception as e:
                logger.error(f"Execution failed: {e}")
                return {
                    'success': False,
                    'stdout': '',
                    'stderr': str(e),
                    'tables': [],
                    'figures': [],
                    'used_files': [{'file': file_name, 'sheet': sheet_name}]
                }
        
        # Parse output
        success = (returncode == 0) and (not stderr or 'ERROR:' not in stderr)
        
        # Extract Plotly JSON if present
        figures = []
        if 'PLOTLY_JSON:' in stdout:
            parts = stdout.split('PLOTLY_JSON:')
            for i in range(1, len(parts)):
                try:
                    json_str = parts[i].strip().split('\n')[0]
                    fig_json = json.loads(json_str)
                    figures.append(fig_json)
                except:
                    pass
        
        # Extract table data (simplified)
        tables = []
        if '=== 分析结果 ===' in stdout:
            # Table is in stdout
            tables.append({
                'data': stdout,  # For now, just include raw output
                'format': 'text'
            })
        
        result_dict = {
            'success': success,
            'stdout': stdout,
            'stderr': stderr,
            'tables': tables,
            'figures': figures,
            'used_files': [{'file': file_name, 'sheet': sheet_name}]
        }
        
        logger.info(f"Execution {'succeeded' if success else 'failed'}")
        
        return result_dict
    
    def execute_with_examples_script(self, code: str, df: pd.DataFrame,
                                     file_name: str = "", sheet_name: str = "") -> Dict[str, Any]:
        """
        Execute using examples/execute_python.py if available
        
        This is the preferred method as specified in the requirements
        
        Args:
            code: Python code
            df: DataFrame
            file_name: File name
            sheet_name: Sheet name
            
        Returns:
            Execution result dict
        """
        # Check if examples/execute_python.py exists
        examples_script = Path("examples/execute_python.py")
        
        if not examples_script.exists():
            # Fallback to direct execution
            logger.warning("examples/execute_python.py not found, using direct execution")
            return self.execute(code, df, file_name, sheet_name)
        
        # Create temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Save DataFrame and code
            df_path = tmpdir_path / "data.pkl"
            df.to_pickle(df_path)
            
            # Modify code to load data
            full_code = f"""
import pandas as pd
df = pd.read_pickle('{df_path}')

{code}
"""
            
            code_path = tmpdir_path / "script.py"
            with open(code_path, 'w', encoding='utf-8') as f:
                f.write(full_code)
            
            # Execute with examples script
            try:
                result = subprocess.run(
                    ['python', str(examples_script), str(code_path), str(tmpdir_path), str(self.timeout)],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout + 5  # Extra buffer
                )
                
                stdout = result.stdout
                stderr = result.stderr
                success = (result.returncode == 0)
                
            except subprocess.TimeoutExpired:
                return {
                    'success': False,
                    'stdout': '',
                    'stderr': f'Execution timeout ({self.timeout}s)',
                    'tables': [],
                    'figures': [],
                    'used_files': [{'file': file_name, 'sheet': sheet_name}]
                }
            except Exception as e:
                logger.error(f"Execution with examples script failed: {e}")
                return self.execute(code, df, file_name, sheet_name)
        
        # Parse output
        figures = []
        if 'PLOTLY_JSON:' in stdout:
            parts = stdout.split('PLOTLY_JSON:')
            for i in range(1, len(parts)):
                try:
                    json_str = parts[i].strip().split('\n')[0]
                    fig_json = json.loads(json_str)
                    figures.append(fig_json)
                except:
                    pass
        
        tables = []
        if '=== 分析结果 ===' in stdout:
            tables.append({
                'data': stdout,
                'format': 'text'
            })
        
        return {
            'success': success,
            'stdout': stdout,
            'stderr': stderr,
            'tables': tables,
            'figures': figures,
            'used_files': [{'file': file_name, 'sheet': sheet_name}]
        }

