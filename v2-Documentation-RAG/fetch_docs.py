"""Fetch and parse documentation from URLs"""
import requests
from bs4 import BeautifulSoup
import json
from typing import List, Dict
import time

def fetch_url(url: str) -> str:
    """Fetch content from a URL"""
    if not url or url.strip() == "":
        return ""

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def extract_text_from_html(html: str) -> str:
    """Extract clean text from HTML"""
    try:
        soup = BeautifulSoup(html, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""

def fetch_all_docs(doc_file: str) -> List[Dict[str, str]]:
    """Fetch all documentation from URLs in file"""
    docs = []

    with open(doc_file, 'r') as f:
        urls = [line.strip() for line in f.readlines() if line.strip() and line.strip().startswith('http')]

    print(f"Found {len(urls)} URLs to fetch")

    for i, url in enumerate(urls):
        print(f"Fetching {i+1}/{len(urls)}: {url}")
        html = fetch_url(url)

        if html:
            text = extract_text_from_html(html)
            if text:
                docs.append({
                    'url': url,
                    'content': text,
                    'title': url.split('/')[-1] or 'kubernetes-docs'
                })

        time.sleep(0.5)  # Be respectful with requests

    return docs

def save_docs(docs: List[Dict[str, str]], output_file: str = "docs.json"):
    """Save fetched docs to JSON"""
    with open(output_file, 'w') as f:
        json.dump(docs, f, indent=2)
    print(f"Saved {len(docs)} documents to {output_file}")

if __name__ == "__main__":
    doc_file = "Kubernetes-Documentation/documentation.txt"
    docs = fetch_all_docs(doc_file)
    save_docs(docs)
