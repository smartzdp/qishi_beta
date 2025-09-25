import time
from elasticsearch import Elasticsearch

from config import ES_URL, ES_LOCAL_API_KEY


class ESClient:    
    def __init__(self):
        """Initialize Elasticsearch client with retry logic."""
        self.es = None
        while self.es is None:
            try:
                es = Elasticsearch(
                    [ES_URL],
                    api_key=ES_LOCAL_API_KEY,
                )
                self.es = es
            except:
                print("ElasticSearch conn failed, retry ...")
                time.sleep(3)

    def create_index(self, index, vector_dims=1024, metadata_fields=None):
        """Create an Elasticsearch index with vector search capabilities."""
        # Check if index already exists and delete it first
        if self.index_exists(index):
            print(f"[Create Vector DB] Index {index} already exists, deleting first...")
            self.delete_index(index)
        
        mappings = {
            "properties": {
                "text": {
                    "type": "text"
                }
            }
        }
        
        # Add vector field if vector_dims is set
        if vector_dims:
            mappings["properties"]["vector"] = {
                "type": "dense_vector",
                "dims": vector_dims,
                "index": True,
                "similarity": "cosine"
            }

        # Add metadata fields if metadata_fields is set
        if metadata_fields:
            for field_name, field_type in metadata_fields.items():
                mappings["properties"][field_name] = {"type": field_type}
        
        try:
            self.es.indices.create(index=index, mappings=mappings)
            print(f"[Create Vector DB] {index} created")
        except Exception as e:
            print(f"Create Vector DB Exception: {e}")

    def delete_index(self, index):
        """Delete an Elasticsearch index."""
        # Check if index exists before deletion
        if not self.index_exists(index):
            print(f"[Delete Vector DB] Index {index} does not exist, skipping deletion")
            return
        
        try:
            self.es.indices.delete(index=index)
            print(f"[Delete Vector DB] {index} deleted")
        except Exception as e:
            print(f"Delete Vector DB Exception: {e}")

    def index(self, index, body):
        """Index a single document."""
        self.es.index(index=index, body=body)

    def search(self, index, query):
        """Perform search on the index."""
        return self.es.search(index=index, query=query)

    def index_exists(self, index):
        """Check if an index exists."""
        return self.es.indices.exists(index=index)

