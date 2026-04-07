"""
LangChain LLM support for Ollama, OpenRouter, and GitHub Models.

This module provides LLM interfaces for:
- Ollama (local models)
- OpenRouter (cloud models via API)
- GitHub Models (GitHub Copilot API access)
"""

from typing import Any, List, Optional, Union
from langchain_core.language_models.llms import LLM
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_openai import ChatOpenAI
import requests
import json
import os


class OllamaLLM(LLM):
    """
    Custom LangChain LLM wrapper for Ollama.
    
    This allows us to use our local Ollama instance with LangChain chains.
    
    Attributes:
        model: Name of the Ollama model to use (e.g., "llama3.2:3b")
        base_url: Ollama API endpoint (default: "http://localhost:11434")
        temperature: Sampling temperature (0.0 to 1.0)
        max_tokens: Maximum tokens to generate
        timeout: Request timeout in seconds (default: 600 for beefier models)
    """
    
    model: str = "llama3.2:3b"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 600
    
    @property
    def _llm_type(self) -> str:
        """Return identifier for this LLM type."""
        return "ollama"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        Call the Ollama API with the given prompt.
        
        Args:
            prompt: The prompt to send to the LLM
            stop: List of stop sequences
            run_manager: Callback manager for tracking runs
            **kwargs: Additional parameters
            
        Returns:
            Generated text response
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            }
        }
        
        if stop:
            payload["options"]["stop"] = stop
        
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error calling Ollama API: {e}")
    
    @property
    def _identifying_params(self) -> dict:
        """Return parameters that identify this LLM."""
        return {
            "model": self.model,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
        }


