# Phase 9: LangGraph Orchestrator with HITL Checkpoints

## Status: Completed

## Overview

Phase 9 implements the core workflow orchestration using LangGraph with Human-in-the-Loop (HITL) checkpoints. This enables persistent, interruptible workflows where humans can review and approve key decisions before the newsletter is sent.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        NEWSLETTER GENERATION WORKFLOW                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐       │
│  │  Preference      │    │  Custom Prompt   │    │  Research        │       │
│  │  Agent           │───▶│  Agent           │───▶│  Agent           │       │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘       │
│                                                           │                  │
│                                                           ▼                  │
│                                            ┌──────────────────────────┐     │
│                                            │  🛑 CHECKPOINT 1         │     │
│                                            │  Review Article Selection │     │
│                                            │  [Approve/Edit/Reject]    │     │
│                                            └──────────────┬───────────┘     │
│                                                           │                  │
│                                                           ▼                  │
│                                            ┌──────────────────────────┐     │
│                                            │  Writing Agent           │     │
│                                            │  (Generate Content)      │     │
│                                            └──────────────┬───────────┘     │
│                                                           │                  │
│                                                           ▼                  │
│                                            ┌──────────────────────────┐     │
│                                            │  🛑 CHECKPOINT 2         │     │
│                                            │  Review Newsletter       │     │
│                                            │  [Approve/Edit/Reject]    │     │
│                                            └──────────────┬───────────┘     │
│                                                           │                  │
│                                                           ▼                  │
│                                            ┌──────────────────────────┐     │
│                                            │  Writing Agent           │     │
│                                            │  (Create Subjects)       │     │
│                                            └──────────────┬───────────┘     │
│                                                           │                  │
│                                                           ▼                  │
│                                            ┌──────────────────────────┐     │
│                                            │  🛑 CHECKPOINT 3         │     │
│                                            │  Select Subject Line     │     │
│                                            │  [Approve/Edit/Reject]    │     │
│                                            └──────────────┬───────────┘     │
│                                                           │                  │
│                                                           ▼                  │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐       │
│  │  Format Email    │───▶│  Store in DB     │───▶│  🛑 CHECKPOINT 4 │       │
│  │                  │    │  (MongoDB)       │    │  Send Approval   │       │
│  └──────────────────┘    └──────────────────┘    │[Send/Schedule/   │       │
│                                                   │ Cancel]          │       │
│                                                   └────────┬─────────┘       │
│                                                            │                 │
│                                                            ▼                 │
│                                                   ┌──────────────────┐       │
│                                                   │  Email Service   │       │
│                                                   │  (Phase 10)      │       │
│                                                   └──────────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Files Created

```
backend/app/platforms/newsletter/orchestrator/
├── __init__.py          # Module exports
├── state.py             # NewsletterState TypedDict (30+ fields)
├── nodes.py             # Agent nodes and checkpoint nodes
├── graph.py             # LangGraph StateGraph definition
├── mongodb_saver.py     # Custom MongoDB checkpointer
└── orchestrator.py      # NewsletterOrchestrator class

backend/app/platforms/newsletter/tests/phase9/
├── __init__.py
├── test_state.py        # 30 tests
├── test_graph.py        # 15 tests
├── test_mongodb_saver.py # 20 tests
├── test_nodes.py        # 24 tests
└── test_orchestrator.py # 30 tests
```

---

## Key Components

### 1. NewsletterState (state.py)

The workflow state is a comprehensive TypedDict that tracks all data through the pipeline:

```python
class NewsletterState(TypedDict, total=False):
    # Input Parameters
    user_id: str
    topics: list[str]
    tone: str
    custom_prompt: str | None
    max_articles: int

    # Preferences (from PreferenceAgent)
    preferences: dict[str, Any]
    preferences_applied: bool

    # Prompt Analysis (from CustomPromptAgent)
    prompt_analysis: dict[str, Any] | None
    extracted_topics: list[str] | None

    # Research Results (from ResearchAgent)
    articles: list[ArticleData]
    research_metadata: dict[str, Any]
    research_completed: bool

    # Newsletter Content (from WritingAgent)
    newsletter_content: str
    newsletter_html: str
    newsletter_plain: str
    word_count: int
    content_generated: bool

    # Subject Lines (from WritingAgent)
    subject_lines: list[str]
    selected_subject: str | None
    subjects_generated: bool

    # Workflow Control
    workflow_id: str
    status: str  # running, paused, completed, cancelled, failed
    current_step: str | None
    error: str | None

    # Checkpoint State
    current_checkpoint: CheckpointData | None
    checkpoint_response: dict[str, Any] | None
    checkpoints_completed: list[str]

    # Storage
    newsletter_id: str | None
    stored_in_db: bool
    stored_in_rag: bool

    # Email Delivery
    email_sent: bool
    email_scheduled: str | None
    recipient_count: int

    # History & Timestamps
    history: list[dict[str, Any]]
    created_at: str
    updated_at: str
```

