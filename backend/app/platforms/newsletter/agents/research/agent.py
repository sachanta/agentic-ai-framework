"""
Research Agent for Newsletter Platform.

Handles content discovery with three internal stages:
1. Search (via Tavily - no LLM)
2. Filter/Score (rules-based + optional LLM)
3. Summarize (LLM)
"""
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

from app.common.base.agent import BaseAgent
from app.platforms.newsletter.services.tavily import get_tavily_service, TavilySearchService
from app.platforms.newsletter.services.memory import get_memory_service, CacheType
from app.platforms.newsletter.agents.research.llm import (
    get_research_llm,
    get_research_config,
    get_summarization_config,
)
from app.platforms.newsletter.agents.research.prompts import (
    RESEARCH_SYSTEM_PROMPT,
    SUMMARIZE_ARTICLE_PROMPT,
    BATCH_SUMMARIZE_PROMPT,
    SCORE_RELEVANCE_PROMPT,
    ENHANCE_QUERY_PROMPT,
    format_articles_for_prompt,
)

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """
    Research Agent for content discovery.

    Implements a three-stage pipeline:
    - Stage 1: Search via Tavily API (no LLM)
    - Stage 2: Filter and score results (rules + optional LLM)
    - Stage 3: Generate summaries (LLM)

    Features:
    - Multi-topic parallel search
    - Custom prompt processing
    - Result caching via Memory Service
    - Quality filtering and deduplication
    - AI-powered summarization
    """

    def __init__(
        self,
        tavily_service: Optional[TavilySearchService] = None,
        use_llm_for_scoring: bool = False,
        cache_results: bool = True,
    ):
        """
        Initialize the Research Agent.

        Args:
            tavily_service: Optional Tavily service (uses singleton if not provided)
            use_llm_for_scoring: Whether to use LLM for relevance scoring
            cache_results: Whether to cache results via Memory Service
        """
        llm = get_research_llm()
        llm_config = get_research_config()

        super().__init__(
            name="research",
            description="Content discovery and research agent for newsletters",
            llm=llm,
            system_prompt=RESEARCH_SYSTEM_PROMPT,
            model=llm_config.get("model"),
            temperature=llm_config.get("temperature", 0.7),
            max_tokens=llm_config.get("max_tokens", 1000),
        )

        self.tavily = tavily_service or get_tavily_service()
        self.memory = get_memory_service()
        self.use_llm_for_scoring = use_llm_for_scoring
        self.cache_results = cache_results

    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the research pipeline.

        Args:
            input: Dict containing:
                - topics: List of topics to research
                - user_id: User ID for caching
                - custom_prompt: Optional natural language prompt
                - max_results: Maximum results to return
                - include_summaries: Whether to generate summaries

        Returns:
            Dict with:
                - success: Whether research completed
                - articles: List of processed articles
                - metadata: Research metadata
        """
        await self.initialize()

        topics = input.get("topics", [])
        user_id = input.get("user_id", "anonymous")
        custom_prompt = input.get("custom_prompt")
        max_results = input.get("max_results", 10)
        include_summaries = input.get("include_summaries", True)

        try:
            # Process custom prompt if provided
            if custom_prompt:
                processed = await self._process_custom_prompt(custom_prompt)
                topics = processed.get("topics", topics)
                logger.info(f"Processed custom prompt into topics: {topics}")

            if not topics:
                return {
                    "success": False,
                    "error": "No topics provided for research",
                    "articles": [],
                }

            # Check cache first
            cache_key = self._generate_cache_key(topics)
            if self.cache_results:
                cached = await self.memory.get_research_results(user_id, cache_key)
                if cached:
                    logger.info(f"Returning cached research results for {topics}")
                    return {
                        "success": True,
                        "articles": cached,
                        "metadata": {"source": "cache", "topics": topics},
                    }

            # Stage 1: Search
            logger.info(f"Stage 1: Searching for topics: {topics}")
            raw_results = await self._search(topics)

            if not raw_results:
                return {
                    "success": True,
                    "articles": [],
                    "metadata": {"topics": topics, "message": "No results found"},
                }

            # Stage 2: Filter and Score
            logger.info(f"Stage 2: Filtering {len(raw_results)} results")
            filtered_results = await self._filter_and_score(raw_results, topics)

            # Limit results
            filtered_results = filtered_results[:max_results]

            # Stage 3: Summarize (optional)
            if include_summaries and filtered_results:
                logger.info(f"Stage 3: Summarizing {len(filtered_results)} articles")
                filtered_results = await self._generate_summaries(filtered_results, topics)

            # Cache results
            if self.cache_results and filtered_results:
                await self.memory.set_research_results(user_id, cache_key, filtered_results)

            return {
                "success": True,
                "articles": filtered_results,
                "metadata": {
                    "topics": topics,
                    "total_found": len(raw_results),
                    "after_filter": len(filtered_results),
                    "source": "tavily",
                },
            }

        except Exception as e:
            logger.error(f"Research failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "articles": [],
            }

    async def search_by_topics(
        self,
        topics: List[str],
        max_results_per_topic: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for articles by topics.

        Args:
            topics: List of topics to search
            max_results_per_topic: Max results per topic

        Returns:
            List of article dicts
        """
        return await self.tavily.search_and_filter(
            topics=topics,
            max_results=max_results_per_topic,
        )

    async def search_custom_prompt(
        self,
        prompt: str,
        user_id: str = "anonymous",
    ) -> Dict[str, Any]:
        """
        Search based on a natural language prompt.

        Args:
            prompt: Natural language description of what to find
            user_id: User ID for caching

        Returns:
            Research results
        """
        return await self.run({
            "custom_prompt": prompt,
            "user_id": user_id,
        })

    async def get_trending(
        self,
        topics: List[str],
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get trending content from the last 24 hours.

        Args:
            topics: Topics to search
            max_results: Maximum results

        Returns:
            List of trending articles
        """
        return await self.tavily.get_trending(topics, max_results)

    # =========================================================================
    # Stage 1: Search (No LLM)
    # =========================================================================

    async def _search(self, topics: List[str]) -> List[Dict[str, Any]]:
        """
        Stage 1: Search via Tavily API.

        This stage uses no LLM - just API calls.

        Args:
            topics: Topics to search

        Returns:
            Raw search results
        """
        try:
            results = await self.tavily.search_and_filter(
                topics=topics,
                deduplicate_results=True,
                apply_quality=True,
                apply_recency=True,
            )
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    # =========================================================================
    # Stage 2: Filter and Score (Rules + Optional LLM)
    # =========================================================================

    async def _filter_and_score(
        self,
        articles: List[Dict[str, Any]],
        topics: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Stage 2: Filter and score articles.

        By default uses rules-based scoring.
        Optionally uses LLM for more nuanced relevance scoring.

        Args:
            articles: Raw articles from search
            topics: Original topics for relevance check

        Returns:
            Filtered and scored articles
        """
        scored_articles = []

        for article in articles:
            # Rules-based scoring (always applied)
            score = self._calculate_base_score(article)

            # LLM-based scoring (optional)
            if self.use_llm_for_scoring and self.llm:
                try:
                    llm_score = await self._score_with_llm(article, topics)
                    # Blend scores: 60% LLM, 40% rules
                    score = (llm_score * 0.6) + (score * 0.4)
                except Exception as e:
                    logger.warning(f"LLM scoring failed, using rules only: {e}")

            article["relevance_score"] = round(score, 3)
            scored_articles.append(article)

        # Sort by score and filter low-quality
        scored_articles.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        # Filter out low-scoring articles (below 0.3)
        min_score = 0.3
        filtered = [a for a in scored_articles if a.get("relevance_score", 0) >= min_score]

        logger.info(f"Filtered {len(articles)} -> {len(filtered)} articles (min_score={min_score})")
        return filtered

    def _calculate_base_score(self, article: Dict[str, Any]) -> float:
        """
        Calculate base relevance score using rules.

        Args:
            article: Article dict

        Returns:
            Score between 0.0 and 1.0
        """
        score = 0.0

        # Base score from search API
        score += article.get("score", 0.5) * 0.4

        # Quality score from Tavily service
        score += article.get("quality_score", 0) * 0.2

        # Recency boost
        score += article.get("recency_boost", 0) * 0.2

        # Content length factor (longer = usually better)
        content = article.get("content", "")
        if len(content) > 500:
            score += 0.1
        if len(content) > 1000:
            score += 0.1

        return min(score, 1.0)

    async def _score_with_llm(
        self,
        article: Dict[str, Any],
        topics: List[str],
    ) -> float:
        """
        Score article relevance using LLM.

        Args:
            article: Article to score
            topics: Topics for relevance check

        Returns:
            Relevance score 0.0-1.0
        """
        prompt = SCORE_RELEVANCE_PROMPT.format(
            topics=", ".join(topics),
            title=article.get("title", ""),
            content=article.get("content", "")[:500],
        )

        response = await self.llm.generate(
            prompt=prompt,
            system=self.system_prompt,
            temperature=0.3,
            max_tokens=200,
        )

        try:
            # Parse JSON response
            content = response.content
            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())
            return float(result.get("score", 0.5))
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse LLM score response: {e}")
            return 0.5

    # =========================================================================
    # Stage 3: Summarize (LLM)
    # =========================================================================

    async def _generate_summaries(
        self,
        articles: List[Dict[str, Any]],
        topics: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Stage 3: Generate summaries for articles.

        Uses LLM to create concise, newsletter-ready summaries.

        Args:
            articles: Filtered articles
            topics: Topics for context

        Returns:
            Articles with summaries added
        """
        if not self.llm:
            logger.warning("No LLM available, skipping summarization")
            return articles

        # Use batch summarization for efficiency
        if len(articles) > 1:
            return await self._batch_summarize(articles, topics)

        # Single article summarization
        for article in articles:
            try:
                summary = await self._summarize_single(article)
                article["summary"] = summary
            except Exception as e:
                logger.warning(f"Failed to summarize article: {e}")
                article["summary"] = self._fallback_summary(article)

        return articles

    async def _summarize_single(self, article: Dict[str, Any]) -> str:
        """
        Summarize a single article.

        Args:
            article: Article to summarize

        Returns:
            Summary string
        """
        prompt = SUMMARIZE_ARTICLE_PROMPT.format(
            title=article.get("title", ""),
            source=article.get("source", ""),
            content=article.get("content", "")[:1500],
        )

        config = get_summarization_config()
        response = await self.llm.generate(
            prompt=prompt,
            system=self.system_prompt,
            temperature=config.get("temperature", 0.5),
            max_tokens=config.get("max_tokens", 500),
        )

        return response.content.strip()

    async def _batch_summarize(
        self,
        articles: List[Dict[str, Any]],
        topics: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Summarize multiple articles in one LLM call.

        Args:
            articles: Articles to summarize
            topics: Topics for context

        Returns:
            Articles with summaries added
        """
        # Format articles for prompt
        formatted = format_articles_for_prompt(articles, max_chars=400)

        prompt = BATCH_SUMMARIZE_PROMPT.format(
            topics=", ".join(topics),
            articles=formatted,
        )

        try:
            response = await self.llm.generate(
                prompt=prompt,
                system=self.system_prompt,
                temperature=0.5,
                max_tokens=1500,
            )

            # Parse JSON response
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            summaries = json.loads(content.strip())

            # Apply summaries to articles
            for item in summaries:
                idx = item.get("index", -1)
                if 0 <= idx < len(articles):
                    articles[idx]["summary"] = item.get("summary", "")
                    articles[idx]["key_takeaway"] = item.get("key_takeaway", "")

        except Exception as e:
            logger.warning(f"Batch summarization failed: {e}")
            # Fallback to individual summaries
            for article in articles:
                article["summary"] = self._fallback_summary(article)

        return articles

    def _fallback_summary(self, article: Dict[str, Any]) -> str:
        """
        Generate a basic summary without LLM.

        Args:
            article: Article to summarize

        Returns:
            Basic summary from first sentences
        """
        content = article.get("content", "")
        # Take first 200 chars or first two sentences
        sentences = content.split(". ")[:2]
        summary = ". ".join(sentences)
        if len(summary) > 200:
            summary = summary[:197] + "..."
        return summary

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _process_custom_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Process a natural language prompt into search parameters.

        Args:
            prompt: Natural language prompt

        Returns:
            Dict with topics, queries, etc.
        """
        if not self.llm:
            # Simple fallback: use prompt as single topic
            return {"topics": [prompt]}

        try:
            enhance_prompt = ENHANCE_QUERY_PROMPT.format(prompt=prompt)

            response = await self.llm.generate(
                prompt=enhance_prompt,
                system=self.system_prompt,
                temperature=0.5,
                max_tokens=300,
            )

            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())
            return {
                "topics": result.get("identified_topics", [prompt]),
                "queries": result.get("queries", []),
            }

        except Exception as e:
            logger.warning(f"Failed to process custom prompt: {e}")
            return {"topics": [prompt]}

    def _generate_cache_key(self, topics: List[str]) -> str:
        """
        Generate a cache key from topics.

        Args:
            topics: List of topics

        Returns:
            Hash string for caching
        """
        sorted_topics = sorted([t.lower().strip() for t in topics])
        key_string = "|".join(sorted_topics)
        return hashlib.md5(key_string.encode()).hexdigest()[:16]
