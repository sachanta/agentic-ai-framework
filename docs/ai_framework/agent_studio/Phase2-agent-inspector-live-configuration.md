Agent Studio — Phase 2: Agent Inspector & Live Configuration                                                                                                                                                                │
│                                                                                                                                                                                                                             │
│ Context                                                                                                                                                                                                                     │
│                                                                                                                                                                                                                             │
│ Phase 1 (Agent Registry & Catalog) is complete. We have a read-only /studio page that discovers all 5 agents across 2 platforms and displays them in a card grid with a detail drawer. Phase 2 transforms this into an      │
│ interactive inspector where users can view/edit LLM config, view/edit system prompts, and run agents interactively with custom input — all session-only (resets on server restart).                                         │
│                                                                                                                                                                                                                             │
│ Key Design Decisions                                                                                                                                                                                                        │
│                                                                                                                                                                                                                             │
│ 1. In-memory override store: A module-level _session_overrides dict stores config/prompt changes keyed by "platform_id/agent_name". Applied after agent instantiation on every request. Resets on server restart.           │
│ 2. Full-page inspector: Replace the dialog drawer with navigation to /studio/:platformId/:agentName. Cards navigate instead of opening a modal.                                                                             │
│ 3. Try It panel: Runs agent.run(input) with a 60s timeout. Returns structured response with output, error, and timing.                                                                                                      │
│ 4. Provider discovery: Iterates LLMProviderType enum, attempts to instantiate each provider, calls list_models(). Gracefully handles missing API keys.                                                                      │
│                                                                                                                                                                                                                             │
│ ---                                                                                                                                                                                                                         │
│ Implementation Plan (13 files: 5 new, 8 modified)                                                                                                                                                                           │
│                                                                                                                                                                                                                             │
│ Step 1: Backend Schemas                                                                                                                                                                                                     │
│                                                                                                                                                                                                                             │
│ MODIFY backend/app/schemas/studio.py                                                                                                                                                                                        │
│                                                                                                                                                                                                                             │
│ Add 6 new Pydantic models:                                                                                                                                                                                                  │
│ - StudioConfigUpdateRequest — provider?, model?, temperature?, max_tokens?                                                                                                                                                  │
│ - StudioPromptUpdateRequest — system_prompt: str                                                                                                                                                                            │
│ - StudioTryRequest — input: Dict, config_override?: StudioConfigUpdateRequest                                                                                                                                               │
│ - StudioTryResponse — success, output?, error?, duration_ms, agent_id                                                                                                                                                       │
│ - StudioProviderInfo — name, provider_type, models[], available                                                                                                                                                             │
│ - StudioProvidersListResponse — providers[], total                                                                                                                                                                          │
│                                                                                                                                                                                                                             │
│ Step 2: Backend Endpoints                                                                                                                                                                                                   │
│                                                                                                                                                                                                                             │
│ MODIFY backend/app/api/v1/endpoints/studio.py                                                                                                                                                                               │
│                                                                                                                                                                                                                             │
│ 2a. Add in-memory override store + helper:                                                                                                                                                                                  │
│ _session_overrides: Dict[str, Dict[str, Any]] = {}                                                                                                                                                                          │
│                                                                                                                                                                                                                             │
│ def _apply_overrides(agent: BaseAgent, agent_id: str) -> BaseAgent:                                                                                                                                                         │
│     # Apply stored temperature, max_tokens, model, system_prompt, provider                                                                                                                                                  │
│                                                                                                                                                                                                                             │
│ 2b. Update existing get_studio_agent to call _apply_overrides() after discovery so detail view reflects saved changes.                                                                                                      │
│                                                                                                                                                                                                                             │
│ 2c. Add 5 new endpoints:                                                                                                                                                                                                    │
│ ┌────────┬──────────────────────────────────────────────────┬───────────────────────────────────────────────┐                                                                                                               │
│ │ Method │                       Path                       │                  Description                  │                                                                                                               │
│ ├────────┼──────────────────────────────────────────────────┼───────────────────────────────────────────────┤                                                                                                               │
│ │ PATCH  │ /studio/agents/{platform_id}/{agent_name}/config │ Update LLM config (session-only)              │                                                                                                               │
│ ├────────┼──────────────────────────────────────────────────┼───────────────────────────────────────────────┤                                                                                                               │
│ │ PUT    │ /studio/agents/{platform_id}/{agent_name}/prompt │ Update system prompt (session-only)           │                                                                                                               │
│ ├────────┼──────────────────────────────────────────────────┼───────────────────────────────────────────────┤                                                                                                               │
│ │ POST   │ /studio/agents/{platform_id}/{agent_name}/try    │ Execute agent with ad-hoc input (60s timeout) │                                                                                                               │
│ ├────────┼──────────────────────────────────────────────────┼───────────────────────────────────────────────┤                                                                                                               │
│ │ GET    │ /studio/providers                                │ List all LLM providers with model lists       │                                                                                                               │
│ ├────────┼──────────────────────────────────────────────────┼───────────────────────────────────────────────┤                                                                                                               │
│ │ DELETE │ /studio/agents/{platform_id}/{agent_name}/config │ Reset overrides to defaults                   │                                                                                                               │
│ └────────┴──────────────────────────────────────────────────┴───────────────────────────────────────────────┘                                                                                                               │
│ Key implementation details:                                                                                                                                                                                                 │
│ - try endpoint: wraps agent.run() in asyncio.wait_for(timeout=60), measures duration with time.perf_counter(), catches all exceptions into structured error responses                                                       │
│ - providers endpoint: iterates LLMProviderType enum, instantiates each provider in try/except, calls list_models() and health_check()                                                                                       │
│ - Config/prompt endpoints: merge updates into _session_overrides, re-discover agent, apply overrides, return updated StudioAgentDetail                                                                                      │
│                                                                                                                                                                                                                             │
│ Step 3: Frontend Types                                                                                                                                                                                                      │
│                                                                                                                                                                                                                             │
│ MODIFY frontend/src/types/studio.ts                                                                                                                                                                                         │
│                                                                                                                                                                                                                             │
│ Add 6 new TypeScript interfaces mirroring backend schemas:                                                                                                                                                                  │
│ - StudioConfigUpdateRequest, StudioPromptUpdateRequest                                                                                                                                                                      │
│ - StudioTryRequest, StudioTryResponse                                                                                                                                                                                       │
│ - StudioProviderInfo, StudioProvidersListResponse                                                                                                                                                                           │
│                                                                                                                                                                                                                             │
│ Step 4: Frontend API Client                                                                                                                                                                                                 │
│                                                                                                                                                                                                                             │
│ MODIFY frontend/src/api/studio.ts                                                                                                                                                                                           │
│                                                                                                                                                                                                                             │
│ Add 5 new methods to studioApi:                                                                                                                                                                                             │
│ - updateConfig(platformId, agentName, data) → PATCH                                                                                                                                                                         │
│ - updatePrompt(platformId, agentName, data) → PUT                                                                                                                                                                           │
│ - tryAgent(platformId, agentName, data) → POST                                                                                                                                                                              │
│ - resetConfig(platformId, agentName) → DELETE                                                                                                                                                                               │
│ - listProviders() → GET                                                                                                                                                                                                     │
│                                                                                                                                                                                                                             │
│ Step 5: Frontend Hooks                                                                                                                                                                                                      │
│                                                                                                                                                                                                                             │
│ MODIFY frontend/src/hooks/useStudio.ts                                                                                                                                                                                      │
│                                                                                                                                                                                                                             │
│ Add 5 new hooks:                                                                                                                                                                                                            │
│ - useStudioProviders() — query, 5min staleTime                                                                                                                                                                              │
│ - useUpdateAgentConfig() — mutation, invalidates agent detail + list cache                                                                                                                                                  │
│ - useUpdateAgentPrompt() — mutation, updates cached agent detail                                                                                                                                                            │
│ - useTryAgent() — mutation (no cache invalidation)                                                                                                                                                                          │
│ - useResetAgentConfig() — mutation, invalidates caches                                                                                                                                                                      │
│                                                                                                                                                                                                                             │
│ Step 6: Route & Navigation Wiring                                                                                                                                                                                           │
│                                                                                                                                                                                                                             │
│ MODIFY frontend/src/utils/constants.ts — Add STUDIO_INSPECTOR: '/studio/:platformId/:agentName'                                                                                                                             │
│                                                                                                                                                                                                                             │
│ MODIFY frontend/src/App.tsx — Add import AgentInspectorPage and route                                                                                                                                                       │
│                                                                                                                                                                                                                             │
│ MODIFY frontend/src/pages/StudioPage.tsx — Replace drawer with useNavigate to inspector route. Remove AgentDetailDrawer import, selectedAgent state, and drawer component.                                                  │
│                                                                                                                                                                                                                             │
│ Step 7: Frontend Components                                                                                                                                                                                                 │
│                                                                                                                                                                                                                             │
│ CREATE frontend/src/pages/AgentInspectorPage.tsx                                                                                                                                                                            │
│ - Full-page view with back button, agent name/badges header                                                                                                                                                                 │
│ - Uses useParams to get platformId and agentName                                                                                                                                                                            │
│ - Fetches detail via useStudioAgent()                                                                                                                                                                                       │
│ - 4 tabs: LLM Config, System Prompt, Try It, Tools                                                                                                                                                                          │
│ - Loading skeleton and not-found state                                                                                                                                                                                      │
│                                                                                                                                                                                                                             │
│ CREATE frontend/src/components/studio/LLMConfigEditor.tsx                                                                                                                                                                   │
│ - Card with form: Provider (Select from providers list), Model (Select if provider has models, otherwise Input), Temperature (Slider 0-2), Max Tokens (Input number)                                                        │
│ - Save and Reset to Defaults buttons                                                                                                                                                                                        │
│ - Uses useStudioProviders(), useUpdateAgentConfig(), useResetAgentConfig()                                                                                                                                                  │
│ - Session-only disclaimer text                                                                                                                                                                                              │
│                                                                                                                                                                                                                             │
│ CREATE frontend/src/components/studio/PromptEditor.tsx                                                                                                                                                                      │
│ - Card with read-only <pre> monospace view by default                                                                                                                                                                       │
│ - Edit button toggles to <Textarea> with Save/Cancel                                                                                                                                                                        │
│ - Uses useUpdateAgentPrompt()                                                                                                                                                                                               │
│ - Empty state with "Click Edit to add one"                                                                                                                                                                                  │
│                                                                                                                                                                                                                             │
│ CREATE frontend/src/components/studio/TryItPanel.tsx                                                                                                                                                                        │
│ - Two-column layout (lg:grid-cols-2): Input card + Output card                                                                                                                                                              │
│ - Input: <Textarea> with pre-populated default JSON based on agent name, Run button                                                                                                                                         │
│ - Output: success/error badge, duration badge, JSON output in <pre> block                                                                                                                                                   │
│ - JSON parse validation before sending                                                                                                                                                                                      │
│ - Uses useTryAgent()                                                                                                                                                                                                        │
│                                                                                                                                                                                                                             │
│ CREATE frontend/src/components/studio/ToolsPanel.tsx                                                                                                                                                                        │
│ - List of tool cards with name, param count badge, description, parameters JSON                                                                                                                                             │
│ - Empty state for agents with no tools                                                                                                                                                                                      │
│                                                                                                                                                                                                                             │
│ ---                                                                                                                                                                                                                         │
│ Files Summary                                                                                                                                                                                                               │
│ ┌─────┬────────────────────────────────────────────────────┬───────────────────────────────────────────┐                                                                                                                    │
│ │  #  │                        File                        │                  Action                   │                                                                                                                    │
│ ├─────┼────────────────────────────────────────────────────┼───────────────────────────────────────────┤                                                                                                                    │
│ │ 1   │ backend/app/schemas/studio.py                      │ MODIFY — add 6 schemas                    │                                                                                                                    │
│ ├─────┼────────────────────────────────────────────────────┼───────────────────────────────────────────┤                                                                                                                    │
│ │ 2   │ backend/app/api/v1/endpoints/studio.py             │ MODIFY — add override store + 5 endpoints │                                                                                                                    │
│ ├─────┼────────────────────────────────────────────────────┼───────────────────────────────────────────┤                                                                                                                    │
│ │ 3   │ frontend/src/types/studio.ts                       │ MODIFY — add 6 interfaces                 │                                                                                                                    │
│ ├─────┼────────────────────────────────────────────────────┼───────────────────────────────────────────┤                                                                                                                    │
│ │ 4   │ frontend/src/api/studio.ts                         │ MODIFY — add 5 API methods                │                                                                                                                    │
│ ├─────┼────────────────────────────────────────────────────┼───────────────────────────────────────────┤                                                                                                                    │
│ │ 5   │ frontend/src/hooks/useStudio.ts                    │ MODIFY — add 5 hooks                      │                                                                                                                    │
│ ├─────┼────────────────────────────────────────────────────┼───────────────────────────────────────────┤                                                                                                                    │
│ │ 6   │ frontend/src/utils/constants.ts                    │ MODIFY — add route                        │                                                                                                                    │
│ ├─────┼────────────────────────────────────────────────────┼───────────────────────────────────────────┤                                                                                                                    │
│ │ 7   │ frontend/src/App.tsx                               │ MODIFY — add route                        │                                                                                                                    │
│ ├─────┼────────────────────────────────────────────────────┼───────────────────────────────────────────┤                                                                                                                    │
│ │ 8   │ frontend/src/pages/StudioPage.tsx                  │ MODIFY — replace drawer with navigation   │                                                                                                                    │
│ ├─────┼────────────────────────────────────────────────────┼───────────────────────────────────────────┤                                                                                                                    │
│ │ 9   │ frontend/src/pages/AgentInspectorPage.tsx          │ CREATE                                    │                                                                                                                    │
│ ├─────┼────────────────────────────────────────────────────┼───────────────────────────────────────────┤                                                                                                                    │
│ │ 10  │ frontend/src/components/studio/LLMConfigEditor.tsx │ CREATE                                    │                                                                                                                    │
│ ├─────┼────────────────────────────────────────────────────┼───────────────────────────────────────────┤                                                                                                                    │
│ │ 11  │ frontend/src/components/studio/PromptEditor.tsx    │ CREATE                                    │                                                                                                                    │
│ ├─────┼────────────────────────────────────────────────────┼───────────────────────────────────────────┤                                                                                                                    │
│ │ 12  │ frontend/src/components/studio/TryItPanel.tsx      │ CREATE                                    │                                                                                                                    │
│ ├─────┼────────────────────────────────────────────────────┼───────────────────────────────────────────┤                                                                                                                    │
│ │ 13  │ frontend/src/components/studio/ToolsPanel.tsx      │ CREATE                                    │                                                                                                                    │
│ └─────┴────────────────────────────────────────────────────┴───────────────────────────────────────────┘                                                                                                                    │
│ Verification                                                                                                                                                                                                                │
│                                                                                                                                                                                                                             │
│ 1. Backend: curl http://localhost:8000/api/v1/studio/providers — list 5 providers                                                                                                                                           │
│ 2. Backend: curl -X PATCH .../studio/agents/hello_world/greeter/config -d '{"temperature":0.5}' — returns updated detail                                                                                                    │
│ 3. Backend: curl .../studio/agents/hello_world/greeter — shows temperature=0.5                                                                                                                                              │
│ 4. Backend: curl -X POST .../studio/agents/hello_world/greeter/try -d '{"input":{"name":"Test"}}' — returns greeting (needs LLM running)                                                                                    │
│ 5. Backend: curl -X DELETE .../studio/agents/hello_world/greeter/config — resets overrides                                                                                                                                  │
│ 6. Frontend: npx tsc --noEmit — no new type errors                                                                                                                                                                          │
│ 7. Frontend: Navigate to /studio, click agent card → navigates to /studio/hello_world/greeter                                                                                                                               │
│ 8. Frontend: Inspector shows 4 tabs with config editor, prompt viewer, try panel, tools list                                                                                                                                │
│ 9. Backend tests: cd backend && .venv/bin/python -m pytest app/platforms/newsletter/tests/ -v — existing tests still pass