def create_github_copilot_llm(
    model: str = "Claude Sonnet 4.5",
    api_key: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> ChatOpenAI:
    """
    Factory function to create a GitHub Copilot LLM instance.
    
    GitHub Copilot provides access to:
    - Claude Sonnet 4.6 (newest, recommended)
    - Claude Sonnet 4.5 (excellent)
    - Claude Opus 4.6 (most capable)
    - GPT-5.4
    - Gemini 2.5 Pro
    - And more...
    
    IMPORTANT: Use model names with spaces as they appear in Copilot:
    - "Claude Sonnet 4.6" (not claude-sonnet-4.6)
    - "Claude Opus 4.6" (not claude-opus-4.6)
    - "GPT-5.4" (not gpt-5.4)
    
    To get your Copilot token:
    1. Run: python scripts/get_copilot_token.py
    2. Follow the instructions (GitHub CLI method is easiest)
    3. Set it as GITHUB_COPILOT_TOKEN in .env
    
    NOTE: This requires an active GitHub Copilot subscription
    (Individual, Business, or Enterprise)
    
    Args:
        model: Name of the Copilot model (use spaces, e.g., "Claude Sonnet 4.5")
        api_key: GitHub Copilot OAuth token (defaults to GITHUB_COPILOT_TOKEN env var)
        temperature: Sampling temperature (0.0 to 1.0)
        max_tokens: Maximum response length
        
    Returns:
        Configured ChatOpenAI instance pointing to GitHub Copilot
        
    Example:
        >>> llm = create_github_copilot_llm(
        ...     model="Claude Sonnet 4.5",
        ...     api_key="gho_..."
        ... )
        >>> response = llm.invoke("Tell me about Srečko Kosovel")
    """
    if api_key is None:
        # Try GITHUB_COPILOT_TOKEN first, then fall back to GITHUB_TOKEN
        api_key = os.getenv("GITHUB_COPILOT_TOKEN") or os.getenv("GITHUB_TOKEN")
        if not api_key:
            raise ValueError(
                "GitHub Copilot token not provided. Run 'python scripts/get_copilot_token.py' "
                "to get your token, then set GITHUB_COPILOT_TOKEN in your .env file."
            )
    
    # GitHub Copilot uses the Azure OpenAI endpoint
    return ChatOpenAI(
        model=model,
        openai_api_key=api_key,
        openai_api_base="https://api.githubcopilot.com",
        temperature=temperature,
        max_tokens=max_tokens,
        default_headers={
            "Copilot-Integration-Id": "srecko-kosovel-chat",
            "Editor-Version": "vscode/1.85.0",
            "Editor-Plugin-Version": "copilot-chat/0.11.0",
        }
    )


def create_github_models_llm(
    model: str = "gpt-4o",
    api_key: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> ChatOpenAI:
    """
    Factory function to create a GitHub Models LLM instance.
    
    GitHub Models provides access to:
    - gpt-4o
    - gpt-4o-mini
    - Meta-Llama-3.1-405B-Instruct
    - Meta-Llama-3.1-8B-Instruct
    
    IMPORTANT: GitHub Models does NOT have Claude!
    For Claude, use create_github_copilot_llm() or create_openrouter_llm()
    
    To get your token:
    1. Go to https://github.com/settings/tokens
    2. Create a new token (classic or fine-grained)
    3. Give it appropriate permissions
    4. Set it as GITHUB_TOKEN in .env
    
    Args:
        model: Name of the GitHub Models model
        api_key: GitHub token (defaults to GITHUB_TOKEN env var)
        temperature: Sampling temperature (0.0 to 1.0)
        max_tokens: Maximum response length
        
    Returns:
        Configured ChatOpenAI instance pointing to GitHub Models
        
    Example:
        >>> llm = create_github_models_llm(
        ...     model="gpt-4o",
        ...     api_key="ghp_..."
        ... )
        >>> response = llm.invoke("Tell me about Srečko Kosovel")
    """
    if api_key is None:
        api_key = os.getenv("GITHUB_TOKEN")
        if not api_key:
            raise ValueError(
                "GitHub token not provided. Set GITHUB_TOKEN "
                "environment variable or pass api_key parameter."
            )
    
    return ChatOpenAI(
        model=model,
        openai_api_key=api_key,
        openai_api_base="https://models.inference.ai.azure.com",
        temperature=temperature,
        max_tokens=max_tokens,
    )


def create_openrouter_llm(
    model: str = "anthropic/claude-3.5-sonnet",
    api_key: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> ChatOpenAI:
    """
    Factory function to create an OpenRouter LLM instance.
    
    OpenRouter provides access to many models:
    - anthropic/claude-3.5-sonnet (recommended)
    - openai/gpt-4o
    - google/gemini-pro-1.5
    - meta-llama/llama-3.1-70b-instruct
    - And many more...
    
    Args:
        model: Name of the OpenRouter model
        api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)
        temperature: Sampling temperature (0.0 to 1.0)
        max_tokens: Maximum response length
        
    Returns:
        Configured ChatOpenAI instance pointing to OpenRouter
        
    Example:
        >>> llm = create_openrouter_llm(
        ...     model="anthropic/claude-3.5-sonnet",
        ...     api_key="sk-or-..."
        ... )
        >>> response = llm.invoke("Tell me about Srečko Kosovel")
    """
    if api_key is None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenRouter API key not provided. Set OPENROUTER_API_KEY "
                "environment variable or pass api_key parameter."
            )
    
    return ChatOpenAI(
        model=model,
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=temperature,
        max_tokens=max_tokens,
        default_headers={
            "HTTP-Referer": "https://github.com/yourusername/srecko-kosovel",
            "X-Title": "Srecko Kosovel AI Chat"  # ASCII-safe version
        }
    )


def create_ollama_llm(
    model: str = "llama3.2:3b",
    base_url: str = "http://localhost:11434",
    temperature: float = 0.7,
    max_tokens: int = 2000,
    timeout: int = 600,
) -> OllamaLLM:
    """
    Factory function to create an Ollama LLM instance.
    
    Args:
        model: Name of the Ollama model
        base_url: Ollama API endpoint
        temperature: Sampling temperature (lower = more focused, higher = more creative)
        max_tokens: Maximum response length
        timeout: Request timeout in seconds (default: 600 for beefier models)
        
    Returns:
        Configured OllamaLLM instance
        
    Example:
        >>> llm = create_ollama_llm(model="qwen3.5:9b", temperature=0.8)
        >>> response = llm.invoke("Tell me about Srečko Kosovel")
    """
    return OllamaLLM(
        model=model,
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )


def create_anthropic_llm(
    model: str = "claude-sonnet-4-5",
    api_key: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> "ChatAnthropic":
    """
    Factory function to create a native Anthropic LLM instance.

    Requires an API key from console.anthropic.com (separate from claude.ai Pro).

    Args:
        model: Anthropic model ID (e.g. "claude-sonnet-4-5", "claude-opus-4-5")
        api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        temperature: Sampling temperature
        max_tokens: Maximum response length

    Returns:
        Configured ChatAnthropic instance
    """
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError:
        raise ImportError(
            "langchain-anthropic is not installed. Run: pip install langchain-anthropic"
        )

    if api_key is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "Anthropic API key not found. Set ANTHROPIC_API_KEY in .env.\n"
                "Get your key at: https://console.anthropic.com"
            )

    from langchain_anthropic import ChatAnthropic
    return ChatAnthropic(
        model=model,
        anthropic_api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def create_llm(
    provider: str = "ollama",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: str = "http://localhost:11434",
    temperature: float = 0.7,
    max_tokens: int = 2000,
    timeout: int = 600,
) -> BaseLanguageModel:
    """
    Factory function to create an LLM instance based on provider.
    
    Args:
        provider: LLM provider - "ollama", "openrouter", "github-copilot", or "github"
        model: Model name (defaults depend on provider)
        api_key: API key for OpenRouter/GitHub (if provider is "openrouter", "github-copilot", or "github")
        base_url: Ollama base URL (if provider is "ollama")
        temperature: Sampling temperature (0.0 to 1.0)
        max_tokens: Maximum response length
        timeout: Request timeout in seconds (default: 600 for beefier models)
        
    Returns:
        Configured LLM instance (OllamaLLM or ChatOpenAI)
        
    Raises:
        ValueError: If provider is not recognized
        
    Example:
        >>> # Use Ollama (local)
        >>> llm = create_llm(provider="ollama", model="llama3.2:3b")
        >>> 
        >>> # Use OpenRouter (cloud)
        >>> llm = create_llm(
        ...     provider="openrouter",
        ...     model="anthropic/claude-3.5-sonnet",
        ...     api_key="sk-or-..."
        ... )
        >>> 
        >>> # Use GitHub Copilot (has Claude!)
        >>> llm = create_llm(
        ...     provider="github-copilot",
        ...     model="Claude Sonnet 4.5",
        ...     api_key="ghp_..."
        ... )
        >>> 
        >>> # Use GitHub Models (no Claude)
        >>> llm = create_llm(
        ...     provider="github",
        ...     model="gpt-4o",
        ...     api_key="ghp_..."
        ... )
    """
    provider = provider.lower()
    
    if provider == "ollama":
        model = model or "llama3.2:3b"
        return create_ollama_llm(
            model=model,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
    
    elif provider == "openrouter":
        model = model or "anthropic/claude-3.5-sonnet"
        return create_openrouter_llm(
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    
    elif provider == "github-copilot":
        model = model or "Claude Sonnet 4.5"
        return create_github_copilot_llm(
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    
    elif provider == "github":
        model = model or "gpt-4o"
        return create_github_models_llm(
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    elif provider == "anthropic":
        model = model or "claude-sonnet-4-5"
        return create_anthropic_llm(
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. "
            f"Must be 'ollama', 'openrouter', 'github-copilot', 'github', or 'anthropic'."
        )


# Test the LLM
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    print("=" * 60)
    print("Testing LLM Integration")
    print("=" * 60)
    
    # Determine which provider to test
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    print(f"\nTesting provider: {provider}")
    
    # Create LLM instance
    print("\n1. Creating LLM instance...")
    
    if provider == "ollama":
        model = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2:3b")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        llm = create_llm(provider="ollama", model=model, base_url=base_url)
        print(f"   Model: {model}")
        print(f"   Base URL: {base_url}")
    elif provider == "github-copilot":
        model = os.getenv("GITHUB_COPILOT_MODEL", "Claude Sonnet 4.5")
        api_key = os.getenv("GITHUB_TOKEN")
        if not api_key:
            print("   ✗ Error: GITHUB_TOKEN not set in .env")
            exit(1)
        llm = create_llm(provider="github-copilot", model=model, api_key=api_key)
        print(f"   Model: {model}")
        print(f"   Provider: GitHub Copilot")
    elif provider == "github":
        model = os.getenv("GITHUB_MODEL", "gpt-4o")
        api_key = os.getenv("GITHUB_TOKEN")
        if not api_key:
            print("   ✗ Error: GITHUB_TOKEN not set in .env")
            exit(1)
        llm = create_llm(provider="github", model=model, api_key=api_key)
        print(f"   Model: {model}")
        print(f"   Provider: GitHub Models")
    else:
        model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("   ✗ Error: OPENROUTER_API_KEY not set in .env")
            exit(1)
        llm = create_llm(provider="openrouter", model=model, api_key=api_key)
        print(f"   Model: {model}")
        print(f"   Provider: OpenRouter")
    
    # Test simple invocation
    print("\n2. Testing simple prompt...")
    prompt = "Who was Srečko Kosovel? Answer in 2-3 sentences."
    print(f"   Prompt: {prompt}")
    print("\n   Response:")
    
    try:
        response = llm.invoke(prompt)
        if hasattr(response, 'content'):
            # ChatOpenAI returns an object with content
            print(f"   {response.content}")
        else:
            # OllamaLLM returns a string
            print(f"   {response}")
        print("\n   ✓ LLM invocation successful!")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("LLM testing complete!")
    print("=" * 60)
