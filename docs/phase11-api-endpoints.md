# Phase 11: Complete REST API Endpoints

## Status: Completed

## Overview

Phase 11 implements a complete REST API for the newsletter platform. This includes endpoints for newsletter management, HITL workflow control, campaign operations, subscriber management, template handling, and analytics. All endpoints are secured with authentication and include proper error handling.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           NEWSLETTER API LAYER                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         Main Router (router.py)                       │   │
│  │                                                                       │   │
│  │  Platform Endpoints:                                                  │   │
│  │  GET  /status    GET  /config    GET  /health    GET  /agents        │   │
│  │  POST /generate (legacy)                                              │   │
│  │                                                                       │   │
│  └───────────────────────────────┬───────────────────────────────────────┘   │
│                                  │                                           │
│                                  ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         Sub-Routers                                   │   │
│  │                                                                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │ /research   │  │ /writing    │  │ /preferences│  │ /newsletters│  │   │
│  │  │ (Phase 6)   │  │ (Phase 7)   │  │ (Phase 8)   │  │ (Phase 11)  │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  │                                                                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │ /workflows  │  │ /campaigns  │  │ /subscribers│  │ /templates  │  │   │
│  │  │ (Phase 11)  │  │ (Phase 11)  │  │ (Phase 11)  │  │ (Phase 11)  │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  │                                                                       │   │
│  │  ┌─────────────┐                                                      │   │
│  │  │ /analytics  │                                                      │   │
│  │  │ (Phase 11)  │                                                      │   │
│  │  └─────────────┘                                                      │   │
│  │                                                                       │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│                                  │                                           │
│                                  ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         Backend Services                              │   │
│  │                                                                       │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐      │   │
│  │  │ Newsletter │  │ Subscriber │  │ Campaign   │  │ Template   │      │   │
│  │  │ Repository │  │ Repository │  │ Repository │  │ Repository │      │   │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘      │   │
│  │                                                                       │   │
│  │  ┌────────────┐  ┌────────────┐                                      │   │
│  │  │ Newsletter │  │ Email      │                                      │   │
│  │  │Orchestrator│  │ Service    │                                      │   │
│  │  └────────────┘  └────────────┘                                      │   │
│  │                                                                       │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Files Created

```
backend/app/platforms/newsletter/routers/
├── __init__.py              # Updated with new router exports
├── newsletters.py           # Newsletter CRUD endpoints
├── workflows.py             # HITL workflow management
├── campaigns.py             # Campaign CRUD and sending
├── subscribers.py           # Subscriber CRUD and import
├── templates.py             # Template CRUD and preview
└── analytics.py             # Analytics and reporting

backend/app/platforms/newsletter/tests/phase11/
├── __init__.py
└── test_api_endpoints.py    # 41 tests
```

---

## Endpoint Reference

### Newsletter Management (`/newsletters`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/newsletters` | List user's newsletters (paginated) |
| GET | `/newsletters/{id}` | Get specific newsletter |
| PATCH | `/newsletters/{id}` | Update newsletter |
| DELETE | `/newsletters/{id}` | Delete newsletter |

#### List Newsletters
```python
GET /newsletters?status=draft&skip=0&limit=20

Response:
{
    "items": [
        {
            "id": "nl-123",
            "title": "Weekly AI Digest",
            "status": "draft",
            "topics_covered": ["AI", "ML"],
            "tone_used": "professional",
            "word_count": 1500,
            "created_at": "2024-01-15T10:00:00Z",
            "sent_at": null
        }
    ],
    "total": 15,
    "skip": 0,
    "limit": 20
}
```

#### Get Newsletter Detail
```python
GET /newsletters/{newsletter_id}

Response:
{
    "id": "nl-123",
    "user_id": "user-456",
    "title": "Weekly AI Digest",
    "content": "# Newsletter Content...",
    "html_content": "<html>...</html>",
    "plain_text": "Newsletter Content...",
    "subject_line": "This Week in AI",
    "subject_line_options": ["Option 1", "Option 2"],
    "status": "ready",
    "workflow_id": "wf-789",
    "topics_covered": ["AI", "ML"],
    "tone_used": "professional",
    "word_count": 1500,
    "read_time_minutes": 6,
    "research_data": {...},
    "writing_data": {...},
    "created_at": "2024-01-15T10:00:00Z"
}
```

---