### 2. MongoDB Checkpointer (mongodb_saver.py)

Custom implementation of LangGraph's `BaseCheckpointSaver` for MongoDB persistence:

```python
class MongoDBSaver(BaseCheckpointSaver):
    """
    MongoDB-based checkpoint saver for LangGraph.

    Stores checkpoints and pending writes in MongoDB collections,
    enabling persistent HITL workflows that survive restarts.
    """

    # Collections
    CHECKPOINTS_COLLECTION = "langgraph_checkpoints"
    WRITES_COLLECTION = "langgraph_writes"

    # Key methods
    def get_tuple(self, config) -> CheckpointTuple | None
    def put(self, config, checkpoint, metadata, new_versions) -> RunnableConfig
    def list(self, config, *, filter, before, limit) -> Iterator[CheckpointTuple]

    # Async versions
    async def aget_tuple(self, config) -> CheckpointTuple | None
    async def aput(self, config, checkpoint, metadata, new_versions) -> RunnableConfig
    async def alist(self, config, *, filter, before, limit) -> AsyncIterator[CheckpointTuple]
```

### 3. Workflow Nodes (nodes.py)

#### Agent Nodes (async)
```python
async def get_preferences_node(state: NewsletterState) -> dict[str, Any]
async def process_prompt_node(state: NewsletterState) -> dict[str, Any]
async def research_node(state: NewsletterState) -> dict[str, Any]
async def generate_content_node(state: NewsletterState) -> dict[str, Any]
async def create_subjects_node(state: NewsletterState) -> dict[str, Any]
async def format_email_node(state: NewsletterState) -> dict[str, Any]
async def store_newsletter_node(state: NewsletterState) -> dict[str, Any]
async def send_email_node(state: NewsletterState) -> dict[str, Any]
```

#### Checkpoint Nodes (sync, using interrupt)
```python
def checkpoint_articles_node(state: NewsletterState) -> dict[str, Any]:
    """HITL Checkpoint 1: Review article selection."""
    checkpoint_data = CheckpointData(
        checkpoint_id=str(uuid4()),
        checkpoint_type="article_review",
        title="Review Article Selection",
        description=f"Review {len(articles)} articles found",
        data={"articles": articles, "topics": topics},
        actions=["approve", "edit", "reject"],
    )

    # This pauses the workflow and waits for human input
    response = interrupt(checkpoint_data)

    if response["action"] == "reject":
        return {"research_completed": False}  # Re-run research
    if response["action"] == "edit":
        return {"articles": response["articles"]}
    return {}  # Approved as-is
```

### 4. Graph Definition (graph.py)

```python
def create_newsletter_graph(use_checkpointer: bool = True) -> StateGraph:
    graph = StateGraph(NewsletterState)

    # Add agent nodes
    graph.add_node("get_preferences", get_preferences_node)
    graph.add_node("process_prompt", process_prompt_node)
    graph.add_node("research", research_node)
    graph.add_node("generate_content", generate_content_node)
    graph.add_node("create_subjects", create_subjects_node)
    graph.add_node("format_email", format_email_node)
    graph.add_node("store_newsletter", store_newsletter_node)
    graph.add_node("send_email", send_email_node)

    # Add checkpoint nodes
    graph.add_node("checkpoint_articles", checkpoint_articles_node)
    graph.add_node("checkpoint_content", checkpoint_content_node)
    graph.add_node("checkpoint_subjects", checkpoint_subjects_node)
    graph.add_node("checkpoint_send", checkpoint_send_node)

    # Set entry point
    graph.set_entry_point("get_preferences")

    # Linear flow to first checkpoint
    graph.add_edge("get_preferences", "process_prompt")
    graph.add_edge("process_prompt", "research")
    graph.add_edge("research", "checkpoint_articles")

    # Conditional edges after checkpoints
    graph.add_conditional_edges(
        "checkpoint_articles",
        route_after_article_checkpoint,
        {"research": "research", "generate_content": "generate_content"},
    )

    # ... more edges ...

    if use_checkpointer:
        return graph.compile(checkpointer=get_mongodb_saver())
    return graph.compile()
```

### 5. Orchestrator (orchestrator.py)

