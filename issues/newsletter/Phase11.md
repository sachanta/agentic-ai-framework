# Phase 11: API Endpoints (Backend)

## Goal
Complete REST API for newsletter platform with HITL workflow support

## Status
- [x] Completed

## Files Created/Modified
```
backend/app/platforms/newsletter/routers/
├── __init__.py              # Router exports (updated)
├── newsletters.py           # Newsletter CRUD (new)
├── workflows.py             # HITL workflow endpoints (new)
├── campaigns.py             # Campaign management (new)
├── subscribers.py           # Subscriber management (new)
├── templates.py             # Template management (new)
├── analytics.py             # Analytics endpoints (new)
├── research.py              # Phase 6 - unchanged
├── writing.py               # Phase 7 - unchanged
└── preference.py            # Phase 8 - unchanged

backend/app/platforms/newsletter/router.py  # Updated to include all routers

backend/app/platforms/newsletter/tests/phase11/
├── __init__.py
└── test_api_endpoints.py    # 41 tests
```

## Endpoints Implemented

### Newsletter Management (/newsletters)
```
GET    /newsletters                    # List user's newsletters (paginated)
GET    /newsletters/{id}               # Get specific newsletter
PATCH  /newsletters/{id}               # Update newsletter
DELETE /newsletters/{id}               # Delete newsletter
```

### HITL Workflow Management (/workflows)
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

### Campaign Management (/campaigns)
```
POST   /campaigns                      # Create campaign
GET    /campaigns                      # List campaigns
GET    /campaigns/{id}                 # Get campaign
PUT    /campaigns/{id}                 # Update campaign
DELETE /campaigns/{id}                 # Delete campaign
POST   /campaigns/{id}/send            # Send now
POST   /campaigns/{id}/schedule        # Schedule send
```

### Subscriber Management (/subscribers)
```
POST   /subscribers                    # Add subscriber
GET    /subscribers                    # List subscribers
GET    /subscribers/{id}               # Get subscriber
PUT    /subscribers/{id}               # Update subscriber
DELETE /subscribers/{id}               # Remove subscriber
POST   /subscribers/import             # Bulk JSON import
POST   /subscribers/import/csv         # Bulk CSV import
POST   /subscribers/{id}/unsubscribe   # Unsubscribe
POST   /subscribers/{id}/resubscribe   # Resubscribe
```

### Template Management (/templates)
```
POST   /templates                      # Create template
GET    /templates                      # List templates
GET    /templates/{id}                 # Get template
PUT    /templates/{id}                 # Update template
DELETE /templates/{id}                 # Delete template
POST   /templates/{id}/duplicate       # Duplicate template
POST   /templates/{id}/set-default     # Set as default
POST   /templates/{id}/preview         # Preview with variables
```

### Analytics (/analytics)
```
GET    /analytics/dashboard            # Dashboard metrics
GET    /analytics/campaigns/{id}       # Campaign analytics
GET    /analytics/engagement           # Engagement metrics
GET    /analytics/subscribers          # Subscriber analytics
GET    /analytics/export               # Export analytics data
```

## Key Features

### Authentication
- All endpoints require authentication via `get_current_user` dependency
- User ownership validated for all resources

### Pagination
- List endpoints support `skip` and `limit` query parameters
- Total counts included in responses

### Filtering
- Status filtering on newsletters, campaigns, subscribers
- Tag/group filtering on subscribers
- Category filtering on templates

### Real-time Updates
- SSE endpoint for workflow progress streaming
- Polling support for checkpoint status

### Bulk Operations
- JSON bulk import for subscribers
- CSV file upload for subscriber import
- Batch email sending in campaigns

### Error Handling
- Consistent 404 for not found resources
- 403 for unauthorized access
- 400 for invalid operations (e.g., delete sent newsletter)
- 409 for conflicts (e.g., duplicate subscriber email)

## Response Schemas

All endpoints return Pydantic-validated responses with:
- Consistent field naming
- Proper datetime serialization
- Nested analytics/preferences objects
- Optional fields clearly marked

## Dependencies
- Phase 2: Repositories (Newsletter, Subscriber, Campaign, Template)
- Phase 9: Orchestrator for workflow management
- Phase 10: Email service for campaign sending

## Tests Created
```
tests/phase11/test_api_endpoints.py:
- TestRouterImports (6 tests)
- TestNewslettersSchemas (3 tests)
- TestWorkflowsSchemas (3 tests)
- TestCampaignsSchemas (3 tests)
- TestSubscribersSchemas (3 tests)
- TestTemplatesSchemas (3 tests)
- TestAnalyticsSchemas (3 tests)
- TestNewslettersEndpoints (3 tests)
- TestCampaignsEndpoints (2 tests)
- TestSubscribersEndpoints (3 tests)
- TestTemplatesEndpoints (2 tests)
- TestAnalyticsEndpoints (2 tests)
- TestMainRouterIntegration (2 tests)
- TestEndpointAuthentication (3 tests)

Total: 41 tests
```

## Verification
- [x] All endpoints respond correctly
- [x] Authentication works
- [x] HITL workflow endpoints function
- [x] SSE streaming works
- [x] Tests passing (745 passed, 15 skipped)
