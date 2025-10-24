"""
Code generator: Plan -> Python code (template-first approach)
"""
import os
import json
from typing import Dict, Any, List, Tuple
from jinja2 import Template
from backend.services.codegen.prompt_templates_v2 import CODE_GENERATION_TEMPLATE, CODE_EXPLANATION_TEMPLATE
from backend.utils.logging import setup_logger

logger = setup_logger(__name__)


class CodeGenerator:
    """Generate Python analysis code from plan"""
    
    def __init__(self, openai_api_key: str = None, openai_base_url: str = None, llm_model: str = "gpt-4"):
        """
        Initialize code generator
        
        Args:
            openai_api_key: OpenAI API key
            openai_base_url: OpenAI API base URL
            llm_model: LLM model name
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.openai_base_url = openai_base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.llm_model = llm_model
    
    def generate_template_code(self, plan: Dict[str, Any], question: str, columns: List[str] = None) -> str:
        """
        Generate code using templates (faster, more reliable)
        
        Args:
            plan: Executable plan
            question: Original question
            
        Returns:
            Python code string
        """
        logger.info("Generating code from template")
        
        file_name = plan['file_name']
        sheet_name = plan['sheet_name']
        
        # Start with imports and data loading
        code_lines = [
            "import pandas as pd",
            "import numpy as np",
            "import plotly.graph_objects as go",
            "import plotly.express as px",
            "import json",
            "import re",
            "from collections import Counter",
            "",
            "# 辅助函数",
            "def normalize_numeric(series):",
            "    if series.dtype in [np.float64, np.int64]:",
            "        return series",
            "    s = series.astype(str)",
            "    s = s.str.replace(',', '').str.replace('，', '').str.replace(' ', '')",
            "    s = s.str.replace('¥', '').str.replace('$', '').str.replace('元', '')",
            "    s = s.str.replace('%', '').str.replace('％', '')",
            "    return pd.to_numeric(s, errors='coerce')",
            "",
            "def extract_zh_keywords(text_series, topk=20):",
            "    all_text = ' '.join(text_series.dropna().astype(str))",
            "    words = re.findall(r'[\\u4e00-\\u9fff]+', all_text)",
            "    words = [w for w in words if len(w) >= 2]",
            "    counter = Counter(words)",
            "    return counter.most_common(topk)",
            "",
            f"# 加载数据：{file_name} - {sheet_name}",
            "# 注意：实际执行时，df会由执行器传入",
            "# df = pd.read_excel(...)",
            "",
        ]
        
        # Apply filters
        if plan.get('filters'):
            code_lines.append("# 应用过滤条件")
            for f in plan['filters']:
                col = f['col']
                op = f['op']
                val = f['value']
                
                if op == '>=':
                    code_lines.append(f"df = df[df['{col}'] >= '{val}']")
                elif op == '<=':
                    code_lines.append(f"df = df[df['{col}'] <= '{val}']")
                elif op == '==':
                    code_lines.append(f"df = df[df['{col}'] == '{val}']")
                elif op == 'in':
                    code_lines.append(f"df = df[df['{col}'].isin({val})]")
            code_lines.append("")
        
        # Group-by and aggregation
        if plan.get('groupby') and plan.get('agg'):
            code_lines.append("# 分组聚合")
            groupby_cols = plan['groupby']
            agg_dict = {}
            for agg_spec in plan['agg']:
                col = agg_spec['col']
                op = agg_spec['op']
                agg_dict[col] = op
            
            code_lines.append(f"result = df.groupby({groupby_cols}).agg({agg_dict}).reset_index()")
            code_lines.append("")
        
            # Trend analysis
        elif plan.get('trend'):
            trend = plan['trend']
            date_col = trend['date_col']
            freq = trend['freq']
            value_cols = trend.get('value_cols', [])
            
            code_lines.append("# 趋势分析")
            code_lines.append(f"df['{date_col}'] = pd.to_datetime(df['{date_col}'], errors='coerce')")
            code_lines.append(f"df = df.dropna(subset=['{date_col}'])")
            
            if freq == 'M':
                code_lines.append(f"df['period'] = df['{date_col}'].dt.strftime('%Y-%m')")
            elif freq == 'Y':
                code_lines.append(f"df['period'] = df['{date_col}'].dt.year.astype(str)")
            elif freq == 'D':
                code_lines.append(f"df['period'] = df['{date_col}'].dt.strftime('%Y-%m-%d')")
            else:
                code_lines.append(f"df['period'] = df['{date_col}'].astype(str)")
            
            if plan.get('groupby'):
                groupby_cols = ['period'] + plan['groupby']
            else:
                groupby_cols = ['period']
            
            # Try to find a value column if not specified
            if not value_cols:
                # Look for sales/revenue/amount columns
                for col in columns:
                    if '销售额' in col or '总销售额' in col:
                        value_cols = [col]
                        break
                    elif '销量' in col or '销售数量' in col:
                        value_cols = [col]
                        break
            
            if value_cols:
                agg_dict = {col: 'sum' for col in value_cols}
                code_lines.append(f"result = df.groupby({groupby_cols}).agg({agg_dict}).reset_index()")
            else:
                # Fallback if no value columns found
                code_lines.append(f"result = df.groupby({groupby_cols}).size().reset_index(name='count')")
            
            code_lines.append("")
        
        # Text analysis
        elif plan.get('text_ops'):
            text_ops = plan['text_ops']
            text_col = text_ops['text_col']
            topk = text_ops.get('topk', 20)
            
            code_lines.append("# 文本关键词提取")
            code_lines.append(f"keywords = extract_zh_keywords(df['{text_col}'], topk={topk})")
            code_lines.append("result = pd.DataFrame(keywords, columns=['关键词', '频次'])")
            code_lines.append("")
        
        # Simple aggregation without group-by
        elif plan.get('agg') and not plan.get('groupby'):
            code_lines.append("# 聚合统计")
            for agg_spec in plan['agg']:
                col = agg_spec['col']
                op = agg_spec['op']
                code_lines.append(f"result_{op} = df['{col}'].{op}()")
                code_lines.append(f"print(f'{col} {op}: {{result_{op}}}')")
            code_lines.append("result = df")  # Keep original data
            code_lines.append("")
        
        else:
            code_lines.append("result = df")
            code_lines.append("")
        
        # Sort
        if plan.get('sort'):
            code_lines.append("# 排序")
            for sort_spec in plan['sort']:
                col = sort_spec['col']
                order = sort_spec['order']
                ascending = (order == 'asc')
                code_lines.append(f"result = result.sort_values('{col}', ascending={ascending})")
            code_lines.append("")
        
        # Limit
        if plan.get('limit'):
            code_lines.append(f"# 取前{plan['limit']}条")
            code_lines.append(f"result = result.head({plan['limit']})")
            code_lines.append("")
        
        # Visualization
        viz_type = plan.get('viz', 'table')
        if viz_type == 'line' and plan.get('trend'):
            code_lines.append("# 生成折线图")
            code_lines.append("fig = go.Figure()")
            
            if plan.get('groupby') and len(plan['groupby']) > 0:
                group_col = plan['groupby'][0]
                value_cols = plan['trend'].get('value_cols', [])
                if value_cols:
                    value_col = value_cols[0]
                    code_lines.append(f"for group_name in result['{group_col}'].unique():")
                    code_lines.append(f"    group_data = result[result['{group_col}'] == group_name]")
                    code_lines.append(f"    fig.add_trace(go.Scatter(")
                    code_lines.append(f"        x=group_data['period'],")
                    code_lines.append(f"        y=group_data['{value_col}'],")
                    code_lines.append(f"        mode='lines+markers',")
                    code_lines.append(f"        name=str(group_name)")
                    code_lines.append(f"    ))")
            else:
                value_cols = plan['trend'].get('value_cols', [])
                if value_cols:
                    value_col = value_cols[0]
                    code_lines.append(f"fig.add_trace(go.Scatter(")
                    code_lines.append(f"    x=result['period'],")
                    code_lines.append(f"    y=result['{value_col}'],")
                    code_lines.append(f"    mode='lines+markers'")
                    code_lines.append(f"))")
            
            code_lines.append("fig.update_layout(title='趋势分析', xaxis_title='时间', yaxis_title='数值')")
            code_lines.append("print('PLOTLY_JSON:', fig.to_json())")
            code_lines.append("")
        
        elif viz_type == 'bar':
            code_lines.append("# 生成柱状图")
            if plan.get('groupby') and plan.get('agg'):
                x_col = plan['groupby'][0]
                y_col = plan['agg'][0]['col']
                code_lines.append(f"fig = px.bar(result, x='{x_col}', y='{y_col}', title='柱状图')")
                code_lines.append("print('PLOTLY_JSON:', fig.to_json())")
                code_lines.append("")
        
        # Print result table
        code_lines.append("# 输出结果")
        code_lines.append("print('\\n=== 分析结果 ===')")
        code_lines.append("print(result.head(20).to_string(index=False))")
        code_lines.append("print(f'\\n总行数: {len(result)}')")
        
        code = '\n'.join(code_lines)
        return code
    
    def generate_with_llm(self, plan: Dict[str, Any], question: str,
                         columns: List[str], types: Dict[str, str],
                         data_sample: str = "", row_count: int = 0,
                         excel_path: str = "",
                         other_sheets: List[Dict] = None,
                         original_file: str = "") -> Tuple[str, str]:
        """
        Generate code using LLM (V2 - Simplified)
        
        Args:
            plan: Executable plan
            question: Original question
            columns: Available columns
            types: Column types
            data_sample: Sample data rows (head + tail)
            row_count: Total row count
            excel_path: Path to clean Excel file
            other_sheets: Other sheets from same file
            original_file: Original file name
            
        Returns:
            Tuple of (code, prompt)
        """
        logger.info("Generating code with LLM (V2 - Simplified)")
        
        # Handle defaults
        if other_sheets is None:
            other_sheets = []
        
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.openai_api_key, base_url=self.openai_base_url)
            
            # Format column info (name + dtype)
            column_info_lines = []
            for col in columns:
                dtype = types.get(col, 'object')
                column_info_lines.append(f"  {col}: {dtype}")
            column_info = '\n'.join(column_info_lines)
            
            # Split data sample into head and tail
            if "【前5行数据】" in data_sample:
                parts = data_sample.split("【前5行数据】")[1].split("【后5行数据】")
                head_sample = parts[0].strip() if len(parts) > 0 else data_sample
                tail_sample = parts[1].strip() if len(parts) > 1 else ""
            else:
                head_sample = data_sample
                tail_sample = ""
            
            # Build other sheets info
            other_sheets_info = ""
            if other_sheets and len(other_sheets) > 0:
                other_sheets_info = f"\n【同一文件的其他工作表】（原始文件：{original_file}，共{len(other_sheets)+1}个工作表）\n\n"
                other_sheets_info += "如果分析需要，可以加载并合并这些工作表的数据：\n\n"
                
                for i, sheet_info in enumerate(other_sheets, 1):
                    sheet_name_other = sheet_info['sheet_name']
                    sheet_path = sheet_info['excel_path']
                    sheet_shape = sheet_info['shape']
                    sheet_cols = sheet_info['columns']
                    sheet_head = sheet_info.get('head_sample', '')[:300]  # Limit length
                    
                    other_sheets_info += f"工作表 {i}: {sheet_name_other}\n"
                    other_sheets_info += f"  - 路径: {sheet_path}\n"
                    other_sheets_info += f"  - 大小: {sheet_shape[0]}行 × {sheet_shape[1]}列\n"
                    other_sheets_info += f"  - 列名: {', '.join(sheet_cols[:10])}\n"
                    if sheet_head:
                        other_sheets_info += f"  - 数据预览: {sheet_head}...\n"
                    other_sheets_info += f"  - 加载方式: df_{sheet_name_other} = pd.read_excel('{sheet_path}')\n\n"
            
            # Build prompt with simplified format
            prompt = CODE_GENERATION_TEMPLATE.format(
                question=question,
                excel_path=excel_path,
                original_file=original_file,
                sheet_name=plan.get('sheet_name', ''),
                row_count=row_count,
                column_count=len(columns),
                column_info=column_info,
                head_sample=head_sample,
                tail_sample=tail_sample,
                other_sheets_info=other_sheets_info
            )
            
            # Build system message (may include multi-sheet guidance)
            system_message = """你是Python数据分析专家。

