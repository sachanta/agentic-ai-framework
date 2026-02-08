# Phase 9: Newsletter Orchestrator with LangGraph HITL

## Goal
Multi-agent workflow coordination with Human-in-the-Loop checkpoints

## Status
- [x] Completed

## Files Created
```
backend/app/platforms/newsletter/orchestrator/
├── __init__.py          # Updated exports
├── state.py             # Workflow state schema (TypedDict)
├── nodes.py             # Agent and checkpoint node implementations
├── graph.py             # LangGraph workflow definition
├── mongodb_saver.py     # Custom MongoDB checkpointer
└── orchestrator.py      # Full LangGraph integration
```

## Implementation Summary

### 1. State Schema (`state.py`)
- `NewsletterState` TypedDict with 30+ fields
- `ArticleData` and `CheckpointData` TypedDicts
- Helper functions: `create_initial_state()`, `add_history_entry()`

### 2. MongoDB Checkpointer (`mongodb_saver.py`)
- Custom `MongoDBSaver` extending LangGraph's `BaseCheckpointSaver`
- Sync and async database access
- Collections: `langgraph_checkpoints`, `langgraph_writes`
- Full serialization/deserialization support

### 3. Workflow Nodes (`nodes.py`)
**Agent Nodes:**
- `get_preferences_node` - Calls PreferenceAgent
- `process_prompt_node` - Calls CustomPromptAgent
- `research_node` - Calls ResearchAgent
- `generate_content_node` - Calls WritingAgent
- `create_subjects_node` - Generates subject lines
- `format_email_node` - Formats for email delivery
- `store_newsletter_node` - Persists to MongoDB
- `send_email_node` - Triggers email delivery

**Checkpoint Nodes (using `interrupt()`):**
- `checkpoint_articles_node` - Review article selection
- `checkpoint_content_node` - Review newsletter content
- `checkpoint_subjects_node` - Select subject line
- `checkpoint_send_node` - Final send approval

### 4. Graph Definition (`graph.py`)
```python
graph = StateGraph(NewsletterState)
graph.add_node("get_preferences", get_preferences_node)
graph.add_node("research", research_node)
graph.add_node("checkpoint_articles", checkpoint_articles_node)
# ... all nodes
graph.set_entry_point("get_preferences")
graph.add_conditional_edges("checkpoint_articles", route_after_article_checkpoint)
# ... all edges
return graph.compile(checkpointer=get_mongodb_saver())
```

### 5. Orchestrator Methods
- `run()` - Start workflow, returns workflow_id
- `get_workflow_status()` - Get current workflow state
- `get_pending_checkpoint()` - Get checkpoint awaiting approval
- `approve_checkpoint()` - Resume with human response
- `cancel_workflow()` - Cancel and cleanup
- `list_workflows()` - Query workflow history

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

## Tests Created
```
backend/app/platforms/newsletter/tests/phase9/
├── __init__.py
├── test_state.py           # 30 tests - State schema
├── test_graph.py           # 15 tests - Graph definition & routing
├── test_mongodb_saver.py   # 20 tests - Checkpointer
├── test_nodes.py           # 24 tests - Node implementations
└── test_orchestrator.py    # 30 tests - Full orchestrator
```

## Verification
- [x] Workflow pauses at each checkpoint (using `interrupt()`)
- [x] State persists across interrupts (MongoDBSaver)
- [x] Approve/Edit/Reject work correctly
- [x] Cancel terminates workflow
- [x] 119 tests passing
