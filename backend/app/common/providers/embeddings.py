"""
Embeddings provider abstraction.
Supports Ollama (primary), OpenAI, and other providers.
"""
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from enum import Enum

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingsProviderType(str, Enum):
    """Supported embeddings provider types."""
    OPENAI = "openai"
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"


class EmbeddingsProvider(ABC):
    """
    Abstract base class for embeddings providers.
    Provides a unified interface for different embeddings backends.
    """

    provider_name: str = "base"

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Generate embeddings for a single text."""
        pass

    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is healthy."""
        pass


class OllamaEmbeddings(EmbeddingsProvider):
    """
    Ollama embeddings provider for local models.

    Uses Ollama's embedding API to generate vector representations.
    Recommended models: nomic-embed-text, mxbai-embed-large, all-minilm
    """

    provider_name = "ollama"

    # Model dimensions (common embedding models)
    MODEL_DIMENSIONS = {
        "nomic-embed-text": 768,
        "mxbai-embed-large": 1024,
        "all-minilm": 384,
        "snowflake-arctic-embed": 1024,
        "bge-m3": 1024,
        "bge-large": 1024,
    }

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: str = "nomic-embed-text",
        timeout: float = 60.0,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._dimension: Optional[int] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embeddings for a single text.

        Args:
            text: The text to embed

        Returns:
            List of floats representing the embedding vector
        """
        client = await self._get_client()

        payload = {
            "model": self.model,
            "prompt": text,
        }

        try:
            response = await client.post("/api/embeddings", json=payload)
            response.raise_for_status()
            data = response.json()

            embedding = data.get("embedding", [])

            # Cache the dimension
            if embedding and self._dimension is None:
                self._dimension = len(embedding)

            return embedding
        except httpx.HTTPError as e:
            logger.error(f"Ollama embeddings error: {e}")
            raise RuntimeError(f"Ollama embeddings API error: {e}")

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        # Ollama doesn't have a batch endpoint, so we process sequentially
        # Could be parallelized with asyncio.gather if needed
        embeddings = []
        for text in texts:
            embedding = await self.embed_text(text)
            embeddings.append(embedding)
        return embeddings

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        if self._dimension is not None:
            return self._dimension

        # Return known dimension for common models
        base_model = self.model.split(":")[0]  # Handle model:tag format
        if base_model in self.MODEL_DIMENSIONS:
            return self.MODEL_DIMENSIONS[base_model]

        # Default dimension (will be updated after first embedding)
        return 768

    async def health_check(self) -> bool:
        """Check if Ollama embeddings are working."""
        try:
            # Try to generate a simple embedding
            embedding = await self.embed_text("test")
            return len(embedding) > 0
        except Exception:
            return False


class OpenAIEmbeddings(EmbeddingsProvider):
    """OpenAI embeddings provider (stub - implement when needed)."""

    provider_name = "openai"

    # OpenAI model dimensions
    MODEL_DIMENSIONS = {
        "text-embedding-ada-002": 1536,
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-ada-002",
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model
        self._dimension = self.MODEL_DIMENSIONS.get(model, 1536)

        if not self.api_key:
            logger.warning("OpenAI API key not configured for embeddings")

    async def embed_text(self, text: str) -> List[float]:
        raise NotImplementedError("OpenAI embeddings not implemented. Use Ollama instead.")

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError("OpenAI embeddings not implemented. Use Ollama instead.")

    @property
    def dimension(self) -> int:
        return self._dimension

    async def health_check(self) -> bool:
        return self.api_key is not None


# Provider registry
_embeddings_providers: Dict[EmbeddingsProviderType, EmbeddingsProvider] = {}


def get_embeddings_provider(
    provider_type: EmbeddingsProviderType = EmbeddingsProviderType.OLLAMA,
    **kwargs,
) -> EmbeddingsProvider:
    """
    Factory function to get an embeddings provider instance.

    Uses singleton pattern to reuse provider instances.
    """
    if provider_type not in _embeddings_providers:
        provider_classes = {
            EmbeddingsProviderType.OPENAI: OpenAIEmbeddings,
            EmbeddingsProviderType.OLLAMA: OllamaEmbeddings,
        }

        provider_class = provider_classes.get(provider_type)
        if not provider_class:
            raise ValueError(f"Unsupported embeddings provider: {provider_type}")

        _embeddings_providers[provider_type] = provider_class(**kwargs)

    return _embeddings_providers[provider_type]


# Convenience function for default provider
async def get_default_embeddings() -> EmbeddingsProvider:
    """Get the default embeddings provider (Ollama)."""
    return get_embeddings_provider(EmbeddingsProviderType.OLLAMA)
