# Phase 9: Newsletter Orchestrator with LangGraph HITL

## Goal
Multi-agent workflow coordination with Human-in-the-Loop checkpoints

## Status
- [ ] In Progress

## Files to Create/Modify
```
backend/app/platforms/newsletter/orchestrator/
├── __init__.py          # Update exports
├── state.py             # NEW: Workflow state schema (TypedDict)
├── graph.py             # NEW: LangGraph workflow definition
├── checkpoints.py       # NEW: HITL checkpoint handlers
└── orchestrator.py      # UPDATE: Integrate LangGraph workflow
```

## Implementation Plan

### 1. State Schema (`state.py`)
```python
class NewsletterState(TypedDict):
    # Input
    user_id: str
    topics: list[str]
    tone: str
    custom_prompt: str | None

    # Preferences (from PreferenceAgent)
    preferences: dict

    # Research results (from ResearchAgent)
    articles: list[dict]
    research_metadata: dict

    # Content (from WritingAgent)
    newsletter_content: str
    newsletter_html: str
    newsletter_plain: str
    subject_lines: list[str]
    selected_subject: str | None

    # Workflow control
    workflow_id: str
    current_checkpoint: str | None
    checkpoint_data: dict
    status: str  # running, paused, completed, cancelled, failed

    # Storage
    newsletter_id: str | None

    # History
    history: list[dict]
    created_at: str
    updated_at: str
```

### 2. Graph Definition (`graph.py`)
```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.mongodb import MongoDBSaver

def create_newsletter_graph():
    graph = StateGraph(NewsletterState)

    # Add nodes
    graph.add_node("get_preferences", get_preferences_node)
    graph.add_node("process_prompt", process_prompt_node)
    graph.add_node("research", research_node)
    graph.add_node("checkpoint_articles", checkpoint_articles_node)
    graph.add_node("generate_content", generate_content_node)
    graph.add_node("checkpoint_content", checkpoint_content_node)
    graph.add_node("create_subjects", create_subjects_node)
    graph.add_node("checkpoint_subjects", checkpoint_subjects_node)
    graph.add_node("format_email", format_email_node)
    graph.add_node("store_newsletter", store_newsletter_node)
    graph.add_node("checkpoint_send", checkpoint_send_node)
    graph.add_node("send_email", send_email_node)

    # Add edges
    graph.set_entry_point("get_preferences")
    graph.add_edge("get_preferences", "process_prompt")
    graph.add_edge("process_prompt", "research")
    graph.add_edge("research", "checkpoint_articles")
    graph.add_conditional_edges("checkpoint_articles", route_after_checkpoint)
    # ... etc

    return graph.compile(checkpointer=MongoDBSaver(...))
```

### 3. Checkpoint Handlers (`checkpoints.py`)
```python
from langgraph.types import interrupt

def checkpoint_articles_node(state: NewsletterState) -> NewsletterState:
    """HITL Checkpoint 1: Review article selection."""
    checkpoint_data = {
        "type": "article_review",
        "articles": state["articles"],
        "metadata": state["research_metadata"],
        "actions": ["approve", "edit", "reject"],
    }

    # This pauses the workflow and waits for human input
    human_response = interrupt(checkpoint_data)

    if human_response["action"] == "reject":
        # Will trigger re-run of research node
        return {**state, "status": "rejected_articles"}

    if human_response["action"] == "edit":
        # Apply edits
        return {**state, "articles": human_response["articles"]}

    return state  # approved as-is
```

