# Phase 9: Hello World API Routes

## Goal
Expose the hello_world platform functionality via REST API endpoints with proper request/response schemas.

---

## Copilot Prompt

```
You are helping implement FastAPI routes for the hello_world platform in a multi-agent AI framework.

### Context
- Routes expose platform functionality via REST API
- Must use Pydantic schemas for request/response validation
- Should integrate with OpenAPI documentation
- Follows existing API patterns in the project

### Files to Read First
Read these files to understand existing patterns:
- backend/app/platforms/hello_world/services/hello_world.py (service layer)
- backend/app/api/v1/ (existing API routes)
- backend/app/main.py (app configuration)
- backend/app/platforms/hello_world/router.py (if exists)

### Implementation Tasks

1. **Create `backend/app/platforms/hello_world/schemas/greeting.py`:**
   ```python
   from pydantic import BaseModel, Field
   from typing import Optional, Literal
   from datetime import datetime

   class GreetingRequest(BaseModel):
       """Request schema for greeting generation."""
       name: str = Field(
           ...,
           min_length=1,
           max_length=100,
           description="The name to greet",
           examples=["Alice", "Bob"],
       )
       style: Literal["friendly", "formal", "casual", "enthusiastic"] = Field(
           default="friendly",
           description="The greeting style",
       )

       model_config = {
           "json_schema_extra": {
               "examples": [
                   {"name": "Alice", "style": "friendly"},
                   {"name": "Bob", "style": "formal"},
               ]
           }
       }

   class GreetingResponse(BaseModel):
       """Response schema for greeting generation."""
       success: bool
       greeting: str
       style: str
       used_fallback: bool = False
       timestamp: datetime
       error: Optional[str] = None

       model_config = {
           "json_encoders": {datetime: lambda v: v.isoformat()},
       }

   class PlatformStatus(BaseModel):
       """Platform status response."""
       platform: str
       status: str
       agents: list[str]
       timestamp: datetime

   class AgentInfo(BaseModel):
       """Agent information."""
       name: str
       description: str
       styles: list[str]

   class HealthResponse(BaseModel):
       """Health check response."""
       status: str
       platform: str
       llm_available: bool
       details: Optional[dict] = None

   class ConfigResponse(BaseModel):
       """Configuration response."""
       provider: str
       model: str
       temperature: float
   ```

2. **Create `backend/app/platforms/hello_world/schemas/__init__.py`:**
   ```python
   from .greeting import (
       GreetingRequest,
       GreetingResponse,
       PlatformStatus,
       AgentInfo,
       HealthResponse,
       ConfigResponse,
   )

   __all__ = [
       "GreetingRequest",
       "GreetingResponse",
       "PlatformStatus",
       "AgentInfo",
       "HealthResponse",
       "ConfigResponse",
   ]
   ```

3. **Create/Update `backend/app/platforms/hello_world/router.py`:**
   ```python
   from fastapi import APIRouter, HTTPException, status
   from typing import List
   import logging

   from .services import get_hello_world_service
   from .schemas import (
       GreetingRequest,
       GreetingResponse,
       PlatformStatus,
       AgentInfo,
       HealthResponse,
       ConfigResponse,
   )
   from .config import config
   from .agents.greeter import get_greeter_llm

   logger = logging.getLogger(__name__)

   router = APIRouter(
       prefix="/platforms/hello-world",
       tags=["Hello World"],
   )

   @router.post(
       "/execute",
       response_model=GreetingResponse,
       summary="Generate a greeting",
       description="Generate a personalized greeting using the specified style.",
   )
   async def execute_greeting(request: GreetingRequest) -> GreetingResponse:
       """Generate a personalized greeting."""
       service = get_hello_world_service()
       result = await service.generate_greeting(
           name=request.name,
           style=request.style,
       )
       return GreetingResponse(**result)

   @router.get(
       "/status",
       response_model=PlatformStatus,
       summary="Get platform status",
   )
   async def get_status() -> PlatformStatus:
       """Get the current status of the Hello World platform."""
       service = get_hello_world_service()
       result = await service.get_status()
       return PlatformStatus(**result)

   @router.get(
       "/agents",
       response_model=List[AgentInfo],
       summary="List available agents",
   )
   async def list_agents() -> List[AgentInfo]:
       """List all agents available in the Hello World platform."""
       service = get_hello_world_service()
       agents = await service.list_agents()
       return [AgentInfo(**agent) for agent in agents]

   @router.get(
       "/health",
       response_model=HealthResponse,
       summary="Health check",
   )
   async def health_check() -> HealthResponse:
       """Check the health of the platform and its dependencies."""
       try:
           llm = get_greeter_llm()
           llm_available = await llm.health_check()
       except Exception as e:
           logger.warning(f"LLM health check failed: {e}")
           llm_available = False

       return HealthResponse(
           status="healthy" if llm_available else "degraded",
           platform="hello_world",
           llm_available=llm_available,
           details={"provider": config.effective_provider},
       )

   @router.get(
       "/config",
       response_model=ConfigResponse,
       summary="Get LLM configuration",
   )
   async def get_config() -> ConfigResponse:
       """Get the current LLM configuration for this platform."""
       return ConfigResponse(
           provider=config.effective_provider,
           model=config.effective_model,
           temperature=0.7,
       )
   ```

4. **Update `backend/app/main.py` to include the router:**
   ```python
   from app.platforms.hello_world.router import router as hello_world_router

   # In the app setup section:
   app.include_router(hello_world_router, prefix="/api/v1")
   ```

5. **Write unit tests in `backend/app/platforms/hello_world/tests/test_hello_world_api.py`:**
   ```python
   import pytest
   from fastapi.testclient import TestClient
   from unittest.mock import patch, AsyncMock

   # Test POST /execute
   # - Valid request returns greeting
   # - Invalid style returns validation error
   # - Empty name returns validation error
   # - Service error returns appropriate response

   # Test GET /status
   # - Returns platform status

   # Test GET /agents
   # - Returns list of agents

   # Test GET /health
   # - Returns health status
   # - Handles LLM unavailable gracefully

   # Test GET /config
   # - Returns configuration
   ```

### Expected Code Style
- Use Pydantic v2 model_config (NOT class Config)
- Add OpenAPI examples and descriptions
- Use appropriate HTTP status codes
- Add logging for requests
- Follow existing API patterns

### Output
After implementing, provide:
1. Summary of files changed
2. Test command: `cd backend && .venv/bin/python -m pytest app/platforms/hello_world/tests/test_hello_world_api.py -v`
3. OpenAPI documentation URL: http://localhost:8000/api/v1/docs
```

