# HITL Checkpoint Flow: Deep Dive

How one Human-in-the-Loop checkpoint works end-to-end, using **Checkpoint 1: Article Review** as the example.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React)                               │
│                                                                             │
│  NewsletterApp.tsx                                                          │
│    ├── GeneratePanel       → user clicks "Generate"                         │
│    ├── WorkflowTracker     → shows step progress                            │
│    ├── ArticleReview       → checkpoint UI for article selection             │
│    └── useWorkflowSSE      → real-time status via SSE                       │
│                                                                             │
│  Hooks:  useGenerateWorkflow()  useWorkflow()  useWorkflowCheckpoint()      │
│          useApproveCheckpoint()  useWorkflowSSE()                           │
│                                                                             │
│  API:    newsletterApi.generateNewsletter()  .getWorkflow()                  │
│          .getCheckpoint()  .approveCheckpoint()  .getWorkflowStreamUrl()    │
└─────────────────────┬───────────────────────────────┬───────────────────────┘
                      │ HTTP                          │ SSE
                      ▼                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BACKEND (FastAPI)                                  │
│                                                                             │
│  /api/v1/platforms/newsletter/                                               │
│    ├── POST /generate              → router.py                              │
│    ├── GET  /workflows/{id}        → routers/workflows.py                   │
│    ├── GET  /workflows/{id}/checkpoint                                      │
│    ├── POST /workflows/{id}/approve                                         │
│    └── GET  /workflows/{id}/stream                                          │
│                                                                             │
│  NewsletterService → NewsletterOrchestrator → LangGraph                     │
│                                                                             │
│  LangGraph nodes:                                                           │
│    get_preferences → process_prompt → research → checkpoint_articles → ...  │
│                                                                             │
│  State persisted in MongoDB via MongoDBSaver (checkpointer)                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The Full Lifecycle of Checkpoint 1 (Article Review)

### Phase A: Starting the Workflow

#### Step 1 — User clicks "Generate" in the frontend

**File:** `frontend/src/components/apps/newsletter/NewsletterApp.tsx`

The `GeneratePanel` component collects topics, tone, max articles, and calls `handleStartWorkflow`:

```tsx
const handleStartWorkflow = (options) => {
  generateWorkflowMutation.mutate(
    {
      topics: options.topics,
      tone: options.tone,
      max_articles: options.maxArticles,
      include_rag: options.includeRag,
    },
    {
      onSuccess: (data) => {
        setActiveWorkflow(data.workflow_id);   // Zustand store
        setView('workflow');                    // switch to workflow tab
      },
    }
  );
};
```

#### Step 2 — React Query mutation fires the API call

**File:** `frontend/src/hooks/useNewsletter.ts`

```tsx
export function useGenerateWorkflow() {
  return useMutation<GenerateWorkflowResponse, Error, GenerateWorkflowRequest>({
    mutationFn: newsletterApi.generateNewsletter,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.workflows() });
    },
  });
}
```

**File:** `frontend/src/api/newsletter.ts`

```tsx
generateNewsletter: async (request) => {
  const response = await apiClient.post(
    `/platforms/newsletter/generate`,
    request,
    { timeout: 120000 }    // 2 min timeout for LLM calls
  );
  return response.data;     // { workflow_id, status, message }
},
```

**HTTP Request:**
```
POST /api/v1/platforms/newsletter/generate
Authorization: Bearer <jwt>
Content-Type: application/json

{
  "topics": ["AI", "robotics"],
  "tone": "professional",
  "max_articles": 10
}
```

#### Step 3 — FastAPI receives the request

**File:** `backend/app/platforms/newsletter/router.py` (line 156)

```python
@router.post("/generate")
async def generate_newsletter_legacy(
    request: GenerateNewsletterRequest,
    current_user: dict = Depends(get_current_user),
):
    service = NewsletterService()
    result = await service.generate_newsletter(
        user_id=current_user["id"],
        topics=request.topics,
        tone=request.tone.value,
        max_articles=request.max_articles,
    )
    return GenerateNewsletterResponse(
        workflow_id=result["workflow_id"],
        status=result["status"],
        message=result.get("message", "Newsletter generation started"),
    )
```

#### Step 4 — NewsletterService delegates to Orchestrator

**File:** `backend/app/platforms/newsletter/services/__init__.py`

```python
async def generate_newsletter(self, user_id, topics, tone, max_articles, custom_prompt=None):
    result = await self.orchestrator.run({
        "user_id": user_id,
        "topics": topics,
        "tone": tone,
        "max_articles": max_articles,
        "custom_prompt": custom_prompt,
    })
    return result
```

#### Step 5 — Orchestrator creates initial state and starts LangGraph

**File:** `backend/app/platforms/newsletter/orchestrator/orchestrator.py`

```python
async def run(self, input):
    initial_state = create_initial_state(
        user_id=input["user_id"],
        topics=input["topics"],
        tone=input["tone"],
        ...
    )
    workflow_id = initial_state["workflow_id"]  # UUID generated here
    config = {"configurable": {"thread_id": workflow_id}}

    # This call runs the graph until it hits an interrupt()
    result = await self.graph.ainvoke(initial_state, config)

    # Check if paused at a checkpoint
    state_snapshot = await self.graph.aget_state(config)
    if state_snapshot.next:
        return {
            "success": True,
            "workflow_id": workflow_id,
            "status": "awaiting_approval",
        }
```

The key insight: `graph.ainvoke()` runs synchronously through all nodes until one calls `interrupt()`. State is persisted to MongoDB after each node by the `MongoDBSaver` checkpointer.

---

### Phase B: LangGraph Runs Until the First `interrupt()`