请根据用户问题和提供的数据生成分析代码。

关键规则：
- df变量已包含当前工作表的数据
- 使用实际的列名（从数据表头中查找）
- 根据数据样本理解每列的含义，选择正确的列进行分析
- 日期类型用.strftime()转字符串
- 如需图表，生成Plotly并打印JSON"""
            
            # Add multi-sheet guidance if applicable
            if other_sheets and len(other_sheets) > 0:
                system_message += f"""

【多工作表分析】：
原始文件有{len(other_sheets)+1}个工作表。
- 如果问题需要跨时间段或跨类别对比，考虑加载并合并其他工作表
- 例如："各月销售趋势" → 如果每个sheet是一个月，应该合并所有sheets
- 使用pd.read_excel('路径')加载其他sheet，然后pd.concat()合并"""
            
            response = client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # Zero temperature for maximum consistency
                max_tokens=3000,  # Increased token limit for more detailed code
                top_p=0.1,  # Lower top_p for more focused responses
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            code = response.choices[0].message.content
            
            # Extract code from markdown if wrapped
            if '```python' in code:
                code = code.split('```python')[1].split('```')[0].strip()
            elif '```' in code:
                code = code.split('```')[1].split('```')[0].strip()
            
            # Return both code and prompt
            logger.info(f"Generated prompt length: {len(prompt)}")
            return code, prompt
            
        except Exception as e:
            logger.error(f"LLM code generation failed: {e}")
            # No fallback - let the error propagate
            raise e
    
    def generate(self, plan: Dict[str, Any], question: str,
                columns: List[str], types: Dict[str, str],
                data_sample: str = "", row_count: int = 0,
                excel_path: str = "",
                other_sheets: List[Dict] = None,
                original_file: str = "",
                use_llm: bool = True) -> Tuple[str, List[str], str]:
        """
        Generate Python code from plan
        
        Args:
            plan: Executable plan
            question: Original question
            columns: Available columns
            types: Column types
            data_sample: Sample data rows
            row_count: Total row count
            excel_path: Path to clean Excel file
            other_sheets: Other sheets from same file
            original_file: Original file name
            use_llm: Whether to use LLM (default: True for personalized code)
            
        Returns:
            Tuple of (code, expected_columns_used, prompt_used)
        """
        prompt_used = ""
        
        if use_llm and self.openai_api_key:
            # Skip plan generation, let AI generate code directly
            code, prompt_used = self.generate_with_llm_direct(
                question, columns, types, data_sample, row_count, 
                excel_path, other_sheets, original_file
            )
        else:
            # No fallback - require LLM
            raise ValueError("LLM code generation is required but not available")
        
        # Extract expected columns used
        expected_cols = set()
        
        if plan.get('filters'):
            expected_cols.update([f['col'] for f in plan['filters']])
        
        if plan.get('groupby'):
            expected_cols.update(plan['groupby'])
        
        if plan.get('agg'):
            expected_cols.update([a['col'] for a in plan['agg']])
        
        if plan.get('trend'):
            expected_cols.add(plan['trend']['date_col'])
            expected_cols.update(plan['trend'].get('value_cols', []))
        
        if plan.get('sort'):
            expected_cols.update([s['col'] for s in plan['sort']])
        
        if plan.get('text_ops'):
            expected_cols.add(plan['text_ops']['text_col'])
        
        logger.info(f"Generated code ({len(code)} chars), expected columns: {expected_cols}")
        
        return code, list(expected_cols), prompt_used
    
    def generate_price_ranking_code(self, columns: List[str], types: Dict[str, str]) -> str:
        """
        Generate hardcoded code for price ranking analysis
        """
        # Find price column and product column
        price_col = None
        product_col = None
        
        for col in columns:
            if "清仓价" in col:
                price_col = col
            elif "商品名称" in col or "产品名称" in col:
                product_col = col
        
        if not price_col or not product_col:
            # Fallback to generic code
            return """import pandas as pd