```python
class NewsletterOrchestrator(BaseOrchestrator):
    """
    Orchestrator for the Newsletter platform using LangGraph.
    """

    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Start newsletter generation workflow."""
        initial_state = create_initial_state(
            user_id=input["user_id"],
            topics=input["topics"],
            tone=input.get("tone", "professional"),
        )

        config = {"configurable": {"thread_id": initial_state["workflow_id"]}}
        result = await self.graph.ainvoke(initial_state, config)

        return {
            "success": True,
            "workflow_id": initial_state["workflow_id"],
            "status": "awaiting_approval" if state_snapshot.next else "completed",
        }

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get current workflow state."""
        ...

    async def get_pending_checkpoint(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get checkpoint awaiting approval."""
        ...

    async def approve_checkpoint(
        self, workflow_id: str, checkpoint_id: str, action: str,
        modifications: Optional[Dict] = None, feedback: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Resume workflow with human decision."""
        ...

    async def cancel_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Cancel and cleanup workflow."""
        ...

    async def list_workflows(
        self, user_id: str = None, status: str = None, limit: int = 10,
    ) -> list[Dict[str, Any]]:
        """List workflows with optional filters."""
        ...
```

---

## HITL Checkpoint Details

| Checkpoint | Trigger | Human Actions | Data Shown |
|------------|---------|---------------|------------|
| **1. Article Selection** | After research | Approve, Edit, Reject | Article titles, URLs, sources, summaries, scores |
| **2. Content Review** | After writing | Approve, Edit, Reject | Full newsletter preview, word count, tone used |
| **3. Subject Selection** | After subjects | Approve, Edit, Reject | 5 subject line options, tone classification |
| **4. Send Approval** | Before sending | Send, Schedule, Cancel | Final preview, recipient count, newsletter ID |

---

## Routing Functions

```python
def route_after_article_checkpoint(state: NewsletterState) -> Literal["research", "generate_content"]:
    """Route based on article review decision."""
    if not state.get("research_completed", False):
        return "research"  # Rejected - re-run research
    return "generate_content"  # Approved

def route_after_send_checkpoint(state: NewsletterState) -> Literal["send_email", "__end__"]:
    """Route based on send approval."""
    status = state.get("status", "running")
    if status in ("cancelled", "scheduled"):
        return END
    return "send_email"
```

---

## Usage Example

### Starting a Workflow

```python
from app.platforms.newsletter.orchestrator import get_newsletter_orchestrator

orchestrator = get_newsletter_orchestrator()

# Start workflow
result = await orchestrator.run({
    "user_id": "user-123",
    "topics": ["AI", "Machine Learning"],
    "tone": "professional",
    "max_articles": 10,
})

print(result)
# {
#     "success": True,
#     "workflow_id": "abc123-...",
#     "status": "awaiting_approval",
#     "current_checkpoint": {...}
# }
```

### Checking for Pending Checkpoint

```python
checkpoint = await orchestrator.get_pending_checkpoint("abc123-...")
print(checkpoint)
# {
#     "workflow_id": "abc123-...",
#     "checkpoint_id": "ckpt-456",
#     "checkpoint_type": "article_review",
#     "title": "Review Article Selection",
#     "data": {"articles": [...], "topics": [...]},
#     "actions": ["approve", "edit", "reject"]
# }
```

### Approving a Checkpoint

```python
result = await orchestrator.approve_checkpoint(
    workflow_id="abc123-...",
    checkpoint_id="ckpt-456",
    action="approve",
)
# Workflow continues to next step
```

### Editing at a Checkpoint

```python
result = await orchestrator.approve_checkpoint(
    workflow_id="abc123-...",
    checkpoint_id="ckpt-456",
    action="edit",
    modifications={"articles": [selected_articles]},
)
```

---

## MongoDB Collections

### langgraph_checkpoints
```json
{
    "thread_id": "workflow-uuid",
    "checkpoint_ns": "",
    "checkpoint_id": "checkpoint-uuid",
    "parent_checkpoint_id": "parent-uuid",
    "checkpoint": {
        "v": 1,
        "id": "...",
        "ts": "...",
        "channel_values": {...},
        "channel_versions": {...}
    },
    "metadata": {...},
    "created_at": "2024-01-15T10:30:00Z"
}
```

### langgraph_writes
```json
{
    "thread_id": "workflow-uuid",
    "checkpoint_ns": "",
    "checkpoint_id": "checkpoint-uuid",
    "task_id": "task-uuid",
    "channel": "channel_name",
    "value": "serialized_value",
    "created_at": "2024-01-15T10:30:00Z"
}
```

---

## Tests

```
tests/phase9/
├── test_state.py           # 30 tests - State creation, history
├── test_graph.py           # 15 tests - Graph routing, compilation
├── test_mongodb_saver.py   # 20 tests - Checkpoint persistence
├── test_nodes.py           # 24 tests - Node execution
└── test_orchestrator.py    # 30 tests - Full workflow lifecycle

Total: 119 tests
```

---

## Dependencies

- LangGraph (`langgraph>=0.0.20`)
- Motor (async MongoDB driver)
- PyMongo (sync MongoDB driver)
- All Phase 6-8 agents (Research, Writing, Preference, CustomPrompt)
