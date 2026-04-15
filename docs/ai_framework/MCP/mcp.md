# MCP Server — Model Context Protocol Integration

## Overview

The MCP server exposes all 16 framework tools over the [Model Context Protocol](https://modelcontextprotocol.io/), making them usable by Claude Desktop, Claude Code, and any MCP-compatible client. It reuses the same shared tool registry that powers the REST API (Tools Studio), ensuring zero tool duplication and a single source of truth.

Two transports are supported:
- **stdio** — standalone process for Claude Desktop / Claude Code
- **SSE** — mounted inside the FastAPI application at `/mcp`

## Architecture

```
                      ┌─────────────────────────────┐
                      │  app/common/tools/registry.py│
                      │  (shared, single source)     │
                      │                              │
                      │  TOOL_REGISTRY (16 tools)    │
                      │  execute_tool()              │
                      │  tool_def_to_input_schema()  │
                      └──────────┬──────────────────┘
                                 │
                 ┌───────────────┼───────────────┐
                 ▼                               ▼
    ┌────────────────────────┐     ┌──────────────────────────┐
    │ tools_studio.py        │     │ app/mcp/server.py        │
    │ (FastAPI REST)         │     │ (MCP Protocol)           │
    │                        │     │                          │
    │ GET  /tools            │     │ list_tools → 16 tools    │
    │ GET  /tools/{id}       │     │ call_tool  → execute_tool│
    │ POST /tools/{id}/try   │     │                          │
    │ GET  /categories       │     │ Transports:              │
    └────────────────────────┘     │  - stdio (standalone)    │
                                   │  - SSE (mounted FastAPI) │
                                   └──────────────────────────┘
```

Both the REST endpoints and the MCP server import from the same `app.common.tools.registry` module. Adding a tool to the registry automatically makes it available through both interfaces.

## Shared Tool Registry

Prior to the MCP server, the tool registry (`_TOOL_REGISTRY`) lived inline inside `tools_studio.py`. It was extracted into a dedicated shared module so both consumers can import from a single source.

### Module: `backend/app/common/tools/registry.py`

**Exports:**

| Symbol | Type | Description |
|--------|------|-------------|
| `TOOL_REGISTRY` | `List[Dict[str, Any]]` | All 16 tool definitions with metadata, parameters, and service bindings |
| `CATEGORIES` | `List[str]` | `["search", "email", "cache", "rag", "llm"]` |
| `get_tool(tool_id)` | `function` | Lookup tool by ID. Raises `KeyError` if not found |
| `execute_tool(tool_def, params)` | `async function` | Dynamically imports the service factory, instantiates the service, calls the method, and serializes the result |
| `tool_def_to_input_schema(tool_def)` | `function` | Converts a tool definition's parameters into a JSON Schema `inputSchema` object for MCP |

**`execute_tool` details:**
1. Dynamically imports the service module via `importlib.import_module(tool_def["service_module"])`
2. Calls the factory function (e.g. `get_tavily_service()`) to instantiate the service
3. For `MemoryService` tools, converts the `cache_type` string parameter to the `CacheType` enum automatically
4. Calls the method with `**params`, awaiting if the result is a coroutine
5. Serializes the result: Pydantic models via `model_dump()`, objects via `__dict__`, lists recursively, or raw values

**`tool_def_to_input_schema` conversion:**

Registry parameter format:
```python
{"name": "topic", "type": "string", "description": "Topic to search for", "required": True}
```

Generated MCP `inputSchema`:
```json
{
  "type": "object",
  "properties": {
    "topic": {"type": "string", "description": "Topic to search for"}
  },
  "required": ["topic"]
}
```

Type mapping is 1:1 — `string`, `integer`, `number`, `boolean`, `array`, and `object` map directly to their JSON Schema counterparts. The `required` array is only included when at least one parameter is required.

## MCP Server Implementation

### Module: `backend/app/mcp/server.py`

Uses the low-level `mcp.server.lowlevel.Server` class (not `FastMCP`) because tools are registered dynamically from a data structure rather than via decorators.

**`create_mcp_server()`** — factory that creates and configures the server:

- **`@server.list_tools()`** handler:
  - Iterates all 16 entries in `TOOL_REGISTRY`
  - Returns `mcp.types.Tool` objects with:
    - `name`: tool_id with `/` replaced by `__` (MCP names cannot contain `/`)
    - `description`: multi-line string combining the tool description, `[category] ServiceClass`, return type, and requirements
    - `inputSchema`: JSON Schema from `tool_def_to_input_schema()`

- **`@server.call_tool()`** handler:
  - Decodes MCP name back to tool_id (`__` → `/`)
  - Looks up the tool definition via `get_tool()`
  - Calls `execute_tool()` with a 60-second timeout via `asyncio.wait_for()`
  - Returns a `TextContent` object with the JSON-serialized result
  - On error (timeout, missing tool, execution failure), returns a `TextContent` with `{"error": "..."}` instead of raising

**`run_stdio()`** — runs the server with `mcp.server.stdio.stdio_server` transport:

```python
async def run_stdio() -> None:
    from mcp.server.stdio import stdio_server
    server = create_mcp_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )
```

### Tool Name Encoding

MCP tool names cannot contain `/`. Registry tool IDs use `/` as the category separator.

| Registry tool_id | MCP tool name |
|---|---|
| `search/tavily_search_topic` | `search__tavily_search_topic` |
| `search/tavily_search_topics` | `search__tavily_search_topics` |
| `search/tavily_search_and_filter` | `search__tavily_search_and_filter` |
| `search/tavily_get_trending` | `search__tavily_get_trending` |
| `email/send_email` | `email__send_email` |
| `email/send_batch` | `email__send_batch` |
| `email/check_health` | `email__check_health` |
| `cache/memory_set` | `cache__memory_set` |
| `cache/memory_get` | `cache__memory_get` |
| `cache/memory_delete` | `cache__memory_delete` |
| `rag/store_newsletter` | `rag__store_newsletter` |
| `rag/search_similar` | `rag__search_similar` |
| `llm/generate` | `llm__generate` |
| `llm/chat` | `llm__chat` |
| `llm/list_models` | `llm__list_models` |
| `llm/health_check` | `llm__health_check` |

The encoding is handled by two helper functions:
- `_tool_id_to_mcp_name(tool_id)` — replaces `/` with `__`
- `_mcp_name_to_tool_id(name)` — replaces `__` with `/`

### Entry Point: `backend/app/mcp/__main__.py`

Allows running the MCP server as a Python module:

```python
"""Entry point for running the MCP server via ``python -m app.mcp``."""
import asyncio
from app.mcp.server import run_stdio

if __name__ == "__main__":
    asyncio.run(run_stdio())
```

### SSE Transport: `backend/app/mcp/sse.py`

Wraps the MCP server with `mcp.server.sse.SseServerTransport` inside a Starlette app for mounting in FastAPI.

**`create_mcp_sse_app()`** returns a `Starlette` application with two routes:
- `GET /sse` — SSE stream endpoint (client connects here)
- `POST /messages/` — message endpoint (client sends requests here)

```python
def create_mcp_sse_app() -> Starlette:
    mcp_server = create_mcp_server()
    sse_transport = SseServerTransport("/messages/")

    async def handle_sse(request):
        async with sse_transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await mcp_server.run(
                streams[0],
                streams[1],
                mcp_server.create_initialization_options(),
            )

    return Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse_transport.handle_post_message),
        ],
    )
```

### FastAPI Mount: `backend/app/main.py`

The SSE app is mounted at `/mcp` with a `try/except ImportError` guard for graceful degradation:

```python
# Mount MCP SSE server (graceful degradation if mcp not installed)
try:
    from app.mcp.sse import create_mcp_sse_app

    app.mount("/mcp", create_mcp_sse_app())
    logger.info("MCP SSE server mounted at /mcp")
except ImportError:
    logger.info("MCP package not installed — MCP SSE endpoint disabled")
```

If the `mcp` package is not installed, the FastAPI application starts normally without the MCP endpoints. All existing REST API routes remain unaffected.

## REST API Refactoring

`backend/app/api/v1/endpoints/tools_studio.py` was refactored to import from the shared registry instead of defining tools inline:

**Before:**
```python
_TOOL_REGISTRY: List[Dict[str, Any]] = [...]  # 16 tools inline
_CATEGORIES = ["search", "email", "cache", "rag", "llm"]

def _get_tool(tool_id: str) -> Dict[str, Any]:
    # ... raises HTTPException(404)

async def _execute_tool(tool_def, params) -> Any:
    # ... inline executor
```

**After:**
```python
from app.common.tools.registry import (
    CATEGORIES,
    TOOL_REGISTRY,
    execute_tool,
    get_tool,
)

def _get_tool_or_404(tool_id: str) -> Dict[str, Any]:
    """Lookup a tool by ID, raise 404 if not found."""
    try:
        return get_tool(tool_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_id}' not found",
        )
```

The `_get_tool_or_404()` wrapper translates the registry's `KeyError` into an HTTP 404 response, keeping the HTTP concern in the endpoint layer. All 4 REST endpoints (`GET /tools`, `GET /tools/{id}`, `POST /tools/{id}/try`, `GET /categories`) work exactly as before.

## Dependencies

Added to `backend/pyproject.toml`:

```toml
"mcp>=1.26.0",
```

This brings in the `mcp` package with its `mcp.server.lowlevel.Server`, `mcp.server.stdio`, `mcp.server.sse`, and `mcp.types` modules.

## Files Summary

| # | File | Action | Description |
|---|------|--------|-------------|
| 1 | `backend/app/common/tools/__init__.py` | Created | Empty package init |
| 2 | `backend/app/common/tools/registry.py` | Created | Shared tool registry (16 tools), `execute_tool()`, `get_tool()`, `tool_def_to_input_schema()` |
| 3 | `backend/app/api/v1/endpoints/tools_studio.py` | Modified | Imports from shared registry, replaced `_get_tool()` with `_get_tool_or_404()` wrapper, removed inline `_TOOL_REGISTRY`, `_CATEGORIES`, `_execute_tool()` |
| 4 | `backend/pyproject.toml` | Modified | Added `mcp>=1.26.0` to dependencies |
| 5 | `backend/app/mcp/__init__.py` | Created | Empty package init |
| 6 | `backend/app/mcp/server.py` | Created | MCP server with `list_tools`/`call_tool` handlers and `run_stdio()` |
| 7 | `backend/app/mcp/__main__.py` | Created | `python -m app.mcp` entry point |
| 8 | `backend/app/mcp/sse.py` | Created | SSE transport wrapper creating a Starlette app with `/sse` and `/messages/` routes |
| 9 | `backend/app/main.py` | Modified | Mounts MCP SSE app at `/mcp` with `ImportError` guard |

## How to Run

### Stdio Transport (Claude Desktop / Claude Code)

```bash
cd backend
python -m app.mcp
```

Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "agentic-ai-framework": {
      "command": "python",
      "args": ["-m", "app.mcp"],
      "cwd": "/path/to/agentic-ai-framework/backend"
    }
  }
}
```

Claude Code configuration (`.mcp.json` in project root):

```json
{
  "mcpServers": {
    "agentic-ai-framework": {
      "command": "python",
      "args": ["-m", "app.mcp"],
      "cwd": "./backend"
    }
  }
}
```

### SSE Transport (Embedded in FastAPI)

```bash
cd backend
uvicorn app.main:app --reload
```

MCP SSE endpoint available at:
- SSE stream: `http://localhost:8000/mcp/sse`
- Messages: `http://localhost:8000/mcp/messages/`