---

## Implementation Summary

**Status: COMPLETE**

All 13 files (5 new, 8 modified) have been implemented and verified.

### Backend Changes

**`backend/app/schemas/studio.py`** (MODIFIED)
- Added 6 Pydantic models: `StudioConfigUpdateRequest`, `StudioPromptUpdateRequest`, `StudioTryRequest`, `StudioTryResponse`, `StudioProviderInfo`, `StudioProvidersListResponse`

**`backend/app/api/v1/endpoints/studio.py`** (MODIFIED)
- Added `_session_overrides` module-level dict for in-memory session-only config storage
- Added `_apply_overrides(agent, agent_id)` helper that applies stored temperature, max_tokens, model, system_prompt, and provider overrides to an agent instance
- Added `_discover_and_apply(platform_id, agent_name)` helper that consolidates agent lookup + override application (used by all new endpoints)
- Updated existing `list_studio_agents` and `get_studio_agent` endpoints to apply session overrides
- Added 5 new endpoints:
  - `PATCH /agents/{platform_id}/{agent_name}/config` — merges config updates into `_session_overrides`, returns updated `StudioAgentDetail`
  - `PUT /agents/{platform_id}/{agent_name}/prompt` — stores system prompt override, returns updated `StudioAgentDetail`
  - `POST /agents/{platform_id}/{agent_name}/try` — executes `agent.run(input)` with `asyncio.wait_for(timeout=60)`, measures duration with `time.perf_counter()`, catches all exceptions into structured `StudioTryResponse`
  - `GET /providers` — iterates `LLMProviderType` enum, instantiates each via `get_llm_provider()`, calls `health_check()` and `list_models()` with graceful error handling
  - `DELETE /agents/{platform_id}/{agent_name}/config` — removes agent entry from `_session_overrides`, returns default `StudioAgentDetail`