#### Step 6 — Graph executes nodes sequentially

**File:** `backend/app/platforms/newsletter/orchestrator/graph.py`

The graph defines this flow:

```
get_preferences → process_prompt → research → checkpoint_articles → ...
```

These edges are defined as:
```python
graph.set_entry_point("get_preferences")
graph.add_edge("get_preferences", "process_prompt")
graph.add_edge("process_prompt", "research")
graph.add_edge("research", "checkpoint_articles")
```

LangGraph executes each node in order. Each node receives the current `NewsletterState` dict and returns a partial dict that gets merged back.

#### Step 7 — `research_node` runs the ResearchAgent

**File:** `backend/app/platforms/newsletter/orchestrator/nodes.py` (line 119)

```python
async def research_node(state):
    agent = ResearchAgent()
    result = await agent.run({
        "topics": state.get("topics", []),
        "user_id": state["user_id"],
        "max_results": state.get("max_articles", 10),
    })
    return {
        "articles": result.get("articles", []),
        "research_metadata": result.get("metadata", {}),
        "research_completed": True,
        "current_step": "research",
    }
```

The ResearchAgent calls Tavily API, scores/ranks results, and returns articles. These get merged into the state dict.

#### Step 8 — `checkpoint_articles_node` calls `interrupt()` — THE KEY MOMENT

**File:** `backend/app/platforms/newsletter/orchestrator/nodes.py` (line 359)

```python
def checkpoint_articles_node(state):
    articles = state.get("articles", [])

    # Build the data payload the frontend will display
    checkpoint_data = CheckpointData(
        checkpoint_id=str(uuid4()),
        checkpoint_type="research_review",
        title="Review Article Selection",
        description=f"Review {len(articles)} articles found for your newsletter",
        data={
            "articles": [
                {
                    "title": a.get("title"),
                    "url": a.get("url"),
                    "source": a.get("source"),
                    "summary": a.get("summary"),
                    "score": a.get("score"),
                }
                for a in articles
            ],
            "topics": state.get("topics", []),
            "total_found": len(articles),
        },
        actions=["approve", "edit", "reject"],
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    # ╔══════════════════════════════════════════════════════════╗
    # ║  THIS IS WHERE THE WORKFLOW PAUSES                      ║
    # ║                                                         ║
    # ║  interrupt() saves state to MongoDB via MongoDBSaver    ║
    # ║  and returns control back to the caller (orchestrator)  ║
    # ║                                                         ║
    # ║  The `response` variable will be populated later when   ║
    # ║  the workflow is resumed with Command(resume=...)       ║
    # ╚══════════════════════════════════════════════════════════╝
    response = interrupt(checkpoint_data)

    # --- Everything below here runs LATER, after resume ---

    action = response.get("action", "approve")

    if action == "reject":
        return {"research_completed": False}   # triggers re-research via routing

    if action == "edit":
        edited_articles = response.get("articles", articles)
        return {"articles": edited_articles, ...}

    # Approved — continue with current articles
    return {
        "checkpoints_completed": state.get("checkpoints_completed", []) + ["research_review"],
    }
```

When `interrupt(checkpoint_data)` is called:
1. LangGraph serializes the current state (including the checkpoint_data) to MongoDB
2. The `ainvoke()` call in the orchestrator returns
3. The `checkpoint_data` is stored as the interrupt value in `state_snapshot.tasks[].interrupts[].value`

#### Step 9 — Orchestrator returns to the API endpoint

Back in the orchestrator's `run()` method, `state_snapshot.next` is `["checkpoint_articles"]` (the node that interrupted), so it returns:

```python
return {
    "success": True,
    "workflow_id": "3028731b-...",
    "status": "awaiting_approval",
}
```

**HTTP Response to frontend:**
```json
{
  "workflow_id": "3028731b-e1ec-498c-913c-ae246ea3fd1b",
  "status": "awaiting_approval",
  "message": "Newsletter generation started"
}
```

---

### Phase C: Frontend Discovers the Checkpoint

#### Step 10 — Frontend stores workflow_id and starts polling + SSE

Back in `NewsletterApp.tsx`, the `onSuccess` callback fires:

```tsx
onSuccess: (data) => {
  setActiveWorkflow(data.workflow_id);  // triggers useWorkflow + useWorkflowCheckpoint
  setView('workflow');
}
```

Setting `activeWorkflowId` in Zustand triggers three things simultaneously. The workflow ID is also **persisted to localStorage** via the store's `partialize` config, so it survives page refreshes (see [Bug Fix #14](#14-workflow-state-lost-on-browser-refresh)).

**a) `useWorkflow` polling query:**

```tsx
const { data: workflowData } = useWorkflow(activeWorkflowId || '');
```

This calls `GET /workflows/{id}` and auto-polls every 2 seconds when status is "running":

```tsx
export function useWorkflow(workflowId) {
  return useQuery({
    queryKey: newsletterKeys.workflowDetail(workflowId),
    queryFn: () => newsletterApi.getWorkflow(workflowId),
    refetchInterval: (query) => {
      if (query.state.data?.status === 'running') return 2000;
      return false;
    },
  });
}
```

**b) `useWorkflowCheckpoint` query:**

```tsx
const { data: checkpoint } = useWorkflowCheckpoint(activeWorkflowId || '');
```

This calls `GET /workflows/{id}/checkpoint` to get the pending checkpoint data.

**c) `useWorkflowSSE` connection:**

```tsx
useWorkflowSSE(activeWorkflowId, {
  onStatus: (event) => setWorkflowStatus(event.status),
  onCheckpoint: () => { /* invalidate checkpoint query */ },
});
```

