# Phase 1: Agent Registry & Catalog

Agent Studio's foundation — a centralized, read-only catalog that automatically discovers and displays every agent across all platforms with rich metadata.

---

## Overview

Before Agent Studio, agent information was scattered across hardcoded platform `/agents` endpoints that returned minimal data (name, description, status). There was no single place to see all agents, their LLM configurations, system prompts, tools, or which platform they belong to. The existing `/agents` page used stubbed CRUD endpoints that returned empty results.

Agent Studio introduces a new `/studio` route with a dedicated backend that **discovers agents at runtime** by introspecting the `PlatformRegistry` and `BaseAgent` instances. No database required — all metadata is extracted from live Python objects.

---

## Architecture

### Data Flow

```
PlatformRegistry                    Studio API                    Frontend
┌─────────────┐                  ┌──────────────┐             ┌──────────────┐
│ list_all()   │─── platforms ──►│ /studio/     │── JSON ────►│ StudioPage   │
│              │                 │  agents      │             │              │
│ create_      │─── orchestrator─►│              │             │ PlatformFilter│
│ orchestrator │                 │ _discover_   │             │ AgentCatalog │
│              │                 │  agent()     │             │ DetailDrawer │
└─────────────┘                 └──────────────┘             └──────────────┘
       │                              │
       ▼                              ▼
 BaseOrchestrator              Agent Factory
 .get_agent(name)              _AGENT_FACTORIES
 (HelloWorld)                  (Newsletter)
```

### Two-Pass Agent Discovery

The framework has two incompatible agent registration patterns:

| Platform | Pattern | Why |
|----------|---------|-----|
| Hello World | `orchestrator.register_agent(greeter)` in `_setup_agents()` | Simple orchestrator, agents are direct attributes |
| Newsletter | LangGraph nodes call agents internally | Orchestrator uses `graph.ainvoke()`, never calls `register_agent()` |

The Studio endpoint uses a **two-pass discovery strategy**:

1. **Pass 1 — Orchestrator**: Call `registry.create_orchestrator(platform_id)`, then `orchestrator.get_agent(name)`. Works for HelloWorld.
2. **Pass 2 — Agent Factory**: If Pass 1 returns `None`, look up `(platform_id, agent_name)` in a static `_AGENT_FACTORIES` dict that maps to import paths. Dynamically import and instantiate the agent class. Works for Newsletter.

```python
_AGENT_FACTORIES = {
    ("newsletter", "research"):      "app.platforms.newsletter.agents:ResearchAgent",
    ("newsletter", "writing"):       "app.platforms.newsletter.agents:WritingAgent",
    ("newsletter", "preference"):    "app.platforms.newsletter.agents:PreferenceAgent",
    ("newsletter", "custom_prompt"): "app.platforms.newsletter.agents:CustomPromptAgent",
}
```

Agents that fail to instantiate (e.g., `mindmap` is listed in the registry but has no implementation) are skipped with a warning log. The endpoint returns only successfully discovered agents.

### LLM Config Extraction

Extracting the LLM provider/model from an agent is non-trivial because `BaseAgent.llm` is a lazy property — accessing it triggers LLM initialization which may fail if no server is running.

The `_extract_llm_config()` helper reads from safe attributes only:

1. `agent.model`, `agent.temperature`, `agent.max_tokens` — always available from `BaseAgent.__init__`
2. `agent._llm_config` — a dict stored by agents that follow the platform convention (GreeterAgent, ResearchAgent, WritingAgent)
3. `agent._llm` — only if already initialized (never triggers lazy init)

```python
def _extract_llm_config(agent: BaseAgent) -> StudioLLMConfig:
    config = StudioLLMConfig(
        model=agent.model,
        temperature=agent.temperature,
        max_tokens=agent.max_tokens,
    )
    if hasattr(agent, "_llm_config") and isinstance(agent._llm_config, dict):
        config.provider = agent._llm_config.get("provider")
        if not config.model:
            config.model = agent._llm_config.get("model")
    elif agent._llm is not None:
        config.provider = getattr(agent._llm, "provider_name", None)
    return config
```

---

## API Endpoints

All endpoints are registered under `/api/v1/studio/`.

### GET /studio/agents

Discover all agents across all platforms.

**Query Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `platform_id` | string | No | Filter to a single platform (e.g., `newsletter`) |

**Response:** `StudioAgentsListResponse`

