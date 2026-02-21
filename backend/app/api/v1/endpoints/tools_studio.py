"""
Tools Studio endpoints — Discover and execute framework tools.

Provides a static registry of all 16 framework tools (search, email, cache,
RAG, LLM) with metadata, parameter schemas, and live execution via the
underlying service classes.
"""
import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status

from app.schemas.tool import (
    ToolStudioDetail,
    ToolStudioListResponse,
    ToolStudioParameter,
    ToolStudioSummary,
    ToolStudioTryRequest,
    ToolStudioTryResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Static Tool Registry
# ---------------------------------------------------------------------------

_TOOL_REGISTRY: List[Dict[str, Any]] = [
    # ---- Search (Tavily) ----
    {
        "tool_id": "search/tavily_search_topic",
        "name": "tavily_search_topic",
        "display_name": "Search Topic",
        "category": "search",
        "platform_id": "newsletter",
        "service_class": "TavilySearchService",
        "service_module": "app.platforms.newsletter.services.tavily",
        "service_factory": "get_tavily_service",
        "method": "search_topic",
        "description": "Search for articles on a single topic using Tavily API.",
        "returns": "List[SearchResult]",
        "requires": ["NEWSLETTER_TAVILY_API_KEY"],
        "parameters": [
            {"name": "topic", "type": "string", "description": "Topic to search for", "required": True},
            {"name": "max_results", "type": "integer", "description": "Maximum number of results", "required": False, "default": None},
            {"name": "search_depth", "type": "string", "description": "Search depth: 'basic' or 'advanced'", "required": False, "default": None},
            {"name": "days", "type": "integer", "description": "Limit results to last N days", "required": False, "default": None},
        ],
    },
    {
        "tool_id": "search/tavily_search_topics",
        "name": "tavily_search_topics",
        "display_name": "Search Topics",
        "category": "search",
        "platform_id": "newsletter",
        "service_class": "TavilySearchService",
        "service_module": "app.platforms.newsletter.services.tavily",
        "service_factory": "get_tavily_service",
        "method": "search_topics",
        "description": "Search multiple topics in parallel using Tavily API.",
        "returns": "Dict[str, List[SearchResult]]",
        "requires": ["NEWSLETTER_TAVILY_API_KEY"],
        "parameters": [
            {"name": "topics", "type": "array", "description": "List of topics to search", "required": True},
            {"name": "max_results_per_topic", "type": "integer", "description": "Max results per topic", "required": False, "default": None},
            {"name": "search_depth", "type": "string", "description": "Search depth: 'basic' or 'advanced'", "required": False, "default": None},
            {"name": "days", "type": "integer", "description": "Limit results to last N days", "required": False, "default": None},
        ],
    },
    {
        "tool_id": "search/tavily_search_and_filter",
        "name": "tavily_search_and_filter",
        "display_name": "Search & Filter",
        "category": "search",
        "platform_id": "newsletter",
        "service_class": "TavilySearchService",
        "service_module": "app.platforms.newsletter.services.tavily",
        "service_factory": "get_tavily_service",
        "method": "search_and_filter",
        "description": "Full pipeline: search + quality filter + dedup.",
        "returns": "List[Dict]",
        "requires": ["NEWSLETTER_TAVILY_API_KEY"],
        "parameters": [
            {"name": "topics", "type": "array", "description": "List of topics to search", "required": True},
            {"name": "max_results", "type": "integer", "description": "Maximum total results", "required": False, "default": None},
            {"name": "deduplicate_results", "type": "boolean", "description": "Enable deduplication", "required": False, "default": True},
            {"name": "apply_quality", "type": "boolean", "description": "Apply quality filter", "required": False, "default": True},
            {"name": "apply_recency", "type": "boolean", "description": "Apply recency boost", "required": False, "default": True},
        ],
    },
    {
        "tool_id": "search/tavily_get_trending",
        "name": "tavily_get_trending",
        "display_name": "Get Trending",
        "category": "search",
        "platform_id": "newsletter",
        "service_class": "TavilySearchService",
        "service_module": "app.platforms.newsletter.services.tavily",
        "service_factory": "get_tavily_service",
        "method": "get_trending",
        "description": "Get trending content for topics.",
        "returns": "List[Dict]",
        "requires": ["NEWSLETTER_TAVILY_API_KEY"],
        "parameters": [
            {"name": "topics", "type": "array", "description": "List of topics", "required": True},
            {"name": "max_results", "type": "integer", "description": "Maximum results", "required": False, "default": 10},
        ],
    },
    # ---- Email (Resend) ----
    {
        "tool_id": "email/send_email",
        "name": "send_email",
        "display_name": "Send Email",
        "category": "email",
        "platform_id": "newsletter",
        "service_class": "EmailService",
        "service_module": "app.platforms.newsletter.services.email",
        "service_factory": "get_email_service",
        "method": "send_email",
        "description": "Send a single email via Resend API.",
        "returns": "EmailResult",
        "requires": ["NEWSLETTER_RESEND_API_KEY"],
        "parameters": [
            {"name": "to", "type": "string", "description": "Recipient email address", "required": True},
            {"name": "subject", "type": "string", "description": "Email subject line", "required": True},
            {"name": "html_content", "type": "string", "description": "HTML email body", "required": True},
            {"name": "plain_text", "type": "string", "description": "Plain text fallback", "required": False, "default": None},
        ],
    },
    {
        "tool_id": "email/send_batch",
        "name": "send_batch",
        "display_name": "Send Batch",
        "category": "email",
        "platform_id": "newsletter",
        "service_class": "EmailService",
        "service_module": "app.platforms.newsletter.services.email",
        "service_factory": "get_email_service",
        "method": "send_batch",
        "description": "Send batch emails to multiple recipients.",
        "returns": "EmailBatch",
        "requires": ["NEWSLETTER_RESEND_API_KEY"],
        "parameters": [
            {"name": "recipients", "type": "array", "description": "List of recipient email addresses", "required": True},
            {"name": "subject", "type": "string", "description": "Email subject line", "required": True},
            {"name": "html_content", "type": "string", "description": "HTML email body", "required": True},
            {"name": "plain_text", "type": "string", "description": "Plain text fallback", "required": False, "default": None},
            {"name": "batch_size", "type": "integer", "description": "Emails per batch", "required": False, "default": 50},
        ],
    },
    {
        "tool_id": "email/check_health",
        "name": "check_health",
        "display_name": "Check Health",
        "category": "email",
        "platform_id": "newsletter",
        "service_class": "EmailService",
        "service_module": "app.platforms.newsletter.services.email",
        "service_factory": "get_email_service",
        "method": "check_health",
        "description": "Check email service health and configuration.",
        "returns": "Dict[str, Any]",
        "requires": ["NEWSLETTER_RESEND_API_KEY"],
        "parameters": [],
    },
    # ---- Cache (MongoDB Memory) ----
    {
        "tool_id": "cache/memory_set",
        "name": "memory_set",
        "display_name": "Cache Set",
        "category": "cache",
        "platform_id": "newsletter",
        "service_class": "MemoryService",
        "service_module": "app.platforms.newsletter.services.memory",
        "service_factory": "get_memory_service",
        "method": "set",
        "description": "Store value in MongoDB cache with optional TTL.",
        "returns": "bool",
        "requires": ["MongoDB"],
        "parameters": [
            {"name": "user_id", "type": "string", "description": "User identifier", "required": True},
            {"name": "cache_type", "type": "string", "description": "Cache type (preferences, research, workflow, session, engagement, analytics)", "required": True},
            {"name": "key", "type": "string", "description": "Cache key", "required": True},
            {"name": "value", "type": "object", "description": "Value to cache (any JSON-serializable data)", "required": True},
            {"name": "ttl", "type": "integer", "description": "Time-to-live in seconds", "required": False, "default": None},
        ],
    },
    {
        "tool_id": "cache/memory_get",
        "name": "memory_get",
        "display_name": "Cache Get",
        "category": "cache",
        "platform_id": "newsletter",
        "service_class": "MemoryService",
        "service_module": "app.platforms.newsletter.services.memory",
        "service_factory": "get_memory_service",
        "method": "get",
        "description": "Retrieve value from MongoDB cache.",
        "returns": "Optional[Any]",
        "requires": ["MongoDB"],
        "parameters": [
            {"name": "user_id", "type": "string", "description": "User identifier", "required": True},
            {"name": "cache_type", "type": "string", "description": "Cache type (preferences, research, workflow, session, engagement, analytics)", "required": True},
            {"name": "key", "type": "string", "description": "Cache key", "required": True},
        ],
    },
    {
        "tool_id": "cache/memory_delete",
        "name": "memory_delete",
        "display_name": "Cache Delete",
        "category": "cache",
        "platform_id": "newsletter",
        "service_class": "MemoryService",
        "service_module": "app.platforms.newsletter.services.memory",
        "service_factory": "get_memory_service",
        "method": "delete",
        "description": "Delete a cache entry.",
        "returns": "bool",
        "requires": ["MongoDB"],
        "parameters": [
            {"name": "user_id", "type": "string", "description": "User identifier", "required": True},
            {"name": "cache_type", "type": "string", "description": "Cache type (preferences, research, workflow, session, engagement, analytics)", "required": True},
            {"name": "key", "type": "string", "description": "Cache key", "required": True},
        ],
    },
    # ---- RAG (Weaviate) ----
    {
        "tool_id": "rag/store_newsletter",
        "name": "store_newsletter",
        "display_name": "Store Newsletter",
        "category": "rag",
        "platform_id": "newsletter",
        "service_class": "NewsletterRAGService",
        "service_module": "app.platforms.newsletter.services.rag",
        "service_factory": "get_rag_service",
        "method": "store_newsletter",
        "description": "Store newsletter in Weaviate vector DB.",
        "returns": "Optional[str]",
        "requires": ["Weaviate"],
        "parameters": [
            {"name": "user_id", "type": "string", "description": "User identifier", "required": True},
            {"name": "newsletter_id", "type": "string", "description": "Newsletter identifier", "required": True},
            {"name": "content", "type": "string", "description": "Newsletter content text", "required": True},
            {"name": "title", "type": "string", "description": "Newsletter title", "required": False, "default": ""},
            {"name": "topics", "type": "array", "description": "List of topic tags", "required": False, "default": None},
            {"name": "tone", "type": "string", "description": "Writing tone", "required": False, "default": "professional"},
        ],
    },
    {
        "tool_id": "rag/search_similar",
        "name": "search_similar",
        "display_name": "Search Similar",
        "category": "rag",
        "platform_id": "newsletter",
        "service_class": "NewsletterRAGService",
        "service_module": "app.platforms.newsletter.services.rag",
        "service_factory": "get_rag_service",
        "method": "search_similar",
        "description": "Search similar newsletters by vector similarity.",
        "returns": "List[Dict]",
        "requires": ["Weaviate"],
        "parameters": [
            {"name": "query", "type": "string", "description": "Search query text", "required": True},
            {"name": "user_id", "type": "string", "description": "Filter by user", "required": False, "default": None},
            {"name": "limit", "type": "integer", "description": "Max results to return", "required": False, "default": 10},
            {"name": "min_score", "type": "number", "description": "Minimum similarity score", "required": False, "default": 0.0},
        ],
    },
    # ---- LLM Provider ----
    {
        "tool_id": "llm/generate",
        "name": "generate",
        "display_name": "Generate Text",
        "category": "llm",
        "platform_id": "common",
        "service_class": "LLMProvider",
        "service_module": "app.common.providers.llm",
        "service_factory": "get_llm_provider",
        "method": "generate",
        "description": "Generate text completion with configured LLM.",
        "returns": "LLMResponse",
        "requires": ["LLM Provider API Key"],
        "parameters": [
            {"name": "prompt", "type": "string", "description": "Text prompt for generation", "required": True},
            {"name": "temperature", "type": "number", "description": "Sampling temperature (0-1)", "required": False, "default": 0.7},
            {"name": "max_tokens", "type": "integer", "description": "Maximum tokens to generate", "required": False, "default": 1000},
        ],
    },
    {
        "tool_id": "llm/chat",
        "name": "chat",
        "display_name": "Chat",
        "category": "llm",
        "platform_id": "common",
        "service_class": "LLMProvider",
        "service_module": "app.common.providers.llm",
        "service_factory": "get_llm_provider",
        "method": "chat",
        "description": "Chat with configured LLM using message history.",
        "returns": "LLMResponse",
        "requires": ["LLM Provider API Key"],
        "parameters": [
            {"name": "messages", "type": "array", "description": "Chat messages: [{role: 'user'|'assistant'|'system', content: '...'}]", "required": True},
            {"name": "temperature", "type": "number", "description": "Sampling temperature (0-1)", "required": False, "default": 0.7},
            {"name": "max_tokens", "type": "integer", "description": "Maximum tokens to generate", "required": False, "default": 1000},
        ],
    },
    {
        "tool_id": "llm/list_models",
        "name": "list_models",
        "display_name": "List Models",
        "category": "llm",
        "platform_id": "common",
        "service_class": "LLMProvider",
        "service_module": "app.common.providers.llm",
        "service_factory": "get_llm_provider",
        "method": "list_models",
        "description": "List available models for current provider.",
        "returns": "List[str]",
        "requires": ["LLM Provider API Key"],
        "parameters": [],
    },
    {
        "tool_id": "llm/health_check",
        "name": "health_check",
        "display_name": "Health Check",
        "category": "llm",
        "platform_id": "common",
        "service_class": "LLMProvider",
        "service_module": "app.common.providers.llm",
        "service_factory": "get_llm_provider",
        "method": "health_check",
        "description": "Check if LLM provider is healthy and reachable.",
        "returns": "bool",
        "requires": ["LLM Provider API Key"],
        "parameters": [],
    },
]

# Categories with display labels
_CATEGORIES = ["search", "email", "cache", "rag", "llm"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_tool(tool_id: str) -> Dict[str, Any]:
    """Lookup a tool by ID, raise 404 if not found."""
    for tool in _TOOL_REGISTRY:
        if tool["tool_id"] == tool_id:
            return tool
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Tool '{tool_id}' not found",
    )


def _build_summary(tool: Dict[str, Any]) -> ToolStudioSummary:
    """Build a summary DTO from a registry entry."""
    return ToolStudioSummary(
        tool_id=tool["tool_id"],
        name=tool["name"],
        display_name=tool["display_name"],
        category=tool["category"],
        platform_id=tool["platform_id"],
        service_class=tool["service_class"],
        description=tool["description"],
        parameter_count=len(tool["parameters"]),
        status="available",
    )


def _build_detail(tool: Dict[str, Any]) -> ToolStudioDetail:
    """Build a full detail DTO from a registry entry."""
    params = [
        ToolStudioParameter(
            name=p["name"],
            type=p["type"],
            description=p["description"],
            required=p.get("required", True),
            default=p.get("default"),
        )
        for p in tool["parameters"]
    ]
    return ToolStudioDetail(
        tool_id=tool["tool_id"],
        name=tool["name"],
        display_name=tool["display_name"],
        category=tool["category"],
        platform_id=tool["platform_id"],
        service_class=tool["service_class"],
        description=tool["description"],
        parameter_count=len(tool["parameters"]),
        status="available",
        parameters=params,
        returns=tool.get("returns"),
        requires=tool.get("requires", []),
    )


async def _execute_tool(tool_def: Dict[str, Any], params: Dict[str, Any]) -> Any:
    """Instantiate the service and call the method with given params."""
    import importlib

    module = importlib.import_module(tool_def["service_module"])
    factory = getattr(module, tool_def["service_factory"])
    service = factory()

    method = getattr(service, tool_def["method"])

    # For MemoryService, convert cache_type string to CacheType enum
    if tool_def["service_class"] == "MemoryService" and "cache_type" in params:
        from app.platforms.newsletter.services.memory import CacheType
        try:
            params["cache_type"] = CacheType(params["cache_type"])
        except ValueError:
            raise ValueError(
                f"Invalid cache_type '{params['cache_type']}'. "
                f"Valid values: {[ct.value for ct in CacheType]}"
            )

    result = method(**params)
    # Await if coroutine
    if asyncio.iscoroutine(result):
        result = await result

    # Serialize result for JSON response
    if hasattr(result, "model_dump"):
        return result.model_dump()
    if hasattr(result, "__dict__"):
        return {k: v for k, v in result.__dict__.items() if not k.startswith("_")}
    if isinstance(result, list):
        serialized = []
        for item in result:
            if hasattr(item, "model_dump"):
                serialized.append(item.model_dump())
            elif hasattr(item, "__dict__"):
                serialized.append({k: v for k, v in item.__dict__.items() if not k.startswith("_")})
            else:
                serialized.append(item)
        return serialized
    return result


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/tools", response_model=ToolStudioListResponse)
async def list_tools(category: Optional[str] = None):
    """
    List all registered tools, optionally filtered by category.

    Query params:
        category: Optional filter (search, email, cache, rag, llm).
    """
    tools = _TOOL_REGISTRY
    if category:
        if category not in _CATEGORIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category '{category}'. Valid: {_CATEGORIES}",
            )
        tools = [t for t in tools if t["category"] == category]

    summaries = [_build_summary(t) for t in tools]
    return ToolStudioListResponse(
        tools=summaries,
        total=len(summaries),
        categories=_CATEGORIES,
    )


