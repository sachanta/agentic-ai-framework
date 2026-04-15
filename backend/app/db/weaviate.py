"""
Weaviate connection and utilities.
"""
import logging
import time
from typing import Optional, Any

from app.config import settings

logger = logging.getLogger(__name__)

# Weaviate client instance
_client: Optional[Any] = None


async def connect_weaviate() -> None:
    """
    Connect to Weaviate and verify the connection.

    Raises:
        RuntimeError: If connection fails
    """
    global _client

    logger.info(f"Connecting to Weaviate at {settings.WEAVIATE_URL}...")

    try:
        import weaviate
        from weaviate.classes.init import Auth

        # Configure authentication if API key is provided
        auth_config = None
        if settings.WEAVIATE_API_KEY:
            auth_config = Auth.api_key(settings.WEAVIATE_API_KEY)

        # Connect using v4 client
        _client = weaviate.connect_to_custom(
            http_host=settings.WEAVIATE_URL.replace("http://", "").replace("https://", "").split(":")[0],
            http_port=int(settings.WEAVIATE_URL.split(":")[-1]) if ":" in settings.WEAVIATE_URL.split("/")[-1] else 8080,
            http_secure=settings.WEAVIATE_URL.startswith("https"),
            grpc_host=settings.WEAVIATE_URL.replace("http://", "").replace("https://", "").split(":")[0],
            grpc_port=50051,
            grpc_secure=settings.WEAVIATE_URL.startswith("https"),
            auth_credentials=auth_config,
            skip_init_checks=False,
        )

        # Verify connection
        if _client.is_ready():
            meta = _client.get_meta()
            logger.info(f"Connected to Weaviate version {meta.get('version', 'unknown')}")
        else:
            raise RuntimeError("Weaviate is not ready")

    except ImportError:
        logger.warning("Weaviate client not installed. Running without Weaviate support.")
        _client = None
    except Exception as e:
        logger.error(f"Failed to connect to Weaviate: {e}")
        # Don't raise - allow running without Weaviate
        _client = None


async def close_weaviate() -> None:
    """Close Weaviate connection."""
    global _client

    if _client is not None:
        try:
            _client.close()
        except Exception as e:
            logger.warning(f"Error closing Weaviate connection: {e}")
        finally:
            _client = None
            logger.info("Weaviate connection closed")


def get_weaviate_client() -> Any:
    """
    Get Weaviate client instance.

    Returns:
        The Weaviate client instance

    Raises:
        RuntimeError: If client is not connected
    """
    if _client is None:
        raise RuntimeError("Weaviate not connected. Call connect_weaviate() first.")
    return _client


def is_weaviate_available() -> bool:
    """Check if Weaviate client is available."""
    return _client is not None


async def get_weaviate_status() -> dict:
    """
    Get Weaviate connection status with latency measurement.

    Returns:
        dict: Status information including health and latency
    """
    if _client is None:
        return {
            "status": "disconnected",
            "healthy": False,
            "latency_ms": None,
            "error": "Client not initialized",
        }

    try:
        start = time.time()
        is_ready = _client.is_ready()
        latency_ms = round((time.time() - start) * 1000, 2)

        if not is_ready:
            return {
                "status": "not_ready",
                "healthy": False,
                "latency_ms": latency_ms,
                "error": "Weaviate is not ready",
            }

        # Get additional info
        meta = _client.get_meta()

        return {
            "status": "connected",
            "healthy": True,
            "latency_ms": latency_ms,
            "version": meta.get("version"),
            "modules": list(meta.get("modules", {}).keys()),
        }
    except Exception as e:
        return {
            "status": "error",
            "healthy": False,
            "latency_ms": None,
            "error": str(e),
        }


async def ensure_collections() -> None:
    """
    Ensure required Weaviate collections exist with properly indexed properties.
    """
    if _client is None:
        return

    try:
        from weaviate.classes.config import Property, DataType, Configure

        # Documents collection
        if not _client.collections.exists("Documents"):
            logger.info("Creating Weaviate collection: Documents")
            _client.collections.create(
                name="Documents",
                description="General document storage for RAG",
                vectorizer_config=Configure.Vectorizer.none(),
                properties=[
                    Property(
                        name="title",
                        data_type=DataType.TEXT,
                        index_filterable=True,
                        index_searchable=True,
                    ),
                    Property(
                        name="content",
                        data_type=DataType.TEXT,
                        index_filterable=True,
                        index_searchable=True,
                    ),
                    Property(
                        name="source",
                        data_type=DataType.TEXT,
                        index_filterable=True,
                        index_searchable=True,
                    ),
                    Property(
                        name="metadata",
                        data_type=DataType.OBJECT,
                        index_filterable=False,
                        index_searchable=False,
                    ),
                ],
            )

        # AgentMemory collection
        if not _client.collections.exists("AgentMemory"):
            logger.info("Creating Weaviate collection: AgentMemory")
            _client.collections.create(
                name="AgentMemory",
                description="Agent conversation and context memory",
                vectorizer_config=Configure.Vectorizer.none(),
                properties=[
                    Property(
                        name="agent_id",
                        data_type=DataType.TEXT,
                        index_filterable=True,
                        index_searchable=True,
                    ),
                    Property(
                        name="content",
                        data_type=DataType.TEXT,
                        index_filterable=True,
                        index_searchable=True,
                    ),
                    Property(
                        name="memory_type",
                        data_type=DataType.TEXT,
                        index_filterable=True,
                        index_searchable=True,
                    ),
                    Property(
                        name="timestamp",
                        data_type=DataType.DATE,
                        index_filterable=True,
                        index_searchable=False,
                    ),
                ],
            )

        logger.info("Weaviate collections verified")

    except Exception as e:
        logger.warning(f"Error ensuring Weaviate collections: {e}")
