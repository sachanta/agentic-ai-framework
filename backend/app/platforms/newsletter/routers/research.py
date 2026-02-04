"""
Research API endpoints for Newsletter Platform.

Phase 6A: Backend API for testing Research Agent.
Provides endpoints to:
- Search by topics
- Search with custom natural language prompts
- Get trending content
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.platforms.newsletter.agents import ResearchAgent
from app.platforms.newsletter.schemas.research import (
    ResearchRequest,
    CustomResearchRequest,
    TrendingRequest,
    ArticleResponse,
    ResearchMetadata,
    ResearchResponse,
)

logger = logging.getLogger(__name__)

# Output directory for saving results
OUTPUT_DIR = Path(__file__).parent.parent.parent.parent.parent / "output" / "research"


def _save_results_to_file(
    result: Dict[str, Any],
    request_type: str,
    request_info: str,
) -> str:
    """
    Save research results to a JSON file for debugging.

    Args:
        result: The raw result from ResearchAgent
        request_type: Type of request (topics, custom, trending)
        request_info: Brief description of the request

    Returns:
        Path to the saved file
    """
    try:
        # Create output directory if it doesn't exist
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_info = "".join(c if c.isalnum() or c in "._-" else "_" for c in request_info[:30])
        filename = f"{timestamp}_{request_type}_{safe_info}.json"
        filepath = OUTPUT_DIR / filename

        # Prepare output data
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "request_type": request_type,
            "request_info": request_info,
            "success": result.get("success", False),
            "article_count": len(result.get("articles", [])),
            "metadata": result.get("metadata", {}),
            "articles": result.get("articles", []),
        }

        # Write to file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, default=str)

        logger.info(f"Research results saved to: {filepath}")
        return str(filepath)

    except Exception as e:
        logger.warning(f"Failed to save research results: {e}")
        return ""

router = APIRouter(prefix="/research", tags=["research"])


def _convert_to_article_response(article: dict) -> ArticleResponse:
    """Convert raw article dict to ArticleResponse schema."""
    return ArticleResponse(
        title=article.get("title", ""),
        url=article.get("url", ""),
        source=article.get("source", ""),
        content=article.get("content"),
        summary=article.get("summary"),
        key_takeaway=article.get("key_takeaway"),
        published_date=article.get("published_date"),
        score=article.get("score", 0.0),
        relevance_score=article.get("relevance_score", 0.0),
        quality_score=article.get("quality_score", 0.0),
        recency_boost=article.get("recency_boost", 0.0),
    )


@router.post("", response_model=ResearchResponse)
async def research_topics(request: ResearchRequest):
    """
    Research content by topics.

    Searches for articles on the specified topics using Tavily,
    filters by quality, and optionally generates AI summaries.

    Args:
        request: Research request with topics and options

    Returns:
        Research results with articles and metadata
    """
    try:
        agent = ResearchAgent()

        result = await agent.run({
            "topics": request.topics,
            "user_id": "api_user",
            "max_results": request.max_results,
            "include_summaries": request.include_summaries,
        })

        # Save results to file for debugging
        _save_results_to_file(result, "topics", "_".join(request.topics[:3]))

        if not result.get("success"):
            return ResearchResponse(
                success=False,
                articles=[],
                metadata=ResearchMetadata(
                    topics=request.topics,
                    message=result.get("error", "Research failed"),
                ),
                error=result.get("error"),
            )

        articles = [
            _convert_to_article_response(a)
            for a in result.get("articles", [])
        ]

        metadata_raw = result.get("metadata", {})
        metadata = ResearchMetadata(
            topics=metadata_raw.get("topics", request.topics),
            total_found=metadata_raw.get("total_found", len(articles)),
            after_filter=metadata_raw.get("after_filter", len(articles)),
            source=metadata_raw.get("source", "tavily"),
            cached=metadata_raw.get("source") == "cache",
        )

        return ResearchResponse(
            success=True,
            articles=articles,
            metadata=metadata,
        )

    except Exception as e:
        logger.error(f"Research endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/custom", response_model=ResearchResponse)
async def research_custom_prompt(request: CustomResearchRequest):
    """
    Research content using a natural language prompt.

    The prompt is processed by LLM to extract topics and search parameters,
    then searches for relevant articles.

    Examples:
    - "Find the latest news about AI in healthcare"
    - "Generate content for an Observability newsletter"
    - "What are the latest developments in quantum computing?"

    Args:
        request: Custom research request with natural language prompt

    Returns:
        Research results with articles and metadata
    """
    try:
        agent = ResearchAgent()

        result = await agent.run({
            "custom_prompt": request.prompt,
            "user_id": "api_user",
            "max_results": request.max_results,
            "include_summaries": request.include_summaries,
        })

        # Save results to file for debugging
        _save_results_to_file(result, "custom", request.prompt[:30])

        if not result.get("success"):
            return ResearchResponse(
                success=False,
                articles=[],
                metadata=ResearchMetadata(
                    topics=[],
                    message=result.get("error", "Research failed"),
                ),
                error=result.get("error"),
            )

        articles = [
            _convert_to_article_response(a)
            for a in result.get("articles", [])
        ]

        metadata_raw = result.get("metadata", {})
        metadata = ResearchMetadata(
            topics=metadata_raw.get("topics", [request.prompt]),
            total_found=metadata_raw.get("total_found", len(articles)),
            after_filter=metadata_raw.get("after_filter", len(articles)),
            source=metadata_raw.get("source", "tavily"),
            cached=metadata_raw.get("source") == "cache",
            message=f"Processed prompt: {request.prompt[:50]}...",
        )

        return ResearchResponse(
            success=True,
            articles=articles,
            metadata=metadata,
        )

    except Exception as e:
        logger.error(f"Custom research endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending", response_model=ResearchResponse)
async def get_trending_content(
    topics: str,
    max_results: int = 10,
):
    """
    Get trending content from the last 24 hours.

    Args:
        topics: Comma-separated list of topics (e.g., "AI,technology")
        max_results: Maximum number of results (1-50)

    Returns:
        Trending articles with metadata
    """
    try:
        topic_list = [t.strip() for t in topics.split(",") if t.strip()]

        if not topic_list:
            raise HTTPException(status_code=400, detail="At least one topic required")

        if max_results < 1 or max_results > 50:
            max_results = min(max(max_results, 1), 50)

        agent = ResearchAgent()
        trending = await agent.get_trending(topic_list, max_results)

        # Save results to file for debugging
        _save_results_to_file(
            {"success": True, "articles": trending, "metadata": {"topics": topic_list}},
            "trending",
            "_".join(topic_list[:3]),
        )

        articles = [_convert_to_article_response(a) for a in trending]

        return ResearchResponse(
            success=True,
            articles=articles,
            metadata=ResearchMetadata(
                topics=topic_list,
                total_found=len(articles),
                after_filter=len(articles),
                source="tavily_trending",
                message="Trending content from last 24 hours",
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trending endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
