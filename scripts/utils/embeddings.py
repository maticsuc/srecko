"""
Ollama embedding generation utilities.
"""

import os
import time
from typing import List, Optional
import requests
from dotenv import load_dotenv

load_dotenv()


class OllamaError(Exception):
    """Custom exception for Ollama errors."""
    pass


class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Ollama API base URL (default: http://localhost:11434)
            model: Embedding model name (default: nomic-embed-text)
            timeout: Request timeout in seconds (default: 300 for larger models, from env OLLAMA_EMBEDDING_TIMEOUT)
        """
        self.base_url = base_url or os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = model or os.getenv('OLLAMA_EMBEDDING_MODEL', 'nomic-embed-text')
        self.timeout = timeout or int(os.getenv('OLLAMA_EMBEDDING_TIMEOUT', '300'))
        self.embeddings_endpoint = f"{self.base_url}/api/embeddings"
        
    def is_available(self) -> bool:
        """
        Check if Ollama is running and accessible.
        
        Returns:
            True if Ollama is available, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def list_models(self) -> List[str]:
        """
        List available models in Ollama.
        
        Returns:
            List of model names
            
        Raises:
            OllamaError: If request fails
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
            
        except requests.exceptions.RequestException as e:
            raise OllamaError(f"Failed to list models: {e}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
            
        Raises:
            OllamaError: If embedding generation fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            response = requests.post(
                self.embeddings_endpoint,
                json={
                    "model": self.model,
                    "prompt": text
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            embedding = data.get('embedding')
            
            if not embedding:
                raise OllamaError("No embedding returned from Ollama")
            
            return embedding
            
        except requests.exceptions.RequestException as e:
            raise OllamaError(f"Failed to generate embedding: {e}")
    
    def generate_embeddings_batch(
        self,
        texts: List[str],
        show_progress: bool = True,
        delay: float = 0.1
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts with progress tracking.
        
        Args:
            texts: List of texts to embed
            show_progress: Show progress output
            delay: Delay between requests in seconds (to avoid overwhelming Ollama)
            
        Returns:
            List of embedding vectors
            
        Raises:
            OllamaError: If batch generation fails
        """
        embeddings = []
        total = len(texts)
        
        for i, text in enumerate(texts, 1):
            try:
                embedding = self.generate_embedding(text)
                embeddings.append(embedding)
                
                if show_progress and i % 10 == 0:
                    print(f"  Generated {i}/{total} embeddings...")
                
                # Small delay to avoid overwhelming Ollama
                if delay > 0 and i < total:
                    time.sleep(delay)
                    
            except OllamaError as e:
                print(f"  Warning: Failed to generate embedding for text {i}: {e}")
                # Append None or zero vector for failed embeddings
                embeddings.append(None)
        
        if show_progress:
            print(f"  Completed {len([e for e in embeddings if e is not None])}/{total} embeddings")
        
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings from this model.
        
        Returns:
            Embedding dimension (e.g., 768 for nomic-embed-text)
            
        Raises:
            OllamaError: If unable to determine dimension
        """
        try:
            # Generate a test embedding to determine dimension
            test_embedding = self.generate_embedding("test")
            return len(test_embedding)
        except OllamaError as e:
            raise OllamaError(f"Failed to determine embedding dimension: {e}")


def test_ollama() -> bool:
    """
    Test Ollama connection and embedding generation.
    
    Returns:
        True if test successful, False otherwise
    """
    print("Testing Ollama connection...")
    
    try:
        client = OllamaClient()
        
        # Check if Ollama is running
        if not client.is_available():
            print("✗ Ollama is not running")
            print("  Start Ollama with: ollama serve")
            return False
        
        print("✓ Ollama is running")
        
        # List available models
        print("\nAvailable models:")
        models = client.list_models()
        for model in models:
            marker = "→" if model.startswith(client.model.split(':')[0]) else " "
            print(f"  {marker} {model}")
        
        # Check if embedding model is available
        model_available = any(
            model.startswith(client.model.split(':')[0]) 
            for model in models
        )
        
        if not model_available:
            print(f"\n✗ Model '{client.model}' not found")
            print(f"  Pull it with: ollama pull {client.model}")
            return False
        
        print(f"\n✓ Model '{client.model}' is available")
        
        # Test embedding generation
        print("\nTesting embedding generation...")
        test_text = "Srečko Kosovel je bil slovenski pesnik."
        embedding = client.generate_embedding(test_text)
        
        print(f"✓ Generated embedding")
        print(f"  Dimension: {len(embedding)}")
        print(f"  Sample values: {embedding[:5]}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


if __name__ == "__main__":
    """Test Ollama connection and embedding generation."""
    import sys
    
    success = test_ollama()
    
    if not success:
        print("\nPlease ensure:")
        print("1. Ollama is installed: https://ollama.ai")
        print("2. Ollama is running: ollama serve")
        print("3. Model is pulled: ollama pull nomic-embed-text")
        sys.exit(1)
    else:
        print("\n✓ All tests passed!")
