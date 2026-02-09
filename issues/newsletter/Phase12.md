# Phase 12: Frontend - Types, API Client, Hooks

## Goal
Frontend infrastructure for newsletter platform

## Status
- [x] Completed

## Files Created
```
frontend/src/types/newsletter.ts     # Extended with all entity types (~400 lines)
frontend/src/api/newsletter.ts       # Complete API client (NEW, ~380 lines)
frontend/src/hooks/useNewsletter.ts  # Extended with all hooks (~740 lines)
frontend/src/hooks/useWorkflowSSE.ts # SSE streaming hook (NEW, ~200 lines)
frontend/src/store/newsletterStore.ts # Zustand store (NEW, ~300 lines)
```

## Implementation Details

### Types (newsletter.ts)
All entity types matching backend Phase 11 schemas:
- `Newsletter`, `NewsletterListResponse`, `NewsletterUpdateRequest`
- `WorkflowState`, `WorkflowListItem`, `Checkpoint`, `ApproveCheckpointRequest`
- `Campaign`, `CampaignAnalytics`, `CreateCampaignRequest`
- `Subscriber`, `SubscriberPreferences`, `SubscriberEngagement`
- `Template`, `TemplateVariable`, `TemplatePreviewResponse`
- `DashboardMetrics`, `EngagementMetrics`, `SubscriberAnalyticsData`
- SSE event types: `SSEStatusEvent`, `SSECheckpointEvent`, `SSECompleteEvent`
- Status enums: `NewsletterEntityStatus`, `CampaignStatus`, `SubscriberStatus`, `WorkflowStepStatus`

### API Client (newsletter.ts)
Complete coverage of Phase 11 endpoints:
- Platform: `getStatus`, `getAgents`
- Research: `research`, `researchCustom`, `getTrending`
- Writing: `generateContent`
- Newsletters: `listNewsletters`, `getNewsletter`, `updateNewsletter`, `deleteNewsletter`
- Workflows: `generateNewsletter`, `listWorkflows`, `getWorkflow`, `getCheckpoint`, `approveCheckpoint`, `editCheckpoint`, `rejectCheckpoint`, `cancelWorkflow`, `getWorkflowHistory`, `getWorkflowStreamUrl`
- Campaigns: full CRUD + `sendCampaign`, `scheduleCampaign`
- Subscribers: full CRUD + `importSubscribers`, `importSubscribersCSV`, `unsubscribe`, `resubscribe`
- Templates: full CRUD + `duplicateTemplate`, `setDefaultTemplate`, `previewTemplate`
- Analytics: `getDashboard`, `getCampaignAnalytics`, `getEngagementMetrics`, `getSubscriberAnalytics`, `exportAnalytics`

### Hooks (useNewsletter.ts)
React Query hooks with query keys factory:
- Query keys for cache management (`newsletterKeys`)
- Platform hooks: `useNewsletterStatus`, `useNewsletterAgents`
- Research: `useResearch`, `useResearchCustom`, `useTrending`
- Writing: `useGenerateContent`
- Newsletter CRUD: `useNewsletters`, `useNewsletter`, `useUpdateNewsletter`, `useDeleteNewsletter`
- Workflow: `useGenerateWorkflow`, `useWorkflows`, `useWorkflow` (with auto-polling), `useWorkflowCheckpoint`, `useWorkflowHistory`, `useApproveCheckpoint`, `useEditCheckpoint`, `useRejectCheckpoint`, `useCancelWorkflow`
- Campaign hooks: full CRUD + send/schedule
- Subscriber hooks: full CRUD + import/unsubscribe
- Template hooks: full CRUD + duplicate/preview
- Analytics hooks: dashboard, campaign, engagement, subscriber, export

### SSE Hook (useWorkflowSSE.ts)
Real-time workflow streaming:
- EventSource connection management
- Auto-reconnection on connection loss
- Callbacks for status, checkpoint, complete, error events
- React Query cache updates on events
- `useWorkflowWithSSE` utility for combined polling + SSE

### Zustand Store (newsletterStore.ts)
Client state management:
- Workflow state: `activeWorkflowId`, `workflowStatus`, `checkpointData`
- Article selection: `selectedArticles` with reorder support
- Form drafts: `researchTopics`, `selectedTone`, `customPrompt`, `maxArticles`
- UI preferences: `showPreview`, `previewFormat`, `listViewMode`, `sidebarExpanded`
- Persistence: Only UI preferences and form drafts persisted to localStorage
- Selectors for performance optimization
- Utility hooks: `useArticleSelection`, `useWorkflowState`, `useFormDraft`

## Dependencies
- Phase 11 (Backend API) - Required
- @tanstack/react-query - Already in codebase
- zustand - Already in codebase
- axios (via client.ts) - Already in codebase

## Verification
- [x] All types match backend schemas
- [x] TypeScript compiles without errors
- [x] API client methods cover all Phase 11 endpoints
- [x] Hooks follow existing codebase patterns
- [x] SSE hook handles connection lifecycle correctly
- [x] Store provides complete client state management