@router.get("/tools/{tool_id:path}", response_model=ToolStudioDetail)
async def get_tool_detail(tool_id: str):
    """Get full detail for a single tool by ID (e.g. search/tavily_search_topic)."""
    tool = _get_tool(tool_id)
    return _build_detail(tool)


@router.post("/tools/{tool_id:path}/try", response_model=ToolStudioTryResponse)
async def try_tool(tool_id: str, request: ToolStudioTryRequest):
    """
    Execute a tool with the provided parameters.

    Times out after 60 seconds.
    """
    tool_def = _get_tool(tool_id)

    start = time.perf_counter()
    try:
        result = await asyncio.wait_for(
            _execute_tool(tool_def, request.parameters),
            timeout=60,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        return ToolStudioTryResponse(
            success=True,
            output=result,
            duration_ms=round(elapsed_ms, 1),
            tool_id=tool_id,
        )
    except asyncio.TimeoutError:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return ToolStudioTryResponse(
            success=False,
            error="Tool execution timed out after 60 seconds",
            duration_ms=round(elapsed_ms, 1),
            tool_id=tool_id,
        )
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.warning(f"Tool execution failed for {tool_id}: {e}")
        return ToolStudioTryResponse(
            success=False,
            error=str(e),
            duration_ms=round(elapsed_ms, 1),
            tool_id=tool_id,
        )


@router.get("/categories")
async def list_categories():
    """List all tool categories with tool counts."""
    counts = {}
    for t in _TOOL_REGISTRY:
        cat = t["category"]
        counts[cat] = counts.get(cat, 0) + 1

    return [
        {"name": cat, "count": counts.get(cat, 0)}
        for cat in _CATEGORIES
    ]