## Design Decisions

1. **Low-level Server, not FastMCP** — The `mcp.server.lowlevel.Server` class was chosen over the higher-level `FastMCP` because tools are registered dynamically from a data structure. `FastMCP`'s decorator-based approach would require writing 16 individual wrapper functions, defeating the purpose of a data-driven registry.

2. **Shared registry extraction** — Moving the registry from `tools_studio.py` to `app.common.tools.registry` ensures both REST and MCP surfaces serve identical tool definitions. Adding a tool to `TOOL_REGISTRY` automatically exposes it through both interfaces.

3. **`KeyError` vs `HTTPException`** — The shared `get_tool()` raises `KeyError` (a Python-native exception) rather than `HTTPException` (a FastAPI-specific exception). Each consumer handles it appropriately: the REST layer wraps it in `_get_tool_or_404()`, and the MCP layer returns a JSON error in `TextContent`.

4. **Name encoding (`/` → `__`)** — MCP tool names cannot contain `/`, but registry tool IDs use `/` as the category separator (e.g. `search/tavily_search_topic`). The double-underscore encoding is reversible and avoids collisions since no tool name contains `__`.

5. **Graceful degradation** — The `mcp` package is a required dependency in `pyproject.toml`, but the FastAPI mount uses `try/except ImportError` so the application can still start if the package is missing (e.g. in minimal deployments).