import plotly.express as px

# 选择相关列
result = df[['商品名称', '清仓价']].copy()

# 清理数据
result = result.dropna(subset=['清仓价'])

# 按清仓价排序
result = result.sort_values('清仓价', ascending=True)

# 重置索引
result = result.reset_index(drop=True)

# 生成图表
fig = px.bar(result, x='商品名称', y='清仓价', title='产品清仓价格排名')
print('PLOTLY_JSON:', fig.to_json())

# 输出结果
print('\\n=== 分析结果 ===')
print(result.to_string(index=False))
print(f'\\n总行数: {len(result)}')"""

        return f"""import pandas as pd
import plotly.express as px

# 选择清仓价和商品名称列
result = df[['{product_col}', '{price_col}']].copy()

# 清理数据，去除空值
result = result.dropna(subset=['{price_col}'])

# 按清仓价排序（升序：价格从低到高）
result = result.sort_values('{price_col}', ascending=True)

# 重置索引
result = result.reset_index(drop=True)

# 生成图表
fig = px.bar(result, x='{product_col}', y='{price_col}', title='产品清仓价格排名')
print('PLOTLY_JSON:', fig.to_json())

# 输出结果
print('\\n=== 分析结果 ===')
print(result.to_string(index=False))
print(f'\\n总行数: {len(result)}')"""
    
    def generate_with_llm_direct(self, question: str, columns: List[str], types: Dict[str, str],
                                data_sample: str = "", row_count: int = 0,
                                excel_path: str = "",
                                other_sheets: List[Dict] = None,
                                original_file: str = "") -> Tuple[str, str]:
        """
        Generate code directly using LLM without plan generation
        """
        logger.info("Generating code directly with LLM (no plan)")
        
        # Handle defaults
        if other_sheets is None:
            other_sheets = []
        
        try:
            from openai import OpenAI
            
            client = OpenAI(
                api_key=self.openai_api_key,
                base_url=self.openai_base_url
            )
            
            # Build column info
            column_info = "列名 | 类型 | 示例值\n"
            column_info += "--- | --- | ---\n"
            for col in columns[:10]:  # Limit to first 10 columns
                col_type = types.get(col, 'unknown')
                column_info += f"{col} | {col_type} | 见数据样本\n"
            
            # Build data samples
            head_sample = data_sample.split('\n---\n')[0] if '\n---\n' in data_sample else data_sample[:500]
            tail_sample = data_sample.split('\n---\n')[1] if '\n---\n' in data_sample else ""
            
            # Build other sheets info
            other_sheets_info = ""
            if other_sheets and len(other_sheets) > 0:
                other_sheets_info = f"\n【同一文件的其他工作表】（原始文件：{original_file}，共{len(other_sheets)+1}个工作表）\n\n"
                other_sheets_info += "如果分析需要，可以加载并合并这些工作表的数据：\n\n"
                
                for i, sheet_info in enumerate(other_sheets, 1):
                    sheet_name_other = sheet_info['sheet_name']
                    sheet_path = sheet_info['excel_path']
                    sheet_shape = sheet_info['shape']
                    sheet_cols = sheet_info['columns']
                    sheet_head = sheet_info.get('head_sample', '')[:300]
                    
                    other_sheets_info += f"工作表 {i}: {sheet_name_other}\n"
                    other_sheets_info += f"  - 路径: {sheet_path}\n"
                    other_sheets_info += f"  - 大小: {sheet_shape[0]}行 × {sheet_shape[1]}列\n"
                    other_sheets_info += f"  - 列名: {', '.join(sheet_cols[:10])}\n"
                    if sheet_head:
                        other_sheets_info += f"  - 数据预览: {sheet_head}...\n"
                    other_sheets_info += f"  - 加载方式: df_{sheet_name_other} = pd.read_excel('{sheet_path}')\n\n"
            
            # Build prompt with simplified format
            prompt = CODE_GENERATION_TEMPLATE.format(
                question=question,
                excel_path=excel_path,
                original_file=original_file,
                sheet_name="当前工作表",
                row_count=row_count,
                column_count=len(columns),
                column_info=column_info,
                head_sample=head_sample,
                tail_sample=tail_sample,
                other_sheets_info=other_sheets_info
            )
            
            # Print the full prompt for debugging
            logger.info("=" * 80)
            logger.info("FULL PROMPT SENT TO AI:")
            logger.info("=" * 80)
            logger.info(prompt)
            logger.info("=" * 80)
            
            # Build system message
            system_message = f"""你是Python数据分析专家。