### Frontend Changes

**`frontend/src/types/studio.ts`** (MODIFIED)
- Added 6 TypeScript interfaces: `StudioConfigUpdateRequest`, `StudioPromptUpdateRequest`, `StudioTryRequest`, `StudioTryResponse`, `StudioProviderInfo`, `StudioProvidersListResponse`

**`frontend/src/api/studio.ts`** (MODIFIED)
- Added 5 API methods: `updateConfig` (PATCH), `updatePrompt` (PUT), `tryAgent` (POST), `resetConfig` (DELETE), `listProviders` (GET)

**`frontend/src/hooks/useStudio.ts`** (MODIFIED)
- Added 5 React Query hooks:
  - `useStudioProviders()` — query with 5min staleTime
  - `useUpdateAgentConfig()` — mutation, invalidates agent detail + list cache
  - `useUpdateAgentPrompt()` — mutation, optimistically updates cached agent detail via `setQueryData`
  - `useTryAgent()` — mutation (no cache invalidation)
  - `useResetAgentConfig()` — mutation, invalidates agent detail + list cache

**`frontend/src/utils/constants.ts`** (MODIFIED)
- Added `STUDIO_INSPECTOR: '/studio/:platformId/:agentName'` route constant

**`frontend/src/App.tsx`** (MODIFIED)
- Added `AgentInspectorPage` import and `<Route path={ROUTES.STUDIO_INSPECTOR}>` entry