### 4. Orchestrator Update (`orchestrator.py`)
```python
class NewsletterOrchestrator(BaseOrchestrator):
    def __init__(self):
        self.graph = create_newsletter_graph()
        self.checkpointer = MongoDBSaver(...)

    async def start_newsletter_generation(
        self, user_id: str, topics: list[str], tone: str, custom_prompt: str = None
    ) -> str:
        """Start workflow, returns workflow_id."""
        workflow_id = str(uuid4())
        initial_state = NewsletterState(
            user_id=user_id,
            topics=topics,
            tone=tone,
            custom_prompt=custom_prompt,
            workflow_id=workflow_id,
            status="running",
            ...
        )

        # Start async execution
        config = {"configurable": {"thread_id": workflow_id}}
        await self.graph.ainvoke(initial_state, config)

        return workflow_id

    async def get_pending_checkpoint(self, workflow_id: str) -> dict | None:
        """Get current checkpoint awaiting approval."""
        config = {"configurable": {"thread_id": workflow_id}}
        state = await self.graph.aget_state(config)

        if state.next:  # Workflow is paused
            return state.values.get("checkpoint_data")
        return None

    async def approve_checkpoint(self, workflow_id: str, checkpoint_id: str) -> dict:
        """Approve and continue workflow."""
        config = {"configurable": {"thread_id": workflow_id}}
        await self.graph.ainvoke(
            None,  # Resume with no modifications
            config,
        )
        return await self.get_workflow_status(workflow_id)
```

## Workflow Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│                    NEWSLETTER GENERATION WORKFLOW                │
├─────────────────────────────────────────────────────────────────┤
│  1. Get user preferences (Preference Agent)                     │
│  2. Process custom prompt if provided (Custom Prompt Agent)     │
│  3. Research content (Research Agent)                           │
│                         │                                        │
│            ┌────────────▼────────────┐                          │
│            │   🛑 CHECKPOINT 1       │                          │
│            │   Review Article        │                          │
│            │   Selection             │                          │
│            │   [Approve/Edit/Reject] │                          │
│            └────────────┬────────────┘                          │
│                         │                                        │
│  4. Generate newsletter (Writing Agent)                         │
│                         │                                        │
│            ┌────────────▼────────────┐                          │
│            │   🛑 CHECKPOINT 2       │                          │
│            │   Review Newsletter     │                          │
│            │   Content               │                          │
│            │   [Approve/Edit/Reject] │                          │
│            └────────────┬────────────┘                          │
│                         │                                        │
│  5. Create subject lines (Writing Agent)                        │
│                         │                                        │
│            ┌────────────▼────────────┐                          │
│            │   🛑 CHECKPOINT 3       │                          │
│            │   Approve Tone &        │                          │
│            │   Subject Lines         │                          │
│            │   [Approve/Edit/Reject] │                          │
│            └────────────┬────────────┘                          │
│                         │                                        │
│  6. Format for email (Writing Agent)                            │
│  7. Store in database (MongoDB)                                 │
│  8. Store in vector DB (Weaviate RAG)                          │
│                         │                                        │
│            ┌────────────▼────────────┐                          │
│            │   🛑 CHECKPOINT 4       │                          │
│            │   Final Send            │                          │
│            │   Approval              │                          │
│            │   [Send/Schedule/Cancel]│                          │
│            └────────────┬────────────┘                          │
│                         │                                        │
│  9. Send if approved (Email Service)                            │
└─────────────────────────────────────────────────────────────────┘
```

## HITL Checkpoint Details

| Checkpoint | Trigger | Human Actions | Data Shown |
|------------|---------|---------------|------------|
| **1. Article Selection** | After research | Approve, Edit, Reject | Article titles, sources, summaries |
| **2. Content Review** | After writing | Approve, Edit, Reject | Full preview, word count, tone |
| **3. Tone & Subject** | After subjects | Approve, Edit, Reject | 5 subject options, tone class |
| **4. Final Approval** | Before sending | Send, Schedule, Cancel | Final preview, recipient count |

## Dependencies
- Phases 6-8 (All agents: Research, Writing, Preference, CustomPrompt)
- Phase 4 (RAG for storage)
- Phase 5 (Memory for state)
- LangGraph (already in deps)
- langgraph-checkpoint-mongodb (need to add)

## Tests to Create
```
backend/app/platforms/newsletter/tests/phase9/
├── __init__.py
├── test_state.py           # State schema tests
├── test_graph.py           # Graph definition tests
├── test_checkpoints.py     # Checkpoint handler tests
└── test_orchestrator.py    # Full orchestrator tests
```

## Verification
- [ ] Workflow pauses at each checkpoint
- [ ] State persists across interrupts
- [ ] Approve/Edit/Reject work correctly
- [ ] Cancel terminates workflow
- [ ] Tests passing
