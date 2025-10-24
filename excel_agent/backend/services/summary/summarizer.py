"""
Result summarizer: generate natural language summary
"""
from typing import Dict, Any
from backend.utils.logging import setup_logger

logger = setup_logger(__name__)


class ResultSummarizer:
    """Summarize analysis results in natural language"""
    
    def __init__(self):
        """Initialize summarizer"""
        pass
    
    def summarize(self, question: str, plan: Dict[str, Any], 
                 execution_result: Dict[str, Any],
                 lineage: Dict[str, Any]) -> str:
        """
        Generate natural language summary
        
        Args:
            question: Original question
            plan: Execution plan
            execution_result: Execution result
            lineage: Data lineage
            
        Returns:
            Summary text in Chinese
        """
        logger.info("Generating summary")
        
        parts = []
        
        # Header
        parts.append(f"## 分析总结\n")
        parts.append(f"**问题**: {question}\n")
        
        # Data source
        file_name = plan.get('file_name', '')
        sheet_name = plan.get('sheet_name', '')
        parts.append(f"**数据来源**: {file_name} - {sheet_name}\n")
        
        # Analysis type
        analysis_types = []
        if plan.get('groupby'):
            analysis_types.append("分组统计")
        if plan.get('agg'):
            analysis_types.append("聚合计算")
        if plan.get('trend'):
            analysis_types.append("趋势分析")
        if plan.get('growth'):
            analysis_types.append("增长分析")
        if plan.get('text_ops'):
            analysis_types.append("文本分析")
        if plan.get('sort'):
            analysis_types.append("排序")
        
        if analysis_types:
            parts.append(f"**分析类型**: {', '.join(analysis_types)}\n")
        
        # Used columns
        if lineage and lineage.get('used_columns'):
            used_cols = lineage['used_columns']
            parts.append(f"**使用字段**: {', '.join(used_cols)} (共{len(used_cols)}个)\n")
        
        # Filters
        if plan.get('filters'):
            filter_strs = []
            for f in plan['filters']:
                filter_strs.append(f"{f['col']} {f['op']} {f['value']}")
            parts.append(f"**筛选条件**: {', '.join(filter_strs)}\n")
        
        # Results
        if execution_result.get('success'):
            parts.append(f"**执行状态**: ✅ 成功\n")
            
            # Check for figures
            if execution_result.get('figures'):
                parts.append(f"**可视化**: 已生成 {len(execution_result['figures'])} 个图表\n")
            
            # Check stdout for result counts
            stdout = execution_result.get('stdout', '')
            if '总行数:' in stdout:
                try:
                    count_line = [l for l in stdout.split('\n') if '总行数:' in l][0]
                    parts.append(f"**{count_line.strip()}**\n")
                except:
                    pass
        else:
            parts.append(f"**执行状态**: ❌ 失败\n")
            stderr = execution_result.get('stderr', '')
            if stderr:
                parts.append(f"**错误信息**: {stderr[:200]}\n")
        
        # Footer
        parts.append(f"\n---\n")
        parts.append(f"*分析由 Excel Agent 自动生成*")
        
        summary = '\n'.join(parts)
        return summary