Opens an EventSource to `GET /workflows/{id}/stream?token=<jwt>` for real-time push updates.

#### Step 11 — Backend serves the checkpoint data

**`GET /workflows/{id}`** returns:

**File:** `backend/app/platforms/newsletter/orchestrator/orchestrator.py`

```python
async def get_workflow_status(self, workflow_id):
    config = {"configurable": {"thread_id": workflow_id}}
    state_snapshot = await self.graph.aget_state(config)
    state = state_snapshot.values

    # Map the LangGraph node name to the frontend step ID
    if state_snapshot.next:
        node_to_step = {
            "checkpoint_articles": "research_review",
            "checkpoint_content": "content_review",
            "checkpoint_subjects": "subject_review",
            "checkpoint_send": "final_review",
        }
        next_node = state_snapshot.next[0]           # "checkpoint_articles"
        current_step = node_to_step.get(next_node)   # "research_review"

    return {
        "status": "awaiting_approval",
        "current_step": "research_review",
        "checkpoints_completed": [],
        ...
    }
```

**`GET /workflows/{id}/checkpoint`** returns:

**File:** `backend/app/platforms/newsletter/orchestrator/orchestrator.py`

```python
async def get_pending_checkpoint(self, workflow_id):
    state_snapshot = await self.graph.aget_state(config)

    # Extract the interrupt value from LangGraph's internal state
    for task in state_snapshot.tasks:
        if hasattr(task, 'interrupts') and task.interrupts:
            interrupt_value = task.interrupts[0].value
            # This is the CheckpointData dict we passed to interrupt()
            checkpoint = vars(interrupt_value)  # or dict directly

    return {
        "workflow_id": workflow_id,
        "checkpoint_id": "abc-123",
        "checkpoint_type": "research_review",
        "title": "Review Article Selection",
        "description": "Review 8 articles found for your newsletter",
        "data": {
            "articles": [...],    # the article list
            "topics": ["AI", "robotics"],
            "total_found": 8,
        },
        "actions": ["approve", "edit", "reject"],
    }
```

#### Step 12 — Frontend renders the ArticleReview component

**File:** `frontend/src/components/apps/newsletter/NewsletterApp.tsx`

The `renderCheckpointUI` function switches on `checkpoint.checkpoint_type`:

```tsx
const renderCheckpointUI = () => {
  const checkpointType = checkpoint.checkpoint_type;
  const checkpointData = checkpoint.data;

  switch (checkpointType) {
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
  }
};
```

The `WorkflowTracker` also updates. Its `getStepStatus` function uses `currentStep="research_review"` (index 1 in WORKFLOW_STEPS) to mark `research` (index 0) as completed:

```tsx
const WORKFLOW_STEPS = [
  { id: 'research',        label: 'Research'       },   // index 0 → completed
  { id: 'research_review', label: 'Review Articles' },   // index 1 → current (spinner)
  { id: 'writing',         label: 'Generate'       },   // index 2 → pending
  { id: 'content_review',  label: 'Review Content'  },   // index 3 → pending
  { id: 'final_review',    label: 'Final Review'    },   // index 4 → pending
];

const getStepStatus = (stepId) => {
  if (status === 'completed') return 'completed';     // all done
  if (completedSteps.includes(stepId)) return 'completed';
  const stepIndex = WORKFLOW_STEPS.findIndex(s => s.id === stepId);
  if (stepIndex < currentStepIndex) return 'completed'; // before current = done
  if (currentStep === stepId) return 'current';          // spinner
  return 'pending';                                      // not yet
};
```

---

### Phase D: User Approves the Checkpoint

#### Step 13 — User clicks "Approve" in ArticleReview

The `onApprove` callback in NewsletterApp triggers:

```tsx
const handleApproveCheckpoint = (data?, feedback?) => {
  setLoadingAction('approve');
  approveMutation.mutate(
    {
      workflowId: activeWorkflowId,
      request: {
        checkpoint_id: checkpoint.checkpoint_id,
        action: 'approve',
        modifications: data,     // { articles: [...] } for edits, or undefined
        feedback: feedback,
      },
    },
    {
      onSuccess: () => {
        setLoadingAction(null);
        // React Query invalidates workflow + checkpoint queries
        // → triggers refetch → renders next checkpoint or completion
      },
    }
  );
};
```

#### Step 14 — React Query mutation fires the approve API call

**File:** `frontend/src/hooks/useNewsletter.ts`

```tsx
export function useApproveCheckpoint() {
  return useMutation({
    mutationFn: ({ workflowId, request }) =>
      newsletterApi.approveCheckpoint(workflowId, request),
    onSuccess: (workflow) => {
      // Invalidate both queries so they refetch
      queryClient.invalidateQueries({ queryKey: workflowDetail(workflow.workflow_id) });
      queryClient.invalidateQueries({ queryKey: workflowCheckpoint(workflow.workflow_id) });
    },
  });
}
```

**HTTP Request:**
```
POST /api/v1/platforms/newsletter/workflows/3028731b-.../approve
Authorization: Bearer <jwt>
Content-Type: application/json

{
  "checkpoint_id": "abc-123",
  "action": "approve",
  "modifications": null,
  "feedback": null
}
```

#### Step 15 — Backend receives approval and resumes LangGraph

**File:** `backend/app/platforms/newsletter/routers/workflows.py`

```python
@router.post("/{workflow_id}/approve")
async def approve_checkpoint(request, workflow_id, current_user):
    orchestrator = get_newsletter_orchestrator()
    result = await orchestrator.approve_checkpoint(
        workflow_id=workflow_id,
        checkpoint_id=request.checkpoint_id,
        action=request.action,
        modifications=request.modifications,
        feedback=request.feedback,
    )
    return result
```

