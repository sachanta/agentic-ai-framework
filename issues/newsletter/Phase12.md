# Phase 12: API Endpoints (Backend)

## Goal
Complete REST API for newsletter platform with HITL workflow support

## Status
- [ ] Not Started

## Files to Modify/Create
```
backend/app/platforms/newsletter/router.py
backend/app/platforms/newsletter/routers/
├── __init__.py
├── newsletters.py       # Newsletter CRUD
├── workflows.py         # HITL workflow endpoints
├── campaigns.py         # Campaign management
├── subscribers.py       # Subscriber management
├── templates.py         # Template management
├── preferences.py       # User preferences
└── analytics.py         # Analytics endpoints
```

## Endpoints

### Newsletter Generation & HITL Workflow
```
POST   /newsletters/generate           # Start generation, returns workflow_id
POST   /newsletters/generate-custom    # Start with custom prompt
GET    /newsletters                    # List user's newsletters
GET    /newsletters/{id}               # Get specific newsletter
DELETE /newsletters/{id}               # Delete newsletter
```

### HITL Workflow Management
```
GET    /workflows                      # List active workflows
GET    /workflows/{workflow_id}        # Get workflow status
GET    /workflows/{workflow_id}/checkpoint  # Get pending checkpoint
POST   /workflows/{workflow_id}/approve     # Approve checkpoint
POST   /workflows/{workflow_id}/edit        # Edit and continue
POST   /workflows/{workflow_id}/reject      # Reject and re-run
POST   /workflows/{workflow_id}/cancel      # Cancel workflow
GET    /workflows/{workflow_id}/history     # Execution history
GET    /workflows/{workflow_id}/stream      # SSE for progress
```

### Campaigns
```
POST   /campaigns                      # Create campaign
GET    /campaigns                      # List campaigns
GET    /campaigns/{id}                 # Get campaign
PUT    /campaigns/{id}                 # Update campaign
DELETE /campaigns/{id}                 # Delete campaign
POST   /campaigns/{id}/send            # Send now
POST   /campaigns/{id}/schedule        # Schedule send
```

### Subscribers
```
POST   /subscribers                    # Add subscriber
GET    /subscribers                    # List subscribers
GET    /subscribers/{id}               # Get subscriber
PUT    /subscribers/{id}               # Update subscriber
DELETE /subscribers/{id}               # Remove subscriber
POST   /subscribers/import             # Bulk import
```

### Preferences
```
GET    /preferences                    # Get user preferences
PUT    /preferences                    # Update preferences
POST   /preferences/analyze            # Analyze patterns
GET    /preferences/recommendations    # Get suggestions
```

### Templates
```
POST   /templates                      # Create template
GET    /templates                      # List templates
GET    /templates/{id}                 # Get template
PUT    /templates/{id}                 # Update template
DELETE /templates/{id}                 # Delete template
```

### Analytics
```
GET    /analytics/dashboard            # Dashboard metrics
GET    /analytics/campaigns/{id}       # Campaign analytics
GET    /analytics/engagement           # Engagement metrics
```

## Response Schemas
```python
class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    status: str  # running, awaiting_approval, completed, cancelled, failed
    current_checkpoint: Optional[str]
    checkpoint_data: Optional[dict]
    created_at: datetime
    updated_at: datetime

class CheckpointResponse(BaseModel):
    checkpoint_id: str
    checkpoint_type: str
    title: str
    description: str
    data: dict
    actions: List[str]
    metadata: dict
```

## Dependencies
- All previous phases (1-11)
- FastAPI (already configured)

## Verification
- [ ] All endpoints respond correctly
- [ ] Authentication works
- [ ] HITL workflow endpoints function
- [ ] SSE streaming works
- [ ] Tests passing