---

## Plan Template

Before making changes, Copilot should propose:

1. **Files to modify/create:**
   - [ ] `backend/app/platforms/hello_world/schemas/__init__.py`
   - [ ] `backend/app/platforms/hello_world/schemas/greeting.py`
   - [ ] `backend/app/platforms/hello_world/router.py`
   - [ ] `backend/app/main.py` (add router)
   - [ ] `backend/app/platforms/hello_world/tests/test_hello_world_api.py`

2. **High-level steps:**
   - Step 1: ...
   - Step 2: ...

---

## Documentation Template

After changes are complete, provide text for `docs/implementation-log.md`:

```markdown
## Phase 9: Hello World API Routes

### Summary of Changes
- `backend/app/platforms/hello_world/schemas/greeting.py`: Request/response schemas
- `backend/app/platforms/hello_world/router.py`: FastAPI router with 5 endpoints

### API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/platforms/hello-world/execute | Generate greeting |
| GET | /api/v1/platforms/hello-world/status | Platform status |
| GET | /api/v1/platforms/hello-world/agents | List agents |
| GET | /api/v1/platforms/hello-world/health | Health check |
| GET | /api/v1/platforms/hello-world/config | LLM config |

### Tests Executed
```bash
cd backend && .venv/bin/python -m pytest app/platforms/hello_world/tests/test_hello_world_api.py -v
```
**Results:** [PASS/FAIL with details]

### Fixes Applied
- [Any issues encountered and how they were resolved]
```

---

## Earlier Mocks to Upgrade
- Uses HelloWorldService from Phase 8 (mocked in API tests)

**Note:** In Phase 18, integration tests will call real service.

---

## Human Checklist
- [ ] Review Copilot's proposed plan before accepting
- [ ] Verify OpenAPI documentation is correct
- [ ] Run tests and confirm they pass
- [ ] Test API manually:
  ```bash
  curl -X POST http://localhost:8000/api/v1/platforms/hello-world/execute \
    -H "Content-Type: application/json" \
    -d '{"name": "Alice", "style": "friendly"}'
  ```