### Workflow Management (`/workflows`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/workflows` | List active workflows |
| GET | `/workflows/{id}` | Get workflow status |
| GET | `/workflows/{id}/checkpoint` | Get pending checkpoint |
| POST | `/workflows/{id}/approve` | Approve/edit/reject checkpoint |
| POST | `/workflows/{id}/edit` | Edit and continue |
| POST | `/workflows/{id}/reject` | Reject and re-run |
| POST | `/workflows/{id}/cancel` | Cancel workflow |
| GET | `/workflows/{id}/history` | Get execution history |
| GET | `/workflows/{id}/stream` | SSE progress stream |

#### Approve Checkpoint
```python
POST /workflows/{workflow_id}/approve
{
    "checkpoint_id": "ckpt-123",
    "action": "approve",  # or "edit", "reject"
    "modifications": null,
    "feedback": null
}

Response:
{
    "workflow_id": "wf-789",
    "status": "running",
    "next_step": "generate_content"
}
```

#### SSE Workflow Stream
```python
GET /workflows/{workflow_id}/stream

# Server-Sent Events:
event: status
data: {"workflow_id": "wf-789", "status": "running", "current_step": "research"}

event: checkpoint
data: {"checkpoint_id": "ckpt-123", "type": "article_review", ...}

event: complete
data: {"status": "completed"}
```

---

### Campaign Management (`/campaigns`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/campaigns` | Create campaign |
| GET | `/campaigns` | List campaigns |
| GET | `/campaigns/{id}` | Get campaign |
| PUT | `/campaigns/{id}` | Update campaign |
| DELETE | `/campaigns/{id}` | Delete campaign |
| POST | `/campaigns/{id}/send` | Send immediately |
| POST | `/campaigns/{id}/schedule` | Schedule for later |

#### Create Campaign
```python
POST /campaigns
{
    "name": "January Newsletter",
    "subject": "Your Weekly AI Update",
    "description": "First newsletter of the year",
    "newsletter_id": "nl-123",
    "subscriber_tags": ["premium"],
    "exclude_tags": ["unengaged"],
    "from_email": "newsletter@example.com",
    "from_name": "AI Weekly"
}

Response:
{
    "id": "camp-456",
    "status": "draft",
    "analytics": {
        "recipient_count": 0,
        "delivered_count": 0,
        ...
    }
}
```

#### Send Campaign
```python
POST /campaigns/{campaign_id}/send

Response:
{
    "success": true,
    "campaign_id": "camp-456",
    "recipient_count": 1000,
    "sent_count": 985,
    "failed_count": 15,
    "message": "Campaign sent to 985 subscribers"
}
```

---

### Subscriber Management (`/subscribers`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/subscribers` | Add subscriber |
| GET | `/subscribers` | List subscribers |
| GET | `/subscribers/{id}` | Get subscriber |
| PUT | `/subscribers/{id}` | Update subscriber |
| DELETE | `/subscribers/{id}` | Delete subscriber |
| POST | `/subscribers/import` | Bulk JSON import |
| POST | `/subscribers/import/csv` | Bulk CSV import |
| POST | `/subscribers/{id}/unsubscribe` | Unsubscribe |
| POST | `/subscribers/{id}/resubscribe` | Resubscribe |

#### Create Subscriber
```python
POST /subscribers
{
    "email": "user@example.com",
    "name": "John Doe",
    "preferences": {
        "topics": ["AI", "ML"],
        "tone": "casual",
        "frequency": "weekly"
    },
    "tags": ["premium"],
    "send_welcome": true
}

Response:
{
    "id": "sub-789",
    "email": "user@example.com",
    "status": "subscribed",
    "preferences": {...},
    "engagement": {
        "emails_received": 0,
        "open_rate": 0.0,
        ...
    }
}
```

#### Bulk Import (JSON)
```python
POST /subscribers/import
{
    "subscribers": [
        {"email": "a@example.com", "name": "Alice"},
        {"email": "b@example.com", "name": "Bob"}
    ],
    "send_welcome": false
}

Response:
{
    "success": true,
    "created": 2,
    "skipped": 0,
    "errors": []
}
```

#### CSV Import
```python
POST /subscribers/import/csv
Content-Type: multipart/form-data
file: subscribers.csv

# CSV format:
# email,name
# alice@example.com,Alice
# bob@example.com,Bob

Response:
{
    "success": true,
    "created": 50,
    "skipped": 5,
    "errors": ["Row 3: invalid email"]
}
```

---