```json
{
  "agents": [
    {
      "agent_id": "hello-world/greeter",
      "name": "greeter",
      "display_name": "Greeter Agent",
      "platform_id": "hello-world",
      "platform_name": "Hello World",
      "description": "Generates personalized greetings based on name and style",
      "llm_config": {
        "provider": "gemini",
        "model": "gemini-2.0-flash",
        "temperature": 0.7,
        "max_tokens": 150
      },
      "tool_count": 0,
      "has_system_prompt": false,
      "agent_class": "GreeterAgent",
      "status": "discovered"
    },
    {
      "agent_id": "newsletter/research",
      "name": "research",
      "display_name": "Research Agent",
      "platform_id": "newsletter",
      "platform_name": "Newsletter",
      "description": "Content discovery and research agent for newsletters",
      "llm_config": {
        "provider": "gemini",
        "model": "gemini-2.0-flash",
        "temperature": 0.7,
        "max_tokens": 1000
      },
      "tool_count": 0,
      "has_system_prompt": true,
      "agent_class": "ResearchAgent",
      "status": "discovered"
    }
  ],
  "total": 5,
  "platforms": [
    {
      "id": "hello-world",
      "name": "Hello World",
      "description": "A sample multi-agent platform for demonstration",
      "version": "1.0.0",
      "agent_count": 1,
      "agents": ["greeter"],
      "enabled": true
    },
    {
      "id": "newsletter",
      "name": "Newsletter",
      "description": "AI-powered newsletter generation with multi-agent architecture",
      "version": "1.0.0",
      "agent_count": 4,
      "agents": ["research", "writing", "preference", "custom_prompt"],
      "enabled": true
    }
  ]
}
```

### GET /studio/agents/{platform_id}/{agent_name}

Get full detail for a single agent including system prompt, tools, and parameters.

**Path Parameters:**
| Param | Description |
|-------|-------------|
| `platform_id` | Platform identifier (e.g., `newsletter`) |
| `agent_name` | Agent name (e.g., `research`) |

**Response:** `StudioAgentDetail`

```json
{
  "agent_id": "newsletter/research",
  "name": "research",
  "display_name": "Research Agent",
  "platform_id": "newsletter",
  "platform_name": "Newsletter",
  "description": "Content discovery and research agent for newsletters",
  "llm_config": {
    "provider": "gemini",
    "model": "gemini-2.0-flash",
    "temperature": 0.7,
    "max_tokens": 1000
  },
  "tool_count": 0,
  "has_system_prompt": true,
  "agent_class": "ResearchAgent",
  "status": "discovered",
  "system_prompt": "You are a research assistant specializing in content discovery...",
  "tools": [],
  "parameters": {
    "temperature": 0.7,
    "max_tokens": 1000,
    "model": "gemini-2.0-flash"
  }
}
```

**Error Responses:**
| Status | Condition |
|--------|-----------|
| 404 | Platform not found |
| 404 | Agent not in platform's agent list |
| 404 | Agent class could not be instantiated |

### GET /studio/platforms

List all platforms with agent counts. Lighter-weight than `/agents` — does not instantiate agent classes.

**Response:** `StudioPlatformsListResponse`

```json
{
  "platforms": [
    {
      "id": "hello-world",
      "name": "Hello World",
      "description": "A sample multi-agent platform for demonstration",
      "version": "1.0.0",
      "agent_count": 1,
      "agents": ["greeter"],
      "enabled": true
    }
  ],
  "total": 1
}
```

---

## Data Contracts

### Backend Schemas

**File:** `backend/app/schemas/studio.py`

| Schema | Purpose | Used By |
|--------|---------|---------|
| `StudioLLMConfig` | Provider, model, temperature, max_tokens | Nested in agent schemas |
| `StudioToolInfo` | Tool name, description, parameter schema | Nested in `StudioAgentDetail` |
| `StudioAgentSummary` | Lightweight agent metadata for grid cards | `GET /studio/agents` response |
| `StudioAgentDetail` | Full metadata with prompt and tools | `GET /studio/agents/{p}/{a}` response |
| `StudioPlatformSummary` | Platform with agent count | Both agent and platform responses |
| `StudioAgentsListResponse` | Agents + platforms wrapper | `GET /studio/agents` |
| `StudioPlatformsListResponse` | Platforms wrapper | `GET /studio/platforms` |

### Frontend Types

**File:** `frontend/src/types/studio.ts`

TypeScript interfaces mirror the backend schemas exactly. All field names use the same casing as the Python models (snake_case — FastAPI serializes Pydantic models as-is).

