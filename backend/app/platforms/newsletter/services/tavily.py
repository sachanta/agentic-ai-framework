"""
Tavily Search Service for content discovery.

Provides web search capabilities for finding relevant articles
to include in newsletters.
"""
import asyncio
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

from tavily import TavilyClient, AsyncTavilyClient

from app.platforms.newsletter.config import config

logger = logging.getLogger(__name__)


class SearchResult:
    """Represents a single search result with metadata."""

    def __init__(
        self,
        title: str,
        url: str,
        content: str,
        score: float = 0.0,
        published_date: Optional[str] = None,
        source: Optional[str] = None,
        raw_content: Optional[str] = None,
    ):
        self.title = title
        self.url = url
        self.content = content
        self.score = score
        self.published_date = published_date
        self.source = source or self._extract_source(url)
        self.raw_content = raw_content
        self.content_hash = self._compute_hash(content)
        self.recency_boost = 0.0
        self.quality_score = 0.0

    def _extract_source(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.replace("www.", "")
        except Exception:
            return "unknown"

    def _compute_hash(self, content: str) -> str:
        """Compute content hash for deduplication."""
        return hashlib.md5(content.lower().strip().encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "url": self.url,
            "content": self.content,
            "score": self.score,
            "published_date": self.published_date,
            "source": self.source,
            "raw_content": self.raw_content,
            "recency_boost": self.recency_boost,
            "quality_score": self.quality_score,
            "final_score": self.score + self.recency_boost + self.quality_score,
        }


class TavilySearchService:
    """
    Service for searching and discovering content via Tavily API.

    Features:
    - Multi-topic parallel search
    - Quality filtering based on content length and source
    - Recency prioritization with configurable boost
    - Duplicate detection via content similarity
    - Domain inclusion/exclusion filters
    """

    # Minimum content length for quality filtering
    MIN_CONTENT_LENGTH = 100

    # High-reputation sources get a quality boost
    HIGH_QUALITY_SOURCES = {
        "reuters.com", "bbc.com", "nytimes.com", "theguardian.com",
        "techcrunch.com", "wired.com", "arstechnica.com", "theverge.com",
        "nature.com", "sciencedaily.com", "mit.edu", "stanford.edu",
        "forbes.com", "bloomberg.com", "economist.com", "wsj.com",
    }

    # Quality boost for high-reputation sources
    QUALITY_BOOST = 0.15

    # Recency boost for articles within 24 hours
    RECENCY_24H_BOOST = 0.2

    # Recency boost for articles within configured recency window
    RECENCY_WINDOW_BOOST = 0.1

    # Similarity threshold for duplicate detection (0-1)
    SIMILARITY_THRESHOLD = 0.85

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Tavily search service.

        Args:
            api_key: Tavily API key. If not provided, uses config.
        """
        self.api_key = api_key or config.TAVILY_API_KEY
        self._client: Optional[AsyncTavilyClient] = None
        self._sync_client: Optional[TavilyClient] = None

    @property
    def client(self) -> AsyncTavilyClient:
        """Get or create async Tavily client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "Tavily API key not configured. "
                    "Set NEWSLETTER_TAVILY_API_KEY environment variable."
                )
            self._client = AsyncTavilyClient(api_key=self.api_key)
        return self._client

    @property
    def sync_client(self) -> TavilyClient:
        """Get or create sync Tavily client."""
        if self._sync_client is None:
            if not self.api_key:
                raise ValueError(
                    "Tavily API key not configured. "
                    "Set NEWSLETTER_TAVILY_API_KEY environment variable."
                )
            self._sync_client = TavilyClient(api_key=self.api_key)
        return self._sync_client

    def is_configured(self) -> bool:
        """Check if the service is properly configured."""
        return bool(self.api_key)

    async def search_topic(
        self,
        topic: str,
        max_results: Optional[int] = None,
        search_depth: Optional[str] = None,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        days: Optional[int] = None,
    ) -> List[SearchResult]:
        """
        Search for articles on a single topic.

        Args:
            topic: The topic to search for
            max_results: Maximum results (default: config value)
            search_depth: "basic" or "advanced" (default: config value)
            include_domains: Only include these domains
            exclude_domains: Exclude these domains
            days: Only include articles from last N days

        Returns:
            List of SearchResult objects
        """
        max_results = max_results or config.MAX_RESULTS_PER_TOPIC
        search_depth = search_depth or config.SEARCH_DEPTH
        include_domains = include_domains or config.include_domains_list
        exclude_domains = exclude_domains or config.exclude_domains_list
        days = days or config.RECENCY_DAYS

        try:
            # Build search parameters
            search_params = {
                "query": topic,
                "max_results": max_results,
                "search_depth": search_depth,
                "include_answer": False,
            }

            # Add domain filters if specified
            if include_domains:
                search_params["include_domains"] = include_domains
            if exclude_domains:
                search_params["exclude_domains"] = exclude_domains

            # Add days filter if specified
            if days:
                search_params["days"] = days

            # Execute search
            response = await self.client.search(**search_params)

            # Parse results
            results = []
            for item in response.get("results", []):
                result = SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("content", ""),
                    score=item.get("score", 0.0),
                    published_date=item.get("published_date"),
                    raw_content=item.get("raw_content"),
                )
                results.append(result)

            logger.info(f"Found {len(results)} results for topic: {topic}")
            return results

        except Exception as e:
            logger.error(f"Search failed for topic '{topic}': {e}")
            raise

    async def search_topics(
        self,
        topics: List[str],
        max_results_per_topic: Optional[int] = None,
        search_depth: Optional[str] = None,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        days: Optional[int] = None,
    ) -> Dict[str, List[SearchResult]]:
        """
        Search for articles on multiple topics in parallel.

        Args:
            topics: List of topics to search
            max_results_per_topic: Max results per topic
            search_depth: "basic" or "advanced"
            include_domains: Only include these domains
            exclude_domains: Exclude these domains
            days: Only include articles from last N days

        Returns:
            Dictionary mapping topic -> list of SearchResult
        """
        # Create search tasks for parallel execution
        tasks = [
            self.search_topic(
                topic=topic,
                max_results=max_results_per_topic,
                search_depth=search_depth,
                include_domains=include_domains,
                exclude_domains=exclude_domains,
                days=days,
            )
            for topic in topics
        ]

        # Execute all searches in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Build result dictionary
        topic_results = {}
        for topic, result in zip(topics, results):
            if isinstance(result, Exception):
                logger.error(f"Search failed for topic '{topic}': {result}")
                topic_results[topic] = []
            else:
                topic_results[topic] = result

        return topic_results

    def apply_quality_filter(
        self,
        results: List[SearchResult],
        min_content_length: Optional[int] = None,
    ) -> List[SearchResult]:
        """
        Filter results based on quality criteria.

        Args:
            results: List of search results
            min_content_length: Minimum content length (default: MIN_CONTENT_LENGTH)

        Returns:
            Filtered list of search results with quality scores applied
        """
        min_length = min_content_length or self.MIN_CONTENT_LENGTH
        filtered = []

        for result in results:
            # Skip if content too short
            if len(result.content) < min_length:
                logger.debug(f"Filtered out (too short): {result.url}")
                continue

            # Apply quality boost for high-reputation sources
            if result.source in self.HIGH_QUALITY_SOURCES:
                result.quality_score = self.QUALITY_BOOST

            filtered.append(result)

        logger.info(f"Quality filter: {len(results)} -> {len(filtered)} results")
        return filtered

    def apply_recency_boost(
        self,
        results: List[SearchResult],
        recency_days: Optional[int] = None,
    ) -> List[SearchResult]:
        """
        Apply recency boost to recent articles.

        Args:
            results: List of search results
            recency_days: Recency window in days (default: config value)

        Returns:
            Results with recency boost applied
        """
        recency_days = recency_days or config.RECENCY_DAYS
        now = datetime.now(timezone.utc)
        cutoff_24h = now - timedelta(hours=24)
        cutoff_window = now - timedelta(days=recency_days)

        for result in results:
            if not result.published_date:
                continue

            try:
                # Parse published date
                pub_date = self._parse_date(result.published_date)
                if not pub_date:
                    continue

                # Apply 24-hour boost
                if pub_date >= cutoff_24h:
                    result.recency_boost = self.RECENCY_24H_BOOST
                    logger.debug(f"24h boost applied: {result.url}")
                # Apply recency window boost
                elif pub_date >= cutoff_window:
                    result.recency_boost = self.RECENCY_WINDOW_BOOST
                    logger.debug(f"Recency boost applied: {result.url}")

            except Exception as e:
                logger.debug(f"Could not parse date '{result.published_date}': {e}")

        return results

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime."""
        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue

        return None

    def deduplicate(
        self,
        results: List[SearchResult],
        similarity_threshold: Optional[float] = None,
    ) -> List[SearchResult]:
        """
        Remove duplicate or near-duplicate results.

        Uses content hash for exact duplicates and text similarity
        for near-duplicates.

        Args:
            results: List of search results
            similarity_threshold: Similarity threshold (0-1)

        Returns:
            Deduplicated list of search results
        """
        threshold = similarity_threshold or self.SIMILARITY_THRESHOLD
        seen_hashes = set()
        unique_results = []

        for result in results:
            # Check exact duplicate via hash
            if result.content_hash in seen_hashes:
                logger.debug(f"Exact duplicate removed: {result.url}")
                continue

            # Check similarity with existing results
            is_duplicate = False
            for existing in unique_results:
                similarity = self._compute_similarity(
                    result.content, existing.content
                )
                if similarity >= threshold:
                    logger.debug(
                        f"Similar duplicate removed ({similarity:.2f}): {result.url}"
                    )
                    is_duplicate = True
                    break

            if not is_duplicate:
                seen_hashes.add(result.content_hash)
                unique_results.append(result)

        logger.info(f"Deduplication: {len(results)} -> {len(unique_results)} results")
        return unique_results

    def _compute_similarity(self, text1: str, text2: str) -> float:
        """Compute text similarity using SequenceMatcher."""
        # Use first 500 chars for efficiency
        t1 = text1[:500].lower()
        t2 = text2[:500].lower()
        return SequenceMatcher(None, t1, t2).ratio()

    def sort_by_score(
        self,
        results: List[SearchResult],
        descending: bool = True,
    ) -> List[SearchResult]:
        """
        Sort results by final score (base + recency + quality).

        Args:
            results: List of search results
            descending: Sort in descending order (default: True)

        Returns:
            Sorted list of search results
        """
        return sorted(
            results,
            key=lambda r: r.score + r.recency_boost + r.quality_score,
            reverse=descending,
        )

    async def search_and_filter(
        self,
        topics: List[str],
        max_results: Optional[int] = None,
        deduplicate_results: bool = True,
        apply_quality: bool = True,
        apply_recency: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Search topics and apply all filters in one call.

        This is the main entry point for newsletter content discovery.

        Args:
            topics: List of topics to search
            max_results: Maximum total results to return
            deduplicate_results: Whether to remove duplicates
            apply_quality: Whether to apply quality filtering
            apply_recency: Whether to apply recency boost

        Returns:
            List of filtered, sorted results as dictionaries
        """
        # Search all topics
        topic_results = await self.search_topics(topics)

        # Flatten results
        all_results = []
        for topic, results in topic_results.items():
            for result in results:
                # Tag with topic for reference
                result.topic = topic
            all_results.extend(results)

        logger.info(f"Total raw results: {len(all_results)}")

        # Apply quality filter
        if apply_quality:
            all_results = self.apply_quality_filter(all_results)

        # Apply recency boost
        if apply_recency:
            all_results = self.apply_recency_boost(all_results)

        # Deduplicate
        if deduplicate_results:
            all_results = self.deduplicate(all_results)

        # Sort by score
        all_results = self.sort_by_score(all_results)

        # Limit results
        if max_results and len(all_results) > max_results:
            all_results = all_results[:max_results]

        # Convert to dictionaries
        return [r.to_dict() for r in all_results]

    async def get_trending(
        self,
        topics: List[str],
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get trending content from the last 24 hours.

        Args:
            topics: Topics to search
            max_results: Maximum results to return

        Returns:
            List of trending articles
        """
        # Search with 1-day window and advanced depth
        topic_results = await self.search_topics(
            topics=topics,
            search_depth="advanced",
            days=1,
        )

        # Flatten and process
        all_results = []
        for results in topic_results.values():
            all_results.extend(results)

        # Apply all boosts
        all_results = self.apply_quality_filter(all_results)
        all_results = self.apply_recency_boost(all_results)
        all_results = self.deduplicate(all_results)
        all_results = self.sort_by_score(all_results)

        # Take top results
        all_results = all_results[:max_results]

        return [r.to_dict() for r in all_results]


# Singleton instance
_tavily_service: Optional[TavilySearchService] = None


def get_tavily_service() -> TavilySearchService:
    """Get the Tavily search service instance."""
    global _tavily_service
    if _tavily_service is None:
        _tavily_service = TavilySearchService()
    return _tavily_service
