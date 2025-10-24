"""
Code router: debug endpoint for manual code execution
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import pandas as pd
import json
from pathlib import Path

from backend.deps import get_settings
from backend.services.exec import CodeRunner
from backend.services.codegen import LineageTracker
from backend.utils.logging import setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/code", tags=["code"])


class CodeExecuteRequest(BaseModel):
    """Code execution request"""
    code: str
    file_name: str
    sheet_name: str
    timeout: Optional[int] = 10


@router.post("/execute")
async def execute_code(
    request: CodeExecuteRequest,
    settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Execute Python code with data context
    
    Args:
        request: Code execution request
        settings: App settings
        
    Returns:
        Execution result
    """
    logger.info(f"Executing code for {request.file_name} - {request.sheet_name}")
    
    # Load data from clean Excel
    data_dir = settings.data_dir
    processed_dir = data_dir / "processed_clean"
    
    df = None
    
    for subdir in processed_dir.iterdir():
        if subdir.is_dir():
            excel_file = subdir / f"{request.sheet_name}.xlsx"
            if excel_file.exists():
                df = pd.read_excel(excel_file)
                logger.info(f"Loaded clean Excel: {excel_file.name}")
                break
    
    if df is None:
        raise HTTPException(status_code=404, detail=f"Data not found: {request.file_name} - {request.sheet_name}")
    
    # Execute
    runner = CodeRunner(timeout=request.timeout)
    exec_result = runner.execute(request.code, df, request.file_name, request.sheet_name)
    
    # Compute lineage (using both AST and regex)
    lineage_tracker = LineageTracker()
    ast_cols = lineage_tracker.extract_columns_from_ast(request.code)
    regex_cols = lineage_tracker.extract_columns_from_code_regex(request.code)
    
    # Combine both methods for better coverage
    all_detected_cols = ast_cols | regex_cols
    
    lineage = lineage_tracker.merge_lineage(
        original_columns=list(df.columns),
        expected_columns=[],
        ast_columns=all_detected_cols,
        columns_map=None  # No mapping needed with clean Excel
    )
    
    return {
        'execution': exec_result,
        'lineage': lineage
    }

