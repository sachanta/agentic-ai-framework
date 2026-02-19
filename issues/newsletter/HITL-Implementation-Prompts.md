# HITL Workflow Implementation Prompts

Detailed, stage-by-stage prompts for implementing a Human-in-the-Loop workflow with LangGraph (backend) and React (frontend). Each prompt is self-contained and includes explicit data contracts, constraints, and pitfalls learned from production debugging.

**Use one prompt per session.** Each prompt assumes the previous stages are complete.

---

## Table of Contents

| # | Stage | Scope |
|---|-------|-------|
| 1 | [State Schema & MongoDB Checkpointer](#prompt-1-state-schema--mongodb-checkpointer) | Backend |
| 2 | [LangGraph Wiring & Orchestrator](#prompt-2-langgraph-wiring--orchestrator) | Backend |
| 3 | [API Endpoints & SSE Streaming](#prompt-3-api-endpoints--sse-streaming) | Backend |
| 4 | [Frontend Infrastructure](#prompt-4-frontend-infrastructure) | Frontend |
| 5 | [Checkpoint 1 — Article Review](#prompt-5-checkpoint-1--article-review) | Full-stack |
| 6 | [Checkpoint 2 — Content Review](#prompt-6-checkpoint-2--content-review) | Full-stack |
| 7 | [Checkpoint 3 — Subject Line Review](#prompt-7-checkpoint-3--subject-line-review) | Full-stack |
| 8 | [Checkpoint 4 — Final Send Approval](#prompt-8-checkpoint-4--final-send-approval) | Full-stack |
| 9 | [Main App Integration & Workflow UI](#prompt-9-main-app-integration--workflow-ui) | Frontend |

---

## Prompt 1: State Schema & MongoDB Checkpointer

### Context

We are building a newsletter generation platform using LangGraph for multi-agent orchestration with Human-in-the-Loop (HITL) checkpoints. The workflow pauses at 4 checkpoints to collect human approval before proceeding. LangGraph's `interrupt()` / `Command(resume=)` mechanism handles pausing and resuming.

State must persist across interrupts so the workflow can resume hours or days later. We use MongoDB as the persistence backend via a custom LangGraph checkpointer.

### Task

Implement two files:

#### 1. `orchestrator/state.py` — NewsletterState TypedDict

Define the full workflow state as a `TypedDict` with `total=False`. Every field must have a clear type annotation. Group fields by purpose with comments.

```python
class NewsletterState(TypedDict, total=False):
    # --- Input Parameters ---
    user_id: str
    topics: list[str]
    tone: str                              # "professional", "casual", "formal", "urgent"
    custom_prompt: str | None
    max_articles: int                      # default: 10

    # --- Preferences (from PreferenceAgent) ---
    preferences: dict[str, Any]
    preferences_applied: bool

    # --- Prompt Analysis (from CustomPromptAgent) ---
    prompt_analysis: dict[str, Any] | None
    extracted_topics: list[str] | None

    # --- Research Results ---
    articles: list[dict[str, Any]]         # Each: {title, url, source, summary, score}
    research_metadata: dict[str, Any]
    research_completed: bool               # routing flag: False triggers re-research

    # --- Newsletter Content ---
    newsletter_content: str                # Markdown
    newsletter_html: str                   # HTML
    newsletter_plain: str                  # Plain text
    word_count: int
    content_generated: bool                # routing flag: False triggers re-generation

    # --- Subject Lines ---
    subject_lines: list[dict[str, str]]    # Each: {"text": "...", "style": "professional|casual|..."}
    selected_subject: str | None
    subjects_generated: bool               # routing flag: False triggers re-generation

    # --- Workflow Control ---
    workflow_id: str
    status: str                            # running, awaiting_approval, completed, cancelled, failed
    current_step: str | None
    error: str | None

    # --- Checkpoint State ---
    current_checkpoint: dict[str, Any] | None   # CheckpointData dict
    checkpoint_response: dict[str, Any] | None  # Last user response
    checkpoints_completed: list[str]             # e.g. ["research_review", "content_review"]

    # --- Storage ---
    newsletter_id: str | None
    stored_in_db: bool
    stored_in_rag: bool

    # --- Email Delivery ---
    email_sent: bool
    email_scheduled: str | None            # ISO datetime
    recipient_count: int
    test_recipients: list[str]             # Ad-hoc test emails from final approval UI

    # --- Timestamps ---
    history: list[dict[str, Any]]
    created_at: str                        # ISO datetime
    updated_at: str                        # ISO datetime
```

Also define a `CheckpointData` TypedDict:

```python
class CheckpointData(TypedDict, total=False):
    checkpoint_id: str
    checkpoint_type: str       # "research_review" | "content_review" | "subject_review" | "final_review"
    title: str
    description: str
    data: dict[str, Any]       # Checkpoint-specific payload
    actions: list[str]         # Available actions: ["approve", "edit", "reject"]
    created_at: str
```

**IMPORTANT — Data format contract for `subject_lines`:**

The field MUST be `list[dict[str, str]]` with keys `text` and `style`, NOT `list[str]`. The WritingAgent may return `{"text": "...", "angle": "curiosity"}` — the checkpoint node must normalize `angle` to `style` before storing. The frontend `SubjectReview` component calls `.style.toLowerCase()` on each entry and will crash with `TypeError` if `style` is missing.

**CRITICAL — `store_newsletter_node` must extract strings from subject dicts:**

The `Newsletter` Pydantic model has `subject_line_options: List[str]`, but `state["subject_lines"]` is `list[dict]` after normalization. Passing dicts directly causes `ValidationError: Input should be a valid string`. Extract text before passing:

```python
subject_line_options=[
    s.get("text", str(s)) if isinstance(s, dict) else str(s)
    for s in state.get("subject_lines", [])
],
```

#### 2. `orchestrator/mongodb_saver.py` — Custom LangGraph Checkpointer

Implement `MongoDBSaver` extending `BaseCheckpointSaver` from `langgraph.checkpoint.base`.

**CRITICAL — Binary serialization:**

LangGraph's `JsonPlusSerializer.dumps_typed()` returns `(type_str: str, data_bytes: bytes)`. The `data_bytes` is **msgpack binary**, NOT valid UTF-8. You MUST base64-encode before storing in MongoDB and base64-decode when loading. Apply this to ALL serialized fields:

```python
import base64

# Storing:
type_str, data_bytes = self.serde.dumps_typed(channel_values)
doc["channel_values"] = base64.b64encode(data_bytes).decode("ascii")
doc["channel_values_type"] = type_str

# Loading:
data_bytes = base64.b64decode(doc["channel_values"])
channel_values = self.serde.loads_typed((doc["channel_values_type"], data_bytes))
```

Without base64 encoding, you'll get `UnicodeDecodeError: 'utf-8' codec can't decode byte 0x81`.

**CRITICAL — PendingWrite is a plain tuple:**

`PendingWrite` from `langgraph.checkpoint.base` is a `tuple[str, str, Any]` type alias, NOT a named tuple. Do NOT use keyword arguments:

```python
# WRONG — raises TypeError: tuple() takes no keyword arguments
PendingWrite(task_id=tid, channel=ch, value=val)

# CORRECT — plain positional tuple
(tid, ch, val)
```

**Methods to implement:**

| Method | Sync/Async | Purpose |
|--------|-----------|---------|
| `get_tuple(config)` | sync | Load latest checkpoint for thread |
| `aget_tuple(config)` | async | Async version |
| `put(config, checkpoint, metadata, new_versions)` | sync | Store checkpoint |
| `aput(config, checkpoint, metadata, new_versions)` | async | Async version |
| `put_writes(config, writes, task_id, task_path)` | sync | Store pending writes |
| `aput_writes(config, writes, task_id, task_path)` | async | Async version |
| `list(config, *, filter, before, limit)` | sync generator | List checkpoints |
| `alist(config, *, filter, before, limit)` | async generator | Async version |

**MongoDB collections:**

- `langgraph_checkpoints` — full state snapshots, indexed on `(thread_id, checkpoint_ns, checkpoint_id)`
- `langgraph_writes` — pending writes between checkpoints, same index

**Use `datetime.now(timezone.utc)` for timestamps**, not `datetime.utcnow()` (deprecated).

### Expected Output

- `orchestrator/state.py` — NewsletterState and CheckpointData TypedDicts
- `orchestrator/mongodb_saver.py` — MongoDBSaver class with all 8 methods
- Unit tests for serialization round-trip (base64 encode → store → load → decode)

---

## Prompt 2: LangGraph Wiring & Orchestrator

### Context

State schema and MongoDB checkpointer are implemented (see `orchestrator/state.py` and `orchestrator/mongodb_saver.py`). Now we need to wire up the LangGraph `StateGraph` and the orchestrator class that manages workflow lifecycle.

### Task

Implement two files:

#### 1. `orchestrator/graph.py` — LangGraph StateGraph Definition

Build the graph with these nodes and edges:

```
get_preferences → process_prompt → research → checkpoint_articles
    → [route_after_article_checkpoint]
        ├─ "research" (rejected) → research
        └─ "generate_content" (approved) → generate_content

generate_content → checkpoint_content
    → [route_after_content_checkpoint]
        ├─ "generate_content" (rejected) → generate_content
        └─ "create_subjects" (approved) → create_subjects

create_subjects → checkpoint_subjects
    → [route_after_subject_checkpoint]
        ├─ "create_subjects" (rejected) → create_subjects
        └─ "format_email" (approved) → format_email

format_email → store_newsletter → checkpoint_send
    → [route_after_send_checkpoint]
        ├─ "send_email" (send now) → send_email → END
        └─ END (cancel/schedule)
```

**Routing functions** — each checks a boolean flag in state:

```python
def route_after_article_checkpoint(state):
    return "research" if not state.get("research_completed", False) else "generate_content"

def route_after_content_checkpoint(state):
    return "generate_content" if not state.get("content_generated", False) else "create_subjects"

def route_after_subject_checkpoint(state):
    return "create_subjects" if not state.get("subjects_generated", False) else "format_email"

def route_after_send_checkpoint(state):
    if state.get("status") in ("cancelled", "scheduled"):
        return END
    return "send_email"
```

**IMPORTANT:** Use `add_conditional_edges` with an explicit mapping dict:

```python
graph.add_conditional_edges(
    "checkpoint_articles",
    route_after_article_checkpoint,
    {"research": "research", "generate_content": "generate_content"},
)
```

The mapping dict must include ALL possible return values from the routing function.

**Graph compilation:**

```python
from langgraph.graph import StateGraph, END
from .mongodb_saver import MongoDBSaver

checkpointer = MongoDBSaver(async_db=get_async_db())
graph = StateGraph(NewsletterState)
# ... add nodes and edges ...
compiled_graph = graph.compile(checkpointer=checkpointer)
```

#### 2. `orchestrator/orchestrator.py` — NewsletterOrchestrator Class

Implement the orchestrator with these methods:

##### `async run(input: dict) -> dict`

- Creates initial state from input parameters
- Generates `workflow_id = str(uuid4())`
- Calls `self.graph.ainvoke(initial_state, config)` where `config = {"configurable": {"thread_id": workflow_id}}`
- After `ainvoke` returns, checks `state_snapshot = await self.graph.aget_state(config)`. If `state_snapshot.next` is not empty, the workflow is paused at a checkpoint
- Returns `{"workflow_id": ..., "status": "awaiting_approval" | "completed", ...}`

##### `async get_workflow_status(workflow_id: str) -> dict`

- Loads state with `aget_state(config)`
- Returns `status`, `current_step`, `checkpoints_completed`, etc.

**CRITICAL — Node-to-step mapping:** LangGraph only knows node names (e.g., `checkpoint_articles`), but the frontend tracker uses step IDs (e.g., `research_review`). You MUST map them:

```python
node_to_step = {
    "checkpoint_articles": "research_review",
    "checkpoint_content": "content_review",
    "checkpoint_subjects": "subject_review",
    "checkpoint_send": "final_review",
}
if state_snapshot.next:
    next_node = state_snapshot.next[0]
    current_step = node_to_step.get(next_node, state.get("current_step"))
```

Without this mapping, the frontend WorkflowTracker won't know which step is current and all step indicators will be wrong.

##### `async get_pending_checkpoint(workflow_id: str) -> dict | None`

- Extracts the interrupt value from `state_snapshot.tasks[].interrupts[].value`
- Returns the `CheckpointData` dict that was passed to `interrupt()`
- Returns `None` if no pending checkpoint

```python
for task in state_snapshot.tasks:
    if hasattr(task, 'interrupts') and task.interrupts:
        interrupt_value = task.interrupts[0].value
        # interrupt_value is the CheckpointData dict passed to interrupt()
        return {
            "workflow_id": workflow_id,
            **vars(interrupt_value) if hasattr(interrupt_value, '__dict__') else interrupt_value,
        }
```

##### `async approve_checkpoint(workflow_id, checkpoint_id, action, modifications, feedback) -> dict`

**CRITICAL — Use `Command(resume=)`, NOT `ainvoke()` with new state:**

```python
from langgraph.types import Command

response = {"action": action, "checkpoint_id": checkpoint_id}
if modifications:
    response.update(modifications)
if feedback:
    response["feedback"] = feedback

# This resumes the interrupted node — interrupt() returns `response`
result = await self.graph.ainvoke(Command(resume=response), config)
```

If you use `self.graph.ainvoke({"checkpoint_response": response}, config)` instead, it will **start a brand new graph execution from scratch** instead of resuming the paused one. The workflow will loop back to `get_preferences` and re-run all previous steps.

**IMPORTANT — This call is BLOCKING.** When `Command(resume=)` runs, LangGraph executes all nodes from the resume point until the next `interrupt()` or `END`. This can take 30-120+ seconds if multiple LLM calls are involved. The HTTP request stays open the entire time. The API endpoint and frontend client must have timeouts of at least 5 minutes.

After the call, check `aget_state(config)` again to determine if there's another checkpoint waiting.

### Expected Output

- `orchestrator/graph.py` — compiled StateGraph with all nodes, edges, and routing functions
- `orchestrator/orchestrator.py` — orchestrator class with `run()`, `get_workflow_status()`, `get_pending_checkpoint()`, `approve_checkpoint()`

---

## Prompt 3: API Endpoints & SSE Streaming

### Context

The LangGraph orchestrator is implemented with `run()`, `approve_checkpoint()`, `get_workflow_status()`, and `get_pending_checkpoint()` methods. Now we need FastAPI router endpoints that the frontend will call, plus a Server-Sent Events (SSE) endpoint for real-time workflow updates.

### Task

Implement two files:

#### 1. `router.py` — Top-level `/generate` endpoint

```python
@router.post("/generate")
async def generate_newsletter(request, current_user = Depends(get_current_user)):
    service = NewsletterService()
    result = await service.generate_newsletter(...)
    return GenerateNewsletterResponse(
        workflow_id=result["workflow_id"],
        status=result["status"],
        message=result.get("message", "Newsletter generation started"),
    )
```

#### 2. `routers/workflows.py` — Workflow HITL endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/workflows` | List workflows with optional `status` filter |
| GET | `/workflows/{id}` | Get workflow status |
| GET | `/workflows/{id}/checkpoint` | Get pending checkpoint data |
| POST | `/workflows/{id}/approve` | Approve/edit checkpoint |
| POST | `/workflows/{id}/reject` | Reject checkpoint |
| POST | `/workflows/{id}/cancel` | Cancel workflow |
| GET | `/workflows/{id}/history` | Get workflow history |
| GET | `/workflows/{id}/stream` | SSE stream |

**CRITICAL — Route ordering:** If you define a catch-all path parameter route like `/{workflow_id}` before specific routes like `/stats`, FastAPI will match "stats" as a workflow_id. Always define specific routes BEFORE parameterized catch-all routes:

```python
# CORRECT order:
@router.get("/stats")           # specific route first
@router.get("/{workflow_id}")   # catch-all last

# WRONG order:
@router.get("/{workflow_id}")   # catches "stats" as a workflow_id
@router.get("/stats")           # never reached
```

**CRITICAL — SSE authentication:** The browser's `EventSource` API **cannot** set custom HTTP headers (like `Authorization: Bearer ...`). It can only send cookies or URL query parameters. You must accept the JWT token as a query parameter for the SSE endpoint:

```python
@router.get("/{workflow_id}/stream")
async def stream_workflow(
    workflow_id: str,
    token: str = Query(..., description="JWT auth token"),
):
    # Validate token manually — can't use Depends(get_current_user)
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    async def event_generator():
        while True:
            status = await orchestrator.get_workflow_status(workflow_id)
            yield {
                "event": "status",
                "data": json.dumps(status),
            }
            if status["status"] in ("completed", "cancelled", "failed"):
                yield {"event": "complete", "data": json.dumps(status)}
                break
            await asyncio.sleep(2)

    return EventSourceResponse(event_generator())
```

The frontend will connect with: `new EventSource(url + "?token=" + jwt)`

**Request/Response schemas** (Pydantic):

```python
class ApproveCheckpointRequest(BaseModel):
    checkpoint_id: str
    action: str                                # "approve", "edit", "reject"
    modifications: dict[str, Any] | None = None
    feedback: str | None = None

class RejectCheckpointRequest(BaseModel):
    checkpoint_id: str
    feedback: str | None = None
```

Use `model_config = {"populate_by_name": True}` for Pydantic v2 models, NOT `class Config`.

**CRITICAL — MemoryService API signatures must be consistent:**

If your `MemoryService.get()` and `.set()` use composite keys with `(user_id, cache_type, key)` parameters, ALL callers must pass all arguments. A common mistake is calling `self._memory_service.get(key)` with just 1 arg when the method requires 3. This causes `TypeError: get() missing 2 required positional arguments` at runtime. Verify EVERY call site matches the method signature.

**CRITICAL — MongoDB naive vs aware datetime comparison:**

MongoDB may return naive datetimes (no timezone info). If your code compares with `datetime.now(timezone.utc)` (timezone-aware), you get `TypeError: can't compare offset-naive and offset-aware datetimes`. Always normalize before comparing:

```python
expires_at = doc.get("expires_at")
if expires_at and expires_at.tzinfo is None:
    expires_at = expires_at.replace(tzinfo=timezone.utc)
if expires_at and expires_at < datetime.now(timezone.utc):
    # expired
```

### Expected Output

- `router.py` — updated with `/generate` endpoint
- `routers/workflows.py` — all workflow endpoints including SSE with query-param auth

---

## Prompt 4: Frontend Infrastructure

### Context

The backend API is complete with workflow CRUD endpoints, checkpoint approve/reject/edit, and SSE streaming. Now we need the frontend TypeScript infrastructure: types, API client, React Query hooks, SSE hook, and Zustand store.

### Task

Implement these 5 files:

#### 1. `types/newsletter.ts` — TypeScript Type Definitions

Define types that exactly match the backend API responses. Pay special attention to:

```typescript
// Step status used throughout the UI
type WorkflowStepStatus = 'running' | 'awaiting_approval' | 'completed' | 'cancelled' | 'failed';

// Checkpoint actions
type CheckpointAction = 'approve' | 'edit' | 'reject';

// The checkpoint_type MUST match the backend's interrupt checkpoint_type exactly
interface Checkpoint {
  checkpoint_id: string;
  checkpoint_type: 'research_review' | 'content_review' | 'subject_review' | 'final_review';
  title: string;
  description: string;
  data: Record<string, unknown>;
  actions: CheckpointAction[];
  created_at?: string;
}

// IMPORTANT: SubjectLine uses "style", not "angle"
// The backend normalizes WritingAgent's "angle" to "style" before sending
interface SubjectLine {
  text: string;
  style: string;  // "professional" | "casual" | "formal" | "enthusiastic" | "urgent"
}

// Workflow state from GET /workflows/{id}
interface WorkflowState {
  workflow_id: string;
  status: WorkflowStepStatus;
  current_step: string | null;        // matches WORKFLOW_STEPS[].id in WorkflowTracker
  topics: string[];
  tone: string;
  article_count: number;
  checkpoints_completed: string[];
  error: string | null;
  created_at: string;
  updated_at: string;
}

// SSE event types
interface SSEStatusEvent {
  workflow_id: string;
  status: WorkflowStepStatus;
  current_step: string | null;
}

interface SSECheckpointEvent {
  checkpoint_id: string;
  checkpoint_type: string;
  title: string;
  data: Record<string, unknown>;
}

interface SSECompleteEvent {
  status: 'completed' | 'cancelled' | 'failed';
  newsletter_id?: string;
}

interface SSEErrorEvent {
  error: string;
}
```

**CRITICAL — include `subject_review` in the checkpoint_type union.** If you only define `'research_review' | 'content_review' | 'final_review'`, the subject review checkpoint will hit the `default` case and show "Unknown checkpoint type" instead of the SubjectReview UI.

#### 2. `api/newsletter.ts` — API Client

**CRITICAL — Timeout configuration:** The default Axios timeout (30s) is NOT enough for checkpoint actions. When the user approves a checkpoint, `POST /approve` blocks while LangGraph runs all nodes up to the next `interrupt()`. This can take 30-120+ seconds for LLM calls (content generation, subject lines, summarization).

If the client times out before the server responds, `onSuccess` never fires, React Query never invalidates queries, and the UI appears stuck with the approve button re-enabled.

```typescript
const TIMEOUTS = {
  DEFAULT: 30000,         // 30s — normal CRUD
  RESEARCH: 180000,       // 3min — research involves external API calls
  GENERATION: 300000,     // 5min — LLM generation + multiple agents
  EXPORT: 120000,         // 2min — analytics export
};

// ALL checkpoint action endpoints need GENERATION timeout:
approveCheckpoint: async (workflowId, request) => {
  const response = await apiClient.post(
    `${BASE_PATH}/workflows/${workflowId}/approve`,
    request,
    { timeout: TIMEOUTS.GENERATION }   // 5 minutes, NOT default 30s
  );
  return response.data;
},

editCheckpoint: async (workflowId, request) => {
  const response = await apiClient.post(
    `${BASE_PATH}/workflows/${workflowId}/edit`,
    request,
    { timeout: TIMEOUTS.GENERATION }   // 5 minutes
  );
  return response.data;
},

rejectCheckpoint: async (workflowId, request) => {
  const response = await apiClient.post(
    `${BASE_PATH}/workflows/${workflowId}/reject`,
    request,
    { timeout: TIMEOUTS.GENERATION }   // 5 minutes
  );
  return response.data;
},
```

Also provide a helper for SSE URL:
```typescript
getWorkflowStreamUrl: (workflowId: string): string => {
  const baseUrl = apiClient.defaults.baseURL || '';
  return `${baseUrl}${BASE_PATH}/workflows/${workflowId}/stream`;
},
```

#### 3. `hooks/useNewsletter.ts` — React Query Hooks

```typescript
// Workflow polling — auto-poll every 2s while running
export function useWorkflow(workflowId: string) {
  return useQuery({
    queryKey: newsletterKeys.workflowDetail(workflowId),
    queryFn: () => newsletterApi.getWorkflow(workflowId),
    enabled: !!workflowId,
    refetchInterval: (query) => {
      if (query.state.data?.status === 'running') return 2000;
      return false;
    },
  });
}

// Checkpoint query — no retry (404 is expected when no checkpoint pending)
export function useWorkflowCheckpoint(workflowId: string) {
  return useQuery({
    queryKey: newsletterKeys.workflowCheckpoint(workflowId),
    queryFn: () => newsletterApi.getCheckpoint(workflowId),
    enabled: !!workflowId,
    retry: false,
  });
}

// **CRITICAL — getCheckpoint must return null on 404, NOT throw:**
// After the final checkpoint is approved, the workflow completes and there's
// no checkpoint left. The approve mutation invalidates the checkpoint query,
// which triggers a refetch BEFORE the SSE complete event arrives. If
// getCheckpoint throws on 404, React Query marks the query as errored and
// may show an error toast or break the UI.
getCheckpoint: async (workflowId: string): Promise<Checkpoint | null> => {
  try {
    const response = await apiClient.get(`.../${workflowId}/checkpoint`);
    return response.data;
  } catch (error: any) {
    if (error?.response?.status === 404) return null;  // no active checkpoint
    throw error;
  }
},

// Approve mutation — invalidate BOTH workflow detail AND checkpoint on success
export function useApproveCheckpoint() {
  return useMutation({
    mutationFn: ({ workflowId, request }) =>
      newsletterApi.approveCheckpoint(workflowId, request),
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: newsletterKeys.workflowDetail(data.workflow_id),
      });
      queryClient.invalidateQueries({
        queryKey: newsletterKeys.workflowCheckpoint(data.workflow_id),
      });
    },
  });
}
```

Cache invalidation on approve/reject is what triggers the UI to refetch and display the next checkpoint. If you only invalidate the workflow detail but not the checkpoint query, the old checkpoint UI will remain visible.

#### 4. `hooks/useWorkflowSSE.ts` — Server-Sent Events Hook

```typescript
export function useWorkflowSSE(
  workflowId: string | null,     // null = don't connect
  callbacks: WorkflowSSECallbacks
): WorkflowSSEState
```

**IMPORTANT — `workflowId` parameter type is `string | null`, not `string | undefined`:**

`useParams()` returns `string | undefined`, but this hook expects `null` for "don't connect". Callers must use `useWorkflowSSE(id ?? null, callbacks)` to convert.

**IMPORTANT — Auth token in URL:** EventSource can't set headers. Pass the JWT as a query parameter:

```typescript
const url = `${newsletterApi.getWorkflowStreamUrl(workflowId)}?token=${token}`;
const es = new EventSource(url);
```

**IMPORTANT — Python dict format:** If the backend uses Python's `json.dumps()` with default settings, the SSE data may contain Python-style values (`True`, `False`, `None`, single quotes in some edge cases). Parse carefully and handle potential format issues.

**Reconnection:** On connection loss, reconnect after 3 seconds. Close the connection on `'complete'` event.

#### 5. `store/newsletterStore.ts` — Zustand Store

```typescript
interface WorkflowUIState {
  activeWorkflowId: string | null;
  workflowStatus: WorkflowStepStatus | null;
  checkpointData: SSECheckpointEvent | Checkpoint | null;
}
```

**CRITICAL — Persist `activeWorkflowId` in localStorage:**

```typescript
persist(
  (set, get) => ({ ... }),
  {
    name: 'newsletter-storage',
    storage: createJSONStorage(() => localStorage),
    partialize: (state) => ({
      activeWorkflowId: state.activeWorkflowId,   // MUST include this
      // ... other persisted fields
    }),
  }
)
```

If you exclude `activeWorkflowId` from `partialize`, the workflow ID is lost on page refresh. The user will see "No Active Workflow" and lose access to their in-progress workflow. The ID is the key that triggers `useWorkflow()`, `useWorkflowCheckpoint()`, and `useWorkflowSSE()` — without it, none of those hooks activate and the entire workflow UI is empty.

### Expected Output

- `types/newsletter.ts` — all TypeScript interfaces
- `api/newsletter.ts` — complete API client with correct timeouts
- `hooks/useNewsletter.ts` — React Query hooks with polling and cache invalidation
- `hooks/useWorkflowSSE.ts` — SSE hook with auth and reconnection
- `store/newsletterStore.ts` — Zustand store with localStorage persistence

---

## Prompt 5: Checkpoint 1 — Article Review

### Context

The HITL infrastructure is in place (state, graph, orchestrator, API, frontend hooks/store). Now implement the first checkpoint end-to-end: the user reviews articles found by the ResearchAgent and approves, edits, or rejects the selection.

### Data Contract

This is the **exact** data flow. Both backend and frontend must follow this contract precisely.

#### Backend → Frontend (interrupt data via `GET /checkpoint`)

```json
{
  "checkpoint_id": "uuid",
  "checkpoint_type": "research_review",
  "title": "Review Article Selection",
  "description": "Review 8 articles found for your newsletter",
  "data": {
    "articles": [
      {
        "title": "Article Title",
        "url": "https://...",
        "source": "techcrunch.com",
        "summary": "Brief summary...",
        "score": 0.85
      }
    ],
    "topics": ["AI", "robotics"],
    "total_found": 8
  },
  "actions": ["approve", "edit", "reject"]
}
```

#### Frontend → Backend (approve via `POST /approve`)

```json
{
  "checkpoint_id": "uuid",
  "action": "approve",
  "modifications": {
    "articles": [/* user's selected/reordered articles */]
  },
  "feedback": "optional user comment"
}
```

#### Resume response keys (received by `checkpoint_articles_node` from `interrupt()`)

```python
{
    "action": "approve" | "edit" | "reject",
    "checkpoint_id": "uuid",
    "articles": [...],           # present for "edit" action
    "feedback": "..."            # optional
}
```

### Task

#### Backend: `checkpoint_articles_node` in `nodes.py`

```python
def checkpoint_articles_node(state: NewsletterState) -> dict:
    articles = state.get("articles", [])

    checkpoint_data = CheckpointData(
        checkpoint_id=str(uuid4()),
        checkpoint_type="research_review",     # MUST match frontend switch case
        title="Review Article Selection",
        description=f"Review {len(articles)} articles found for your newsletter",
        data={
            "articles": [
                {
                    "title": a.get("title", ""),
                    "url": a.get("url", ""),
                    "source": a.get("source", ""),
                    "summary": a.get("summary", ""),
                    "score": a.get("score", 0),
                }
                for a in articles
            ],
            "topics": state.get("topics", []),
            "total_found": len(articles),
        },
        actions=["approve", "edit", "reject"],
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    response = interrupt(checkpoint_data)

    # --- After resume ---
    action = response.get("action", "approve")

    if action == "reject":
        return {
            "research_completed": False,    # triggers re-research via routing
            "current_checkpoint": None,
            "checkpoint_response": response,
        }

    if action == "edit":
        return {
            "articles": response.get("articles", articles),
            "research_completed": True,
            "current_checkpoint": None,
            "checkpoint_response": response,
            "checkpoints_completed": state.get("checkpoints_completed", []) + ["research_review"],
        }

    # approve
    return {
        "current_checkpoint": None,
        "checkpoint_response": response,
        "checkpoints_completed": state.get("checkpoints_completed", []) + ["research_review"],
    }
```

#### Frontend: `workflow/ArticleReview.tsx`

Props interface:

```typescript
interface ArticleReviewProps {
  checkpoint: Checkpoint;
  articles: Article[];
  onApprove: (selectedArticles: Article[], feedback?: string) => void;
  onReject: (feedback?: string) => void;
  isLoading?: boolean;
  loadingAction?: CheckpointAction | null;
}
```

Features:
- Checkbox selection for each article (select/deselect)
- Select All / Clear All buttons
- Drag-to-reorder or Move Up/Down buttons
- Expandable article details (summary, scores)
- Score color coding: >= 0.8 green, >= 0.6 amber, < 0.6 red
- "Approve Selected" and "Reject & Re-research" action buttons
- Disable buttons while `isLoading` is true
- Show loading spinner on the button matching `loadingAction`

#### Frontend: Integration in `NewsletterApp.tsx`

```typescript
case 'research_review':
  return (
    <ArticleReview
      checkpoint={checkpoint}
      articles={(checkpointData.articles as Article[]) || []}
      onApprove={(articles, feedback) => {
        handleApproveCheckpoint({ articles }, feedback);
      }}
      onReject={handleRejectCheckpoint}
      isLoading={isWorkflowLoading}
      loadingAction={loadingAction}
    />
  );
```

### Expected Output

- Backend: `checkpoint_articles_node` function in `nodes.py`
- Frontend: `workflow/ArticleReview.tsx` component
- Frontend: `research_review` case in `NewsletterApp.tsx` `renderCheckpointUI()`

---

## Prompt 6: Checkpoint 2 — Content Review

### Context

Checkpoint 1 (Article Review) is complete. After the user approves articles, `generate_content_node` runs the WritingAgent to create newsletter content, then the workflow pauses at Checkpoint 2 for content review.

### Data Contract

#### Backend → Frontend (interrupt data)

```json
{
  "checkpoint_type": "content_review",
  "data": {
    "content": "# Newsletter Title\n\nMarkdown content...",
    "html_preview": "<h1>Newsletter Title</h1><p>HTML content...</p>",
    "word_count": 1250,
    "tone": "professional"
  }
}
```

**IMPORTANT — Key names in checkpoint data:**

The `generate_content_node` stores content in state as `newsletter_content` and `newsletter_html`. But the checkpoint's `data` dict should use `content` and `html_preview` as keys. These are what the frontend reads:
- `checkpointData.content` — markdown content for the editor
- `checkpointData.html_preview` — HTML for the preview pane

Do NOT nest these under a `newsletter` key. The frontend maps these flat fields directly.

#### Frontend → Backend (approve)

```json
{
  "action": "approve",
  "modifications": {
    "content": "edited markdown content..."
  }
}
```

#### Resume response keys

```python
{
    "action": "approve" | "edit" | "reject",
    "content": "...",            # present for "edit" action
    "feedback": "..."
}
```

### Task

#### Backend: `generate_content_node` and `checkpoint_content_node` in `nodes.py`

**IMPORTANT — WritingAgent output key:** `WritingAgent.run()` returns the newsletter under `result["newsletter"]`, NOT `result["content"]`. The newsletter dict has `markdown`, `html`, `plain_text` sub-keys:

```python
async def generate_content_node(state):
    agent = WritingAgent()
    result = await agent.run({
        "articles": state.get("articles", []),
        "tone": state.get("tone", "professional"),
    })
    newsletter = result.get("newsletter", {})    # NOT result.get("content")
    return {
        "newsletter_content": newsletter.get("markdown", newsletter.get("content", "")),
        "newsletter_html": newsletter.get("html", ""),
        "newsletter_plain": newsletter.get("plain_text", ""),
        "word_count": newsletter.get("word_count", 0),
        "content_generated": True,
        "current_step": "writing",
    }
```

#### Frontend: `workflow/ContentReview.tsx`

Props interface:

```typescript
interface ContentReviewProps {
  checkpoint: Checkpoint;
  content: { content: string; word_count: number } | Record<string, unknown>;
  formats?: { html?: string; text?: string; markdown?: string };
  onApprove: (content: string, feedback?: string) => void;
  onEdit: (content: string, feedback?: string) => void;
  onReject: (feedback?: string) => void;
  isLoading?: boolean;
  loadingAction?: CheckpointAction | null;
}
```

Features:
- Side-by-side layout: editor (left) and preview (right)
- Format tabs: HTML / Text / Markdown
- Editable textarea for content
- Word count and reading time (200 words/min)
- "Modified" badge when content differs from original
- Reset button to revert edits
- "Approve", "Approve with Edits", "Reject & Regenerate" buttons

#### Frontend: Integration in `NewsletterApp.tsx`

```typescript
case 'content_review':
  return (
    <ContentReview
      checkpoint={checkpoint}
      content={(checkpointData.newsletter as any) || {
        content: String(checkpointData.content || ''),
        word_count: Number(checkpointData.word_count || 0),
      }}
      formats={(checkpointData.formats as any) ||
        (checkpointData.html_preview
          ? { html: String(checkpointData.html_preview) }
          : undefined)}
      onApprove={(content, feedback) => {
        handleApproveCheckpoint({ content }, feedback);
      }}
      onEdit={(content, feedback) => {
        handleApproveCheckpoint({ content, action: 'edit' }, feedback);
      }}
      onReject={handleRejectCheckpoint}
      isLoading={isWorkflowLoading}
      loadingAction={loadingAction}
    />
  );
```

Note the defensive fallback: try `checkpointData.newsletter` first, then fall back to building an object from flat fields (`content`, `word_count`). This handles both possible backend formats.

### Expected Output

- Backend: `generate_content_node` and `checkpoint_content_node` in `nodes.py`
- Frontend: `workflow/ContentReview.tsx` component
- Frontend: `content_review` case in `renderCheckpointUI()`

---

## Prompt 7: Checkpoint 3 — Subject Line Review

### Context

Checkpoint 2 (Content Review) is complete. After content is approved, `create_subjects_node` runs the WritingAgent to generate subject line options, then the workflow pauses at Checkpoint 3.

### Data Contract

#### Backend → Frontend (interrupt data)

```json
{
  "checkpoint_type": "subject_review",
  "data": {
    "subject_lines": [
      {"text": "Your Weekly AI Digest: Breakthrough in Robotics", "style": "professional"},
      {"text": "You Won't Believe What AI Did This Week", "style": "casual"},
      {"text": "AI & Robotics: This Week's Must-Know Updates", "style": "professional"}
    ],
    "tone": "professional"
  }
}
```

**CRITICAL — Subject line normalization:**

The WritingAgent's `create_subject_lines()` returns dicts with key `"angle"` (e.g., `"curiosity"`, `"benefit"`, `"question"`). The frontend SubjectReview component expects key `"style"` (e.g., `"professional"`, `"casual"`, `"urgent"`). The backend checkpoint node MUST normalize before passing to `interrupt()`.

The frontend's `getStyleColor()` function calls `style.toLowerCase()`. If `style` is `undefined` (because the dict only has `angle`), you get `TypeError: can't access property "toLowerCase", style is undefined`.

Normalization mapping:

```python
angle_to_style = {
    "curiosity": "casual",
    "benefit": "professional",
    "question": "casual",
    "news": "professional",
    "urgency": "urgent",
    "direct": "professional",
}
```

Also handle edge cases:
- WritingAgent returns plain strings instead of dicts → wrap in `{"text": s, "style": default_tone}`
- WritingAgent returns unexpected types → convert with `str(s)`
- Empty list → provide fallback: `[{"text": "Your Newsletter Update", "style": tone}]`

#### Frontend → Backend (approve)

```json
{
  "action": "approve",
  "modifications": {
    "selected_subject": "Your Weekly AI Digest: Breakthrough in Robotics"
  }
}
```

**IMPORTANT:** The key is `selected_subject`, NOT `subject`. The `checkpoint_subjects_node` reads `response.get("selected_subject")` on resume.

#### Resume response keys

```python
{
    "action": "approve" | "edit" | "reject",
    "selected_subject": "...",       # for approve — text of chosen subject
    "custom_subject": "...",         # for edit — user-typed custom subject
    "feedback": "..."
}
```

### Task

#### Backend: `create_subjects_node` and `checkpoint_subjects_node` in `nodes.py`

Implement `_normalize_subject_lines()` helper:

```python
def _normalize_subject_lines(raw_subjects: list, default_tone: str = "professional") -> list[dict]:
    angle_to_style = {
        "curiosity": "casual", "benefit": "professional", "question": "casual",
        "news": "professional", "urgency": "urgent", "direct": "professional",
    }
    normalized = []
    for s in raw_subjects:
        if isinstance(s, dict):
            text = s.get("text", "")
            style = s.get("style") or angle_to_style.get(s.get("angle", ""), default_tone)
            normalized.append({"text": text, "style": style})
        elif isinstance(s, str):
            normalized.append({"text": s, "style": default_tone})
        else:
            normalized.append({"text": str(s), "style": default_tone})
    return normalized
```

Also implement `_extract_subject_text()` for safe text extraction (used in `store_newsletter_node` as title fallback):

```python
def _extract_subject_text(subject) -> str:
    if isinstance(subject, dict):
        return subject.get("text", str(subject))
    return str(subject)
```

#### Frontend: `workflow/SubjectReview.tsx`

Props interface:

```typescript
interface SubjectReviewProps {
  checkpoint: Checkpoint;
  subjectLines: SubjectLine[];     // MUST be {text: string, style: string}[]
  onApprove: (subject: string, feedback?: string) => void;
  onReject: (feedback?: string) => void;
  isLoading?: boolean;
  loadingAction?: CheckpointAction | null;
}
```

Features:
- Radio card selection (one at a time)
- Custom subject line text input option
- Style badge with color coding via `getStyleColor(style)`
- Character count per subject line
- Email preview showing selected subject
- "Select & Continue" and "Reject & Regenerate" buttons

#### Frontend: Integration in `NewsletterApp.tsx`

Add defensive normalization in the switch case to handle any format the backend might send:

```typescript
case 'subject_review':
  return (
    <SubjectReview
      checkpoint={checkpoint}
      subjectLines={((checkpointData.subject_lines as any[]) || []).map((s: any) =>
        typeof s === 'string'
          ? { text: s, style: 'professional' }
          : { text: s.text || String(s), style: s.style || s.angle || 'professional' }
      )}
      onApprove={(subject, feedback) => {
        handleApproveCheckpoint({ selected_subject: subject }, feedback);
      }}
      onReject={handleRejectCheckpoint}
      isLoading={isWorkflowLoading}
      loadingAction={loadingAction}
    />
  );
```

This double normalization (backend + frontend) ensures the component never receives `undefined` for `style`, regardless of what the WritingAgent returns.

### Expected Output

- Backend: `_normalize_subject_lines()`, `_extract_subject_text()`, `create_subjects_node`, `checkpoint_subjects_node`
- Frontend: `workflow/SubjectReview.tsx` component
- Frontend: `subject_review` case in `renderCheckpointUI()`

---

## Prompt 8: Checkpoint 4 — Final Send Approval

### Context

Checkpoint 3 (Subject Review) is complete. After a subject is selected, `format_email_node` formats the final email and `store_newsletter_node` saves it to the database. Then the workflow pauses at Checkpoint 4 for final send approval.

### Data Contract

#### Backend → Frontend (interrupt data)

```json
{
  "checkpoint_type": "final_review",
  "data": {
    "subject": "Your Weekly AI Digest: Breakthrough in Robotics",
    "preview_html": "<html>..full email HTML...</html>",
    "word_count": 1250,
    "recipient_count": 0,
    "newsletter_id": "mongo-object-id"
  }
}
```

**IMPORTANT:** The key for HTML content is `preview_html`, NOT `html_preview` (which is used in content_review) or `content`. The frontend must read `checkpointData.preview_html`.

#### Frontend → Backend (approve)

```json
{
  "action": "approve",
  "modifications": {
    "schedule_at": "2026-02-15T09:00:00"
  }
}
```

`schedule_at` is optional — omitted for "Send Now", present for "Schedule".

#### Resume response keys

```python
{
    "action": "send" | "schedule" | "cancel",
    "schedule_time": "...",          # ISO datetime for "schedule"
    "feedback": "..."
}
```

### Task

#### Backend: `checkpoint_send_node` in `nodes.py`

```python
def checkpoint_send_node(state):
    checkpoint_data = CheckpointData(
        checkpoint_type="final_review",    # NOT "send_approval"
        data={
            "subject": state.get("selected_subject", "Newsletter"),
            "preview_html": state.get("newsletter_html", ""),
            "word_count": state.get("word_count", 0),
            "recipient_count": state.get("recipient_count", 0),
            "newsletter_id": state.get("newsletter_id"),
        },
        ...
    )
    response = interrupt(checkpoint_data)

    action = response.get("action", "send")
    if action == "cancel":
        return {"status": "cancelled", "checkpoints_completed": ... + ["final_review"]}
    if action == "schedule":
        return {"email_scheduled": response.get("schedule_time"), "status": "scheduled", ...}
    return {"checkpoints_completed": ... + ["final_review"]}  # proceed to send_email
```

#### Frontend: `workflow/FinalApproval.tsx`

Props interface:

```typescript
interface FinalApprovalProps {
  checkpoint: Checkpoint;
  subject: string;
  content: string;              // HTML content for preview
  formats?: NewsletterFormats;
  articleCount: number;
  recipientCount?: number;      // defaults to 0
  onApprove: (scheduleAt?: string, feedback?: string) => void;
  onReject: (feedback?: string) => void;
  isLoading?: boolean;
  loadingAction?: CheckpointAction | null;
}
```

**CRITICAL — Disable send when no recipients, but provide a test email escape hatch:**

When `recipientCount === 0` from the subscriber list, the Send button must be disabled. But for development/testing, add a text input for ad-hoc test email addresses that bypasses the subscriber requirement:

```typescript
const [testEmails, setTestEmails] = useState('');
const parsedTestEmails = testEmails.split(',').map(e => e.trim()).filter(e => e.includes('@'));
const effectiveRecipientCount = recipientCount + parsedTestEmails.length;

// Send button uses effectiveRecipientCount, NOT recipientCount:
<Button disabled={isLoading || effectiveRecipientCount === 0} ... />
```

Show the test email input when there are no subscribers:

```typescript
{recipientCount === 0 && (
  <div className="space-y-2 p-4 bg-amber-50 rounded-lg">
    <span>No subscribers configured. Enter test email(s):</span>
    <Input
      value={testEmails}
      onChange={(e) => setTestEmails(e.target.value)}
      placeholder="email@example.com, another@example.com"
    />
  </div>
)}
```

Pass test recipients through the approve callback so the backend can use them:

```typescript
onApprove: (scheduleAt?, feedback?, testRecipients?: string[]) => void;
// In handleApprove:
onApprove(scheduleAt, undefined, parsedTestEmails.length > 0 ? parsedTestEmails : undefined);
```

Features:
- 4-column summary grid: subject chars, article count, reading time (word_count/200), recipient count
- Subject line preview
- HTML content preview via `<iframe srcDoc>` (h-[300px]) — NOT `dangerouslySetInnerHTML` (see Pitfall #33)
- Schedule toggle with date/time inputs (min date = today)
- "Send Now" / "Schedule" / "Go Back" buttons
- Warning + disabled button when no recipients

#### Frontend: Integration in `NewsletterApp.tsx`

```typescript
case 'final_review':
  return (
    <FinalApproval
      checkpoint={checkpoint}
      subject={String(checkpointData.subject || '')}
      content={String(checkpointData.preview_html || checkpointData.content || '')}
      formats={(checkpointData.formats as any) ||
        (checkpointData.preview_html
          ? { html: String(checkpointData.preview_html) }
          : undefined)}
      articleCount={Number(checkpointData.word_count || workflowData.article_count || 0)}
      recipientCount={Number(checkpointData.recipient_count || 0)}
      onApprove={(scheduleAt, feedback, testRecipients) => {
        handleApproveCheckpoint({ schedule_at: scheduleAt, test_recipients: testRecipients }, feedback);
      }}
      onReject={handleRejectCheckpoint}
      isLoading={isWorkflowLoading}
      loadingAction={loadingAction}
    />
  );
```

**IMPORTANT:** Pass `recipientCount` explicitly from checkpoint data. If you don't pass it, the component defaults to 0 but the button won't be disabled (it was a separate bug).

**CRITICAL — Construct `formats` from `preview_html` when `formats` is not in checkpoint data:**

The backend `checkpoint_send_node` sends `preview_html` but NOT `formats`. If you pass `formats={checkpointData.formats}` without a fallback, it will be `undefined`. The `FinalApproval` component checks `formats?.html` to decide whether to use `dangerouslySetInnerHTML` or a `<pre>` tag. Without `formats`, the HTML content will render as raw HTML tags in a `<pre>` block instead of as a rendered page.

The fix: `formats={(checkpointData.formats as any) || (checkpointData.preview_html ? { html: String(checkpointData.preview_html) } : undefined)}`

### Expected Output

- Backend: `format_email_node`, `store_newsletter_node`, `checkpoint_send_node`, `send_email_node`
- Frontend: `workflow/FinalApproval.tsx` component
- Frontend: `final_review` case in `renderCheckpointUI()`

---

## Prompt 9: Main App Integration & Workflow UI

### Context

All 4 checkpoint components are implemented. Now we need to integrate them into the main app with the workflow progress tracker, history timeline, tab routing, and state management.

### Task

Implement three components and update `NewsletterApp.tsx`:

#### 1. `workflow/WorkflowTracker.tsx` — Step Progress Indicator

Visual progress bar showing all workflow stages:

```
●────────●────────◉────────○────────○
Research  Review   Write    Final    Done
  ✓         ✓      ⏳       ...      ...
```

Define the step array that the tracker and the backend's `current_step` field share:

```typescript
export const WORKFLOW_STEPS: WorkflowStep[] = [
  { id: 'research',        label: 'Research',        description: 'Discover relevant articles' },
  { id: 'research_review', label: 'Review Articles',  description: 'Select and reorder articles' },
  { id: 'writing',         label: 'Generate',        description: 'Create newsletter content' },
  { id: 'content_review',  label: 'Review Content',   description: 'Edit and approve content' },
  { id: 'subject_review',  label: 'Select Subject',   description: 'Choose a subject line' },
  { id: 'final_review',    label: 'Final Review',    description: 'Confirm and schedule' },
];
```

**CRITICAL — `subject_review` MUST be in this array (Pitfall #32).** The backend sets `current_step = "subject_review"` when the subject checkpoint is active. If this step ID is missing from `WORKFLOW_STEPS`, `currentStepIndex` becomes `-1`, which breaks the `stepIndex < currentStepIndex` comparison — earlier steps like Research and Generate won't show checkmarks.

**CRITICAL — `getStepStatus` logic must handle the completed state:**

When the workflow completes, `current_step` is `"send_email"` which is NOT in `WORKFLOW_STEPS`. This makes `currentStepIndex = -1`, which breaks the index comparison logic. Without special handling, completed steps like "research" and "writing" won't show checkmarks.

```typescript
const getStepStatus = (stepId: string): 'completed' | 'current' | 'pending' | 'error' => {
  // MUST check this first — when workflow is done, all steps are complete
  if (status === 'completed') return 'completed';

  if (completedSteps.includes(stepId)) return 'completed';

  const stepIndex = WORKFLOW_STEPS.findIndex((s) => s.id === stepId);
  // Steps before the current step are implicitly completed
  if (currentStepIndex >= 0 && stepIndex >= 0 && stepIndex < currentStepIndex) {
    return 'completed';
  }

  if (currentStep === stepId) {
    if (status === 'failed') return 'error';
    return 'current';
  }
  return 'pending';
};
```

Also set progress bar width to 100% when completed:

```typescript
width: `${status === 'completed' ? 100 : Math.max(0, (currentStepIndex / (WORKFLOW_STEPS.length - 1)) * 100)}%`
```

Step indicators:
- Completed: filled circle with Check icon (primary color)
- Current: circle with spinning Loader2 icon
- Pending: circle with small dot
- Error: filled circle with "!" icon (destructive color)

#### 2. `workflow/WorkflowHistory.tsx` — Timeline of Steps

Display a timeline of workflow history entries. Each entry has step name, status, timestamp, and optional data (message, article_count, error).

#### 3. `NewsletterApp.tsx` — Main App Integration

Add a "Workflow" tab to the tab list:

```typescript
<TabsTrigger value="workflow">
  <GitBranch className="h-4 w-4" />
  Workflow
</TabsTrigger>
```

**CRITICAL — Initial view must check for persisted workflow:**

```typescript
const { activeWorkflowId, ... } = useWorkflowState();

// Auto-open workflow tab if a workflow was active before page refresh
const [view, setView] = useState<AppView>(
  activeWorkflowId ? 'workflow' : 'dashboard'
);
```

If you hardcode `useState<AppView>('dashboard')`, the user always lands on the Dashboard tab after refresh, even if they had an active workflow.

**Workflow tab layout — use full width:**

```typescript
<TabsContent value="workflow">
  {activeWorkflowId ? (
    <div className="space-y-6">
      {/* Workflow tracker — full width */}
      <Card>
        <CardContent className="pt-6">
          <WorkflowTracker
            currentStep={workflowData?.current_step || null}
            completedSteps={workflowData?.checkpoints_completed || []}
            status={workflowData?.status || null}
          />
        </CardContent>
      </Card>

      {/* Info bar — compact stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Workflow ID, Topics, Tone, Articles */}
      </div>

      {/* Checkpoint UI — full width */}
      <div className="w-full">
        {workflowData?.status === 'awaiting_approval' && checkpoint
          ? renderCheckpointUI()
          : /* processing or status display */}
      </div>

      {/* History — full width */}
      <WorkflowHistory history={history?.history || []} />
    </div>
  ) : (
    /* No active workflow — show empty state with link to Generate tab */
  )}
</TabsContent>
```

Do NOT use a multi-column grid layout (like `lg:grid-cols-3` with `col-span-2`) for the checkpoint UI. The review screens (especially ContentReview with its side-by-side editor) need the full page width. A 66% width constraint makes them unusable.

**`renderCheckpointUI` switch:**

Must handle ALL four checkpoint types: `research_review`, `content_review`, `subject_review`, `final_review`, plus a `default` case for unknown types.

**SSE integration:**

```typescript
useWorkflowSSE(activeWorkflowId, {
  onStatus: (event) => setWorkflowStatus(event.status),
  onCheckpoint: (event) => {
    setCheckpointData(event);
    toast({ title: 'Checkpoint Ready', description: `${event.title} - Your review is needed` });
  },
  onComplete: (event) => {
    if (event.status === 'completed') {
      toast({ title: 'Newsletter Complete!' });
    }
    setView('dashboard');
    clearWorkflowState();
  },
  onError: (event) => {
    toast({ title: 'Workflow Error', description: event.error, variant: 'destructive' });
  },
});
```

**Approve handler with loading state tracking:**

```typescript
const [loadingAction, setLoadingAction] = useState<CheckpointAction | null>(null);

const handleApproveCheckpoint = (data?, feedback?) => {
  if (!activeWorkflowId || !checkpoint) return;
  setLoadingAction('approve');
  approveMutation.mutate(
    { workflowId: activeWorkflowId, request: { checkpoint_id: checkpoint.checkpoint_id, action: 'approve', modifications: data, feedback } },
    {
      onSuccess: () => setLoadingAction(null),
      onError: (error) => {
        setLoadingAction(null);
        toast({ title: 'Approval Failed', description: error.message, variant: 'destructive' });
      },
    }
  );
};
```

### Expected Output

- `workflow/WorkflowTracker.tsx` — step progress indicator with compact variant
- `workflow/WorkflowHistory.tsx` — timeline component
- Updated `NewsletterApp.tsx` — Workflow tab, `renderCheckpointUI()`, SSE integration, loading states, persisted initial view

---

## Checklist of All Pitfalls

A quick reference of every issue these prompts address:

| # | Pitfall | Where Addressed |
|---|---------|----------------|
| 1 | Binary msgpack stored as UTF-8 → `UnicodeDecodeError` | Prompt 1 |
| 2 | `PendingWrite` is a plain tuple, not named tuple | Prompt 1 |
| 3 | `subject_lines` typed as `list[str]` instead of `list[dict]` | Prompt 1 |
| 4 | WritingAgent `angle` key vs frontend `style` key | Prompt 7 |
| 5 | `ainvoke()` with new state vs `Command(resume=)` for resume | Prompt 2 |
| 6 | Missing node-to-step mapping → wrong WorkflowTracker state | Prompt 2 |
| 7 | Blocking `POST /approve` + 30s Axios timeout → stuck UI | Prompt 2, 4 |
| 8 | FastAPI catch-all route before specific routes | Prompt 3 |
| 9 | EventSource can't set HTTP headers → 401 on SSE | Prompt 3, 4 |
| 10 | WritingAgent output key `newsletter` vs `content` | Prompt 6 |
| 11 | Flat checkpoint data fields vs nested `newsletter` key | Prompt 6 |
| 12 | `checkpoint_type` naming mismatch backend/frontend | Prompt 5-8 |
| 13 | `currentStepIndex = -1` when step not in WORKFLOW_STEPS | Prompt 9 |
| 14 | Missing `subject_review` in TypeScript union type | Prompt 4 |
| 15 | Narrow grid layout squishes review components | Prompt 9 |
| 16 | `activeWorkflowId` not persisted → lost on refresh | Prompt 4, 9 |
| 17 | Hardcoded `'dashboard'` initial view ignores active workflow | Prompt 9 |
| 18 | Send button enabled with zero recipients | Prompt 8 |
| 19 | `recipientCount` prop not passed to FinalApproval | Prompt 8 |
| 20 | `selected_subject` key mismatch in approve payload | Prompt 7 |
| 21 | Missing Workflow tab in UI | Prompt 9 |
| 22 | `useParams` returns `undefined`, SSE expects `null` | Prompt 4 |
| 23 | `datetime.utcnow()` deprecated → use `datetime.now(timezone.utc)` | Prompt 1 |
| 24 | Pydantic v2 `model_config` dict, not `class Config` | Prompt 3 |
| 25 | `MemoryService.get()` callers pass 1 arg, method needs 3 | Prompt 3 |
| 26 | MongoDB naive datetime vs `datetime.now(timezone.utc)` aware → `TypeError` | Prompt 3 |
| 27 | `store_newsletter_node` passes `list[dict]` to `List[str]` field → `ValidationError` | Prompt 1 |
| 28 | `getCheckpoint` throws on 404 after workflow completes → error in UI | Prompt 4 |
| 29 | Final approval shows raw HTML — `formats` not constructed from `preview_html` | Prompt 8 |
| 30 | No test email escape hatch when `recipientCount === 0` → can't test flow | Prompt 8 |
| 31 | `test_recipients` not in state schema → lost between nodes | Prompt 1 |
| 32 | `subject_review` missing from `WORKFLOW_STEPS` → checkmarks break | Prompt 9 |
| 33 | Newsletter HTML `<style>` bleeds into parent via `dangerouslySetInnerHTML` | Prompt 6, 8, 9 |

---

## Appendix: Post-Implementation Fixes (Session 2)

Fixes applied after the initial HITL implementation was running end-to-end. These were discovered during manual QA testing of the full workflow.

### Fix 1: MemoryService API Signature Mismatch (Pitfall #25)

**Symptom:** `TypeError: MemoryService.get() missing 2 required positional arguments: 'cache_type' and 'key'`

**Root cause:** `PreferenceAgent` called `self._memory_service.get(key)` and `self._memory_service.set(key, data, ttl=None)` with old-style arguments. But `MemoryService` requires `(user_id, cache_type, key)` for `get()` and `(user_id, cache_type, key, value, ttl)` for `set()`.

**Fix:** Updated all 5 call sites in `preference/agent.py`:
```python
# Before:
data = await self._memory_service.get(key)
await self._memory_service.set(key, preferences.to_dict(), ttl=None)

# After:
from app.platforms.newsletter.services.memory import CacheType
data = await self._memory_service.get(user_id, CacheType.PREFERENCES, "settings")
await self._memory_service.set(user_id, CacheType.PREFERENCES, "settings", preferences.to_dict(), ttl=None)
```

**Files:** `backend/app/platforms/newsletter/agents/preference/agent.py`

### Fix 2: MongoDB Naive vs Aware Datetime (Pitfall #26)

**Symptom:** `TypeError: can't compare offset-naive and offset-aware datetimes`

**Root cause:** MongoDB may store or return `expires_at` as a naive datetime (no timezone). Code compared it with `datetime.now(timezone.utc)` (timezone-aware).

**Fix:** Normalize before comparing in `memory.py`:
```python
expires_at = doc.get("expires_at")
if expires_at:
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None  # expired
```

**Files:** `backend/app/platforms/newsletter/services/memory.py`

### Fix 3: store_newsletter_node Pydantic Validation (Pitfall #27)

**Symptom:** `ValidationError: 1 validation error for Newsletter subject_line_options.0 Input should be a valid string`

**Root cause:** `state["subject_lines"]` is `list[dict]` after normalization (e.g., `[{"text": "...", "style": "..."}]`), but `Newsletter.subject_line_options` is `List[str]`.

**Fix:** Extract text strings before passing to the model:
```python
subject_line_options=[
    s.get("text", str(s)) if isinstance(s, dict) else str(s)
    for s in state.get("subject_lines", [])
],
```

**Files:** `backend/app/platforms/newsletter/orchestrator/nodes.py`

### Fix 4: Checkpoint 404 After Final Approval (Pitfall #28)

**Symptom:** `GET /workflows/{id}/checkpoint` returns 404 after final approval, causing UI error.

**Root cause:** After the user approves the final checkpoint, the `useApproveCheckpoint` mutation invalidates the checkpoint query. React Query refetches, but the workflow has already completed — no checkpoint exists. The `getCheckpoint` API function threw on 404, which React Query treated as an error.

**Fix:** Catch 404 in the API client and return `null`:
```typescript
getCheckpoint: async (workflowId: string): Promise<Checkpoint | null> => {
  try {
    const response = await apiClient.get(`.../${workflowId}/checkpoint`);
    return response.data;
  } catch (error: any) {
    if (error?.response?.status === 404) return null;
    throw error;
  }
},
```

**Files:** `frontend/src/api/newsletter.ts`

### Fix 5: Final Approval Shows Raw HTML (Pitfall #29)

**Symptom:** The final approval content preview shows raw HTML tags (`<h1>`, `<p>`, etc.) instead of rendered content.

**Root cause:** The backend `checkpoint_send_node` sends `preview_html` in the checkpoint data but does NOT include a `formats` key. The frontend passed `formats={checkpointData.formats}` which evaluated to `undefined`. In `FinalApproval`, the component checks `formats?.html` to decide between `dangerouslySetInnerHTML` and a `<pre>` tag. With `formats` undefined, it fell through to the `<pre>` path, displaying raw HTML.

**Fix:** Construct `formats` from `preview_html` when `formats` isn't present:
```typescript
formats={(checkpointData.formats as any) ||
  (checkpointData.preview_html
    ? { html: String(checkpointData.preview_html) }
    : undefined)}
```

**Files:** `frontend/src/components/apps/newsletter/NewsletterApp.tsx`

### Fix 6: Test Email Input for Zero Subscribers (Pitfall #30)

**Symptom:** Cannot complete the workflow when `recipientCount === 0` — the Send button is permanently disabled.

**Root cause:** The Send button was `disabled` when `recipientCount === 0`, and there was no way to provide recipients outside of the subscriber management system.

**Fix:** Added a comma-separated email input shown when no subscribers exist:
- Parse valid emails (must contain `@`) and count as `effectiveRecipientCount`
- Enable Send button when `effectiveRecipientCount > 0`
- Pass `test_recipients` array through approve callback to backend
- Backend `checkpoint_send_node` stores `test_recipients` in state for `send_email_node`

**Files:**
- `frontend/src/components/apps/newsletter/workflow/FinalApproval.tsx`
- `frontend/src/components/apps/newsletter/NewsletterApp.tsx`
- `backend/app/platforms/newsletter/orchestrator/nodes.py`
- `backend/app/platforms/newsletter/orchestrator/state.py`

### Fix 7: Missing `subject_review` in WorkflowTracker (Pitfall #32)

**Symptom:** At the "Select Subject" step, the Research and Generate steps don't show checkmarks — they appear as pending dots instead of completed.

**Root cause:** `WORKFLOW_STEPS` in `WorkflowTracker.tsx` only had 5 steps and was missing `subject_review`. The backend sets `current_step = "subject_review"` during the subject checkpoint. Since `"subject_review"` wasn't in the array, `currentStepIndex` resolved to `-1`. The implicit completion logic (`stepIndex < currentStepIndex`) then failed because no index is less than `-1`, so all prior steps stayed "pending".

**Fix:** Added `subject_review` to the `WORKFLOW_STEPS` array between `content_review` and `final_review`:
```typescript
export const WORKFLOW_STEPS: WorkflowStep[] = [
  { id: 'research',        label: 'Research',        description: 'Discover relevant articles' },
  { id: 'research_review', label: 'Review Articles',  description: 'Select and reorder articles' },
  { id: 'writing',         label: 'Generate',        description: 'Create newsletter content' },
  { id: 'content_review',  label: 'Review Content',   description: 'Edit and approve content' },
  { id: 'subject_review',  label: 'Select Subject',   description: 'Choose a subject line' },
  { id: 'final_review',    label: 'Final Review',    description: 'Confirm and schedule' },
];
```

**Files:** `frontend/src/components/apps/newsletter/workflow/WorkflowTracker.tsx`

### Fix 8: Newsletter HTML CSS Bleeds into Parent Page (Pitfall #33)

**Symptom:** The newsletter content preview renders at ~25% width in both ContentReview and FinalApproval. The squishing only happens when HTML content is displayed.

**Root cause:** The newsletter HTML template (generated in `formatters.py`) contains `<style>` tags with global CSS rules:
```css
* { margin: 0; padding: 0; box-sizing: border-box; }
body { max-width: 800px; margin: 0 auto; padding: 20px; }
```

When injected via `dangerouslySetInnerHTML`, these styles are NOT scoped — they bleed into the parent React app. The `*` selector resets margins/padding on all elements, and the `body { max-width: 800px }` constrains the page width. The `prose` class from `@tailwindcss/typography` was supposed to scope the rendering, but that plugin was never installed.

**Fix:** Replace `dangerouslySetInnerHTML` with `<iframe srcDoc>` in all 3 components that render newsletter HTML. The iframe provides full CSS isolation — the newsletter's `<style>` tags only affect the iframe's document, not the parent page.

```tsx
// Before (CSS bleeds into parent):
<div dangerouslySetInnerHTML={{ __html: formats.html }} />

// After (CSS isolated in iframe):
<iframe
  srcDoc={formats.html}
  title="Newsletter preview"
  className="w-full h-[500px] border-0"
  sandbox="allow-same-origin"
/>
```

**Files:**
- `frontend/src/components/apps/newsletter/workflow/ContentReview.tsx`
- `frontend/src/components/apps/newsletter/workflow/FinalApproval.tsx`
- `frontend/src/components/apps/newsletter/NewsletterPreview.tsx`
