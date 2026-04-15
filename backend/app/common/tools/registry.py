"""
Shared Tool Registry — single source of truth for all framework tools.

This module contains the tool registry, executor, and JSON Schema converter
used by both the REST API (Tools Studio) and the MCP server.
"""
import asyncio
import base64
import importlib
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Static Tool Registry
# ---------------------------------------------------------------------------

TOOL_REGISTRY: List[Dict[str, Any]] = [
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
    # ---- Document (PDFProcessor) ----
    {
        "tool_id": "document/pdf_extract_text",
        "name": "pdf_extract_text",
        "display_name": "Extract PDF Text",
        "category": "document",
        "platform_id": "common",
        "service_class": "PDFProcessor",
        "service_module": "app.services.pdf_processor",
        "service_factory": "get_pdf_processor",
        "method": "extract_text",
        "description": "Extract text from a base64-encoded PDF. Returns (text, page_count).",
        "returns": "Tuple[str, int]",
        "requires": [],
        "parameters": [
            {"name": "content", "type": "string", "description": "Base64-encoded PDF content", "required": True},
        ],
    },
    {
        "tool_id": "document/pdf_chunk_text",
        "name": "pdf_chunk_text",
        "display_name": "Chunk Text",
        "category": "document",
        "platform_id": "common",
        "service_class": "PDFProcessor",
        "service_module": "app.services.pdf_processor",
        "service_factory": "get_pdf_processor",
        "method": "chunk_text",
        "description": "Split text into overlapping chunks for RAG ingestion.",
        "returns": "List[TextChunk]",
        "requires": [],
        "parameters": [
            {"name": "text", "type": "string", "description": "Text to split into chunks", "required": True},
            {"name": "chunk_size", "type": "integer", "description": "Target chunk size in characters", "required": False, "default": None},
            {"name": "chunk_overlap", "type": "integer", "description": "Overlap between chunks in characters", "required": False, "default": None},
        ],
    },
    {
        "tool_id": "document/pdf_process",
        "name": "pdf_process",
        "display_name": "Process PDF",
        "category": "document",
        "platform_id": "common",
        "service_class": "PDFProcessor",
        "service_module": "app.services.pdf_processor",
        "service_factory": "get_pdf_processor",
        "method": "process",
        "description": "Full PDF processing pipeline: extract text and chunk. Accepts base64-encoded PDF.",
        "returns": "PDFProcessingResult",
        "requires": [],
        "parameters": [
            {"name": "content", "type": "string", "description": "Base64-encoded PDF content", "required": True},
        ],
    },
    # ---- Embeddings ----
    {
        "tool_id": "embeddings/embed_text",
        "name": "embed_text",
        "display_name": "Embed Text",
        "category": "embeddings",
        "platform_id": "common",
        "service_class": "EmbeddingsProvider",
        "service_module": "app.common.providers.embeddings",
        "service_factory": "get_embeddings_provider",
        "method": "embed_text",
        "description": "Generate embedding vector for a single text.",
        "returns": "List[float]",
        "requires": ["Embeddings Provider"],
        "parameters": [
            {"name": "text", "type": "string", "description": "Text to embed", "required": True},
        ],
    },
    {
        "tool_id": "embeddings/embed_texts",
        "name": "embed_texts",
        "display_name": "Embed Texts",
        "category": "embeddings",
        "platform_id": "common",
        "service_class": "EmbeddingsProvider",
        "service_module": "app.common.providers.embeddings",
        "service_factory": "get_embeddings_provider",
        "method": "embed_texts",
        "description": "Generate embedding vectors for multiple texts.",
        "returns": "List[List[float]]",
        "requires": ["Embeddings Provider"],
        "parameters": [
            {"name": "texts", "type": "array", "description": "List of texts to embed", "required": True},
        ],
    },
    {
        "tool_id": "embeddings/health_check",
        "name": "embeddings_health_check",
        "display_name": "Embeddings Health Check",
        "category": "embeddings",
        "platform_id": "common",
        "service_class": "EmbeddingsProvider",
        "service_module": "app.common.providers.embeddings",
        "service_factory": "get_embeddings_provider",
        "method": "health_check",
        "description": "Check if embeddings provider is healthy and reachable.",
        "returns": "bool",
        "requires": ["Embeddings Provider"],
        "parameters": [],
    },
]

CATEGORIES = ["search", "email", "cache", "rag", "llm", "document", "embeddings"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_tool(tool_id: str) -> Dict[str, Any]:
    """Lookup a tool by ID. Raises KeyError if not found."""
    for tool in TOOL_REGISTRY:
        if tool["tool_id"] == tool_id:
            return tool
    raise KeyError(f"Tool '{tool_id}' not found")


def _serialize_value(value: Any) -> Any:
    """Recursively serialize a value for JSON response.

    Handles Pydantic models, dataclasses (via __dict__), lists, tuples, and dicts.
    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize_value(item) for item in value]
    if hasattr(value, "__dict__"):
        return {
            k: _serialize_value(v)
            for k, v in value.__dict__.items()
            if not k.startswith("_")
        }
    return value


async def execute_tool(tool_def: Dict[str, Any], params: Dict[str, Any]) -> Any:
    """Instantiate the service and call the method with given params."""
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

    # For PDFProcessor, decode base64 content to bytes
    if tool_def["service_class"] == "PDFProcessor" and "content" in params:
        params["content"] = base64.b64decode(params["content"])

    result = method(**params)
    # Await if coroutine
    if asyncio.iscoroutine(result):
        result = await result

    # Convert tuples to lists for JSON serialization (e.g. extract_text returns Tuple)
    if isinstance(result, tuple):
        result = list(result)

    # Serialize result for JSON response
    return _serialize_value(result)


def tool_def_to_input_schema(tool_def: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a tool definition's parameters to a JSON Schema object for MCP inputSchema."""
    properties: Dict[str, Any] = {}
    required: List[str] = []

    for param in tool_def.get("parameters", []):
        prop: Dict[str, Any] = {"type": param["type"]}
        if param.get("description"):
            prop["description"] = param["description"]
        properties[param["name"]] = prop

        if param.get("required", False):
            required.append(param["name"])

    schema: Dict[str, Any] = {
        "type": "object",
        "properties": properties,
    }
    if required:
        schema["required"] = required

    return schema
