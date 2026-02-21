# Tools Studio — Phase 1: Tool Registry, Catalog & Inspector

## Overview

Phase 1 replaces the empty Tools page with a discovery-based **Tools Studio** that mirrors the Agent Studio pattern. It registers all 16 framework tools in a static backend registry, serves them through 4 REST endpoints, and renders a catalog grid with category filtering and a full-page inspector with schema display and live "Try It" execution.

## Architecture

```
Backend                                 Frontend
┌──────────────────────────┐           ┌──────────────────────────────┐
│  _TOOL_REGISTRY (16)     │           │  /tools          ToolsPage  │
│  ┌────────────────────┐  │  REST     │  ┌─────────────────────┐    │
│  │ search (4 tools)   │──┼──────────>│  │ CategoryFilter      │    │
│  │ email  (3 tools)   │  │           │  │ ToolStudioCard grid │    │
│  │ cache  (3 tools)   │  │           │  └─────────────────────┘    │
│  │ rag    (2 tools)   │  │           │                              │
│  │ llm    (4 tools)   │  │           │  /tools/:toolId              │
│  └────────────────────┘  │           │  ┌─────────────────────┐    │
│                          │           │  │ ToolInspectorPage   │    │
│  4 endpoints:            │           │  │ - Schema tab        │    │
│  GET  /tools             │           │  │ - Try It tab        │    │
│  GET  /tools/{id}        │           │  │ - Info tab          │    │
│  POST /tools/{id}/try    │           │  └─────────────────────┘    │
│  GET  /categories        │           │                              │
└──────────────────────────┘           └──────────────────────────────┘
```

## Tool Inventory (16 tools)

| # | Tool ID | Category | Service Class | Method | Description |
|---|---------|----------|---------------|--------|-------------|
| 1 | `search/tavily_search_topic` | search | TavilySearchService | `search_topic` | Search for articles on a single topic |
| 2 | `search/tavily_search_topics` | search | TavilySearchService | `search_topics` | Search multiple topics in parallel |
| 3 | `search/tavily_search_and_filter` | search | TavilySearchService | `search_and_filter` | Full pipeline: search + quality filter + dedup |
| 4 | `search/tavily_get_trending` | search | TavilySearchService | `get_trending` | Get trending content for topics |
| 5 | `email/send_email` | email | EmailService | `send_email` | Send a single email via Resend API |
| 6 | `email/send_batch` | email | EmailService | `send_batch` | Send batch emails to multiple recipients |
| 7 | `email/check_health` | email | EmailService | `check_health` | Check email service health and configuration |
| 8 | `cache/memory_set` | cache | MemoryService | `set` | Store value in MongoDB cache with TTL |
| 9 | `cache/memory_get` | cache | MemoryService | `get` | Retrieve value from MongoDB cache |
| 10 | `cache/memory_delete` | cache | MemoryService | `delete` | Delete a cache entry |
| 11 | `rag/store_newsletter` | rag | NewsletterRAGService | `store_newsletter` | Store newsletter in Weaviate vector DB |
| 12 | `rag/search_similar` | rag | NewsletterRAGService | `search_similar` | Search similar newsletters by vector similarity |
| 13 | `llm/generate` | llm | LLMProvider | `generate` | Generate text completion with configured LLM |
| 14 | `llm/chat` | llm | LLMProvider | `chat` | Chat with configured LLM using message history |
| 15 | `llm/list_models` | llm | LLMProvider | `list_models` | List available models for current provider |
| 16 | `llm/health_check` | llm | LLMProvider | `health_check` | Check if LLM provider is healthy and reachable |

## API Endpoints

