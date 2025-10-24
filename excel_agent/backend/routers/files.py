"""
Files API router
"""
from fastapi import APIRouter, Depends
from typing import List, Dict, Any
import json
from pathlib import Path
from backend.config import settings
from backend.utils.logging import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/files", tags=["files"])


def get_file_metadata() -> List[Dict[str, Any]]:
    """Load file metadata from RAG index"""
    metadata_path = Path(settings.knowledge_base_dir) / "doc_metadata.json"
    
    if not metadata_path.exists():
        logger.warning("No metadata file found")
        return []
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Group by file name and count sheets
        file_groups = {}
        for item in metadata:
            file_name = item.get('file_name', 'Unknown')
            if file_name not in file_groups:
                file_groups[file_name] = {
                    'file_name': file_name,
                    'sheets': [],
                    'total_rows': 0,
                    'total_columns': 0
                }
            
            sheet_info = {
                'sheet_name': item.get('sheet_name', 'Unknown'),
                'row_count': item.get('row_count', 0),
                'column_count': item.get('column_count', 0),
                'columns': item.get('columns', [])
            }
            file_groups[file_name]['sheets'].append(sheet_info)
            file_groups[file_name]['total_rows'] += item.get('row_count', 0)
            file_groups[file_name]['total_columns'] = max(
                file_groups[file_name]['total_columns'], 
                item.get('column_count', 0)
            )
        
        # Convert to list and add descriptions
        result = []
        for file_name, info in file_groups.items():
            # Generate description based on file name and content
            description = generate_file_description(file_name, info)
            
            result.append({
                'file_name': file_name,
                'sheets': len(info['sheets']),
                'total_rows': info['total_rows'],
                'total_columns': info['total_columns'],
                'description': description,
                'sheet_details': info['sheets']
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error loading file metadata: {e}")
        return []


def generate_file_description(file_name: str, info: Dict[str, Any]) -> str:
    """Generate a description for the file based on its name and content"""
    file_lower = file_name.lower()
    
    # Check file name patterns
    if '学生' in file_name or '答辩' in file_name or '开题' in file_name:
        return '学术评审数据'
    elif '产品' in file_name or '清仓' in file_name or '价格' in file_name:
        return '产品定价数据'
    elif '复杂表头' in file_name:
        return '多级表头示例'
    elif '预算' in file_name or '支出' in file_name or '财政' in file_name:
        return '财政预算数据'
    elif '发电' in file_name or '日志' in file_name:
        return '发电运行数据'
    elif 'cola' in file_lower or '可乐' in file_name:
        return '销售数据分析'
    else:
        # Try to infer from column names
        all_columns = []
        for sheet in info['sheets']:
            all_columns.extend(sheet.get('columns', []))
        
        if any('销售' in col for col in all_columns):
            return '销售数据分析'
        elif any('学生' in col or '答辩' in col for col in all_columns):
            return '学术评审数据'
        elif any('价格' in col or '成本' in col for col in all_columns):
            return '产品定价数据'
        elif any('预算' in col or '支出' in col for col in all_columns):
            return '财政预算数据'
        else:
            return '数据分析文件'


@router.get("/list")
async def list_files() -> Dict[str, Any]:
    """Get list of available files in the knowledge base"""
    try:
        files = get_file_metadata()
        
        return {
            "success": True,
            "files": files,
            "total_files": len(files),
            "total_sheets": sum(f['sheets'] for f in files)
        }
        
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return {
            "success": False,
            "error": str(e),
            "files": [],
            "total_files": 0,
            "total_sheets": 0
        }


@router.get("/{file_name}")
async def get_file_details(file_name: str) -> Dict[str, Any]:
    """Get detailed information about a specific file"""
    try:
        files = get_file_metadata()
        
        for file_info in files:
            if file_info['file_name'] == file_name:
                return {
                    "success": True,
                    "file": file_info
                }
        
        return {
            "success": False,
            "error": f"File '{file_name}' not found"
        }
        
    except Exception as e:
        logger.error(f"Error getting file details for {file_name}: {e}")
        return {
            "success": False,
            "error": str(e)
        }