### Agent ID Format

Agent IDs are composite strings: `"{platform_id}/{agent_name}"` (e.g., `"newsletter/research"`, `"hello-world/greeter"`). This ensures global uniqueness across platforms without requiring a database.

---

## Frontend Components

### Page & Routing

| Item | Value |
|------|-------|
| Route | `/studio` |
| Sidebar entry | "Studio" with `FlaskConical` icon, placed after "Agents" |
| Page component | `frontend/src/pages/StudioPage.tsx` |

### Component Hierarchy

```
StudioPage
├── PlatformFilter          # Tab bar: All | Newsletter | Hello World
├── AgentCatalogGrid        # Responsive grid of agent cards
│   └── AgentStudioCard     # Individual agent card (repeated)
└── AgentDetailDrawer       # Dialog opened on card click
    └── Tabs: Overview | Config | Prompt | Tools
```

### PlatformFilter

**File:** `frontend/src/components/studio/PlatformFilter.tsx`

Tab bar using shadcn `Tabs` component. Shows "All" plus one tab per discovered platform. Each tab displays a `Badge` with the agent count. Selecting a platform filters the grid by passing `platformId` to the `useStudioAgents` hook.

### AgentStudioCard

**File:** `frontend/src/components/studio/AgentStudioCard.tsx`

Card showing:
- **Header:** Display name + platform badge + Bot icon
- **Body:** Description (2-line clamp)
- **Footer grid:** LLM model, tool count, prompt indicator, Python class name

Clicking the card sets `selectedAgent` state, which opens the detail drawer.

### AgentCatalogGrid

**File:** `frontend/src/components/studio/AgentCatalogGrid.tsx`

Responsive grid: `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`. Shows 6 skeleton cards during loading, empty state message when no agents are found.

### AgentDetailDrawer

**File:** `frontend/src/components/studio/AgentDetailDrawer.tsx`

Dialog (`max-w-2xl`) with 4 tabs. Lazy-loads full agent detail via `useStudioAgent()` when opened (only the summary is available from the grid — the detail endpoint returns system prompt, tools, and parameters).

| Tab | Content |
|-----|---------|
| Overview | Description, platform, agent class, agent ID, status |
| Config | LLM provider, model, temperature, max tokens, raw parameters JSON |
| Prompt | System prompt in monospace `<pre>` block, or "No system prompt" message |
| Tools | List of tool cards with name, description, and parameter JSON |

### React Query Hooks

**File:** `frontend/src/hooks/useStudio.ts`

| Hook | Endpoint | Parameters |
|------|----------|------------|
| `useStudioAgents(platformId?)` | `GET /studio/agents` | Optional platform filter |
| `useStudioAgent(platformId, agentName)` | `GET /studio/agents/{p}/{a}` | Both required, `enabled` guard |
| `useStudioPlatforms()` | `GET /studio/platforms` | None |

All hooks are read-only (no mutations in Phase 1).

---

## Files Created & Modified

### New Files (10)

| File | Layer | Purpose |
|------|-------|---------|
| `backend/app/schemas/studio.py` | Backend | Pydantic response models |
| `backend/app/api/v1/endpoints/studio.py` | Backend | API endpoints + agent discovery logic |
| `frontend/src/types/studio.ts` | Frontend | TypeScript interfaces |
| `frontend/src/api/studio.ts` | Frontend | Axios API client |
| `frontend/src/hooks/useStudio.ts` | Frontend | React Query hooks |
| `frontend/src/pages/StudioPage.tsx` | Frontend | Main Studio page |
| `frontend/src/components/studio/PlatformFilter.tsx` | Frontend | Platform tab filter |
| `frontend/src/components/studio/AgentStudioCard.tsx` | Frontend | Agent card for grid |
| `frontend/src/components/studio/AgentCatalogGrid.tsx` | Frontend | Responsive grid container |
| `frontend/src/components/studio/AgentDetailDrawer.tsx` | Frontend | Detail dialog with tabs |

### Modified Files (4)

| File | Change |
|------|--------|
| `backend/app/api/v1/router.py` | Import + register `studio.router` under `/studio` prefix |
| `frontend/src/utils/constants.ts` | Add `STUDIO: '/studio'` to `ROUTES` |
| `frontend/src/components/layout/Sidebar.tsx` | Add "Studio" nav item with `FlaskConical` icon |
| `frontend/src/App.tsx` | Import `StudioPage` + add `<Route path={ROUTES.STUDIO}>` |