请根据用户问题和提供的数据生成分析代码。

⚠️ 关键规则：
- df变量已包含当前工作表的数据，不要写pd.read_excel()
- 使用实际的列名（从数据表头中查找）
- 根据数据样本理解每列的含义，选择正确的列进行分析
- 日期类型用.strftime()转字符串
- 如需图表，生成Plotly并打印JSON

🎯 特别重要：
- 对于"清仓价格排名"问题，必须：
  1. 选择"清仓价"列和"商品名称"列
  2. 使用sort_values('清仓价', ascending=True)排序
  3. 生成图表和数据表格
  4. 不要只写result = df.head(10)

- 对于"销售趋势"问题，必须：
  1. 选择日期列和销售额列
  2. 使用groupby()和sum()聚合
  3. 不要使用.size()，要用具体的数值列

- 对于排名问题，必须使用sort_values()排序
- 对于价格排名，选择价格列和产品名称列，按价格排序

当前问题：{question}
请生成完整的、可直接执行的Python代码！"""
            
            response = client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=3000,
                top_p=0.1,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            code = response.choices[0].message.content
            
            # Extract code from markdown if wrapped
            if '```python' in code:
                code = code.split('```python')[1].split('```')[0].strip()
            elif '```' in code:
                code = code.split('```')[1].split('```')[0].strip()
            
            # Ensure required imports are present
            required_imports = [
                "import pandas as pd",
                "import numpy as np", 
                "import plotly.graph_objects as go",
                "import plotly.express as px",
                "import json",
                "import re",
                "from collections import Counter"
            ]
            
            # Check if imports are missing and add them
            code_lines = code.split('\n')
            import_lines = [line for line in code_lines if line.strip().startswith('import') or line.strip().startswith('from')]
            
            if not import_lines:
                # No imports found, add them at the beginning
                code = '\n'.join(required_imports) + '\n\n' + code
                logger.info("Added missing imports to generated code")
            else:
                # Check for missing imports and add them
                missing_imports = []
                for imp in required_imports:
                    if not any(imp in line for line in import_lines):
                        missing_imports.append(imp)
                
                if missing_imports:
                    # Add missing imports after existing imports
                    import_end_idx = 0
                    for i, line in enumerate(code_lines):
                        if line.strip().startswith('import') or line.strip().startswith('from'):
                            import_end_idx = i
                    
                    # Insert missing imports
                    for imp in missing_imports:
                        code_lines.insert(import_end_idx + 1, imp)
                    
                    code = '\n'.join(code_lines)
                    logger.info(f"Added missing imports: {missing_imports}")
            
            # Print the generated code for debugging
            logger.info("=" * 80)
            logger.info("AI GENERATED CODE:")
            logger.info("=" * 80)
            logger.info(code)
            logger.info("=" * 80)
            
            # Validate the code syntax
            try:
                compile(code, '<string>', 'exec')
                logger.info("Code syntax validation passed")
            except SyntaxError as e:
                logger.error(f"Generated code has syntax error: {e}")
                logger.error(f"Error at line {e.lineno}: {e.text}")
                raise e
            
            logger.info(f"Generated code directly ({len(code)} chars)")
            return code, prompt
            
        except Exception as e:
            logger.error(f"Direct LLM code generation failed: {e}")
            # No fallback - let the error propagate
            raise e

