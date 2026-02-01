"""
Vector store provider abstraction.
Supports Weaviate as the primary vector database.
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum

from app.config import settings
from app.db.weaviate import get_weaviate_client, is_weaviate_available

logger = logging.getLogger(__name__)


class VectorStoreProviderType(str, Enum):
    """Supported vector store provider types."""
    WEAVIATE = "weaviate"
    CHROMA = "chroma"
    FAISS = "faiss"


class SearchResult:
    """Standardized search result."""

    def __init__(
        self,
        id: str,
        content: Dict[str, Any],
        score: Optional[float] = None,
        vector: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.content = content
        self.score = score
        self.vector = vector
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "score": self.score,
            "metadata": self.metadata,
        }


class VectorStoreProvider(ABC):
    """
    Abstract base class for vector store providers.
    Provides a unified interface for different vector databases.
    """

    provider_name: str = "base"

    @abstractmethod
    async def add_documents(
        self,
        collection: str,
        documents: List[Dict[str, Any]],
        embeddings: Optional[List[List[float]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """Add documents to the vector store."""
        pass

    @abstractmethod
    async def search(
        self,
        collection: str,
        query_vector: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search for similar documents by vector."""
        pass

    @abstractmethod
    async def search_by_text(
        self,
        collection: str,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search for similar documents by text (if vectorizer is configured)."""
        pass

    @abstractmethod
    async def get(
        self,
        collection: str,
        ids: List[str],
    ) -> List[Dict[str, Any]]:
        """Get documents by ID."""
        pass

    @abstractmethod
    async def delete(
        self,
        collection: str,
        ids: List[str],
    ) -> bool:
        """Delete documents from the vector store."""
        pass

    @abstractmethod
    async def create_collection(
        self,
        name: str,
        properties: Optional[List[Dict[str, Any]]] = None,
        vectorizer: Optional[str] = None,
    ) -> bool:
        """Create a new collection."""
        pass

    @abstractmethod
    async def delete_collection(self, name: str) -> bool:
        """Delete a collection."""
        pass

    @abstractmethod
    async def list_collections(self) -> List[str]:
        """List all collections."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the vector store is healthy."""
        pass


class WeaviateVectorStore(VectorStoreProvider):
    """
    Weaviate vector store provider.

    Uses the existing Weaviate connection from app.db.weaviate.
    """

    provider_name = "weaviate"

    def __init__(self):
        """Initialize the Weaviate vector store."""
        pass

    def _get_client(self):
        """Get the Weaviate client."""
        if not is_weaviate_available():
            raise RuntimeError("Weaviate is not available")
        return get_weaviate_client()

    async def add_documents(
        self,
        collection: str,
        documents: List[Dict[str, Any]],
        embeddings: Optional[List[List[float]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Add documents to a Weaviate collection.

        Args:
            collection: The collection name
            documents: List of document dictionaries
            embeddings: Optional pre-computed embeddings
            ids: Optional document IDs

        Returns:
            List of document IDs
        """
        client = self._get_client()

        if not client.collections.exists(collection):
            raise ValueError(f"Collection '{collection}' does not exist")

        coll = client.collections.get(collection)
        result_ids = []

        with coll.batch.dynamic() as batch:
            for i, doc in enumerate(documents):
                vector = embeddings[i] if embeddings and i < len(embeddings) else None
                doc_id = ids[i] if ids and i < len(ids) else None

                try:
                    if vector:
                        uuid = batch.add_object(properties=doc, vector=vector, uuid=doc_id)
                    else:
                        uuid = batch.add_object(properties=doc, uuid=doc_id)
                    result_ids.append(str(uuid) if uuid else f"doc_{i}")
                except Exception as e:
                    logger.warning(f"Failed to add document: {e}")
                    result_ids.append(None)

        return [id for id in result_ids if id is not None]

    async def search(
        self,
        collection: str,
        query_vector: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        Search for similar documents by vector.

        Args:
            collection: The collection name
            query_vector: The query embedding vector
            limit: Maximum number of results
            filters: Optional filters

        Returns:
            List of search results
        """
        client = self._get_client()

        if not client.collections.exists(collection):
            raise ValueError(f"Collection '{collection}' does not exist")

        coll = client.collections.get(collection)

        try:
            # Build filter if provided
            weaviate_filter = None
            if filters:
                from weaviate.classes.query import Filter
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, str):
                        conditions.append(Filter.by_property(key).equal(value))
                    elif isinstance(value, (int, float)):
                        conditions.append(Filter.by_property(key).equal(value))
                    elif isinstance(value, bool):
                        conditions.append(Filter.by_property(key).equal(value))
                if conditions:
                    weaviate_filter = conditions[0]
                    for cond in conditions[1:]:
                        weaviate_filter = weaviate_filter & cond

            # Perform vector search
            response = coll.query.near_vector(
                near_vector=query_vector,
                limit=limit,
                filters=weaviate_filter,
                return_metadata=["certainty", "distance"],
            )

            results = []
            for obj in response.objects:
                results.append(SearchResult(
                    id=str(obj.uuid),
                    content=obj.properties,
                    score=getattr(obj.metadata, 'certainty', None),
                    metadata={
                        "distance": getattr(obj.metadata, 'distance', None),
                    },
                ))

            return results
        except Exception as e:
            logger.error(f"Weaviate search error: {e}")
            raise RuntimeError(f"Weaviate search failed: {e}")

    async def search_by_text(
        self,
        collection: str,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        Search for similar documents by text.

        Requires a text vectorizer to be configured on the collection.

        Args:
            collection: The collection name
            query: The text query
            limit: Maximum number of results
            filters: Optional filters

        Returns:
            List of search results
        """
        client = self._get_client()

        if not client.collections.exists(collection):
            raise ValueError(f"Collection '{collection}' does not exist")

        coll = client.collections.get(collection)

        try:
            weaviate_filter = None
            if filters:
                from weaviate.classes.query import Filter
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, str):
                        conditions.append(Filter.by_property(key).equal(value))
                if conditions:
                    weaviate_filter = conditions[0]
                    for cond in conditions[1:]:
                        weaviate_filter = weaviate_filter & cond

            response = coll.query.near_text(
                query=query,
                limit=limit,
                filters=weaviate_filter,
                return_metadata=["certainty", "distance"],
            )

            results = []
            for obj in response.objects:
                results.append(SearchResult(
                    id=str(obj.uuid),
                    content=obj.properties,
                    score=getattr(obj.metadata, 'certainty', None),
                    metadata={
                        "distance": getattr(obj.metadata, 'distance', None),
                    },
                ))

            return results
        except Exception as e:
            logger.error(f"Weaviate text search error: {e}")
            raise RuntimeError(f"Weaviate text search failed: {e}")

    async def get(
        self,
        collection: str,
        ids: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Get documents by ID.

        Args:
            collection: The collection name
            ids: List of document IDs

        Returns:
            List of documents
        """
        client = self._get_client()

        if not client.collections.exists(collection):
            raise ValueError(f"Collection '{collection}' does not exist")

        coll = client.collections.get(collection)
        results = []

        for doc_id in ids:
            try:
                obj = coll.query.fetch_object_by_id(doc_id)
                if obj:
                    results.append({
                        "id": str(obj.uuid),
                        **obj.properties,
                    })
            except Exception as e:
                logger.warning(f"Failed to fetch document {doc_id}: {e}")

        return results

    async def delete(
        self,
        collection: str,
        ids: List[str],
    ) -> bool:
        """
        Delete documents by ID.

        Args:
            collection: The collection name
            ids: List of document IDs to delete

        Returns:
            True if successful
        """
        client = self._get_client()

        if not client.collections.exists(collection):
            raise ValueError(f"Collection '{collection}' does not exist")

        coll = client.collections.get(collection)

        try:
            for doc_id in ids:
                coll.data.delete_by_id(doc_id)
            return True
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            return False

    async def create_collection(
        self,
        name: str,
        properties: Optional[List[Dict[str, Any]]] = None,
        vectorizer: Optional[str] = None,
    ) -> bool:
        """
        Create a new collection.

        Args:
            name: The collection name
            properties: List of property definitions
            vectorizer: Optional vectorizer configuration

        Returns:
            True if successful
        """
        client = self._get_client()

        if client.collections.exists(name):
            logger.warning(f"Collection '{name}' already exists")
            return True

        try:
            from weaviate.classes.config import Property, DataType, Configure

            # Build properties
            weaviate_properties = []
            if properties:
                type_map = {
                    "text": DataType.TEXT,
                    "string": DataType.TEXT,
                    "int": DataType.INT,
                    "integer": DataType.INT,
                    "number": DataType.NUMBER,
                    "float": DataType.NUMBER,
                    "boolean": DataType.BOOL,
                    "bool": DataType.BOOL,
                    "date": DataType.DATE,
                }

                for prop in properties:
                    prop_name = prop.get("name")
                    prop_type = prop.get("dataType", ["text"])[0] if isinstance(prop.get("dataType"), list) else prop.get("dataType", "text")
                    data_type = type_map.get(prop_type.lower(), DataType.TEXT)

                    weaviate_properties.append(Property(
                        name=prop_name,
                        data_type=data_type,
                        description=prop.get("description"),
                    ))

            # Configure vectorizer
            vectorizer_config = Configure.Vectorizer.none()
            if vectorizer:
                if vectorizer == "text2vec-openai":
                    vectorizer_config = Configure.Vectorizer.text2vec_openai()
                elif vectorizer == "text2vec-cohere":
                    vectorizer_config = Configure.Vectorizer.text2vec_cohere()

            client.collections.create(
                name=name,
                vectorizer_config=vectorizer_config,
                properties=weaviate_properties if weaviate_properties else None,
            )

            logger.info(f"Created collection: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            return False

    async def delete_collection(self, name: str) -> bool:
        """
        Delete a collection.

        Args:
            name: The collection name

        Returns:
            True if successful
        """
        client = self._get_client()

        try:
            if client.collections.exists(name):
                client.collections.delete(name)
                logger.info(f"Deleted collection: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            return False

    async def list_collections(self) -> List[str]:
        """List all collections."""
        client = self._get_client()

        try:
            collections = client.collections.list_all()
            return list(collections.keys())
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []

    async def health_check(self) -> bool:
        """Check if Weaviate is healthy."""
        try:
            client = self._get_client()
            return client.is_ready()
        except Exception:
            return False


# Provider registry
_vectorstore_providers: Dict[VectorStoreProviderType, VectorStoreProvider] = {}


def get_vectorstore_provider(
    provider_type: VectorStoreProviderType = VectorStoreProviderType.WEAVIATE,
    **kwargs,
) -> VectorStoreProvider:
    """
    Factory function to get a vector store provider instance.

    Uses singleton pattern to reuse provider instances.
    """
    if provider_type not in _vectorstore_providers:
        provider_classes = {
            VectorStoreProviderType.WEAVIATE: WeaviateVectorStore,
        }

        provider_class = provider_classes.get(provider_type)
        if not provider_class:
            raise ValueError(f"Unsupported vector store provider: {provider_type}")

        _vectorstore_providers[provider_type] = provider_class(**kwargs)

    return _vectorstore_providers[provider_type]


# Convenience function
async def get_default_vectorstore() -> VectorStoreProvider:
    """Get the default vector store provider (Weaviate)."""
    return get_vectorstore_provider(VectorStoreProviderType.WEAVIATE)