**`frontend/src/pages/StudioPage.tsx`** (MODIFIED)
- Replaced `AgentDetailDrawer` modal with `useNavigate` to `/studio/{platformId}/{agentName}`
- Removed `selectedAgent` state, drawer component, and drawer import

**`frontend/src/pages/AgentInspectorPage.tsx`** (CREATED)
- Full-page inspector using `useParams` for `platformId` and `agentName`
- Back button navigating to `/studio`
- Header with agent display name, platform badge, class badge, tool count badge
- 4 tabs: LLM Config, System Prompt, Try It, Tools
- Loading skeleton and not-found state

**`frontend/src/components/studio/LLMConfigEditor.tsx`** (CREATED)
- Card with Provider (Select populated from `useStudioProviders()`), Model (Select if provider has models, otherwise free-text Input), Temperature (Slider 0–2, step 0.05), Max Tokens (number Input)
- Save and Reset to Defaults buttons using `useUpdateAgentConfig()` and `useResetAgentConfig()`
- Form syncs with detail via `useEffect` (e.g. after reset)
- Session-only disclaimer text

**`frontend/src/components/studio/PromptEditor.tsx`** (CREATED)
- Read-only `<pre>` monospace view by default
- Edit button toggles to `<Textarea>` with Save/Cancel buttons
- Uses `useUpdateAgentPrompt()` for persistence
- Empty state: "No system prompt configured. Click Edit to add one."

**`frontend/src/components/studio/TryItPanel.tsx`** (CREATED)
- Two-column layout (`lg:grid-cols-2`): Input card + Output card
- Input textarea pre-populated with agent-specific default JSON (e.g. `{name: "World"}` for greeter, `{topic: "AI agents"}` for research)
- JSON parse validation before sending, toast on invalid JSON
- Output card shows success/error badge, duration badge (ms), and JSON output in `<pre>` block
- Uses `useTryAgent()` mutation

**`frontend/src/components/studio/ToolsPanel.tsx`** (CREATED)
- Renders each tool as a Card with name, param count badge, description, and parameters JSON in `<pre>`
- Empty state: "No tools registered for this agent."

### Verification Results

- **TypeScript**: `npx tsc --noEmit` — zero new type errors in any studio-related files (all pre-existing errors are in unrelated `mocks/`, `main.tsx`, etc.)
- **Navigation**: `/studio` card click navigates to `/studio/:platformId/:agentName`
- **Inspector**: 4-tab layout renders LLM config editor, prompt viewer, try panel, and tools list