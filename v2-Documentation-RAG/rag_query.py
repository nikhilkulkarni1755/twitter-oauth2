"""RAG query pipeline - retrieve relevant docs and answer questions"""
import json
import pickle
from typing import List, Dict
import numpy as np
import gensim.downloader as api
import os
import requests

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

try:
    from openai import OpenAI
    LMSTUDIO_AVAILABLE = True
except ImportError:
    LMSTUDIO_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# Load embedding model
EMBEDDING_DIM = 300
try:
    EMBEDDING_MODEL = api.load("word2vec-google-news-300")
    MODEL_AVAILABLE = True
except Exception as e:
    EMBEDDING_MODEL = None
    MODEL_AVAILABLE = False
    print(f"Warning: Could not load embedding model: {e}")

# LM Studio configuration
LMSTUDIO_BASE_URL = os.getenv("LMSTUDIO_BASE_URL", "http://192.168.1.98:1234/v1")
LMSTUDIO_MODEL = os.getenv("LMSTUDIO_MODEL", "qwen/qwen3-4b-2507")
LMSTUDIO_API_KEY = os.getenv("LMSTUDIO_API_KEY", "not-needed")


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
        return np.zeros(EMBEDDING_DIM, dtype='float32')


class RAGSystem:
    def __init__(
        self,
        index_path: str = "faiss_index.bin",
        metadata_path: str = "metadata.pkl"
    ):
        """Initialize RAG system with FAISS index and metadata"""
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS not installed")
        if not MODEL_AVAILABLE:
            raise ImportError("Embedding model not available")

        self.index = faiss.read_index(index_path)
        with open(metadata_path, 'rb') as f:
            self.chunks = pickle.load(f)

        print(f"RAG system loaded with {len(self.chunks)} chunks")

    def retrieve(self, query: str, k: int = 5) -> List[Dict]:
        """Retrieve top-k most relevant chunks for a query"""
        # Embed query using same method as chunks
        query_embedding = text_to_embedding(query, EMBEDDING_MODEL)
        query_embedding = np.expand_dims(query_embedding, axis=0)

        # Search FAISS index
        distances, indices = self.index.search(query_embedding, k)

        # Get relevant chunks
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            chunk = self.chunks[int(idx)]
            results.append({
                'distance': float(distance),
                'chunk_id': chunk['chunk_id'],
                'url': chunk['url'],
                'content': chunk['content'][:200] + "...",  # Preview
                'full_content': chunk['content']
            })

        return results

    def format_context(self, results: List[Dict], max_chars: int = 2000) -> str:
        """Format retrieved results for LLM context, with char limit"""
        context = "Based on the following documentation excerpts:\n\n"
        current_length = 0

        for i, result in enumerate(results, 1):
            content = result['full_content']
            # Limit individual content to avoid context overflow
            if len(content) > 500:
                content = content[:500] + "...[truncated]"

            entry = f"[Source {i}: {result['url']}]\n{content}\n\n"

            if current_length + len(entry) > max_chars:
                break

            context += entry
            current_length += len(entry)

        return context

    def query(self, question: str, k: int = 5, use_llm: bool = True, llm_backend: str = "lmstudio") -> Dict:
        """
        Answer a question using RAG

        Args:
            question: User question
            k: Number of chunks to retrieve
            use_llm: Use LLM to synthesize answer
            llm_backend: "lmstudio" or "claude"

        Returns:
            Dict with answer, sources, and retrieved chunks
        """
        # Retrieve relevant chunks
        results = self.retrieve(question, k=k)

        response = {
            'question': question,
            'sources': [r['url'] for r in results],
            'retrieved_chunks': results,
            'answer': None
        }

        if not use_llm:
            # Simple retrieval-based answer
            response['answer'] = "Retrieved the following relevant documentation:\n\n"
            for i, result in enumerate(results, 1):
                response['answer'] += f"{i}. {result['url']}\n   {result['content']}\n\n"
            return response

        # Use LLM to synthesize answer
        if llm_backend == "lmstudio":
            return self._query_lmstudio(question, results, response)
        elif llm_backend == "claude":
            return self._query_claude(question, results, response)
        else:
            response['answer'] = f"Unknown LLM backend: {llm_backend}"
            return response

    def _query_lmstudio(self, question: str, results: List[Dict], response: Dict) -> Dict:
        """Query using LM Studio (local Qwen)"""
        if not LMSTUDIO_AVAILABLE:
            response['answer'] = "OpenAI SDK not installed. Install with: pip install openai"
            return response

        try:
            client = OpenAI(base_url=LMSTUDIO_BASE_URL, api_key=LMSTUDIO_API_KEY)

            # Limit context for 4K context models
            context = self.format_context(results, max_chars=1500)
            prompt = f"""{context}
Question: {question}

Answer concisely:"""

            message = client.chat.completions.create(
                model=LMSTUDIO_MODEL,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=256,
            )

            response['answer'] = message.choices[0].message.content

        except Exception as e:
            response['answer'] = f"Error calling LM Studio: {e}"

        return response

    def _query_claude(self, question: str, results: List[Dict], response: Dict) -> Dict:
        """Query using Claude API"""
        if not ANTHROPIC_AVAILABLE:
            response['answer'] = "Anthropic SDK not installed. Install with: pip install anthropic"
            return response

        try:
            client = anthropic.Anthropic()

            context = self.format_context(results)
            prompt = f"""{context}

Question: {question}

Based on the documentation above, provide a clear and concise answer to the question.
If the information is not available in the documentation, say so."""

            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response['answer'] = message.content[0].text

        except Exception as e:
            response['answer'] = f"Error calling Claude API: {e}"

        return response

    def batch_query(self, questions: List[str], k: int = 5) -> List[Dict]:
        """Answer multiple questions"""
        return [self.query(q, k=k) for q in questions]


def interactive_mode():
    """Run interactive RAG query mode"""
    try:
        rag = RAGSystem()
    except (ImportError, FileNotFoundError) as e:
        print(f"Error loading RAG system: {e}")
        print("Make sure you've run fetch_docs.py, chunk_docs.py, and embed_and_store.py first")
        return

    print("\n=== Kubernetes RAG Query System ===")
    print("Ask questions about Kubernetes documentation")
    print("Using local Qwen via LM Studio for answer synthesis")
    print("Type 'exit' to quit, 'sources' to see all sources, 'mode' to toggle LLM\n")

    use_llm = True
    llm_backend = "lmstudio"

    while True:
        question = input("Question: ").strip()

        if question.lower() == 'exit':
            break

        if question.lower() == 'sources':
            print("\nAvailable sources:")
            urls_seen = set()
            for chunk in rag.chunks:
                if chunk['url'] not in urls_seen:
                    print(f"  - {chunk['url']}")
                    urls_seen.add(chunk['url'])
            continue

        if question.lower() == 'mode':
            use_llm = not use_llm
            print(f"\nLLM synthesis: {'ON' if use_llm else 'OFF'}")
            if use_llm:
                print(f"Using backend: {llm_backend}")
            continue

        if not question:
            continue

        print("\nRetrieving relevant documentation...")
        result = rag.query(question, k=5, use_llm=use_llm, llm_backend=llm_backend)

        print(f"\n--- Answer ---")
        print(result['answer'])

        print(f"\n--- Sources ---")
        for i, source in enumerate(result['sources'], 1):
            print(f"{i}. {source}")

        print()


if __name__ == "__main__":
    interactive_mode()
