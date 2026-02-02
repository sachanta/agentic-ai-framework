"""
RAG (Retrieval-Augmented Generation) Service for Newsletter Platform.

Provides vector storage for newsletter personalization using Weaviate.
Supports similarity search, user-scoped filtering, and content recommendations.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.db.weaviate import get_weaviate_client, is_weaviate_available
from app.common.providers.embeddings import (
    get_embeddings_provider,
    EmbeddingsProviderType,
)

logger = logging.getLogger(__name__)


# Collection name for newsletter RAG
COLLECTION_NAME = "NewsletterRAG"


class NewsletterRAGService:
    """
    RAG service for newsletter personalization.

    Features:
    - Vector storage for newsletters
    - User-scoped similarity search
    - Content recommendations based on history
    - Preference pattern analysis
    - Engagement-based ranking
    """

    def __init__(
        self,
        embeddings_provider: Optional[EmbeddingsProviderType] = None,
        embeddings_model: Optional[str] = None,
    ):
        """
        Initialize the RAG service.

        Args:
            embeddings_provider: Provider type (default: OLLAMA)
            embeddings_model: Model to use (default: nomic-embed-text)
        """
        self._embeddings_provider = embeddings_provider or EmbeddingsProviderType.OLLAMA
        self._embeddings_model = embeddings_model or "nomic-embed-text"
        self._embeddings = None
        self._collection_initialized = False

    @property
    def embeddings(self):
        """Get or create embeddings provider."""
        if self._embeddings is None:
            self._embeddings = get_embeddings_provider(
                self._embeddings_provider,
                model=self._embeddings_model,
            )
        return self._embeddings

    def is_available(self) -> bool:
        """Check if Weaviate is available."""
        return is_weaviate_available()

    async def ensure_collection(self) -> bool:
        """
        Ensure the NewsletterRAG collection exists.

        Returns:
            True if collection exists or was created, False if Weaviate unavailable
        """
        if not self.is_available():
            logger.warning("Weaviate not available, cannot create collection")
            return False

        if self._collection_initialized:
            return True

        try:
            client = get_weaviate_client()

            # Check if collection exists
            if client.collections.exists(COLLECTION_NAME):
                logger.info(f"Collection {COLLECTION_NAME} already exists")
                self._collection_initialized = True
                return True

            # Import Weaviate v4 classes
            from weaviate.classes.config import Configure, Property, DataType

            # Create collection with schema
            client.collections.create(
                name=COLLECTION_NAME,
                description="Newsletter content for RAG and personalization",
                vectorizer_config=Configure.Vectorizer.none(),  # We provide vectors
                properties=[
                    Property(
                        name="content",
                        data_type=DataType.TEXT,
                        description="Newsletter content text",
                    ),
                    Property(
                        name="user_id",
                        data_type=DataType.TEXT,
                        description="User who owns this newsletter",
                    ),
                    Property(
                        name="newsletter_id",
                        data_type=DataType.TEXT,
                        description="Newsletter document ID",
                    ),
                    Property(
                        name="title",
                        data_type=DataType.TEXT,
                        description="Newsletter title",
                    ),
                    Property(
                        name="topics",
                        data_type=DataType.TEXT_ARRAY,
                        description="Topics covered in the newsletter",
                    ),
                    Property(
                        name="tone",
                        data_type=DataType.TEXT,
                        description="Newsletter tone",
                    ),
                    Property(
                        name="engagement_score",
                        data_type=DataType.NUMBER,
                        description="Engagement score (opens, clicks)",
                    ),
                    Property(
                        name="metadata_json",
                        data_type=DataType.TEXT,
                        description="Additional metadata as JSON",
                    ),
                    Property(
                        name="created_at",
                        data_type=DataType.DATE,
                        description="When the newsletter was created",
                    ),
                ],
            )

            logger.info(f"Created collection {COLLECTION_NAME}")
            self._collection_initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            return False

    def _get_collection(self):
        """Get the newsletter collection."""
        if not self.is_available():
            raise RuntimeError("Weaviate not available")

        client = get_weaviate_client()
        return client.collections.get(COLLECTION_NAME)

    async def store_newsletter(
        self,
        user_id: str,
        newsletter_id: str,
        content: str,
        title: str = "",
        topics: Optional[List[str]] = None,
        tone: str = "professional",
        engagement_score: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Store a newsletter in the vector database.

        Args:
            user_id: Owner of the newsletter
            newsletter_id: Newsletter document ID
            content: Full newsletter content
            title: Newsletter title
            topics: List of topics covered
            tone: Newsletter tone
            engagement_score: Engagement metric (0-1)
            metadata: Additional metadata

        Returns:
            UUID of the stored document, or None if failed
        """
        if not await self.ensure_collection():
            logger.warning("Cannot store newsletter: collection not available")
            return None

        try:
            # Generate embedding for the content
            embedding = await self.embeddings.embed_text(content)

            # Prepare document
            doc = {
                "content": content,
                "user_id": user_id,
                "newsletter_id": newsletter_id,
                "title": title,
                "topics": topics or [],
                "tone": tone,
                "engagement_score": engagement_score,
                "metadata_json": json.dumps(metadata or {}),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            # Store in Weaviate
            collection = self._get_collection()
            doc_uuid = str(uuid4())

            collection.data.insert(
                uuid=doc_uuid,
                properties=doc,
                vector=embedding,
            )

            logger.info(f"Stored newsletter {newsletter_id} for user {user_id}")
            return doc_uuid

        except Exception as e:
            logger.error(f"Failed to store newsletter: {e}")
            return None

    async def search_similar(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 10,
        min_score: float = 0.0,
        topics_filter: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar newsletters by query.

        Args:
            query: Search query text
            user_id: Filter by user (optional)
            limit: Maximum results
            min_score: Minimum similarity score (0-1)
            topics_filter: Filter by topics (any match)

        Returns:
            List of matching newsletters with scores
        """
        if not self.is_available():
            return []

        try:
            await self.ensure_collection()

            # Generate query embedding
            query_embedding = await self.embeddings.embed_text(query)

            # Build filters
            filters = self._build_filters(user_id=user_id, topics=topics_filter)

            # Execute search
            collection = self._get_collection()

            # Build query with optional filter
            if filters:
                results = collection.query.near_vector(
                    near_vector=query_embedding,
                    limit=limit,
                    filters=filters,
                    return_metadata=["distance", "certainty"],
                )
            else:
                results = collection.query.near_vector(
                    near_vector=query_embedding,
                    limit=limit,
                    return_metadata=["distance", "certainty"],
                )

            # Process results
            output = []
            for obj in results.objects:
                # Calculate score from distance/certainty
                score = 1.0 - (obj.metadata.distance or 0.0) if obj.metadata.distance else (obj.metadata.certainty or 0.0)

                if score < min_score:
                    continue

                output.append({
                    "uuid": str(obj.uuid),
                    "newsletter_id": obj.properties.get("newsletter_id"),
                    "user_id": obj.properties.get("user_id"),
                    "title": obj.properties.get("title"),
                    "content": obj.properties.get("content"),
                    "topics": obj.properties.get("topics", []),
                    "tone": obj.properties.get("tone"),
                    "engagement_score": obj.properties.get("engagement_score", 0.0),
                    "score": score,
                    "metadata": self._parse_metadata(obj.properties.get("metadata_json")),
                })

            return output

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def get_recommendations(
        self,
        user_id: str,
        based_on_newsletter_id: Optional[str] = None,
        limit: int = 5,
        exclude_seen: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get content recommendations for a user.

        Args:
            user_id: User to get recommendations for
            based_on_newsletter_id: Base recommendations on specific newsletter
            limit: Maximum recommendations
            exclude_seen: Exclude user's own newsletters

        Returns:
            List of recommended newsletters
        """
        if not self.is_available():
            return []

        try:
            await self.ensure_collection()

            # If based on specific newsletter, use that for similarity
            if based_on_newsletter_id:
                return await self._recommendations_by_newsletter(
                    based_on_newsletter_id, user_id, limit, exclude_seen
                )

            # Otherwise, use user's recent engagement history
            return await self._recommendations_by_history(
                user_id, limit, exclude_seen
            )

        except Exception as e:
            logger.error(f"Failed to get recommendations: {e}")
            return []

    async def _recommendations_by_newsletter(
        self,
        newsletter_id: str,
        user_id: str,
        limit: int,
        exclude_seen: bool,
    ) -> List[Dict[str, Any]]:
        """Get recommendations based on a specific newsletter."""
        collection = self._get_collection()

        from weaviate.classes.query import Filter

        # Find the source newsletter
        results = collection.query.fetch_objects(
            filters=Filter.by_property("newsletter_id").equal(newsletter_id),
            limit=1,
            include_vector=True,
        )

        if not results.objects:
            logger.warning(f"Newsletter {newsletter_id} not found for recommendations")
            return []

        source = results.objects[0]
        source_vector = source.vector.get("default", []) if isinstance(source.vector, dict) else source.vector

        if not source_vector:
            return []

        # Search for similar, excluding user's own if requested
        filters = None
        if exclude_seen:
            filters = Filter.by_property("user_id").not_equal(user_id)

        similar = collection.query.near_vector(
            near_vector=source_vector,
            limit=limit + 1,  # Extra in case source is included
            filters=filters,
            return_metadata=["distance", "certainty"],
        )

        output = []
        for obj in similar.objects:
            # Skip the source newsletter itself
            if obj.properties.get("newsletter_id") == newsletter_id:
                continue

            score = 1.0 - (obj.metadata.distance or 0.0) if obj.metadata.distance else (obj.metadata.certainty or 0.0)

            output.append({
                "uuid": str(obj.uuid),
                "newsletter_id": obj.properties.get("newsletter_id"),
                "title": obj.properties.get("title"),
                "topics": obj.properties.get("topics", []),
                "tone": obj.properties.get("tone"),
                "engagement_score": obj.properties.get("engagement_score", 0.0),
                "score": score,
            })

            if len(output) >= limit:
                break

        return output

    async def _recommendations_by_history(
        self,
        user_id: str,
        limit: int,
        exclude_seen: bool,
    ) -> List[Dict[str, Any]]:
        """Get recommendations based on user's engagement history."""
        collection = self._get_collection()

        from weaviate.classes.query import Filter, Sort

        # Get user's recent newsletters sorted by engagement
        user_results = collection.query.fetch_objects(
            filters=Filter.by_property("user_id").equal(user_id),
            limit=5,  # Use top 5 for recommendations
            sort=Sort.by_property("engagement_score", ascending=False),
            include_vector=True,
        )

        if not user_results.objects:
            # No history - return popular newsletters
            return await self._get_popular_newsletters(limit, exclude_user=user_id if exclude_seen else None)

        # Average the vectors of top engaged newsletters
        vectors = []
        for obj in user_results.objects:
            vec = obj.vector.get("default", []) if isinstance(obj.vector, dict) else obj.vector
            if vec:
                vectors.append(vec)

        if not vectors:
            return []

        # Compute average vector
        avg_vector = [sum(x) / len(vectors) for x in zip(*vectors)]

        # Search for similar
        filters = None
        if exclude_seen:
            filters = Filter.by_property("user_id").not_equal(user_id)

        similar = collection.query.near_vector(
            near_vector=avg_vector,
            limit=limit,
            filters=filters,
            return_metadata=["distance", "certainty"],
        )

        output = []
        for obj in similar.objects:
            score = 1.0 - (obj.metadata.distance or 0.0) if obj.metadata.distance else (obj.metadata.certainty or 0.0)

            output.append({
                "uuid": str(obj.uuid),
                "newsletter_id": obj.properties.get("newsletter_id"),
                "title": obj.properties.get("title"),
                "topics": obj.properties.get("topics", []),
                "tone": obj.properties.get("tone"),
                "engagement_score": obj.properties.get("engagement_score", 0.0),
                "score": score,
            })

        return output

    async def _get_popular_newsletters(
        self,
        limit: int,
        exclude_user: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get popular newsletters by engagement score."""
        collection = self._get_collection()

        from weaviate.classes.query import Filter, Sort

        filters = None
        if exclude_user:
            filters = Filter.by_property("user_id").not_equal(exclude_user)

        results = collection.query.fetch_objects(
            filters=filters,
            limit=limit,
            sort=Sort.by_property("engagement_score", ascending=False),
        )

        output = []
        for obj in results.objects:
            output.append({
                "uuid": str(obj.uuid),
                "newsletter_id": obj.properties.get("newsletter_id"),
                "title": obj.properties.get("title"),
                "topics": obj.properties.get("topics", []),
                "tone": obj.properties.get("tone"),
                "engagement_score": obj.properties.get("engagement_score", 0.0),
                "score": obj.properties.get("engagement_score", 0.0),
            })

        return output

    async def get_user_patterns(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Analyze user's newsletter patterns for personalization.

        Args:
            user_id: User to analyze

        Returns:
            Dictionary with pattern analysis
        """
        if not self.is_available():
            return {"error": "Weaviate not available"}

        try:
            await self.ensure_collection()
            collection = self._get_collection()

            from weaviate.classes.query import Filter
            from weaviate.classes.aggregate import GroupByAggregate

            # Fetch user's newsletters
            results = collection.query.fetch_objects(
                filters=Filter.by_property("user_id").equal(user_id),
                limit=100,
            )

            if not results.objects:
                return {
                    "total_newsletters": 0,
                    "topic_distribution": {},
                    "preferred_tones": {},
                    "avg_engagement": 0.0,
                }

            # Analyze patterns
            topics_count = {}
            tones_count = {}
            total_engagement = 0.0

            for obj in results.objects:
                # Count topics
                for topic in obj.properties.get("topics", []):
                    topics_count[topic] = topics_count.get(topic, 0) + 1

                # Count tones
                tone = obj.properties.get("tone", "unknown")
                tones_count[tone] = tones_count.get(tone, 0) + 1

                # Sum engagement
                total_engagement += obj.properties.get("engagement_score", 0.0)

            total = len(results.objects)
            avg_engagement = total_engagement / total if total > 0 else 0.0

            # Sort by frequency
            sorted_topics = dict(sorted(topics_count.items(), key=lambda x: x[1], reverse=True))
            sorted_tones = dict(sorted(tones_count.items(), key=lambda x: x[1], reverse=True))

            return {
                "total_newsletters": total,
                "topic_distribution": sorted_topics,
                "top_topics": list(sorted_topics.keys())[:5],
                "preferred_tones": sorted_tones,
                "primary_tone": list(sorted_tones.keys())[0] if sorted_tones else "professional",
                "avg_engagement": round(avg_engagement, 3),
            }

        except Exception as e:
            logger.error(f"Failed to analyze patterns: {e}")
            return {"error": str(e)}

    async def update_engagement(
        self,
        newsletter_id: str,
        engagement_score: float,
    ) -> bool:
        """
        Update engagement score for a newsletter.

        Args:
            newsletter_id: Newsletter to update
            engagement_score: New engagement score

        Returns:
            True if updated successfully
        """
        if not self.is_available():
            return False

        try:
            collection = self._get_collection()

            from weaviate.classes.query import Filter

            # Find the newsletter
            results = collection.query.fetch_objects(
                filters=Filter.by_property("newsletter_id").equal(newsletter_id),
                limit=1,
            )

            if not results.objects:
                logger.warning(f"Newsletter {newsletter_id} not found for engagement update")
                return False

            obj = results.objects[0]

            # Update the engagement score
            collection.data.update(
                uuid=obj.uuid,
                properties={"engagement_score": engagement_score},
            )

            logger.info(f"Updated engagement score for {newsletter_id}: {engagement_score}")
            return True

        except Exception as e:
            logger.error(f"Failed to update engagement: {e}")
            return False

    async def delete_newsletter(
        self,
        newsletter_id: str,
    ) -> bool:
        """
        Delete a newsletter from the vector store.

        Args:
            newsletter_id: Newsletter to delete

        Returns:
            True if deleted successfully
        """
        if not self.is_available():
            return False

        try:
            collection = self._get_collection()

            from weaviate.classes.query import Filter

            # Find and delete
            results = collection.query.fetch_objects(
                filters=Filter.by_property("newsletter_id").equal(newsletter_id),
                limit=1,
            )

            if not results.objects:
                logger.warning(f"Newsletter {newsletter_id} not found for deletion")
                return False

            collection.data.delete_by_id(results.objects[0].uuid)
            logger.info(f"Deleted newsletter {newsletter_id} from RAG")
            return True

        except Exception as e:
            logger.error(f"Failed to delete newsletter: {e}")
            return False

    async def delete_user_data(
        self,
        user_id: str,
    ) -> int:
        """
        Delete all newsletters for a user.

        Args:
            user_id: User whose data to delete

        Returns:
            Number of documents deleted
        """
        if not self.is_available():
            return 0

        try:
            collection = self._get_collection()

            from weaviate.classes.query import Filter

            # Delete all matching
            result = collection.data.delete_many(
                where=Filter.by_property("user_id").equal(user_id),
            )

            deleted_count = result.successful if hasattr(result, 'successful') else 0
            logger.info(f"Deleted {deleted_count} newsletters for user {user_id}")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to delete user data: {e}")
            return 0

    def _build_filters(
        self,
        user_id: Optional[str] = None,
        topics: Optional[List[str]] = None,
    ):
        """Build Weaviate filters from parameters."""
        from weaviate.classes.query import Filter

        filters = []

        if user_id:
            filters.append(Filter.by_property("user_id").equal(user_id))

        if topics:
            # Match any of the topics
            topic_filters = [
                Filter.by_property("topics").contains_any([topic])
                for topic in topics
            ]
            if len(topic_filters) == 1:
                filters.append(topic_filters[0])
            elif len(topic_filters) > 1:
                combined = topic_filters[0]
                for tf in topic_filters[1:]:
                    combined = combined | tf
                filters.append(combined)

        if not filters:
            return None

        if len(filters) == 1:
            return filters[0]

        # Combine with AND
        combined = filters[0]
        for f in filters[1:]:
            combined = combined & f

        return combined

    def _parse_metadata(self, metadata_json: Optional[str]) -> Dict[str, Any]:
        """Parse metadata JSON string."""
        if not metadata_json:
            return {}
        try:
            return json.loads(metadata_json)
        except (json.JSONDecodeError, TypeError):
            return {}

    async def health_check(self) -> Dict[str, Any]:
        """
        Check RAG service health.

        Returns:
            Health status dictionary
        """
        status = {
            "available": self.is_available(),
            "collection_initialized": self._collection_initialized,
            "embeddings_provider": self._embeddings_provider.value,
            "embeddings_model": self._embeddings_model,
        }

        if not self.is_available():
            status["error"] = "Weaviate not available"
            return status

        try:
            # Test embeddings
            embeddings_healthy = await self.embeddings.health_check()
            status["embeddings_healthy"] = embeddings_healthy

            # Test collection access
            await self.ensure_collection()
            collection = self._get_collection()

            # Get count
            response = collection.aggregate.over_all(total_count=True)
            status["document_count"] = response.total_count if hasattr(response, 'total_count') else 0
            status["healthy"] = embeddings_healthy

        except Exception as e:
            status["healthy"] = False
            status["error"] = str(e)

        return status


# Singleton instance
_rag_service: Optional[NewsletterRAGService] = None


def get_rag_service() -> NewsletterRAGService:
    """Get the RAG service singleton instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = NewsletterRAGService()
    return _rag_service
