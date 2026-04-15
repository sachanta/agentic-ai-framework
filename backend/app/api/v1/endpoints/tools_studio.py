"""
Tools Studio endpoints — Discover and execute framework tools.

Provides a static registry of all 16 framework tools (search, email, cache,
RAG, LLM) with metadata, parameter schemas, and live execution via the
underlying service classes.
"""
import asyncio
import logging
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, status

from app.common.tools.registry import (
    CATEGORIES,
    TOOL_REGISTRY,
    execute_tool,
    get_tool,
)
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
# Helpers
# ---------------------------------------------------------------------------


def _get_tool_or_404(tool_id: str) -> Dict[str, Any]:
    """Lookup a tool by ID, raise 404 if not found."""
    try:
        return get_tool(tool_id)
    except KeyError:
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
    tools = TOOL_REGISTRY
    if category:
        if category not in CATEGORIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category '{category}'. Valid: {CATEGORIES}",
            )
        tools = [t for t in tools if t["category"] == category]

    summaries = [_build_summary(t) for t in tools]
    return ToolStudioListResponse(
        tools=summaries,
        total=len(summaries),
        categories=CATEGORIES,
    )


@router.get("/tools/{tool_id:path}", response_model=ToolStudioDetail)
async def get_tool_detail(tool_id: str):
    """Get full detail for a single tool by ID (e.g. search/tavily_search_topic)."""
    tool = _get_tool_or_404(tool_id)
    return _build_detail(tool)


@router.post("/tools/{tool_id:path}/try", response_model=ToolStudioTryResponse)
async def try_tool(tool_id: str, request: ToolStudioTryRequest):
    """
    Execute a tool with the provided parameters.

    Times out after 60 seconds.
    """
    tool_def = _get_tool_or_404(tool_id)

    start = time.perf_counter()
    try:
        result = await asyncio.wait_for(
            execute_tool(tool_def, request.parameters),
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
    for t in TOOL_REGISTRY:
        cat = t["category"]
        counts[cat] = counts.get(cat, 0) + 1

    return [
        {"name": cat, "count": counts.get(cat, 0)}
        for cat in CATEGORIES
    ]