**File:** `backend/app/platforms/newsletter/orchestrator/orchestrator.py`

```python
async def approve_checkpoint(self, workflow_id, checkpoint_id, action, modifications, feedback):
    config = {"configurable": {"thread_id": workflow_id}}

    # Build the response dict that becomes the return value of interrupt()
    response = {
        "action": action,              # "approve"
        "checkpoint_id": checkpoint_id,
    }
    if modifications:
        response.update(modifications)  # e.g., edited article list
    if feedback:
        response["feedback"] = feedback

    # ╔══════════════════════════════════════════════════════════╗
    # ║  Command(resume=response) resumes the interrupted node  ║
    # ║                                                         ║
    # ║  The `response` dict becomes the return value of the    ║
    # ║  interrupt() call in checkpoint_articles_node.          ║
    # ║                                                         ║
    # ║  LangGraph loads state from MongoDB, feeds `response`   ║
    # ║  to the interrupt(), and continues execution.           ║
    # ╚══════════════════════════════════════════════════════════╝
    result = await self.graph.ainvoke(
        Command(resume=response),
        config,
    )

    # Check if there's another checkpoint waiting
    state_snapshot = await self.graph.aget_state(config)
    if state_snapshot.next:
        return {"status": "awaiting_approval", ...}
    else:
        return {"status": "completed", ...}
```

#### Step 16 — LangGraph resumes from the interrupt point

Back in `checkpoint_articles_node`, the `interrupt()` call now returns the `response` dict:

```python
response = interrupt(checkpoint_data)
# response = {"action": "approve", "checkpoint_id": "abc-123"}

action = response.get("action", "approve")  # "approve"

# Since action is "approve", we fall through to:
return {
    "current_checkpoint": None,
    "checkpoint_response": response,
    "checkpoints_completed": state.get("checkpoints_completed", []) + ["research_review"],
}
```

#### Step 17 — LangGraph routing decides what's next

**File:** `backend/app/platforms/newsletter/orchestrator/graph.py`

After `checkpoint_articles`, a conditional edge runs:

```python
graph.add_conditional_edges(
    "checkpoint_articles",
    route_after_article_checkpoint,
    {
        "research": "research",            # if rejected → re-research
        "generate_content": "generate_content",  # if approved → move on
    },
)
```

```python
def route_after_article_checkpoint(state):
    if not state.get("research_completed", False):
        return "research"        # rejection loops back
    return "generate_content"    # approval moves forward
```

Since `research_completed=True` (we approved), the graph proceeds to `generate_content_node`, then hits `checkpoint_content` (the next `interrupt()`), and the cycle repeats.

#### Step 18 — Response arrives at frontend

