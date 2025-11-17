"""Chunk documentation into logical sections"""
import json
from typing import List, Dict
import re

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    """
    Split text into chunks with overlap

    Args:
        text: Text to chunk
        chunk_size: Target characters per chunk
        overlap: Characters to overlap between chunks
    """
    chunks = []

    # Split by paragraphs first (separated by double newlines)
    paragraphs = text.split('\n\n')

    current_chunk = ""
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) < chunk_size:
            current_chunk += paragraph + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = paragraph + "\n\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def chunk_docs(docs: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Chunk all documents by article

    Returns list of chunks with metadata
    """
    all_chunks = []

    for doc in docs:
        url = doc['url']
        title = doc['title']
        content = doc['content']

        # Chunk the content
        chunks = chunk_text(content)

        for i, chunk in enumerate(chunks):
            all_chunks.append({
                'url': url,
                'title': title,
                'chunk_index': i,
                'content': chunk,
                'chunk_id': f"{title}_{i}"
            })

    return all_chunks

def save_chunks(chunks: List[Dict[str, str]], output_file: str = "chunks.json"):
    """Save chunks to JSON"""
    with open(output_file, 'w') as f:
        json.dump(chunks, f, indent=2)
    print(f"Saved {len(chunks)} chunks to {output_file}")
    return chunks

if __name__ == "__main__":
    with open("docs.json", 'r') as f:
        docs = json.load(f)

    chunks = chunk_docs(docs)
    save_chunks(chunks)
