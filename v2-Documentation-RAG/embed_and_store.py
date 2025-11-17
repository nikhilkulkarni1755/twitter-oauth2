"""Create embeddings and store in FAISS - using local gensim embeddings"""
import json
import numpy as np
from typing import List, Dict
import pickle
from gensim.models import KeyedVectors
import gensim.downloader as api

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("FAISS not installed. Install with: pip install faiss-cpu")

# Use lightweight Word2Vec embeddings (no torch required)
MODEL = None
EMBEDDING_DIM = 300

def load_embedding_model():
    """Load gensim Word2Vec model"""
    global MODEL
    if MODEL is None:
        print("Loading Word2Vec embedding model (this may take a moment on first run)...")
        try:
            # Download and load pre-trained Word2Vec model
            MODEL = api.load("word2vec-google-news-300")
            print(f"Loaded Word2Vec model with {len(MODEL)} words, {EMBEDDING_DIM} dimensions")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise
    return MODEL

def text_to_embedding(text: str, model) -> np.ndarray:
    """Convert text to embedding by averaging word vectors"""
    words = text.lower().split()
    embeddings = []

    for word in words:
        try:
            if word in model:
                embeddings.append(model[word])
        except KeyError:
            pass

    if embeddings:
        return np.mean(embeddings, axis=0).astype('float32')
    else:
        # Return zero vector if no words found
        return np.zeros(EMBEDDING_DIM, dtype='float32')

def create_embeddings(chunks: List[Dict[str, str]]) -> np.ndarray:
    """Create embeddings for all chunks"""
    model = load_embedding_model()
    texts = [chunk['content'] for chunk in chunks]
    print(f"\nCreating embeddings for {len(texts)} chunks...")

    embeddings = []
    for i, text in enumerate(texts):
        if (i + 1) % 10 == 0:
            print(f"  Embedded {i+1}/{len(texts)}...")
        embedding = text_to_embedding(text, model)
        embeddings.append(embedding)

    print(f"Created {len(embeddings)} embeddings")
    return np.array(embeddings).astype('float32')

def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatL2:
    """Build FAISS index"""
    if not FAISS_AVAILABLE:
        raise ImportError("FAISS not installed")

    print(f"\nBuilding FAISS index with {len(embeddings)} vectors of {embeddings.shape[1]} dimensions...")
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    print(f"✓ FAISS index built")
    return index

def save_index_and_metadata(
    index: faiss.IndexFlatL2,
    chunks: List[Dict[str, str]],
    index_path: str = "faiss_index.bin",
    metadata_path: str = "metadata.pkl"
):
    """Save FAISS index and metadata"""
    faiss.write_index(index, index_path)
    print(f"✓ Saved FAISS index to {index_path}")

    with open(metadata_path, 'wb') as f:
        pickle.dump(chunks, f)
    print(f"✓ Saved metadata to {metadata_path}")

def embed_and_store(chunks_file: str = "chunks.json"):
    """Main function to embed and store"""
    # Load chunks
    print(f"Loading chunks from {chunks_file}...")
    with open(chunks_file, 'r') as f:
        chunks = json.load(f)
    print(f"✓ Loaded {len(chunks)} chunks")

    # Create embeddings
    embeddings = create_embeddings(chunks)

    # Build and save FAISS index
    index = build_faiss_index(embeddings)
    save_index_and_metadata(index, chunks)

    print(f"\n{'='*60}")
    print(f"✓ RAG storage ready!")
    print(f"{'='*60}")
    print(f"  - Index: faiss_index.bin")
    print(f"  - Metadata: metadata.pkl")
    print(f"  - Total chunks: {len(chunks)}")
    print(f"  - Embedding dimension: {embeddings.shape[1]}")

if __name__ == "__main__":
    embed_and_store()
