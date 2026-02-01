"""
Greeter Vectorstore configuration.

This file is a placeholder for agents that need vector storage.
The greeter agent doesn't need a vectorstore, but this demonstrates
the pattern for agents that do.
"""
from typing import Any, Optional

from app.common.providers.vectorstore import (
    VectorStoreProvider,
    VectorStoreProviderType,
    get_vectorstore_provider,
)


def get_greeter_vectorstore() -> Optional[VectorStoreProvider]:
    """
    Get the vectorstore provider for the greeter agent.

    The greeter agent doesn't need a vectorstore, so this returns None.
    For agents that need vector storage (e.g., RAG-based agents),
    this would return a configured vectorstore provider.

    Returns:
        None (greeter doesn't need vectorstore)
    """
    # Example of how to configure a vectorstore:
    # return get_vectorstore_provider(
    #     VectorStoreProviderType.WEAVIATE,
    #     collection="greeter_knowledge",
    # )
    return None