**Important timing note:** The `POST /approve` call is **blocking** — it does not return until LangGraph finishes running all nodes up to the next `interrupt()`. This means the HTTP request stays open while multiple LLM calls execute (content generation, subject lines, summary). A single approve can take 30-120 seconds depending on the LLM provider. The frontend API client must use a long timeout (5 minutes) for checkpoint actions to avoid client-side timeouts. See [Bug Fix #10](#10-approve-button-stays-enabled-after-clicking--ui-stuck-on-review-articles) for details.

Once the response arrives, React Query invalidates the workflow and checkpoint queries, which refetch:
- `GET /workflows/{id}` now returns `current_step: "content_review"`
- `GET /workflows/{id}/checkpoint` now returns the content review checkpoint data

The `WorkflowTracker` updates to show `research_review` as completed and `content_review` as current. The `renderCheckpointUI` renders `<ContentReview>` instead of `<ArticleReview>`.

---

## State Persistence: How MongoDB Fits In

```
                    LangGraph Runtime
                          │
                    ┌─────┴─────┐
                    │MongoDBSaver│  ← custom checkpointer
                    └─────┬─────┘
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
  checkpoints       checkpoint_writes   checkpoint_blobs
  collection        collection          collection
         │                │                │
         └────────────────┴────────────────┘
                     MongoDB
```

**File:** `backend/app/platforms/newsletter/orchestrator/mongodb_saver.py`

After each node executes, `MongoDBSaver` serializes the state:
- `channel_values` (the full `NewsletterState` dict) → msgpack binary → base64 → stored as string
- `channel_versions` → tracks which channels changed
- `pending_writes` → writes from the current step

When `Command(resume=response)` is called:
1. MongoDBSaver loads the last checkpoint from MongoDB
2. Deserializes base64 → msgpack → Python dict
3. LangGraph restores the full state and resumes the interrupted node
4. The `response` becomes the return value of `interrupt()`

---

## Data Format Mapping: Backend → Frontend

| Backend field | Stored in | Frontend reads | Component uses |
|---|---|---|---|
| `checkpoint_type: "research_review"` | interrupt value | `checkpoint.checkpoint_type` | `switch` in `renderCheckpointUI` |
| `data.articles` | interrupt value | `checkpointData.articles` | `ArticleReview` props |
| `data.topics` | interrupt value | `checkpointData.topics` | displayed in review UI |
| `actions: ["approve","edit","reject"]` | interrupt value | `checkpoint.actions` | button visibility |
| `current_step` | mapped in `get_workflow_status` | `workflowData.current_step` | `WorkflowTracker` |
| `checkpoints_completed` | state dict | `workflowData.checkpoints_completed` | `WorkflowTracker` |

The `current_step` mapping is critical. LangGraph only knows node names (`checkpoint_articles`), but the frontend tracker uses step IDs (`research_review`). The orchestrator maps these:

```python
node_to_step = {
    "checkpoint_articles": "research_review",
    "checkpoint_content":  "content_review",
    "checkpoint_subjects": "subject_review",
    "checkpoint_send":     "final_review",
}
```

---

## Sequence Diagram

```
 User          Frontend                  Backend API            Orchestrator         LangGraph         MongoDB
  │               │                          │                      │                    │                │
  │ click Generate│                          │                      │                    │                │
  │──────────────>│                          │                      │                    │                │
  │               │ POST /generate           │                      │                    │                │
  │               │─────────────────────────>│                      │                    │                │
  │               │                          │ service.generate()   │                    │                │
  │               │                          │─────────────────────>│                    │                │
  │               │                          │                      │ graph.ainvoke()    │                │
  │               │                          │                      │───────────────────>│                │
  │               │                          │                      │                    │ run nodes...   │
  │               │                          │                      │                    │───────────────>│ save state
  │               │                          │                      │                    │                │ after each
  │               │                          │                      │                    │                │ node
  │               │                          │                      │                    │ interrupt()    │
  │               │                          │                      │                    │───────────────>│ save + pause
  │               │                          │                      │<───────────────────│                │
  │               │                          │<─────────────────────│                    │                │
  │               │ {workflow_id, status}     │                      │                    │                │
  │               │<─────────────────────────│                      │                    │                │
  │               │                          │                      │                    │                │
  │               │ GET /workflows/{id}      │                      │                    │                │
  │               │─────────────────────────>│ get_workflow_status() │                    │                │
  │               │                          │─────────────────────>│ aget_state()       │                │
  │               │                          │                      │───────────────────>│                │
  │               │                          │                      │                    │───────────────>│ load state
  │               │                          │                      │<───────────────────│<───────────────│
  │               │ {status, current_step}   │<─────────────────────│                    │                │
  │               │<─────────────────────────│                      │                    │                │
  │               │                          │                      │                    │                │
  │               │ GET /workflows/{id}/checkpoint                  │                    │                │
  │               │─────────────────────────>│ get_pending_checkpoint()                  │                │
  │               │                          │─────────────────────>│                    │                │
  │               │                          │                      │ read tasks[].interrupts[].value    │
  │               │ {checkpoint_data}        │<─────────────────────│                    │                │
  │               │<─────────────────────────│                      │                    │                │
  │               │                          │                      │                    │                │
  │ sees articles │                          │                      │                    │                │
  │ clicks Approve│                          │                      │                    │                │
  │──────────────>│                          │                      │                    │                │
  │               │ POST /workflows/{id}/approve                    │                    │                │
  │               │─────────────────────────>│ approve_checkpoint() │                    │                │
  │               │                          │─────────────────────>│                    │                │
  │               │                          │                      │ Command(resume=    │                │
  │               │                          │                      │   {action:approve})│                │
  │               │                          │                      │───────────────────>│                │
  │               │                          │                      │                    │───────────────>│ load state
  │               │                          │                      │                    │ resume node    │
  │               │                          │                      │                    │ continue to    │
  │               │                          │                      │                    │ next nodes...  │
  │               │                          │                      │                    │ next interrupt()
  │               │                          │                      │                    │───────────────>│ save + pause
  │               │                          │                      │<───────────────────│                │
  │               │                          │<─────────────────────│                    │                │
  │               │ {status: awaiting_approval}                     │                    │                │
  │               │<─────────────────────────│                      │                    │                │
  │               │                          │                      │                    │                │
  │               │ (queries invalidate → refetch → render next checkpoint)              │                │
```

---

## File Reference

| Layer | File | Role |
|---|---|---|
| **Frontend UI** | `NewsletterApp.tsx` | Main component, tab routing, checkpoint rendering |
| **Frontend UI** | `workflow/ArticleReview.tsx` | Checkpoint 1 review interface |
| **Frontend UI** | `workflow/WorkflowTracker.tsx` | Step progress indicator |
| **Frontend Hook** | `hooks/useNewsletter.ts` | React Query hooks for all API calls |
| **Frontend Hook** | `hooks/useWorkflowSSE.ts` | SSE EventSource for real-time updates |
| **Frontend API** | `api/newsletter.ts` | HTTP client functions |
| **Frontend Store** | `store/newsletterStore.ts` | Zustand store (activeWorkflowId persisted to localStorage) |
| **Frontend Types** | `types/newsletter.ts` | TypeScript interfaces |
| **Backend Router** | `router.py` | Top-level `/generate` endpoint |
| **Backend Router** | `routers/workflows.py` | `/workflows/{id}`, `/checkpoint`, `/approve`, `/stream` |
| **Backend Service** | `services/__init__.py` | Delegates to orchestrator |
| **Backend Orchestrator** | `orchestrator/orchestrator.py` | `run()`, `get_workflow_status()`, `approve_checkpoint()` |
| **Backend Graph** | `orchestrator/graph.py` | LangGraph node wiring and conditional edges |
| **Backend Nodes** | `orchestrator/nodes.py` | Node functions including `interrupt()` calls |
| **Backend State** | `orchestrator/state.py` | `NewsletterState` TypedDict |
| **Backend Persistence** | `orchestrator/mongodb_saver.py` | Custom LangGraph checkpointer for MongoDB |
| **Frontend API Client** | `api/client.ts` | Axios instance with interceptors (30s default timeout) |

---

## Bug Fixes

All bugs discovered and fixed while building and testing the end-to-end HITL flow. Listed in the order they were encountered.

---

### #1. Missing "Workflow" tab in the UI

**Symptom:** No way to see or interact with the workflow after starting it.

**Root cause:** The `NewsletterApp.tsx` had 3 tabs (Dashboard, Generate, Manual Mode) but the workflow view was only accessible programmatically via `setView('workflow')` — there was no tab for it.

**Fix:** Added a "Workflow" tab with `GitBranch` icon to the `TabsList`. Moved the workflow UI into a `TabsContent` block and added an empty state when no workflow is active.

**File:** `frontend/src/components/apps/newsletter/NewsletterApp.tsx`

---

### #2. 500 error on `/api/v1/executions/stats`

**Symptom:** `ResponseValidationError` — endpoint returned `None`.

**Root cause:** The route `/{execution_id}` (a catch-all path parameter) was defined before `/stats`, so FastAPI matched "stats" as an execution ID. The handler had `pass` (returns `None`), failing Pydantic response validation.

**Fix:** Moved the `/stats` route definition above `/{execution_id}`. Changed the stub handler from `pass` to `raise HTTPException(status_code=404)`.

**File:** `backend/app/api/v1/endpoints/executions.py`

---

### #3. 401 Unauthorized on SSE stream endpoint

**Symptom:** `EventSource` connection to `/workflows/{id}/stream` returned 401.

**Root cause:** The SSE endpoint used `Depends(get_current_user)` for auth, which reads the `Authorization` header. The browser's `EventSource` API cannot set custom headers — it can only send cookies or URL parameters.

**Fix:** Changed the endpoint to accept a `token` query parameter instead. The frontend passes the JWT as `?token=<jwt>`. The backend validates it with `decode_access_token()`.

**Files:**
- `backend/app/platforms/newsletter/routers/workflows.py` — accept `token: Query` param
- `frontend/src/hooks/useWorkflowSSE.ts` — append `?token=` to the EventSource URL

---

### #4. `UnicodeDecodeError` in MongoDB checkpoint serialization

**Symptom:** `'utf-8' codec can't decode byte 0x81 in position 1` when saving LangGraph state to MongoDB.

**Root cause:** `JsonPlusSerializer.dumps_typed()` returns `(type_str, data_bytes)` where `data_bytes` is msgpack binary, not valid UTF-8. The code tried to store raw bytes as a MongoDB string field.

**Fix:** Encode all serialized binary data with `base64.b64encode()` before storing, and decode with `base64.b64decode()` when loading. Applied to 6 locations across `_serialize_checkpoint`, `_deserialize_checkpoint`, `put_writes`, and `aput_writes`.

**File:** `backend/app/platforms/newsletter/orchestrator/mongodb_saver.py`

---

### #5. `TypeError: tuple() takes no keyword arguments` for PendingWrite

**Symptom:** Crash when loading checkpoint writes from MongoDB.

**Root cause:** The code used `PendingWrite(task_id=..., channel=..., value=...)` but `PendingWrite` in LangGraph is a plain `tuple[str, str, Any]` type alias, not a named tuple. Named keyword arguments don't work.

**Fix:** Changed all `PendingWrite(...)` constructors to plain tuples: `(task_id, channel, value)`. Removed the `PendingWrite` import.

**File:** `backend/app/platforms/newsletter/orchestrator/mongodb_saver.py`

---

### #6. Checkpoint type mismatch — tracker spinning, no review UI

**Symptom:** The WorkflowTracker showed "Research" as spinning endlessly. The ArticleReview component sometimes didn't render. Logs showed the checkpoint was reached but the frontend `switch` didn't match.

**Root cause:** The backend checkpoint nodes used different type names than the frontend expected:
- Backend: `article_review` → Frontend expected: `research_review`
- Backend: `send_approval` → Frontend expected: `final_review`
- `subject_review` existed in backend but was missing from the frontend `Checkpoint.checkpoint_type` union type.

**Fix:**
- Renamed backend `checkpoint_type` values: `article_review` → `research_review`, `send_approval` → `final_review`
- Added `'subject_review'` to the TypeScript `Checkpoint.checkpoint_type` union
- Added `SubjectReview` component case in `renderCheckpointUI`

**Files:**
- `backend/app/platforms/newsletter/orchestrator/nodes.py` — renamed types
- `frontend/src/types/newsletter.ts` — added `subject_review` to union
- `frontend/src/components/apps/newsletter/NewsletterApp.tsx` — added switch case

---

### #7. WorkflowTracker didn't mark steps before current as completed

**Symptom:** When at `research_review`, the `research` step still showed as pending (no checkmark).

**Root cause:** `get_workflow_status()` returned `current_step` from `state.get("current_step")` which was `"research"` (set by `research_node`). But at the checkpoint, the graph was paused at `checkpoint_articles` — the `current_step` field in state hadn't been updated to reflect the checkpoint's position.

**Fix (backend):** Added a `node_to_step` mapping in `get_workflow_status()` that translates the paused LangGraph node name to the frontend step ID when the workflow is at a checkpoint:

```python
if state_snapshot.next:
    node_to_step = {
        "checkpoint_articles": "research_review",
        "checkpoint_content": "content_review",
        "checkpoint_subjects": "subject_review",
        "checkpoint_send": "final_review",
    }
    current_step = node_to_step.get(state_snapshot.next[0], current_step)
```

**Fix (frontend):** Updated `getStepStatus()` in `WorkflowTracker` to mark all steps with an index lower than `currentStepIndex` as completed, so non-checkpoint steps (like `research`) get checkmarks when the tracker moves past them.

**Files:**
- `backend/app/platforms/newsletter/orchestrator/orchestrator.py`
- `frontend/src/components/apps/newsletter/workflow/WorkflowTracker.tsx`

---

### #8. Approve restarted the workflow from scratch instead of resuming

**Symptom:** After approving article review, the backend logs showed the workflow starting over from `get_preferences_node` instead of continuing to `generate_content_node`.

**Root cause:** The `approve_checkpoint()` method used `self.graph.ainvoke({"checkpoint_response": response}, config)` which starts a **new** graph execution with a fresh initial state, not a resume.

**Fix:** Changed to `self.graph.ainvoke(Command(resume=response), config)`. The `Command(resume=...)` from `langgraph.types` tells LangGraph to load the persisted state from MongoDB and feed `response` as the return value of the interrupted `interrupt()` call.

**File:** `backend/app/platforms/newsletter/orchestrator/orchestrator.py`

---

### #9. Content review showed empty content

**Symptom:** The ContentReview component rendered but all fields were blank.

**Root cause (backend):** `generate_content_node` read `result.get("content", {})` but `WritingAgent.run()` returns the newsletter under `result["newsletter"]`, not `result["content"]`.

**Root cause (frontend):** The `content_review` switch case passed `checkpointData.newsletter` to the `ContentReview` component, but the backend's `checkpoint_content_node` stored the data as separate flat fields: `content`, `html_preview`, `word_count` — not nested under a `newsletter` key.

**Fix (backend):** Changed `generate_content_node` to read from the correct key:
```python
newsletter = result.get("newsletter", {})
return {
    "newsletter_content": newsletter.get("markdown", newsletter.get("content", "")),
    "newsletter_html": newsletter.get("html", ""),
    ...
}
```

**Fix (frontend):** Updated the `content_review` case to map from the backend's flat fields:
```tsx
content={checkpointData.newsletter || {
  content: String(checkpointData.content || ''),
  word_count: Number(checkpointData.word_count || 0),
}}
```

**Files:**
- `backend/app/platforms/newsletter/orchestrator/nodes.py`
- `frontend/src/components/apps/newsletter/NewsletterApp.tsx`

---

### #10. Approve button stays enabled after clicking / UI stuck on "Review Articles"

**Symptom:** After clicking Approve on article review, the button briefly showed loading, then re-enabled. The WorkflowTracker kept spinning on "Review Articles". No GET requests appeared in logs after the POST /approve response.

**Root cause:** The Axios HTTP client has a **30-second default timeout** (`api/client.ts` line 7: `timeout: 30000`). But `POST /approve` is **blocking** — when LangGraph resumes, it runs through `generate_content_node` (LLM call ~37s), `create_subjects_node` (LLM ~3s), and `create_summary` (LLM ~15s) before hitting the next `interrupt()`. Total: **~55 seconds**. The Axios request timed out at 30s, triggering `onError` instead of `onSuccess`. Since `onSuccess` never fired, React Query never invalidated the workflow/checkpoint queries, so the UI never updated.

**Fix:** Added `{ timeout: TIMEOUTS.GENERATION }` (5 minutes / 300,000ms) to the `approveCheckpoint`, `editCheckpoint`, and `rejectCheckpoint` API calls. These calls resume the LangGraph workflow which runs LLM agents, so they need the same generous timeout as the initial `/generate` call.

**File:** `frontend/src/api/newsletter.ts`

```tsx
// Before (inherited 30s default — too short)
approveCheckpoint: async (workflowId, request) => {
  const response = await apiClient.post(`/approve`, request);
  ...
};

// After (5 minute timeout for LLM resume)
approveCheckpoint: async (workflowId, request) => {
  const response = await apiClient.post(`/approve`, request, {
    timeout: TIMEOUTS.GENERATION    // 300000ms = 5 minutes
  });
  ...
};
```

---

### #11. SubjectReview crashed with `TypeError: style is undefined`

**Symptom:** `TypeError: can't access property "toLowerCase", style is undefined` when reaching the subject review checkpoint.

**Root cause:** Data format mismatch across three layers:
1. `WritingAgent.create_subject_lines()` returns `[{"text": "...", "angle": "curiosity"}, ...]` — key is `angle`
2. `NewsletterState.subject_lines` was typed as `list[str]` — plain strings
3. Frontend `SubjectReview` component expects `SubjectLine[]` where `SubjectLine = { text: string, style: string }` — key is `style`

The `create_subjects_node` passed the raw agent output through without transformation. The fallback values were plain strings (`["Your Newsletter Update"]`).

**Fix (backend):** Added `_normalize_subject_lines()` helper that converts any format to `{text, style}`:
- Maps `angle` values to `style` values (e.g., `"curiosity"` → `"casual"`)
- Wraps plain strings in `{"text": s, "style": default_tone}`
- Updated `create_subjects_node` to normalize before storing
- Updated fallback values to use dict format
- Changed state type from `list[str]` to `list[dict[str, str]]`
- Added `_extract_subject_text()` helper for `store_newsletter_node` title fallback

**Fix (frontend):** Added defensive normalization in the `subject_review` switch case to handle any format. Fixed `onApprove` to send `selected_subject` key matching what `checkpoint_subjects_node` expects.

**Files:**
- `backend/app/platforms/newsletter/orchestrator/nodes.py`
- `backend/app/platforms/newsletter/orchestrator/state.py`
- `frontend/src/components/apps/newsletter/NewsletterApp.tsx`

---

### #12. WorkflowTracker didn't show all checkmarks when workflow completed

**Symptom:** After the workflow finished, `research` and `writing` steps still showed as pending (no checkmark). The progress bar didn't fill completely.

**Root cause:** When the workflow completes, `current_step` is `"send_email"` which isn't in the `WORKFLOW_STEPS` array. `currentStepIndex` becomes `-1`, so the index-based completion check (`stepIndex < currentStepIndex`) fails for all steps. Only steps in `checkpoints_completed` (like `research_review`) got checkmarks — non-checkpoint steps (`research`, `writing`) were never in that list.

**Fix:** Added `if (status === 'completed') return 'completed'` at the top of `getStepStatus()`. When the workflow status is `"completed"`, all steps show checkmarks regardless of index. Also set the progress bar to 100% width when completed. Applied the same fix to `WorkflowTrackerCompact`.

**File:** `frontend/src/components/apps/newsletter/workflow/WorkflowTracker.tsx`

---

### #13. Send allowed without subscribers

**Symptom:** The final review checkpoint allowed sending even though `recipient_count` was 0.

**Root cause:** `FinalApproval` had a warning banner for `recipientCount === 0` but the `recipientCount` prop was never passed from `NewsletterApp.tsx` (defaulted to 0 in the component). The Send button was not disabled when there were no recipients.

**Fix:** Passed `recipientCount={Number(checkpointData.recipient_count || 0)}` from the `final_review` switch case. Disabled the Send/Schedule button when `recipientCount === 0`.

**Files:**
- `frontend/src/components/apps/newsletter/NewsletterApp.tsx` — pass prop
- `frontend/src/components/apps/newsletter/workflow/FinalApproval.tsx` — disable button

---

### #14. Workflow state lost on browser refresh

**Symptom:** Refreshing the browser during an active workflow returned the user to the Dashboard tab with "No Active Workflow" displayed. All in-progress workflow context (workflow ID, status, checkpoint data) was gone. The user had to start a new workflow from scratch.

**Root cause:** The Zustand store (`newsletterStore.ts`) uses the `persist` middleware with a `partialize` config that controls which fields are saved to `localStorage`. The config only persisted UI preferences (`showPreview`, `previewFormat`, `listViewMode`, `sidebarExpanded`) and form drafts (`researchTopics`, `selectedTone`, `maxArticles`). The critical `activeWorkflowId` field was **excluded** from persistence, so it was lost on page refresh (reset to `null`).

Additionally, `NewsletterApp.tsx` initialized the view state as `useState<AppView>('dashboard')` unconditionally, so even if the workflow ID were persisted, the user would land on the Dashboard tab instead of the Workflow tab.

**Fix (store):** Added `activeWorkflowId` to the `partialize` config so it persists in `localStorage` across page refreshes:

```tsx
// Before — activeWorkflowId NOT persisted
partialize: (state) => ({
  researchTopics: state.researchTopics,
  selectedTone: state.selectedTone,
  maxArticles: state.maxArticles,
  showPreview: state.showPreview,
  previewFormat: state.previewFormat,
  listViewMode: state.listViewMode,
  sidebarExpanded: state.sidebarExpanded,
}),

// After — activeWorkflowId IS persisted
partialize: (state) => ({
  activeWorkflowId: state.activeWorkflowId,
  researchTopics: state.researchTopics,
  selectedTone: state.selectedTone,
  maxArticles: state.maxArticles,
  showPreview: state.showPreview,
  previewFormat: state.previewFormat,
  listViewMode: state.listViewMode,
  sidebarExpanded: state.sidebarExpanded,
}),
```

**Fix (app):** Changed the initial `view` state to check for a persisted workflow ID. Moved `useWorkflowState()` above the `useState` so the restored `activeWorkflowId` is available at initialization time:

```tsx
// Before — always starts on dashboard
const [view, setView] = useState<AppView>('dashboard');

// After — opens workflow tab if a workflow was active before refresh
const {
  activeWorkflowId,
  ...
} = useWorkflowState();
const [view, setView] = useState<AppView>(activeWorkflowId ? 'workflow' : 'dashboard');
```

On refresh, the restored `activeWorkflowId` triggers `useWorkflow`, `useWorkflowCheckpoint`, `useWorkflowHistory`, and `useWorkflowSSE` to refetch from the backend, fully restoring the workflow UI state (tracker position, checkpoint data, history).

**Files:**
- `frontend/src/store/newsletterStore.ts` — added `activeWorkflowId` to `partialize`
- `frontend/src/components/apps/newsletter/NewsletterApp.tsx` — conditional initial view

---

### Bug Fix Summary Table

| # | Bug | Layer | Root Cause Category |
|---|---|---|---|
| 1 | Missing Workflow tab | Frontend | Missing UI element |
| 2 | 500 on /executions/stats | Backend | Route ordering (catch-all before specific) |
| 3 | 401 on SSE stream | Both | EventSource can't set headers |
| 4 | UnicodeDecodeError in MongoDB | Backend | Binary data stored as UTF-8 string |
| 5 | tuple() keyword args | Backend | Wrong type assumption (named vs plain tuple) |
| 6 | Checkpoint type mismatch | Both | Backend/frontend naming disagreement |
| 7 | Steps not marked completed | Both | Missing node-to-step mapping |
| 8 | Approve restarts workflow | Backend | `ainvoke()` vs `Command(resume=)` |
| 9 | Empty content review | Both | Wrong dict key + wrong field mapping |
| 10 | Approve timeout / UI stuck | Frontend | 30s Axios timeout vs 55s+ LLM resume |
| 11 | SubjectReview crash | Both | `angle` vs `style` + `str` vs `dict` |
| 12 | Missing checkmarks on complete | Frontend | `currentStepIndex = -1` when step not in list |
| 13 | Send without subscribers | Frontend | Prop not passed + button not disabled |
| 14 | Workflow lost on refresh | Frontend | `activeWorkflowId` excluded from localStorage persistence |
