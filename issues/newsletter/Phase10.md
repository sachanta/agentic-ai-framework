# Phase 10: Newsletter Orchestrator with LangGraph HITL

## Goal
Multi-agent workflow coordination with Human-in-the-Loop checkpoints

## Status
- [ ] Not Started

## Files to Create/Modify
```
backend/app/platforms/newsletter/orchestrator/
├── __init__.py
├── orchestrator.py      # LangGraph-based orchestrator
├── graph.py             # LangGraph workflow definition
├── checkpoints.py       # HITL checkpoint handlers
└── state.py             # Workflow state schema
```

## Why LangGraph
- Native `interrupt()` function for HITL checkpoints
- State persistence across interrupts (MongoDB checkpointer)
- Built-in approve/edit/reject workflow
- Already in dependencies (`langgraph>=0.0.20`)

## Workflow with HITL Checkpoints
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

## Orchestrator Methods
- `start_newsletter_generation()` - Start workflow, returns workflow_id
- `get_pending_checkpoint()` - Get current checkpoint awaiting approval
- `approve_checkpoint()` - Approve and continue
- `edit_checkpoint()` - Modify data and continue
- `reject_checkpoint()` - Reject and re-run previous step
- `cancel_workflow()` - Cancel entire workflow
- `get_workflow_status()` - Get current state and history

## Dependencies
- Phases 6-9 (All agents)
- Phase 4 (RAG for storage)
- Phase 5 (Memory for state)
- LangGraph (already in deps)

## Verification
- [ ] Workflow pauses at each checkpoint
- [ ] State persists across interrupts
- [ ] Approve/Edit/Reject work correctly
- [ ] Cancel terminates workflow
- [ ] Tests passing
