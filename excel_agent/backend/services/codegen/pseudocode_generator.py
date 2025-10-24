"""
伪代码生成服务
将原始Python代码转换为简洁的伪代码，方便用户理解分析流程
"""

import openai
from typing import Optional
from backend.config import settings
from backend.utils.logging import setup_logger

logger = setup_logger(__name__)

class PseudocodeGenerator:
    """伪代码生成器"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
    
    def generate_pseudocode(self, python_code: str, question: str) -> Optional[str]:
        """
        将Python代码转换为伪代码
        
        Args:
            python_code: 原始Python代码
            question: 用户问题
            
        Returns:
            生成的伪代码，如果失败返回None
        """
        try:
            prompt = f"""
你是一个代码解释专家。请将以下Python数据分析代码转换为简洁易懂的伪代码，帮助用户理解分析流程。

用户问题：{question}

原始Python代码：
```python
{python_code}
```

请生成伪代码，要求：
1. 使用中文描述
2. 突出关键步骤和逻辑
3. 简洁明了，不超过10个步骤
4. 使用缩进表示层级关系
5. 不要包含具体的变量名，用通用描述
6. 重点说明数据处理和分析的核心流程

伪代码格式示例：
```
1. 导入必要的库
2. 加载数据
3. 数据清洗
   - 处理缺失值
   - 转换数据类型
4. 选择相关列
5. 数据排序/分组
6. 生成图表
7. 输出结果
```

请直接输出伪代码，不要包含其他内容：
"""

            response = self.client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": "你是一个专业的代码解释专家，擅长将复杂的Python代码转换为简洁易懂的伪代码。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            pseudocode = response.choices[0].message.content.strip()
            logger.info(f"Generated pseudocode ({len(pseudocode)} chars)")
            return pseudocode
            
        except Exception as e:
            logger.error(f"Failed to generate pseudocode: {e}")
            return None

# 全局实例
_pseudocode_generator = None

def get_pseudocode_generator() -> PseudocodeGenerator:
    """获取伪代码生成器实例"""
    global _pseudocode_generator
    if _pseudocode_generator is None:
        _pseudocode_generator = PseudocodeGenerator()
    return _pseudocode_generator
