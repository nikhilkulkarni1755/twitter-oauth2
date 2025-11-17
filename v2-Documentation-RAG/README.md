# Kubernetes Documentation RAG System

A local Retrieval-Augmented Generation (RAG) system for querying Kubernetes documentation using embeddings and FAISS vector search.

## Architecture

```
Kubernetes Docs URLs
        ↓
   Fetch HTML
        ↓
   Extract Text
        ↓
   Chunk by Article
        ↓
   Create Embeddings (Word2Vec)
        ↓
   FAISS Index
        ↓
   Query + Retrieve (Local)
        ↓
   Generate Answer (Claude API)
```

## Components

### 1. `fetch_docs.py`
- Fetches HTML from all Kubernetes documentation URLs
- Extracts clean text using BeautifulSoup
- Saves raw documents to `docs.json`

### 2. `chunk_docs.py`
- Chunks documents into logical sections (500 char chunks with overlap)
- Preserves metadata (URL, title, chunk index)
- Outputs to `chunks.json`

### 3. `embed_and_store.py`
- Loads pre-trained Word2Vec embeddings (300-dim vectors)
- Embeds all chunks using word-level averaging
- Builds FAISS index for efficient similarity search
- Saves index to `faiss_index.bin` and metadata to `metadata.pkl`

### 4. `rag_query.py`
- `RAGSystem` class for querying
- Retrieves top-k relevant chunks via FAISS
- Optionally synthesizes answers using Claude API
- Interactive query mode available

## Setup & Usage

### Installation

```bash
uv sync --python 3.13
```

### Build the Index

```bash
# Step 1: Fetch all docs
uv run fetch_docs.py

# Step 2: Chunk docs
uv run chunk_docs.py

# Step 3: Create embeddings and FAISS index
uv run embed_and_store.py
```

### Query the RAG System

**Interactive mode:**
```bash
uv run rag_query.py
```

**Programmatic usage:**
```python
from rag_query import RAGSystem

rag = RAGSystem()

# Query without LLM (just retrieval)
result = rag.query("What is Kubernetes?", use_llm=False)
print(result['answer'])

# Query with Claude API for synthesis (requires ANTHROPIC_API_KEY)
result = rag.query("How do I deploy an app?", use_llm=True)
print(result['answer'])
print("Sources:", result['sources'])
```

## Embeddings

Uses **Word2Vec (Google News 300D)** embeddings:
- 300-dimensional vectors
- Pre-trained on 3 billion words from Google News
- Lightweight (~1.6GB download, one-time)
- No GPU required
- Word-level averaging for documents

Other options:
- TF-IDF (lightweight, no downloads)
- sentence-transformers (requires PyTorch on some systems)
- OpenAI API embeddings (requires API key)

## Vector Database

**FAISS (Facebook AI Similarity Search)**:
- IndexFlatL2: L2 distance-based search
- Fast and efficient for similarity queries
- Scales to millions of vectors
- No external dependencies

## Files Generated

- `docs.json`: Raw fetched documents
- `chunks.json`: Chunked documents with metadata
- `faiss_index.bin`: FAISS vector index
- `metadata.pkl`: Chunk metadata (for retrieval)

## Dependencies

- `requests`: HTTP fetching
- `beautifulsoup4`: HTML parsing
- `gensim`: Word2Vec embeddings
- `faiss-cpu`: Vector indexing
- `numpy`: Numerical operations
- `anthropic`: Claude API (optional, for answer synthesis)

## Configuration

Edit `embed_and_store.py` to change:
- `EMBEDDING_DIM`: Vector dimensions
- `chunk_size`: Characters per chunk
- `overlap`: Overlap between chunks

Edit `rag_query.py` to change:
- `k`: Number of retrieved chunks (default: 5)
- `model`: Claude model for synthesis
- Embedding method