### Template Management (`/templates`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/templates` | Create template |
| GET | `/templates` | List templates |
| GET | `/templates/{id}` | Get template |
| PUT | `/templates/{id}` | Update template |
| DELETE | `/templates/{id}` | Delete template |
| POST | `/templates/{id}/duplicate` | Duplicate template |
| POST | `/templates/{id}/set-default` | Set as default |
| POST | `/templates/{id}/preview` | Preview with variables |

#### Create Template
```python
POST /templates
{
    "name": "Standard Newsletter",
    "category": "newsletter",
    "html_content": "<html>{{content}}</html>",
    "plain_text_content": "{{content}}",
    "subject_template": "{{title}} - Weekly Update",
    "variables": [
        {
            "name": "content",
            "description": "Main content",
            "required": true
        },
        {
            "name": "title",
            "description": "Newsletter title",
            "default_value": "Newsletter"
        }
    ]
}
```

#### Preview Template
```python
POST /templates/{template_id}/preview
{
    "variables": {
        "content": "Hello World",
        "title": "January Update"
    }
}

Response:
{
    "html": "<html>Hello World</html>",
    "plain_text": "Hello World",
    "subject": "January Update - Weekly Update"
}
```

---

### Analytics (`/analytics`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/dashboard` | Overall metrics |
| GET | `/analytics/campaigns/{id}` | Campaign analytics |
| GET | `/analytics/engagement` | Engagement metrics |
| GET | `/analytics/subscribers` | Subscriber analytics |
| GET | `/analytics/export` | Export data |

#### Dashboard Metrics
```python
GET /analytics/dashboard

Response:
{
    "total_newsletters": 25,
    "total_campaigns": 12,
    "total_subscribers": 5000,
    "active_subscribers": 4500,
    "newsletters_created": 4,
    "campaigns_sent": 2,
    "new_subscribers": 150,
    "unsubscribes": 10,
    "average_open_rate": 0.42,
    "average_click_rate": 0.12,
    "total_emails_sent": 10000
}
```

#### Engagement Analytics
```python
GET /analytics/engagement?period=30d

Response:
{
    "summary": {
        "period": "30d",
        "total_sent": 5000,
        "total_delivered": 4900,
        "total_opens": 2100,
        "total_clicks": 600,
        "average_open_rate": 0.428,
        "average_click_rate": 0.122
    },
    "top_by_opens": [
        {
            "campaign_id": "camp-123",
            "campaign_name": "AI Weekly",
            "metric_value": 0.55,
            "sent_at": "2024-01-10T10:00:00Z"
        }
    ],
    "top_by_clicks": [...]
}
```

---

## Authentication

All endpoints require authentication via the `get_current_user` dependency:

```python
from app.core.security import get_current_user

@router.get("/newsletters")
async def list_newsletters(
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["id"]
    # ... filter by user_id
```

---

## Error Handling

| Status Code | Condition |
|-------------|-----------|
| 400 | Invalid operation (e.g., delete sent newsletter) |
| 401 | Missing authentication |
| 403 | Not authorized (wrong user) |
| 404 | Resource not found |
| 409 | Conflict (e.g., duplicate email) |
| 422 | Validation error |
| 500 | Internal server error |

Example error response:
```json
{
    "detail": "Newsletter not found"
}
```

---

## Fixes Applied During Implementation

### 1. Router Path Corrections

**Issue:** Phase 1 tests used incorrect paths after router restructuring.

**Before:**
```python
response = test_client.post(
    "/api/v1/platforms/newsletter/newsletters/generate",  # Wrong
    json={"topics": ["AI"]},
)
```

**After:**
```python
response = test_client.post(
    "/api/v1/platforms/newsletter/generate",  # Correct - legacy endpoint
    json={"topics": ["AI"]},
)
```

### 2. Mock Path Updates

**Issue:** Tests were mocking `router.NewsletterService` but workflow endpoints moved to sub-router.

**Before:**
```python
with patch("app.platforms.newsletter.router.NewsletterService") as MockService:
    mock_instance.get_workflow_status = AsyncMock(return_value=None)
```

**After:**
```python
with patch("app.platforms.newsletter.routers.workflows.get_newsletter_orchestrator") as MockOrch:
    mock_instance = MockOrch.return_value
    mock_instance.get_workflow_status = AsyncMock(return_value=None)
```

### 3. Missing Approve Endpoint

**Issue:** The `/workflows/{id}/approve` endpoint was removed during router refactoring but tests expected it.

**Fix:** Added `ApproveCheckpointRequest` schema and `/approve` endpoint to workflows router:

