# PDF Search RAG System

A comprehensive Retrieval-Augmented Generation (RAG) system for querying PDF documents stored in Elasticsearch with intelligent query enhancement and web search fallback.

## 🚀 Features

- **PDF Ingestion**: Extract text, images, and tables from PDFs
- **Elasticsearch Integration**: Vector and keyword hybrid search
- **Query Enhancement**: Coreference resolution, query decomposition, and RAG fusion
- **Intelligent Reranking**: External reranking service for better results
- **Web Search Fallback**: Automatic web search when database retrieval fails
- **Interactive Interfaces**: Command-line tools for ingestion and querying

## 📁 Code Structure

```
pdf_search/
├── config.py                 # Configuration and environment variables
├── constants.py              # Static constants (stop words, etc.)
├── utils.py                  # Utility functions (token counting, text splitting)
├── start_es_db.py           # Interactive PDF ingestion script
├── query_es_db.py           # Interactive query interface
├── elastic_search/          # Elasticsearch client
│   ├── __init__.py
│   └── es_client.py
├── rag/                     # RAG pipeline components
│   ├── __init__.py
│   ├── ingest.py           # PDF processing and indexing
│   ├── retrieve.py         # Document retrieval and reranking
│   ├── query.py            # Query enhancement functions
│   └── web_search.py       # Web search functionality
├── extract/                 # PDF extraction modules
│   ├── __init__.py
│   ├── extract_image.py    # Image extraction and summarization
│   └── extract_table.py    # Table extraction and context augmentation
└── embedding/               # Embedding service
    ├── __init__.py
    └── embedding_service.py
```

## 🛠️ Setup

1. **Start Elasticsearch service**:
   ```bash
   # Install and start Elasticsearch locally (Elasticsearch only)
   curl -fsSL https://elastic.co/start-local | sh -s -- --esonly
   ```
   Follow the [official guide](https://github.com/elastic/start-local) for detailed instructions.

2. **Install dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   # Create .env file with your API keys and URLs
   ES_URL=http://localhost:9200
   ES_LOCAL_API_KEY=your_elasticsearch_api_key
   OPENAI_API_KEY=your_openai_api_key
   BOCHAAI_API_KEY=your_bochaai_api_key
   IMAGE_MODEL_API_KEY=your_image_model_api_key
   ```

## 📖 Usage

### 1. Ingest PDFs
```bash
python start_es_db.py
```
- Select Elasticsearch index
- Choose PDF directory
- Enable/disable image and table extraction
- Automatic indexing with progress tracking

### 2. Query Documents
```bash
python query_es_db.py
```
- Enter Elasticsearch index name
- Ask questions about your documents
- Automatic query enhancement and web search fallback
- Chat history support for context-aware responses

### 3. Available Commands
- `help` - Show available commands
- `history` - Display chat history
- `clear` - Clear chat history
- `quit`/`exit` - End session

## 🔧 Key Functions

- **`ingest_pdf()`**: Process and index PDF documents
- **`enhance_query()`**: Improve queries with decomposition and fusion
- **`enhance_retrieve()`**: Hybrid search with reranking
- **`extract_images_from_pdf()`**: Extract and summarize images
- **`extract_tables_from_pdf()`**: Extract and augment tables
- **`ESClient`**: Elasticsearch operations (create, delete, search indices)

## 🌐 Web Search Integration

When database retrieval fails, the system automatically:
1. Detects "检索失败" (search failed) in GPT response
2. Triggers web search using `bocha_web_search()`
3. Processes results with `ask_llm()`
4. Provides clean, source-attributed responses