6. **60-second timeout** — Both `call_tool` (MCP) and `try_tool` (REST) enforce a 60-second timeout via `asyncio.wait_for()`, providing consistent execution limits across both interfaces.

7. **Error handling in MCP** — Errors are returned as `TextContent` with `{"error": "..."}` JSON rather than raising exceptions. This follows MCP conventions where tool results are always content objects, and allows the LLM client to see and reason about errors.

## Verification

### 1. REST API Regression

```bash
# All 16 tools still returned
curl http://localhost:8000/api/v1/tools-studio/tools | jq '.total'
# -> 16

# Category filter still works
curl http://localhost:8000/api/v1/tools-studio/tools?category=search | jq '.total'
# -> 4

# Tool detail still works
curl http://localhost:8000/api/v1/tools-studio/tools/llm/health_check | jq '.tool_id'
# -> "llm/health_check"

# Categories endpoint still works
curl http://localhost:8000/api/v1/tools-studio/categories | jq '.'
# -> 5 categories with counts
```

### 2. MCP Tool Count

```python
from app.common.tools.registry import TOOL_REGISTRY
assert len(TOOL_REGISTRY) == 16
```

### 3. MCP Tool Name Encoding

```python
from app.mcp.server import _tool_id_to_mcp_name, _mcp_name_to_tool_id
from app.common.tools.registry import TOOL_REGISTRY

for tool in TOOL_REGISTRY:
    mcp_name = _tool_id_to_mcp_name(tool["tool_id"])
    assert "/" not in mcp_name              # no slashes in MCP names
    assert _mcp_name_to_tool_id(mcp_name) == tool["tool_id"]  # roundtrip
```