All endpoints are mounted at `/api/v1/tools-studio`.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/tools` | List all tools. Optional `?category=` filter (search, email, cache, rag, llm) |
| `GET` | `/tools/{tool_id:path}` | Get tool detail by ID (e.g. `search/tavily_search_topic`) |
| `POST` | `/tools/{tool_id:path}/try` | Execute tool with `{"parameters": {...}}` body. 60s timeout |
| `GET` | `/categories` | List categories with tool counts |

## Files Changed

### Backend (3 files)

| # | File | Action |
|---|------|--------|
| 1 | `backend/app/schemas/tool.py` | Modified — Added 6 schemas: `ToolStudioParameter`, `ToolStudioSummary`, `ToolStudioDetail`, `ToolStudioListResponse`, `ToolStudioTryRequest`, `ToolStudioTryResponse` |
| 2 | `backend/app/api/v1/endpoints/tools_studio.py` | Created — Static `_TOOL_REGISTRY` (16 tools) + 4 endpoints + `_execute_tool` service runner |
| 3 | `backend/app/api/v1/router.py` | Modified — Mounted `tools_studio.router` at prefix `/tools-studio` |

### Frontend (10 files)

| # | File | Action |
|---|------|--------|
| 4 | `frontend/src/types/tool.ts` | Modified — Added 7 interfaces: `ToolStudioParameter`, `ToolStudioSummary`, `ToolStudioDetail`, `ToolStudioListResponse`, `ToolStudioTryRequest`, `ToolStudioTryResponse`, `ToolStudioCategory` |
| 5 | `frontend/src/api/toolsStudio.ts` | Created — 4 API methods: `listTools`, `getTool`, `tryTool`, `listCategories` |
| 6 | `frontend/src/hooks/useToolsStudio.ts` | Created — 4 React Query hooks: `useToolsStudioList`, `useToolsStudioDetail`, `useToolsStudioCategories` (queries) + `useTryTool` (mutation) |
| 7 | `frontend/src/utils/constants.ts` | Modified — Added `TOOLS_INSPECTOR: '/tools/:toolId'` route constant |
| 8 | `frontend/src/App.tsx` | Modified — Added `ToolInspectorPage` import and route at `ROUTES.TOOLS_INSPECTOR` |
| 9 | `frontend/src/components/layout/Sidebar.tsx` | Modified — Renamed sidebar entry from "Tools" to "Tools Studio" |
| 10 | `frontend/src/pages/ToolsPage.tsx` | Modified — Replaced `<ToolList />` with Tools Studio layout: header, `CategoryFilter`, responsive card grid |
| 11 | `frontend/src/pages/ToolInspectorPage.tsx` | Created — Full-page inspector with 3 tabs: Schema (parameter table, return type, requirements), Try It (form inputs + execution output), Info (metadata grid) |
| 12 | `frontend/src/components/tools-studio/ToolStudioCard.tsx` | Created — Card component: display name, category/platform badges, description, parameter count, service class, status indicator |
| 13 | `frontend/src/components/tools-studio/CategoryFilter.tsx` | Created — Tabs-based filter: All + one tab per category, each with tool count badge |

## Design Decisions

1. **Static registry** — `_TOOL_REGISTRY` is a plain list of dicts in the endpoint file (mirrors `_AGENT_FACTORIES` pattern). No database required. Adding a tool means adding a dict entry.

2. **Service-backed execution** — Each registry entry maps `service_module` + `service_factory` + `method`. The `_execute_tool` helper dynamically imports the factory, instantiates the service, and calls the method. Results are serialized (Pydantic `model_dump()`, `__dict__`, or raw return).

3. **CacheType enum handling** — MemoryService methods require a `CacheType` enum. The executor automatically converts the string parameter to the enum before calling the method.

4. **Tool ID encoding** — Tool IDs use `/` (e.g. `search/tavily_search_topic`). In frontend URLs, `/` is replaced with `--` for routing safety. The inspector page decodes `--` back to `/` before API calls.

5. **Route coexistence** — The new `TOOLS_INSPECTOR` route (`/tools/:toolId`) is added alongside the existing `TOOL_DETAIL` route (`/tools/:id`). The `--` encoding in tool IDs prevents conflicts.

6. **Tool #7 change** — The plan specified `email/get_delivery_status`, but `EmailService` has no `get_delivery_status` method. Replaced with `email/check_health` using the existing `check_health` method.

## Verification

```bash
# Backend
curl http://localhost:8000/api/v1/tools-studio/tools              # 16 tools
curl http://localhost:8000/api/v1/tools-studio/tools?category=search  # 4 search tools
curl http://localhost:8000/api/v1/tools-studio/tools/llm/list_models  # detail with params
curl -X POST http://localhost:8000/api/v1/tools-studio/tools/llm/health_check/try \
  -H 'Content-Type: application/json' -d '{"parameters":{}}'     # execute
curl http://localhost:8000/api/v1/tools-studio/categories         # 5 categories

# Frontend
cd frontend && npx tsc --noEmit   # zero new type errors
# Navigate to /tools              # catalog with category tabs + 16 cards
# Click a card                    # inspector with Schema / Try It / Info tabs
```
