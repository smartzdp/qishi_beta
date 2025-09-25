import re

import jieba
import requests

from config import RERANK_URL
from constants import STOP_WORDS
from elastic_search import ESClient
from embedding import embedding


# =============================================================================
# Core Search Functions
# =============================================================================

def get_keyword(query):
    """Extract keywords from query using jieba."""
    
    # 确保输入是字符串类型
    if not isinstance(query, str):
        print(f"[Get Keyword] Received non-string query: {query} (type: {type(query)}), converting to string")
        query = str(query) if query is not None else ""
    
    # 确保查询不为空
    if not query.strip():
        print("[Get Keyword] Empty query string, returning empty list")
        return []
    
    try:
        # 使用搜索引擎模式进行分词
        seg_list = jieba.cut_for_search(query)
        # Filter out stop words
        filtered_keywords = [word for word in seg_list if word not in STOP_WORDS]
        return filtered_keywords
    except Exception as e:
        print(f"[Get Keyword] Error processing query \"{query}\": {e}")
        return []


def hybrid_search_rrf(keyword_hits, vector_hits, k=60):
    """Combine keyword and vector search results using Reciprocal Rank Fusion."""
    
    # Initialize score dictionary
    scores = {}
    
    # Process keyword hits
    for hit in keyword_hits:
        doc_id = hit["id"]
        if doc_id not in scores:
            scores[doc_id] = {"score": 0, "text": hit["text"], "id": doc_id, 
                             "file_id": hit["file_id"], "image_id": hit["image_id"], 
                             "metadata": hit["metadata"]}
        scores[doc_id]["score"] += 1 / (k + hit["rank"])
    
    # Process vector hits
    for hit in vector_hits:
        doc_id = hit["id"]
        if doc_id not in scores:
            scores[doc_id] = {"score": 0, "text": hit["text"], "id": doc_id, 
                             "file_id": hit["file_id"], "image_id": hit["image_id"], 
                             "metadata": hit["metadata"]}
        scores[doc_id]["score"] += 1 / (k + hit["rank"])
    
    # Sort documents by their RRF score and assign ranks
    ranked_docs = sorted(scores.values(), key=lambda x: x["score"], reverse=True)

    # Removing the timestamps
    for _, doc in enumerate(ranked_docs):
        timestamp_pattern = re.compile(r"\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}\.\d{3}")
        doc["text"] = re.sub(timestamp_pattern, "", doc["text"])    
        
    # Format the final list of results
    final_results = [{"id": doc["id"], "text": doc["text"], "file_id": doc["file_id"], 
                     "image_id": doc["image_id"], "metadata": doc["metadata"], "rank": idx + 1} 
                    for idx, doc in enumerate(ranked_docs)]
    return final_results


def elastic_search(es, text, es_index):
    """Perform hybrid search (keyword + vector) on Elasticsearch."""
    
    key_words = get_keyword(text)

    keyword_query = {
        "bool": {
            "should": [
                {"match": {"text": {"query": keyword, "fuzziness": "AUTO"}}} for keyword in key_words
            ],
            "minimum_should_match": 1
        }
    }
    res_keyword = es.search(index=es_index, query=keyword_query)
    keyword_hits = [{"id": hit["_id"], "text": hit["_source"].get("text"), 
                     "file_id": hit["_source"].get("file_id"), "image_id": hit["_source"].get("image_id"), 
                     "metadata": hit["_source"].get("metadata"), "rank": idx + 1} 
                    for idx, hit in enumerate(res_keyword["hits"]["hits"])]

    embedding_vector = embedding([text])
    vector_query = {
        "bool": {
            "must": [{"match_all": {}}],
            "should": [
                {"script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.queryVector, \"vector\") + 1.0",
                        "params": {"queryVector": embedding_vector[0]}
                    }
                }}
            ]
        }
    }
    res_vector = es.search(index=es_index, query=vector_query)
    
    vector_hits = [{"id": hit["_id"], "text": hit["_source"].get("text"), 
                    "file_id": hit["_source"].get("file_id"), "image_id": hit["_source"].get("image_id"), 
                    "metadata": hit["_source"].get("metadata"), "rank": idx + 1} 
                   for idx, hit in enumerate(res_vector["hits"]["hits"])]
    
    combined_results = hybrid_search_rrf(keyword_hits, vector_hits)
    return combined_results


# =============================================================================
# Post-Processing Functions
# =============================================================================

def rerank(query, result_doc):
    """Rerank documents using external reranking service."""
    
    res = requests.post(RERANK_URL, json={"query": query, "documents": [doc["text"] for doc in result_doc]}).json()
    if res and "scores" in res and len(res["scores"]) == len(result_doc):
        for idx, doc in enumerate(result_doc):
            result_doc[idx]["score"] = res["scores"][idx]
        
        # Sort documents by rerank score in descending order (highest scores first)
        result_doc.sort(key=lambda x: x["score"], reverse=True)
            
    return result_doc


def enhance_retrieve(es, query, es_index, top_k=10):
    """
    Combine elastic search and reranking to return top-k results.
    
    Args:
        es: Elasticsearch client
        query (str): Search query
        es_index (str): Elasticsearch index name
        top_k (int): Number of top results to return (default: 10)
    
    Returns:
        list: Top-k reranked search results
    """
    # Perform elastic search
    search_results = elastic_search(es, query, es_index)
    
    # Rerank the results
    reranked_results = rerank(query, search_results)
    
    # Return only the top-k results
    return reranked_results[:top_k]


