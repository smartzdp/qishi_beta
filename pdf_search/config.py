import os


# =============================================================================
# Elasticsearch Configuration
# =============================================================================
ES_URL = os.getenv("ES_URL")
ES_LOCAL_API_KEY = os.getenv("ES_LOCAL_API_KEY")


# =============================================================================
# AI Model Configuration
# =============================================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ARK_URL = os.getenv("ARK_URL")
ARK_API_KEY = os.getenv("ARK_API_KEY")


# =============================================================================
# External Service Configuration
# =============================================================================
BOCHAAI_URL = os.getenv("BOCHAAI_URL")
BOCHAAI_API_KEY = os.getenv("BOCHAAI_API_KEY")


# =============================================================================
# Processing Service URLs
# =============================================================================
EMBEDDING_URL = os.getenv("EMBEDDING_URL")
RERANK_URL = os.getenv("RERANK_URL")
IMAGE_MODEL_URL = os.getenv("IMAGE_MODEL_URL")
IMAGE_MODEL_API_KEY = os.getenv("IMAGE_MODEL_API_KEY")
