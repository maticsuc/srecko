"""
Ollama embeddings wrapper for LangChain.

Embeddings are always generated locally via Ollama — they never go to a cloud API.
The chat LLM can be remote (OpenRouter, Anthropic), but embeddings stay local
because the model (mxbai-embed-large) is already downloaded and fast.
"""

import os
from typing import List, Optional
from langchain_core.embeddings import Embeddings

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.utils.embeddings import OllamaClient


class OllamaEmbeddings(Embeddings):
    """LangChain-compatible wrapper around the local Ollama embeddings API."""

    def __init__(self, model: Optional[str] = None):
        # Defaults to OLLAMA_EMBEDDING_MODEL env var, then mxbai-embed-large
        self.client = OllamaClient(model=model)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        dim = int(os.getenv("EMBEDDING_DIMENSION", "1024"))
        embeddings = []
        for text in texts:
            try:
                embeddings.append(self.client.generate_embedding(text))
            except Exception:
                embeddings.append([0.0] * dim)
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        return self.client.generate_embedding(text)
