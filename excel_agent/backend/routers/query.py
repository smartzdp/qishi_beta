"""
Query router: natural language query with SSE streaming
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, AsyncGenerator
import json
import pandas as pd
from pathlib import Path

from backend.deps import get_rag_retriever, get_settings
from backend.services.intent import IntentParser
from backend.services.planner import FileSelector, QueryRewriter
from backend.services.codegen import CodeGenerator, LineageTracker
from backend.services.codegen.pseudocode_generator import get_pseudocode_generator
from backend.services.exec import CodeRunner
from backend.services.summary import ResultSummarizer
from backend.utils.sse import sse_message
from backend.utils.logging import setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/query", tags=["query"])


class QueryRequest(BaseModel):
    """Query request"""
    question: str
    language: Optional[str] = "zh"
    top_k: Optional[int] = 3
    allow_files: Optional[List[str]] = None
    disallow_files: Optional[List[str]] = None
    use_llm_codegen: Optional[bool] = True


async def query_stream_generator(request: QueryRequest, 
                                 retriever, settings) -> AsyncGenerator[str, None]:
    """
    Generate SSE stream for query processing
    
    Args:
        request: Query request
        retriever: RAG retriever
        settings: App settings
        
    Yields:
        SSE messages
    """
    try:
        # Step 1: Parse intent
        logger.info(f"Parsing intent for: {request.question}")
        parser = IntentParser()
        intent = parser.parse(request.question)
        
        yield await sse_message("intent", {
            "intent": intent.to_dict()
        })
        
        # Step 2: Select candidates
        logger.info("Selecting candidate files")
        selector = FileSelector(retriever)
        candidates = selector.select(
            intent,
            top_k=request.top_k,
            allow_files=request.allow_files,
            disallow_files=request.disallow_files
        )
        
        if not candidates:
            yield await sse_message("error", {
                "message": "未找到匹配的数据文件"
            })
            return
        
        yield await sse_message("candidates", {
            "candidates": candidates
        })
        
        # Step 3: Rewrite to plan (use first candidate)
        candidate = candidates[0]
        logger.info(f"Rewriting query for: {candidate['file_name']} - {candidate['sheet_name']}")
        
        rewriter = QueryRewriter()
        plan = rewriter.rewrite(intent, candidate)
        
        yield await sse_message("plan", {
            "plan": plan
        })
        
        # Step 4: Load data first (to get sample for code generation)
        logger.info("Loading data")
        
        # Find processed clean Excel file
        file_name = candidate['file_name']
        sheet_name = candidate['sheet_name']
        
        # Try to find the clean Excel file
        data_dir = settings.data_dir
        processed_dir = data_dir / "processed_clean"
        
        # Get clean Excel path from candidate summary
        clean_excel_path = candidate.get('summary', {}).get('clean_excel_path')
        
        if not clean_excel_path or not Path(clean_excel_path).exists():
            # Fallback: search for it
            for subdir in processed_dir.iterdir():
                if subdir.is_dir():
                    excel_file = subdir / f"{sheet_name}.xlsx"
                    if excel_file.exists():
                        clean_excel_path = str(excel_file)
                        break
        
        if not clean_excel_path or not Path(clean_excel_path).exists():
            yield await sse_message("error", {
                "message": f"未找到数据文件: {file_name} - {sheet_name}"
            })
            return
        
        # Load DataFrame
        df = pd.read_excel(clean_excel_path)
        logger.info(f"Loaded clean Excel: {Path(clean_excel_path).name}")
        
        if df is None:
            yield await sse_message("error", {
                "message": f"未找到数据文件: {file_name} - {sheet_name}"
            })
            return
        
        # Prepare detailed data sample for LLM (head 5 + tail 5)
        head5_str = df.head(5).to_string(index=False)
        tail5_str = df.tail(5).to_string(index=False)
        data_sample = f"【前5行数据】\n{head5_str}\n\n【后5行数据】\n{tail5_str}"
        
        # Get other sheets from the same original file
        original_file = candidate.get('summary', {}).get('original_file', file_name)
        all_sheets_info = candidate.get('summary', {}).get('all_sheets', [])
        
        other_sheets_data = []
        if len(all_sheets_info) > 1:
            logger.info(f"Found {len(all_sheets_info)} sheets in {original_file}")
            
            # Load info for other sheets
            for other_sheet in all_sheets_info:
                if other_sheet == sheet_name:
                    continue  # Skip current sheet
                
                # Try to load this sheet's data
                for subdir in processed_dir.iterdir():
                    if subdir.is_dir():
                        other_excel = subdir / f"{other_sheet}.xlsx"
                        other_meta = subdir / f"{other_sheet}_meta.json"
                        
                        if other_excel.exists():
                            try:
                                other_df = pd.read_excel(other_excel)
                                other_head = other_df.head(3).to_string(index=False)
                                other_tail = other_df.tail(2).to_string(index=False)
                                
                                # Load metadata for column info
                                other_columns = list(other_df.columns)
                                other_types = {}
                                if other_meta.exists():
                                    with open(other_meta, 'r', encoding='utf-8') as f:
                                        meta = json.load(f)
                                        other_types = meta.get('summary', {}).get('types', {})
                                
                                other_sheets_data.append({
                                    'sheet_name': other_sheet,
                                    'excel_path': str(other_excel),
                                    'shape': other_df.shape,
                                    'columns': other_columns,
                                    'types': other_types,
                                    'head_sample': other_head,
                                    'tail_sample': other_tail
                                })
                                
                                logger.info(f"  Loaded related sheet: {other_sheet} {other_df.shape}")
                            except Exception as e:
                                logger.warning(f"  Failed to load {other_sheet}: {e}")
                            break
        
        # Step 5: Generate code (with data context)
        logger.info("Generating code with LLM")
        code_generator = CodeGenerator(
            openai_api_key=settings.openai_api_key,
            openai_base_url=settings.openai_base_url,
            llm_model=settings.llm_model
        )
        
        try:
            code, expected_cols, prompt_used = code_generator.generate(
                plan,
                request.question,
                candidate['columns'],
                candidate['types'],
                data_sample=data_sample,
                row_count=len(df),
                excel_path=clean_excel_path,
                other_sheets=other_sheets_data,
                original_file=original_file,
                use_llm=request.use_llm_codegen if request.use_llm_codegen is not None else True
            )
        except Exception as e:
            yield await sse_message("error", {
                "message": f"AI代码生成失败: {str(e)}"
            })
            return
        
        # Send the prompt used (for debugging/transparency)
        logger.info(f"Prompt used length: {len(prompt_used) if prompt_used else 0}")
        if prompt_used and prompt_used.strip():
            yield await sse_message("prompt", {
                "prompt": prompt_used
            })
        else:
            logger.warning("Prompt used is empty or None")
        
        yield await sse_message("code", {
            "code": code,
            "language": "python"
        })
        
        # Generate pseudocode
        logger.info("Generating pseudocode")
        pseudocode_generator = get_pseudocode_generator()
        pseudocode = pseudocode_generator.generate_pseudocode(code, request.question)
        
        if pseudocode:
            yield await sse_message("pseudocode", {
                "pseudocode": pseudocode
            })
        
        yield await sse_message("exec_log", {
            "message": f"已加载数据: {df.shape[0]} 行 × {df.shape[1]} 列"
        })
        
        # Step 7: Execute code
        logger.info("Executing code")
        runner = CodeRunner(timeout=settings.code_execution_timeout)
        
        try:
            exec_result = runner.execute(
                code=code, 
                df=df, 
                file_name=file_name, 
                sheet_name=sheet_name,
                excel_path=clean_excel_path  # Pass clean Excel path for consistent loading
            )
        except Exception as e:
            yield await sse_message("error", {
                "message": f"代码执行失败: {str(e)}"
            })
            return
        
        # Stream execution logs
        if exec_result.get('stdout'):
            yield await sse_message("exec_log", {
                "message": exec_result['stdout'][:500]  # First 500 chars
            })
        
        if exec_result.get('stderr'):
            yield await sse_message("exec_log", {
                "message": f"警告: {exec_result['stderr'][:500]}",
                "level": "warning"
            })
        
        # Step 8: Result preview
        if exec_result.get('success'):
            result_data = {
                "tables": exec_result.get('tables', []),
                "figures": exec_result.get('figures', [])
            }
            
            yield await sse_message("result_preview", result_data)
        else:
            yield await sse_message("error", {
                "message": "执行失败",
                "stderr": exec_result.get('stderr', '')
            })
        
        # Step 9: Lineage
        logger.info("Computing lineage")
        lineage_tracker = LineageTracker()
        
        # Extract columns using both AST and regex
        ast_cols = lineage_tracker.extract_columns_from_ast(code)
        regex_cols = lineage_tracker.extract_columns_from_code_regex(code)
        
        # Combine both methods
        all_detected_cols = ast_cols | regex_cols
        
        lineage = lineage_tracker.merge_lineage(
            original_columns=list(df.columns),
            expected_columns=expected_cols,
            ast_columns=all_detected_cols,
            columns_map=None  # No mapping needed with clean Excel
        )
        
        yield await sse_message("lineage", lineage)
        
        # Step 10: Summary
        logger.info("Generating summary")
        summarizer = ResultSummarizer()
        summary = summarizer.summarize(
            request.question,
            plan,
            exec_result,
            lineage
        )
        
        yield await sse_message("summary", {
            "summary": summary
        })
        
        # Done
        yield await sse_message("done", {})
    
    except Exception as e:
        logger.error(f"Query stream error: {e}", exc_info=True)
        yield await sse_message("error", {
            "message": f"处理错误: {str(e)}"
        })


@router.post("/stream")
async def query_stream(
    request: QueryRequest,
    retriever = Depends(get_rag_retriever),
    settings = Depends(get_settings)
):
    """
    Stream query processing via SSE
    
    Args:
        request: Query request
        retriever: RAG retriever
        settings: App settings
        
    Returns:
        SSE streaming response
    """
    return StreamingResponse(
        query_stream_generator(request, retriever, settings),
        media_type="text/event-stream"
    )

