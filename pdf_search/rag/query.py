import json

from openai import OpenAI


# =============================================================================
# Query Enhancement Functions
# =============================================================================

def rag_fusion(query):
    """Generate multiple query variations using RAG fusion technique."""
    
    prompt = f"""请根据用户的查询，将其重新改写为 2 个不同的查询。这些改写后的查询应当尽可能覆盖原始查询中的不同方面或角度，以便更全面地获取相关信息。请确保每个改写后的查询仍然与原始查询相关，并且在内容上有所不同。

用JSON的格式输出：
{{
    "rag_fusion":["query1","query2"]
}}

原始查询：{query}
"""
    # Call OpenAI ChatGPT 4o nano to generate query variations
    
    client = OpenAI()
    
    try:
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": "你是一个智能AI助手，专注于改写用户查询，并以 JSON 格式输出"},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = response.choices[0].message.content
        parsed_result = json.loads(result)
        return parsed_result.get("rag_fusion", [])
        
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return []


def coreference_resolution(query, chat_history):
    """Resolve pronouns and references in queries using chat history context."""
    
    prompt = f"""目标：根据提供的用户与知识库助手的历史记录，做指代消解，将用户最新问题中出现的代词或指代内容替换为历史记录中的明确对象，生成一条完整的独立问题。

说明：
- 将用户问题中的指代词替换为历史记录中的具体内容，生成一条独立问题。

以JSON的格式输出
{{"query":["替换指代后的完整问题"]}}

以下是一些案例

----------
历史记录：
["user": Milvus是什么?
"assistant": Milvus 是一个向量数据库]
用户问题：怎么使用它？

输出JSON：{{"query":["怎么使用Milvus?"]}}
----------
历史记录：
["user": PyTorch是什么?
"assistant": PyTorch是一个开源的机器学习库，用于Python。它提供了一个灵活且高效的框架，用于构建和训练深度神经网络。
"user": TensorFlow是什么?
"assistant": TensorFlow是一个开源的机器学习框架。它提供了一套全面的工具、库和资源，用于构建和部署机器学习模型。]
用户问题: 它们的区别是什么？

输出JSON：{{"query":["PyTorch和TensorFlow的区别是什么？"]}}
----------
历史记录：
["user": 四川有哪些城市
"assistant": 1. 成都。 2. 绵阳。 3. 资阳。]
用户问题: 介绍一下第二个

输出JSON：{{"query":["介绍一下绵阳"]}}
----------
历史记录：
{chat_history}
用户问题：{query}

输出JSON：
""" 
    # Call OpenAI ChatGPT 4o nano to generate query variations
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": "你是一个智能AI助手，专注于做指代消解，并以 JSON 格式输出"},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    result = response.choices[0].message.content
    parsed_result = json.loads(result)
    return parsed_result.get("query")


def query_decompositon(query, max_queries=5):
    """Decompose complex queries into simpler sub-queries for better retrieval."""
    
    prompt = f""" 
目标：分析用户的问题，判断其是否需要拆分为子问题以提高信息检索的准确性。如果需要拆分，提供拆分后的子问题列表；如果不需要，直接返回原问题。最多拆分出{max_queries}个子问题。

说明：
- 用户的问题可能含糊不清或包含多个概念，导致难以直接回答。
- 为提高知识库查询的质量和相关性，需评估问题是否应分解为更具体的子问题。
- 根据问题的复杂性和广泛性，判断是否需要拆分：
  - 如果问题涉及多个方面（如比较多个实体、包含多个独立步骤），需要拆分为子问题。
  - 如果问题已集中且明确，无需拆分。
- 最多拆分为{max_queries}个子问题，避免过度拆分。
- 输出结果必须为 JSON 格式。请直接输出JSON，不需要做任何解释。

输出格式：
{{
  "query": ["子问题1", "子问题2"...] 
}}  

案例 1
---
用户问题: "林冲、关羽、孙悟空的性格有什么不同？"
推理过程: 该问题涉及多个实体的比较，需要分别了解每个实体的性格。
输出:
{{
  "query": ["林冲的性格是什么？", "关羽的性格是什么？", "孙悟空的性格是什么？"]
}}

案例 2
---
用户问题: "哪些OpenAI的前在职员工成立了自己的公司？"
推理过程: 解答需要先识别前员工，再判断谁创立公司，涉及多个步骤。
输出:
{{
  "query": ["OpenAI的前在职员工有哪些？", "谁成立了自己的公司？"]
}}

案例 3
---
用户问题: "Find environmentally friendly electric cars with over 300 miles of range under $40,000."
推理过程: 问题包含多个条件要求，需要拆分为具体的子问题以提高检索准确性。
输出:
{{
  "query": ["Which cars are environmentally friendly electric vehicles?", "Which electric vehicles have a range of over 300 miles?", "What electric vehicles are priced under $40,000?"]
}}

案例 4
---
用户问题: "如何设计一个智能家居系统并实时监控设备状态？"
推理过程: 问题包含两个独立方面（设计系统和监控状态），需要拆分。
输出:
{{
  "query": ["如何设计一个智能家居系统？", "如何实时监控智能家居系统的设备状态？"]
}}

案例 5
---
用户问题: "Covid对经济的影响是什么？"
推理过程: 问题集中且明确，无需拆分。
输出:
{{
  "query": []
}}

案例 6
---
用户问题: "LangChain和LangGraph的区别是什么？"
推理过程: 该问题涉及比较，可拆分为各自定义再加比较，以提高检索准确性。
输出:
{{
  "query": ["LangChain是什么？", "LangGraph是什么？", "LangChain和LangGraph的区别是什么？"]
}}

用户问题:
"{query}"
"""
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": "你是一个智能AI助手，专注于做查询拆分，并以 JSON 格式输出"},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
    )
    result = response.choices[0].message.content
    parsed_result = json.loads(result)
    return parsed_result.get("query")


def enhance_query(query, chat_history=None, max_queries=5):
    """
    Combine multiple query enhancement techniques to generate a comprehensive list of queries.
    
    Args:
        query (str): The original user query
        chat_history (str, optional): Chat history for coreference resolution
        max_queries (int, optional): Maximum number of queries to generate from query decomposition (default: 5)
    
    Returns:
        list: List of enhanced queries
    """
    enhanced_queries = []
    
    # Step 1: Coreference resolution (if chat history is provided)
    if chat_history:
        resolved_query = coreference_resolution(query, chat_history)
        if resolved_query and len(resolved_query) > 0:
            query = resolved_query[0]  # Use the first resolved query
    
    # Step 2: Query decomposition
    decomposed_queries = query_decompositon(query, max_queries)
    
    # If decomposition returns empty list, use original query
    if not decomposed_queries:
        decomposed_queries = [query]
    
    # Step 3: RAG fusion for each decomposed query
    for q in decomposed_queries:
        fusion_queries = rag_fusion(q)
        if fusion_queries:
            enhanced_queries.extend(fusion_queries)
        else:
            enhanced_queries.append(q)  # Fallback to original if fusion fails
    
    # Remove duplicates while preserving order
    seen = set()
    unique_queries = []
    for q in enhanced_queries:
        if q not in seen:
            seen.add(q)
            unique_queries.append(q)
    
    return unique_queries