```python
class ApproveCheckpointRequest(BaseModel):
    checkpoint_id: str
    action: str = "approve"  # approve, edit, reject
    modifications: Optional[Dict[str, Any]] = None
    feedback: Optional[str] = None

@router.post("/{workflow_id}/approve")
async def approve_checkpoint(
    request: ApproveCheckpointRequest,
    workflow_id: str = Path(..., description="Workflow ID"),
    current_user: dict = Depends(get_current_user),
):
    ...
```

### 4. Query Parameter Defaults in Tests

**Issue:** Direct function calls didn't resolve FastAPI `Query()` defaults.

**Before:**
```python
result = await list_newsletters(current_user=MOCK_USER)  # Failed - Query defaults not resolved
```

**After:**
```python
result = await list_newsletters(
    status=None, skip=0, limit=20,  # Explicit values
    current_user=MOCK_USER
)
```

### 5. Stub Test Updates

**Issue:** Phase 1 stub tests expected `"not_implemented"` status but real implementation returns `"awaiting_approval"`.

**Before:**
```python
mock_instance.generate_newsletter = AsyncMock(return_value={
    "status": "not_implemented",  # Old stub response
})
```

**After:**
```python
mock_instance.generate_newsletter = AsyncMock(return_value={
    "status": "awaiting_approval",  # Real implementation response
})
```

---

## Tests

```
tests/phase11/test_api_endpoints.py

TestRouterImports              # 6 tests - Router imports work
TestNewslettersSchemas         # 3 tests - Newsletter schema validation
TestWorkflowsSchemas           # 3 tests - Workflow schema validation
TestCampaignsSchemas           # 3 tests - Campaign schema validation
TestSubscribersSchemas         # 3 tests - Subscriber schema validation
TestTemplatesSchemas           # 3 tests - Template schema validation
TestAnalyticsSchemas           # 3 tests - Analytics schema validation
TestNewslettersEndpoints       # 3 tests - Newsletter CRUD operations
TestCampaignsEndpoints         # 2 tests - Campaign operations
TestSubscribersEndpoints       # 3 tests - Subscriber operations
TestTemplatesEndpoints         # 2 tests - Template operations
TestAnalyticsEndpoints         # 2 tests - Analytics queries
TestMainRouterIntegration      # 2 tests - Router composition
TestEndpointAuthentication     # 3 tests - Auth requirements

Total: 41 tests
```

---

## Dependencies

- **Phase 2:** Repository classes (Newsletter, Subscriber, Campaign, Template)
- **Phase 9:** NewsletterOrchestrator for workflow management
- **Phase 10:** EmailService for campaign sending
- **FastAPI:** Router, Depends, HTTPException, Query, Path, UploadFile

---

## Usage Examples

### Full Newsletter Workflow via API

```python
import httpx

client = httpx.AsyncClient(
    base_url="http://localhost:8000/api/v1/platforms/newsletter",
    headers={"Authorization": f"Bearer {token}"}
)

# 1. Start newsletter generation
response = await client.post("/generate", json={
    "topics": ["AI", "Machine Learning"],
    "tone": "professional",
    "max_articles": 10
})
workflow_id = response.json()["workflow_id"]

# 2. Poll for checkpoint (or use SSE)
while True:
    checkpoint = await client.get(f"/workflows/{workflow_id}/checkpoint")
    if checkpoint.status_code == 200:
        break
    await asyncio.sleep(2)

# 3. Approve article selection
checkpoint_data = checkpoint.json()
await client.post(f"/workflows/{workflow_id}/approve", json={
    "checkpoint_id": checkpoint_data["checkpoint_id"],
    "action": "approve"
})

# 4. Continue through all checkpoints...

# 5. Get final newsletter
status = await client.get(f"/workflows/{workflow_id}")
newsletter_id = status.json()["newsletter_id"]
newsletter = await client.get(f"/newsletters/{newsletter_id}")

# 6. Create and send campaign
campaign = await client.post("/campaigns", json={
    "name": "Weekly Update",
    "subject": newsletter.json()["subject_line"],
    "newsletter_id": newsletter_id
})

await client.post(f"/campaigns/{campaign.json()['id']}/send")
```

---

## Verification Checklist

- [x] All endpoints respond correctly with proper status codes
- [x] Authentication required on all endpoints
- [x] User ownership validated for all resources
- [x] HITL workflow endpoints function correctly
- [x] SSE streaming works for real-time updates
- [x] Bulk operations (import, batch email) work
- [x] Pagination and filtering work on list endpoints
- [x] All 41 Phase 11 tests passing
- [x] All 745 total tests passing (15 skipped)
