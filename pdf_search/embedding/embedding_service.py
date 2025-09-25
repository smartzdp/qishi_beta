# =============================================================================
# Embedding Service
# =============================================================================

import requests

from config import EMBEDDING_URL


def embedding(texts: list) -> list:
    """Generate embeddings for input texts using the local embedding service."""
    headers = {"Content-Type": "application/json"}
    data = {"texts": texts}
    
    response = requests.post(EMBEDDING_URL, headers=headers, json=data)
    result = response.json()
    
    return result["data"]["text_vectors"]