### 4. Input Schemas

```python
from app.common.tools.registry import get_tool, tool_def_to_input_schema

schema = tool_def_to_input_schema(get_tool("search/tavily_search_topic"))
assert schema["type"] == "object"
assert "topic" in schema["properties"]
assert "topic" in schema["required"]
```

### 5. SSE Connectivity

```bash
# Opens an SSE stream (Ctrl+C to close)
curl -N http://localhost:8000/mcp/sse
```

### 6. Graceful Degradation

If the `mcp` package is not installed, the FastAPI app starts normally with this log message:
```
MCP package not installed -- MCP SSE endpoint disabled
```

All REST endpoints continue to function.

## Tool Inventory (16 tools)

| # | MCP Tool Name | Category | Service Class | Description |
|---|---------------|----------|---------------|-------------|
| 1 | `search__tavily_search_topic` | search | TavilySearchService | Search for articles on a single topic |
| 2 | `search__tavily_search_topics` | search | TavilySearchService | Search multiple topics in parallel |
| 3 | `search__tavily_search_and_filter` | search | TavilySearchService | Full pipeline: search + quality filter + dedup |
| 4 | `search__tavily_get_trending` | search | TavilySearchService | Get trending content for topics |
| 5 | `email__send_email` | email | EmailService | Send a single email via Resend API |
| 6 | `email__send_batch` | email | EmailService | Send batch emails to multiple recipients |
| 7 | `email__check_health` | email | EmailService | Check email service health and configuration |
| 8 | `cache__memory_set` | cache | MemoryService | Store value in MongoDB cache with TTL |
| 9 | `cache__memory_get` | cache | MemoryService | Retrieve value from MongoDB cache |
| 10 | `cache__memory_delete` | cache | MemoryService | Delete a cache entry |
| 11 | `rag__store_newsletter` | rag | NewsletterRAGService | Store newsletter in Weaviate vector DB |
| 12 | `rag__search_similar` | rag | NewsletterRAGService | Search similar newsletters by vector similarity |
| 13 | `llm__generate` | llm | LLMProvider | Generate text completion with configured LLM |
| 14 | `llm__chat` | llm | LLMProvider | Chat with configured LLM using message history |
| 15 | `llm__list_models` | llm | LLMProvider | List available models for current provider |
| 16 | `llm__health_check` | llm | LLMProvider | Check if LLM provider is healthy and reachable |
