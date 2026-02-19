# Agent Studio — Detailed Implementation Plan

A centralized interface for inspecting, configuring, testing, and managing every AI agent in the framework. Agent Studio surfaces all agents across all platforms in a single, well-organized UI — giving developers and operators full visibility into the agents powering their applications.

---

## Table of Contents

| Phase | Name | Priority | Summary |
|-------|------|----------|---------|
| 1 | [Agent Registry & Catalog](#phase-1-agent-registry--catalog) | Highest | Browse all agents, view parameters, descriptions, and platform associations |
| 2 | [Agent Inspector & Live Configuration](#phase-2-agent-inspector--live-configuration) | High | Deep-dive into agent internals, edit configs, test prompts interactively |
| 3 | [Agent Evaluation & Testing](#phase-3-agent-evaluation--testing) | Medium | Run agents with test inputs, compare outputs, track quality over time |
| 4 | [Agent Lifecycle Management](#phase-4-agent-lifecycle-management) | Medium-Low | Private/staging/published states, versioning, environment promotion |
| 5 | [Agent Templates & Extensibility](#phase-5-agent-templates--extensibility) | Low | Starter templates, agent cloning, custom agent creation wizard |

---

## Current State of Agents in the Framework

### Existing Agents

| Agent | Platform | File | Purpose |
|-------|----------|------|---------|
| ResearchAgent | Newsletter | `platforms/newsletter/agents/research/agent.py` | Discover and score articles via Tavily API |
| WritingAgent | Newsletter | `platforms/newsletter/agents/writing/agent.py` | Generate newsletter content in multiple formats |
| PreferenceAgent | Newsletter | `platforms/newsletter/agents/preference/agent.py` | Manage user preferences and engagement learning |
| CustomPromptAgent | Newsletter | `platforms/newsletter/agents/custom_prompt/agent.py` | Parse natural-language prompts into execution parameters |
| GreeterAgent | Hello World | `platforms/hello_world/agents/greeter/agent.py` | Simple greeting generation (demo agent) |

### Existing Infrastructure

| Component | Location | What It Provides |
|-----------|----------|------------------|
| BaseAgent | `common/base/agent.py` | Abstract base class with LLM, memory, tools, state |
| AgentTool | `common/base/agent.py` | Tool abstraction with name, description, parameters |
| AgentMemory | `common/base/agent.py` | Conversation history with context storage |
| LLMProvider | `common/providers/llm.py` | Multi-provider LLM abstraction (Gemini, Ollama, OpenAI, Bedrock, Perplexity) |
| BaseOrchestrator | `common/base/orchestrator.py` | Agent coordination (simple, sequential, parallel) |
| Agent API | `api/v1/agents/` | CRUD endpoints for agent management |
| Agent types | `frontend/src/types/agent.ts` | TypeScript interfaces (Agent, AgentConfig, AgentExecution) |
| Agent UI | `frontend/src/components/agents/` | AgentCard, AgentList, AgentForm, AgentDetail |

### Agent Structure Convention

Every agent follows this directory pattern:

```
platforms/{platform}/agents/{agent_name}/
  agent.py      # Agent class extending BaseAgent
  llm.py        # get_{name}_llm() factory + config helpers
  prompts.py    # Prompt templates and system prompts
  tools.py      # Optional — agent-specific tools
```

---

## Phase 1: Agent Registry & Catalog

**Priority:** Highest — This is the foundation. Without a central registry, the framework has no single place to see what agents exist, what they do, or how they're configured.

### Goal

A read-only catalog UI that automatically discovers and displays every agent across all platforms, with rich metadata: description, parameters, LLM config, tools, platform association, and health status.

### 1.1 Backend: Agent Discovery Service

Create a service that introspects all registered agents at runtime and returns standardized metadata.

**File:** `backend/app/common/services/agent_registry.py`

```python
class AgentRegistryEntry:
    """Standardized metadata for a single agent."""
    agent_id: str               # Unique ID (e.g., "newsletter.research")
    name: str                   # Human-readable name
    class_name: str             # Python class name (e.g., "ResearchAgent")
    platform: str               # Platform name (e.g., "newsletter")
    module_path: str            # Full Python module path
    description: str            # From agent.description
    status: str                 # "active" | "inactive" | "error"

    # Configuration
    llm_config: dict            # provider, model, temperature, max_tokens, timeout
    parameters: list[dict]      # Constructor params with types, defaults, descriptions
    system_prompt: str | None   # The agent's system prompt

    # Tools
    tools: list[dict]           # [{name, description, parameters}]

    # Capabilities
    capabilities: list[str]     # ["search", "generate", "summarize", ...]
    input_schema: dict          # Expected input to run()
    output_schema: dict         # Expected output from run()

    # Metadata
    platform_config: dict       # Platform-specific env var overrides
    created_at: str
    last_executed_at: str | None
    execution_count: int
    success_rate: float


class AgentRegistryService:
    """Central registry that discovers and catalogs all agents."""

    async def discover_agents(self) -> list[AgentRegistryEntry]:
        """Scan all platforms and return agent metadata."""

    async def get_agent(self, agent_id: str) -> AgentRegistryEntry:
        """Get detailed metadata for a single agent."""

    async def get_agents_by_platform(self, platform: str) -> list[AgentRegistryEntry]:
        """List agents belonging to a specific platform."""

    async def get_agent_health(self, agent_id: str) -> dict:
        """Check if agent's LLM provider is reachable."""
```

**Discovery mechanism:** Each platform orchestrator already calls `register_agent()` during setup. The registry service queries all registered orchestrators and extracts agent metadata via introspection (`inspect` module for constructor params, docstrings, type annotations).

### 1.2 Backend: Agent Studio API

**File:** `backend/app/api/v1/agent_studio.py`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/studio/agents` | List all agents with filters (platform, status, capability) |
| GET | `/api/v1/studio/agents/{id}` | Full agent detail with config, tools, prompts |
| GET | `/api/v1/studio/agents/{id}/health` | LLM provider health check |
| GET | `/api/v1/studio/platforms` | List all platforms with agent counts |
| GET | `/api/v1/studio/providers` | List available LLM providers and their models |

### 1.3 Frontend: Agent Catalog Page

**Route:** `/studio` or as a tab within the main app

#### Layout

```
+------------------------------------------------------------------+
|  Agent Studio                                          [Search]   |
|------------------------------------------------------------------|
|  [All] [Newsletter] [Hello World]    Filter: [Status ▼] [LLM ▼] |
|------------------------------------------------------------------|
|                                                                   |
|  +---------------------------+  +---------------------------+     |
|  | Research Agent        [●] |  | Writing Agent         [●] |     |
|  | newsletter                |  | newsletter                |     |
|  |                           |  |                           |     |
|  | Discover and score        |  | Generate newsletter       |     |
|  | articles via Tavily API   |  | content in HTML, text,    |     |
|  |                           |  | and markdown formats      |     |
|  | LLM: Gemini / gemini-pro |  | LLM: Ollama / llama3     |     |
|  | Tools: 2  |  Runs: 142   |  | Tools: 0  |  Runs: 89    |     |
|  | Success: 97.2%            |  | Success: 94.4%            |     |
|  +---------------------------+  +---------------------------+     |
|                                                                   |
|  +---------------------------+  +---------------------------+     |
|  | Preference Agent     [●] |  | Custom Prompt Agent   [●] |     |
|  | newsletter                |  | newsletter                |     |
|  | ...                       |  | ...                       |     |
|  +---------------------------+  +---------------------------+     |
|                                                                   |
|  +---------------------------+                                    |
|  | Greeter Agent         [●] |                                    |
|  | hello_world               |                                    |
|  | ...                       |                                    |
|  +---------------------------+                                    |
+------------------------------------------------------------------+
```

#### Components

| Component | File | Purpose |
|-----------|------|---------|
| StudioPage | `pages/StudioPage.tsx` | Main page with platform tabs and filters |
| AgentCatalogCard | `components/studio/AgentCatalogCard.tsx` | Summary card with status, LLM, stats |
| AgentCatalogGrid | `components/studio/AgentCatalogGrid.tsx` | Responsive grid of agent cards |
| PlatformFilter | `components/studio/PlatformFilter.tsx` | Platform tab bar with counts |
| AgentSearch | `components/studio/AgentSearch.tsx` | Search by name, description, capability |

#### Agent Detail Drawer/Panel

Clicking an agent card opens a detail view with:

- **Overview tab:** Full description, platform, class name, module path
- **Configuration tab:** LLM provider, model, temperature, max_tokens, timeout, all constructor parameters with types and defaults
- **System Prompt tab:** Read-only view of the agent's system prompt
- **Tools tab:** List of registered tools with parameter schemas
- **I/O Schema tab:** Expected input/output structure for `run()`
- **Stats tab:** Execution count, success rate, average duration, last run

### 1.4 Frontend Types

**File:** `frontend/src/types/studio.ts`

```typescript
interface AgentRegistryEntry {
  agent_id: string;
  name: string;
  class_name: string;
  platform: string;
  module_path: string;
  description: string;
  status: 'active' | 'inactive' | 'error';
  llm_config: {
    provider: string;
    model: string;
    temperature: number;
    max_tokens: number;
    timeout: number;
  };
  parameters: AgentParameter[];
  system_prompt: string | null;
  tools: AgentToolInfo[];
  capabilities: string[];
  input_schema: Record<string, unknown>;
  output_schema: Record<string, unknown>;
  execution_count: number;
  success_rate: number;
  last_executed_at: string | null;
}

interface AgentParameter {
  name: string;
  type: string;
  required: boolean;
  default: unknown;
  description: string;
}

interface AgentToolInfo {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
}
```

### 1.5 Deliverables

- [ ] `AgentRegistryService` with platform discovery
- [ ] `/api/v1/studio/` endpoints
- [ ] `StudioPage` with catalog grid
- [ ] `AgentCatalogCard` component
- [ ] Agent detail drawer with all tabs
- [ ] Platform filter and search
- [ ] React Query hooks for studio API
- [ ] TypeScript types

---

## Phase 2: Agent Inspector & Live Configuration

**Priority:** High — Once agents are visible, operators need to inspect internals and adjust configuration without code changes.

### Goal

A deep-dive UI for each agent that allows real-time configuration editing, prompt previewing, and interactive testing within the Agent Studio.

### 2.1 Backend: Configuration API

**File:** `backend/app/api/v1/agent_studio.py` (extend)

| Method | Path | Description |
|--------|------|-------------|
| PATCH | `/api/v1/studio/agents/{id}/config` | Update agent LLM config at runtime |
| PUT | `/api/v1/studio/agents/{id}/prompt` | Update system prompt |
| POST | `/api/v1/studio/agents/{id}/try` | Execute agent with ad-hoc input (single run, no side effects) |
| GET | `/api/v1/studio/agents/{id}/prompt/variables` | List template variables in prompt |

**Runtime config updates** are non-persistent by default (reset on restart). A `persist: true` flag writes to the platform config file or env override.

### 2.2 Frontend: Agent Inspector

#### Inspector Layout

```
+------------------------------------------------------------------+
|  ← Back to Catalog    Research Agent                    [● Active]|
|------------------------------------------------------------------|
|  [Overview] [Config] [Prompt] [Tools] [Try It] [Execution Log]   |
|------------------------------------------------------------------|
|                                                                   |
|  Config                                                           |
|  +--------------------------+  +------------------------------+   |
|  | LLM Provider             |  | Parameters                   |   |
|  |                          |  |                              |   |
|  | Provider: [Gemini    ▼]  |  | tavily_service:  [connected] |   |
|  | Model:    [gemini-pro ▼] |  | use_llm_scoring: [✓]        |   |
|  | Temp:     [===●===] 0.7  |  | cache_results:   [✓]        |   |
|  | Tokens:   [1000      ]   |  |                              |   |
|  | Timeout:  [300s      ]   |  |                              |   |
|  |                          |  |                              |   |
|  | [Save] [Reset]           |  |                              |   |
|  +--------------------------+  +------------------------------+   |
|                                                                   |
+------------------------------------------------------------------+
```

#### Prompt Editor

- Syntax-highlighted view of the system prompt
- Template variable detection (`{topics}`, `{tone}`, etc.) with annotation
- Side-by-side: template on left, rendered preview on right
- Edit mode with save/revert
- Prompt version diff (if versioning enabled in Phase 4)

#### Try It Panel

Interactive single-run executor:

```
+------------------------------------------------------------------+
|  Try It — Research Agent                                          |
|------------------------------------------------------------------|
|  Input (JSON)                    |  Output                       |
|  +----------------------------+ |  +----------------------------+|
|  | {                          | |  | {                          ||
|  |   "topics": ["AI"],        | |  |   "articles": [...],       ||
|  |   "max_articles": 5        | |  |   "total_found": 5,        ||
|  | }                          | |  |   "search_metadata": {...}  ||
|  +----------------------------+ |  +----------------------------+|
|  [▶ Run]         Duration: 4.2s |  Status: ✓ Success            |
+------------------------------------------------------------------+
```

- Pre-populated input schema based on agent's `run()` signature
- JSON editor with validation
- Output display with syntax highlighting
- Duration and token usage tracking
- Error display with stack trace (in dev mode)

#### Components

| Component | File | Purpose |
|-----------|------|---------|
| AgentInspector | `components/studio/AgentInspector.tsx` | Main inspector with tab navigation |
| LLMConfigEditor | `components/studio/LLMConfigEditor.tsx` | Provider/model/temp/tokens form |
| PromptEditor | `components/studio/PromptEditor.tsx` | System prompt viewer/editor |
| TryItPanel | `components/studio/TryItPanel.tsx` | Interactive agent executor |
| ParameterPanel | `components/studio/ParameterPanel.tsx` | Constructor params display |
| ExecutionLog | `components/studio/ExecutionLog.tsx` | Recent executions with filters |

### 2.3 Deliverables

- [ ] Runtime config update endpoints
- [ ] System prompt update endpoint
- [ ] Ad-hoc execution endpoint (sandbox mode)
- [ ] Agent Inspector page with tabs
- [ ] LLM config editor with provider/model dropdowns
- [ ] Prompt editor with template variable detection
- [ ] Try It panel with JSON input editor
- [ ] Execution log with filtering

---

## Phase 3: Agent Evaluation & Testing

**Priority:** Medium — Quality assurance becomes important as the number of agents and use cases grows. This phase provides the tools to measure and compare agent performance systematically.

### Goal

A testing and evaluation framework that lets operators define test cases, run evaluations, compare results across models/configs, and track quality trends over time.

### 3.1 Backend: Evaluation Engine

**File:** `backend/app/common/services/agent_evaluation.py`

```python
class TestCase:
    """A single test case for an agent."""
    id: str
    name: str
    agent_id: str
    input: dict                 # Input to agent.run()
    expected_output: dict | None  # Optional expected output for exact matching
    assertions: list[dict]      # [{type: "contains", field: "articles", value: ...}]
    tags: list[str]             # ["smoke", "regression", "edge-case"]

class EvaluationRun:
    """Results of running a test suite against an agent."""
    id: str
    agent_id: str
    config_snapshot: dict       # Agent config at time of evaluation
    test_cases: list[TestCaseResult]
    summary: EvaluationSummary
    started_at: datetime
    completed_at: datetime

class EvaluationSummary:
    total: int
    passed: int
    failed: int
    errors: int
    avg_duration_ms: float
    avg_tokens_used: int
    pass_rate: float

class AgentEvaluationService:
    """Run test suites and track evaluation results."""

    async def create_test_case(self, test_case: TestCase) -> TestCase:
        """Create a new test case for an agent."""

    async def run_evaluation(
        self,
        agent_id: str,
        test_case_ids: list[str] | None = None,
        tags: list[str] | None = None,
        config_override: dict | None = None,
    ) -> EvaluationRun:
        """Run test cases against an agent. Optionally override config."""

    async def compare_evaluations(
        self,
        run_ids: list[str],
    ) -> ComparisonReport:
        """Compare results across multiple evaluation runs."""

    async def get_evaluation_history(
        self,
        agent_id: str,
        limit: int = 20,
    ) -> list[EvaluationRun]:
        """Get historical evaluation results for trend analysis."""
```

#### Assertion Types

| Type | Description | Example |
|------|-------------|---------|
| `contains` | Output field contains value | `{field: "articles", value: "AI"}` |
| `length_gte` | Array field has at least N items | `{field: "articles", min: 3}` |
| `key_exists` | Output contains key | `{field: "newsletter.html"}` |
| `type_check` | Field is expected type | `{field: "word_count", expected_type: "int"}` |
| `range` | Numeric field in range | `{field: "score", min: 0.0, max: 1.0}` |
| `latency_under` | Execution under N ms | `{max_ms: 5000}` |
| `llm_judge` | LLM evaluates quality | `{prompt: "Is this professional?", threshold: 0.8}` |

### 3.2 Backend: Evaluation API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/studio/agents/{id}/test-cases` | Create test case |
| GET | `/api/v1/studio/agents/{id}/test-cases` | List test cases |
| PUT | `/api/v1/studio/agents/{id}/test-cases/{tc_id}` | Update test case |
| DELETE | `/api/v1/studio/agents/{id}/test-cases/{tc_id}` | Delete test case |
| POST | `/api/v1/studio/agents/{id}/evaluate` | Run evaluation |
| GET | `/api/v1/studio/agents/{id}/evaluations` | List evaluation runs |
| GET | `/api/v1/studio/evaluations/{run_id}` | Get evaluation details |
| POST | `/api/v1/studio/evaluations/compare` | Compare multiple runs |

### 3.3 Frontend: Evaluation UI

#### Test Case Manager

```
+------------------------------------------------------------------+
|  Research Agent — Test Cases                      [+ New Test Case]|
|------------------------------------------------------------------|
|  [All (12)] [Smoke (3)] [Regression (7)] [Edge Cases (2)]        |
|------------------------------------------------------------------|
|                                                                   |
|  ✓ Basic topic search               smoke      Last: ✓  2.1s    |
|  ✓ Multi-topic search               smoke      Last: ✓  3.4s    |
|  ✗ Empty topics fallback            edge-case   Last: ✗  0.3s    |
|  ✓ Custom prompt search             regression  Last: ✓  4.8s    |
|  ...                                                              |
|                                                                   |
|  [▶ Run All] [▶ Run Smoke] [▶ Run Selected]                      |
+------------------------------------------------------------------+
```

#### Evaluation Results

```
+------------------------------------------------------------------+
|  Evaluation Run #42                          Feb 10, 2026 14:30   |
|------------------------------------------------------------------|
|  Agent: Research Agent    Config: Gemini / gemini-pro / temp=0.7  |
|                                                                   |
|  Summary:  12 total | 10 passed | 1 failed | 1 error             |
|  Pass rate: 83.3%   | Avg duration: 3.2s  | Avg tokens: 1,420    |
|                                                                   |
|  +------+--------------------+--------+-------+-------+          |
|  | #    | Test Case          | Status | Time  | Tokens|          |
|  +------+--------------------+--------+-------+-------+          |
|  | 1    | Basic topic search | ✓ Pass | 2.1s  | 980   |          |
|  | 2    | Multi-topic search | ✓ Pass | 3.4s  | 1,540 |          |
|  | 3    | Empty topics       | ✗ Fail | 0.3s  | 0     |          |
|  | ...                                                  |          |
|  +------+--------------------+--------+-------+-------+          |
|                                                                   |
|  [Compare with Previous] [Export CSV]                             |
+------------------------------------------------------------------+
```

#### Trend Chart

Line chart showing pass rate, average duration, and token usage across evaluation runs over time. Useful for catching regressions when models or prompts change.

### 3.4 Deliverables

- [ ] Test case CRUD with assertion types
- [ ] Evaluation runner with config override support
- [ ] Comparison engine for multiple runs
- [ ] Evaluation API endpoints
- [ ] Test case manager UI
- [ ] Evaluation results view with per-test-case details
- [ ] Comparison view (side-by-side)
- [ ] Trend chart for historical quality tracking
- [ ] LLM-as-judge assertion type
- [ ] MongoDB storage for test cases and evaluation results

---

## Phase 4: Agent Lifecycle Management

**Priority:** Medium-Low — Important for production deployments with multiple environments, but not needed until the team has multiple agents in active development.

### Goal

Manage agent lifecycle states (private/staging/published), version configurations, and promote agents between environments with audit trails.

### 4.1 Agent States

```
  ┌──────────┐    promote     ┌──────────┐    publish    ┌──────────┐
  │  PRIVATE  │ ────────────► │ STAGING  │ ────────────► │ PUBLISHED│
  │  (draft)  │               │ (testing) │               │  (live)  │
  └──────────┘               └──────────┘               └──────────┘
       ▲                           │                          │
       │         unpublish         │       unpublish          │
       └───────────────────────────┴──────────────────────────┘
```

| State | Description | Who Can See | Who Can Execute |
|-------|-------------|-------------|-----------------|
| Private | In development, not visible to other users | Creator only | Creator only |
| Staging | Available for testing, not used by live workflows | Team members | Team + evaluations |
| Published | Active in production workflows | Everyone | All workflows |

### 4.2 Backend: Versioning Model

```python
class AgentVersion:
    """Immutable snapshot of an agent's configuration."""
    version_id: str
    agent_id: str
    version: str                # Semantic version: "1.2.0"
    state: str                  # "private" | "staging" | "published"
    config: dict                # Full agent config at this version
    system_prompt: str
    changelog: str              # What changed in this version
    created_by: str
    created_at: datetime
    promoted_at: datetime | None
    published_at: datetime | None

class AgentLifecycleService:
    async def create_version(self, agent_id: str, config: dict, changelog: str) -> AgentVersion
    async def promote_to_staging(self, version_id: str) -> AgentVersion
    async def publish(self, version_id: str) -> AgentVersion
    async def unpublish(self, version_id: str) -> AgentVersion
    async def rollback(self, agent_id: str, target_version: str) -> AgentVersion
    async def get_version_history(self, agent_id: str) -> list[AgentVersion]
    async def diff_versions(self, v1: str, v2: str) -> dict
```

### 4.3 Backend: Lifecycle API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/studio/agents/{id}/versions` | Create new version |
| GET | `/api/v1/studio/agents/{id}/versions` | List version history |
| GET | `/api/v1/studio/agents/{id}/versions/{vid}` | Get version detail |
| POST | `/api/v1/studio/agents/{id}/versions/{vid}/promote` | Promote to staging |
| POST | `/api/v1/studio/agents/{id}/versions/{vid}/publish` | Publish to production |
| POST | `/api/v1/studio/agents/{id}/versions/{vid}/unpublish` | Unpublish |
| POST | `/api/v1/studio/agents/{id}/rollback` | Rollback to previous version |
| GET | `/api/v1/studio/agents/{id}/versions/diff` | Diff two versions |

### 4.4 Frontend: Lifecycle UI

#### Version Timeline

```
+------------------------------------------------------------------+
|  Research Agent — Versions                                        |
|------------------------------------------------------------------|
|                                                                   |
|  v1.3.0  ● PUBLISHED   Feb 10, 2026                              |
|  │  "Improved scoring prompt for better relevance"                |
|  │  Config: Gemini / gemini-2.0-flash / temp=0.5                  |
|  │  [View] [Diff with Previous] [Rollback to This]               |
|  │                                                                |
|  v1.2.0  ○ STAGING     Feb 8, 2026                                |
|  │  "Added custom prompt search capability"                       |
|  │  Config: Gemini / gemini-2.0-flash / temp=0.7                  |
|  │  [View] [Promote] [Diff]                                      |
|  │                                                                |
|  v1.1.0  ○ PRIVATE     Feb 5, 2026                                |
|  │  "Switched from Ollama to Gemini"                              |
|  │  [View] [Diff]                                                 |
|  │                                                                |
|  v1.0.0  ○ PRIVATE     Jan 28, 2026                               |
|     "Initial implementation"                                      |
|     [View]                                                        |
|                                                                   |
+------------------------------------------------------------------+
```

#### Version Diff View

Side-by-side comparison of config, prompt, and tool changes between two versions. Highlights additions, removals, and modifications.

### 4.5 Deliverables

- [ ] AgentVersion model in MongoDB
- [ ] AgentLifecycleService with state transitions
- [ ] Version CRUD API endpoints
- [ ] Promote/publish/rollback endpoints
- [ ] Version diff engine (config + prompt)
- [ ] Version timeline UI
- [ ] Diff view component
- [ ] State badges in catalog cards
- [ ] Rollback confirmation dialog with evaluation gate

---

## Phase 5: Agent Templates & Extensibility

**Priority:** Low — Quality-of-life feature for teams creating new agents frequently. Builds on all previous phases.

### Goal

Provide starter templates and a guided wizard for creating new agents without writing boilerplate. Enable cloning existing agents as starting points.

### 5.1 Agent Templates

Pre-built templates covering common agent patterns:

| Template | Description | Includes |
|----------|-------------|----------|
| Simple Responder | Single-turn Q&A agent | Basic prompt, no tools |
| Search & Summarize | Research agent with web search | Tavily tool, scoring prompt |
| Content Generator | Multi-format content creation | Format templates, tone support |
| Data Processor | Structured data transformation | JSON schema validation |
| Conversational | Multi-turn chat agent | Memory config, context management |
| RAG Agent | Retrieval-augmented generation | Vector store config, retrieval prompt |

Each template generates:
- `agent.py` with the agent class and `run()` implementation
- `llm.py` with provider configuration
- `prompts.py` with system prompt templates
- `tools.py` if tools are included
- Test file with basic test cases

### 5.2 Agent Creation Wizard

```
+------------------------------------------------------------------+
|  Create New Agent                                    Step 2 of 4  |
|  ○────────●────────○────────○                                     |
|  Template  Config   Prompt   Review                               |
|------------------------------------------------------------------|
|                                                                   |
|  Agent Configuration                                              |
|                                                                   |
|  Name:        [  my_analyzer                  ]                   |
|  Platform:    [  newsletter              ▼    ]                   |
|  Description: [  Analyze article sentiment    ]                   |
|                                                                   |
|  LLM Provider                                                     |
|  Provider:    [  Gemini                  ▼    ]                   |
|  Model:       [  gemini-2.0-flash        ▼    ]                   |
|  Temperature: [=====●===========] 0.3                             |
|  Max Tokens:  [  500                          ]                   |
|                                                                   |
|  Tools                                                            |
|  [✓] Web Search (Tavily)                                          |
|  [ ] Vector Store Retrieval                                       |
|  [ ] Custom Function                                              |
|                                                                   |
|                                    [← Back]  [Next: Prompt →]     |
+------------------------------------------------------------------+
```

### 5.3 Agent Cloning

Clone an existing agent as a starting point:

- Copies config, prompt, and tools
- Assigns a new name and ID
- Starts in PRIVATE state
- Preserves test cases (optional)
- Links back to source agent for reference

### 5.4 Backend: Template Service

```python
class AgentTemplateService:
    async def list_templates(self) -> list[AgentTemplate]
    async def get_template(self, template_id: str) -> AgentTemplate
    async def generate_from_template(
        self, template_id: str, config: dict
    ) -> GeneratedAgentFiles
    async def clone_agent(
        self, source_agent_id: str, new_name: str, platform: str
    ) -> AgentRegistryEntry
```

### 5.5 Backend: Template API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/studio/templates` | List available templates |
| GET | `/api/v1/studio/templates/{id}` | Get template details |
| POST | `/api/v1/studio/templates/{id}/generate` | Generate agent from template |
| POST | `/api/v1/studio/agents/{id}/clone` | Clone an existing agent |

### 5.6 Deliverables

- [ ] Template definitions for 6 common patterns
- [ ] Code generation engine (Jinja2 templates for Python files)
- [ ] Agent creation wizard (4-step form)
- [ ] Agent cloning with config/prompt/tool copy
- [ ] Template API endpoints
- [ ] Template browser UI
- [ ] Generated file preview before creation

---

## File Structure

After all 5 phases, the Agent Studio adds:

```
backend/
├── app/
│   ├── api/v1/
│   │   └── agent_studio.py              # All studio endpoints
│   └── common/
│       └── services/
│           ├── agent_registry.py         # Phase 1: Discovery & catalog
│           ├── agent_evaluation.py       # Phase 3: Testing & evaluation
│           ├── agent_lifecycle.py        # Phase 4: Versioning & promotion
│           └── agent_templates.py        # Phase 5: Templates & cloning

frontend/
├── src/
│   ├── pages/
│   │   └── StudioPage.tsx               # Main studio page
│   ├── components/
│   │   └── studio/
│   │       ├── AgentCatalogCard.tsx      # Phase 1
│   │       ├── AgentCatalogGrid.tsx      # Phase 1
│   │       ├── PlatformFilter.tsx        # Phase 1
│   │       ├── AgentSearch.tsx           # Phase 1
│   │       ├── AgentDetailDrawer.tsx     # Phase 1
│   │       ├── AgentInspector.tsx        # Phase 2
│   │       ├── LLMConfigEditor.tsx       # Phase 2
│   │       ├── PromptEditor.tsx          # Phase 2
│   │       ├── TryItPanel.tsx            # Phase 2
│   │       ├── ExecutionLog.tsx          # Phase 2
│   │       ├── TestCaseManager.tsx       # Phase 3
│   │       ├── EvaluationResults.tsx     # Phase 3
│   │       ├── EvaluationComparison.tsx  # Phase 3
│   │       ├── TrendChart.tsx            # Phase 3
│   │       ├── VersionTimeline.tsx       # Phase 4
│   │       ├── VersionDiff.tsx           # Phase 4
│   │       ├── TemplateBrowser.tsx       # Phase 5
│   │       └── AgentWizard.tsx           # Phase 5
│   ├── api/
│   │   └── studio.ts                    # Studio API client
│   ├── hooks/
│   │   └── useStudio.ts                 # React Query hooks
│   └── types/
│       └── studio.ts                    # TypeScript types
```

---

## Dependencies Between Phases

```
Phase 1 (Registry & Catalog)
    │
    ├──► Phase 2 (Inspector & Config)
    │        │
    │        └──► Phase 3 (Evaluation & Testing)
    │                 │
    │                 └──► Phase 4 (Lifecycle Management)
    │                          │
    │                          └──► Phase 5 (Templates & Extensibility)
    │
    └──► Phase 5 can start partially after Phase 1 (template browsing)
```

Phase 1 is the foundation — all other phases build on it. Phase 2 and Phase 3 are the most valuable follow-ups. Phase 4 and 5 can be deferred until the team scales.
