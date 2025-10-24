"""
Ingest router: upload, preprocess, and index files
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from typing import Dict, Any
import tempfile
from pathlib import Path
import shutil

from backend.deps import get_rag_indexer, get_settings
from backend.services.preprocessing import FileLoader, ExcelReshaper, DataFrameProfiler
from backend.services.rag.indexer import json_serializable
from backend.utils.file_utils import is_excel_file, compute_file_hash
from backend.utils.logging import setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/ingest", tags=["ingest"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    indexer = Depends(get_rag_indexer),
    settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Upload and process an Excel file
    
    Args:
        file: Uploaded file
        indexer: RAG indexer
        settings: App settings
        
    Returns:
        Processing summary
    """
    logger.info(f"Received file upload: {file.filename}")
    
    # Validate file type
    if not is_excel_file(file.filename):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
        shutil.copyfileobj(file.file, tmp_file)
        tmp_path = Path(tmp_file.name)
    
    try:
        # Compute file hash
        file_hash = compute_file_hash(tmp_path)
        
        # Load sheets
        loader = FileLoader()
        sheets = loader.load_excel_sheets(tmp_path)
        
        if not sheets:
            raise HTTPException(status_code=400, detail="No sheets found in file")
        
        # Reshape each sheet
        reshaper = ExcelReshaper()
        profiler = DataFrameProfiler()
        
        sheets_results = {}
        summaries = []
        
        for sheet_name, raw_df in sheets.items():
            logger.info(f"Processing sheet: {sheet_name}")
            
            # Reshape
            result = reshaper.reshape_sheet(raw_df, sheet_name)
            df = result['df']
            
            if df.empty:
                logger.warning(f"Sheet {sheet_name} is empty after reshape, skipping")
                continue
            
            sheets_results[sheet_name] = result
            
            # Profile
            profile = profiler.profile(df, sheet_name)
            
            # Generate summary
            summary = profiler.generate_summary(
                df, profile, sheet_name, file.filename
            )
            
            summaries.append(summary)
            
            # Save processed data
            processed_dir = settings.data_dir / "processed" / file_hash
            processed_dir.mkdir(parents=True, exist_ok=True)
            
            df.to_pickle(processed_dir / f"{sheet_name}.pkl")
            
            # Save metadata (convert to JSON serializable format)
            import json
            meta_data = json_serializable({
                'file_name': file.filename,
                'sheet_name': sheet_name,
                'columns_map': result['columns_map'],
                'log': result['log'],
                'issues': result['issues'],
                'profile': profile,
                'summary': summary
            })
            
            with open(processed_dir / f"{sheet_name}_meta.json", 'w', encoding='utf-8') as f:
                json.dump(meta_data, f, ensure_ascii=False, indent=2)
        
        # Select best sheets
        best_sheets = reshaper.select_best_sheets(sheets_results, top_k=3)
        
        # Build index
        indexer.build_index(summaries)
        
        # Copy file to data directory
        saved_path = settings.data_dir / "uploaded" / file.filename
        saved_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(tmp_path, saved_path)
        
        return {
            'success': True,
            'file_name': file.filename,
            'file_hash': file_hash,
            'sheets_count': len(sheets),
            'processed_sheets': len(summaries),
            'best_sheets': best_sheets,
            'summaries': summaries[:3]  # Return first 3 summaries
        }
    
    except Exception as e:
        logger.error(f"Failed to process file: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up temp file
        tmp_path.unlink()