---

## Discovered Agents

Phase 1 discovers the following agents at runtime:

| Agent ID | Class | Platform | LLM | System Prompt | Tools |
|----------|-------|----------|-----|---------------|-------|
| `hello-world/greeter` | `GreeterAgent` | Hello World | Configured via platform config | No | 0 |
| `newsletter/research` | `ResearchAgent` | Newsletter | Configured via platform config | Yes | 0 |
| `newsletter/writing` | `WritingAgent` | Newsletter | Configured via platform config | Yes | 0 |
| `newsletter/preference` | `PreferenceAgent` | Newsletter | Configured via platform config | Yes | 0 |
| `newsletter/custom_prompt` | `CustomPromptAgent` | Newsletter | Configured via platform config | Yes | 0 |

Note: `mindmap` is listed in the Newsletter platform's agent list in the registry but has no implementation. It is silently skipped during discovery.

---

## Adding a New Platform / Agent

Agent Studio discovers agents automatically. To make a new agent appear:

### If using BaseOrchestrator.register_agent()

Just register the agent in your orchestrator's `_setup_agents()`:

```python
class MyOrchestrator(BaseOrchestrator):
    def _setup_agents(self):
        self.register_agent(MyAgent())
```

No changes to Studio code needed — the agent will be discovered via Pass 1.

### If using LangGraph (or not registering agents)

Add an entry to `_AGENT_FACTORIES` in `backend/app/api/v1/endpoints/studio.py`:

```python
_AGENT_FACTORIES = {
    ...
    ("my-platform", "my_agent"): "app.platforms.my_platform.agents:MyAgent",
}
```

The agent must also be listed in the platform's `agents` list when calling `registry.register()`.

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| No database — introspect live objects | Agents are Python classes with all metadata available at runtime. A database would just be a stale copy. |
| Two-pass discovery instead of requiring `register_agent()` | Newsletter platform uses LangGraph and can't easily retrofit `register_agent()` calls. The factory approach is minimal and explicit. |
| Avoid accessing `agent.llm` property | The property triggers lazy LLM initialization which requires a running LLM server. Studio should work even when LLM servers are down. |
| Separate `/studio` endpoints from existing `/agents` | The existing `/agents` CRUD endpoints are stubbed and serve a different purpose (generic agent management). Studio is discovery-focused and platform-aware. |
| `agent_id` as `"{platform}/{name}"` composite | Simple, human-readable, globally unique, no UUID generation needed. |
| Dialog instead of Sheet for detail view | The project's shadcn/ui installation doesn't include the Sheet component. Dialog achieves the same UX. |
| Read-only for Phase 1 | Configuration editing, evaluation, and lifecycle management are scoped to Phases 2-4. |

---

## Testing & Verification

### Backend

```bash
# Verify the endpoint returns discovered agents
curl http://localhost:8000/api/v1/studio/agents | python -m json.tool

# Verify single agent detail with system prompt
curl http://localhost:8000/api/v1/studio/agents/newsletter/research | python -m json.tool

# Verify platform filter
curl http://localhost:8000/api/v1/studio/agents?platform_id=hello-world | python -m json.tool

# Verify platforms endpoint
curl http://localhost:8000/api/v1/studio/platforms | python -m json.tool

# Existing tests still pass
cd backend && .venv/bin/python -m pytest app/platforms/newsletter/tests/ -v
```

### Frontend

```bash
# Type check — no new errors
cd frontend && npx tsc --noEmit

# Dev server — navigate to /studio
npm run dev
```

### Manual QA Checklist

- [ ] `/studio` page loads with agent grid
- [ ] Platform filter tabs show correct agent counts
- [ ] Clicking a platform tab filters the grid
- [ ] Clicking "All" shows all agents
- [ ] Each agent card shows: display name, platform badge, model, tool count, prompt indicator, class name
- [ ] Clicking an agent card opens the detail dialog
- [ ] Overview tab shows description, platform, class, ID, status
- [ ] Config tab shows provider, model, temperature, max tokens
- [ ] Prompt tab shows system prompt text (or "No system prompt" message)
- [ ] Tools tab shows tool list (or "No tools registered" message)
- [ ] Closing the dialog returns to the grid
- [ ] Sidebar shows "Studio" entry with FlaskConical icon
- [ ] Sidebar "Studio" entry highlights when on `/studio` route
