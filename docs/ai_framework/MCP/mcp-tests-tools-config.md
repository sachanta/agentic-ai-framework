# MCP Integration: Tests, New Tools & .mcp.json

Summary of changes made to add test coverage, expand the tool registry, and enable Claude Code auto-discovery.

---

## 1. `.mcp.json` — Claude Code Auto-Discovery

**File created:** `/.mcp.json` (project root)

Enables Claude Code to automatically detect and connect to the MCP server when working in this repository.

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

---

## 2. Tool Registry Expansion

**File modified:** `backend/app/common/tools/registry.py`

### 2a. New Import

Added `import base64` for PDF content decoding.

### 2b. 3 Document Tools (PDFProcessor)

| Tool ID | Method | Description |
|---------|--------|-------------|
| `document/pdf_extract_text` | `PDFProcessor.extract_text` | Extract text from base64-encoded PDF. Returns `(text, page_count)`. |
| `document/pdf_chunk_text` | `PDFProcessor.chunk_text` | Split text into overlapping chunks for RAG ingestion. |
| `document/pdf_process` | `PDFProcessor.process` | Full extract + chunk pipeline on base64-encoded PDF. |

- Service module: `app.services.pdf_processor`
- Factory: `get_pdf_processor()`
- MCP callers pass PDF content as a base64-encoded string; `execute_tool` decodes it to `bytes` before calling the service.

### 2c. 3 Embeddings Tools (EmbeddingsProvider)

| Tool ID | Method | Description |
|---------|--------|-------------|
| `embeddings/embed_text` | `EmbeddingsProvider.embed_text` | Embed a single text string. |
| `embeddings/embed_texts` | `EmbeddingsProvider.embed_texts` | Embed multiple texts in batch. |
| `embeddings/health_check` | `EmbeddingsProvider.health_check` | Check embeddings provider health. |

- Service module: `app.common.providers.embeddings`
- Factory: `get_embeddings_provider()`

### 2d. Updated Categories

```python
# Before
CATEGORIES = ["search", "email", "cache", "rag", "llm"]

# After
CATEGORIES = ["search", "email", "cache", "rag", "llm", "document", "embeddings"]
```

**Totals:** 16 → 22 tools, 5 → 7 categories.

### 2e. `_serialize_value()` Helper

Added a recursive serialization helper that handles:
- Primitives (`None`, `str`, `int`, `float`, `bool`) — returned as-is
- Pydantic models — calls `model_dump()`
- Dicts — recursively serializes values
- Lists and tuples — recursively serializes elements (tuples become lists)
- Dataclasses / objects with `__dict__` — recursively serializes attributes

This replaces the previous flat serialization logic in `execute_tool`, fixing nested dataclass serialization (e.g., `PDFProcessingResult` containing `List[TextChunk]`).

### 2f. `execute_tool()` Updates

Two new special cases added before method invocation:

1. **Base64 decode for PDFProcessor:** When `service_class == "PDFProcessor"` and `content` is in params, the base64 string is decoded to `bytes` via `base64.b64decode()`.
2. **Tuple handling:** After execution, if the result is a `tuple` (e.g., `extract_text` returns `Tuple[str, int]`), it is converted to a `list` for JSON serialization.

The serialization section now delegates entirely to `_serialize_value()`.

---

## 3. MCP Test Suite

**Directory created:** `backend/tests/mcp/`

All tests use `@pytest.mark.mcp` and mock external services via `unittest.mock` to avoid requiring live infrastructure.

### 3a. `conftest.py`

- Registers the `mcp` pytest marker
- Provides a `sample_tool_def` fixture — a minimal tool definition for isolated testing

### 3b. `test_registry.py` — 27 tests

| Test Class | Count | What It Validates |
|------------|-------|-------------------|
| `TestToolRegistryStructure` | 8 | Registry non-empty, required fields present, unique IDs, category/name format, all categories used, parameter fields, exact tool count (22), exact category count (7) |
| `TestGetTool` | 3 | Existing tool lookup, `KeyError` on missing, correct structure returned |
| `TestToolDefToInputSchema` | 4 | Basic schema generation, required/optional field separation, empty params, property type mapping |
| `TestSerializeValue` | 5 | Primitives, Pydantic models, nested dataclasses, tuples, recursive dicts |
| `TestExecuteTool` | 7 | Service method invocation, param passing, Pydantic serialization, dataclass serialization, MemoryService `cache_type` enum conversion, PDFProcessor base64 decode, tuple-to-list conversion |
| `TestDocumentTools` | 4 | Category exists, all 3 tool IDs registered, base64 documented in param description, execute decodes base64 |
| `TestEmbeddingsTools` | 2 | Category exists, all 3 tool IDs registered |

**Mock pattern:** `importlib.import_module` is patched to return a mock module whose factory returns a mock service. For `MemoryService` tests, the `CacheType` enum module is injected via `sys.modules` to avoid triggering heavy import chains.

### 3c. `test_server.py` — 11 tests

| Test Class | Count | What It Validates |
|------------|-------|-------------------|
| `TestNameEncoding` | 4 | Slash→double-underscore encoding, reverse decoding, roundtrip for all 22 tools, no slashes in any MCP name |
| `TestCreateMcpServer` | 1 | Returns an `mcp.server.lowlevel.Server` instance |
| `TestListToolsHandler` | 3 | Returns all tools, names are encoded, every tool has an `inputSchema` with `type: "object"` |
| `TestCallToolHandler` | 4 | Successful call returns JSON result, unknown tool returns error JSON, timeout returns error, exception returns error |

**Handler invocation pattern:**
```python
server = create_mcp_server()
handler = server.request_handlers[types.ListToolsRequest]
result = await handler(types.ListToolsRequest(method="tools/list"))
tools = result.root.tools
```

### 3d. `test_sse.py` — 3 tests

| Test Class | Count | What It Validates |
|------------|-------|-------------------|
| `TestCreateMcpSseApp` | 3 | Returns a `Starlette` instance, has `/sse` route, has `/messages` mount |

### Test Execution

```bash
cd backend
.venv/bin/python -m pytest tests/mcp/ -v
# 48 passed in ~0.2s
```

---

## Verification Commands

```bash
cd backend

# Tool count
.venv/bin/python -c "from app.common.tools.registry import TOOL_REGISTRY, CATEGORIES; print(f'{len(TOOL_REGISTRY)} tools, {len(CATEGORIES)} categories')"
# → 22 tools, 7 categories

# MCP server tool count
.venv/bin/python -c "
import asyncio, mcp.types as types
from app.mcp.server import create_mcp_server
async def check():
    s = create_mcp_server()
    r = await s.request_handlers[types.ListToolsRequest](types.ListToolsRequest(method='tools/list'))
    print(f'{len(r.root.tools)} MCP tools')
asyncio.run(check())
"
# → 22 MCP tools

# Validate .mcp.json
python3 -c "import json; json.load(open('.mcp.json')); print('OK')"
# → OK
```

---

## Files Changed

| File | Action |
|------|--------|
| `.mcp.json` | Created |
| `backend/app/common/tools/registry.py` | Modified — 6 new tools, `_serialize_value()`, `execute_tool` updates |
| `backend/tests/mcp/__init__.py` | Created (empty) |
| `backend/tests/mcp/conftest.py` | Created — fixtures and markers |
| `backend/tests/mcp/test_registry.py` | Created — 27 tests |
| `backend/tests/mcp/test_server.py` | Created — 11 tests |
| `backend/tests/mcp/test_sse.py` | Created — 3 tests |
