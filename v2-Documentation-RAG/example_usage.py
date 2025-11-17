#!/usr/bin/env python3
"""Example usage of the RAG system"""

from rag_query import RAGSystem

def main():
    print("Loading RAG system...")
    rag = RAGSystem()

    # Example questions
    questions = [
        "What is Kubernetes?",
        "How do I create a pod?",
        "What are the main components of Kubernetes?",
        "How do I set up kubectl?",
        "What is a Kubernetes cluster?",
    ]

    for question in questions:
        print(f"\n{'='*70}")
        print(f"Q: {question}")
        print(f"{'='*70}")

        # Query with LM Studio (Qwen) for synthesis
        print("\n[Retrieving documentation and generating answer with Qwen...]")
        result = rag.query(question, k=3, use_llm=True, llm_backend="lmstudio")

        print("\nAnswer:")
        print(result['answer'])

        print("\nSources:")
        for i, source in enumerate(result['sources'], 1):
            print(f"  {i}. {source}")

if __name__ == "__main__":
    main()
