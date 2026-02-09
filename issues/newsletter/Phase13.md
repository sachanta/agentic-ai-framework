# Phase 13: Frontend - Pages & Components

## Goal
Newsletter platform UI with HITL approval workflow

## Status
- [x] Completed

## Files Created

### Pages
```
frontend/src/pages/apps/NewsletterPage.tsx     # Main entry (existing)
frontend/src/pages/newsletter/
├── CampaignsPage.tsx                          # Campaign list & management
├── CampaignDetailPage.tsx                     # Single campaign view
├── SubscribersPage.tsx                        # Subscriber management
├── TemplatesPage.tsx                          # Template gallery
├── AnalyticsPage.tsx                          # Performance metrics
├── WorkflowPage.tsx                           # Active workflow management
└── index.ts                                   # Exports
```

### Components
```
frontend/src/components/apps/newsletter/
├── NewsletterApp.tsx           # Main app with dashboard, generate, manual modes
├── NewsletterDashboard.tsx     # Overview with stats, active workflows, recent newsletters
├── GeneratePanel.tsx           # Newsletter generation form with topics, tone, RAG
├── ResearchPanel.tsx           # Manual research form (existing)
├── ArticleResults.tsx          # Article list display (existing)
├── WritingPanel.tsx            # Manual writing panel (existing)
├── NewsletterPreview.tsx       # Newsletter preview (existing)
│
│   # HITL Workflow Components
├── workflow/
│   ├── WorkflowTracker.tsx     # Visual step progress with icons
│   ├── CheckpointPanel.tsx     # Generic checkpoint container
│   ├── ArticleReview.tsx       # Checkpoint 1: Article selection with drag-reorder
│   ├── ContentReview.tsx       # Checkpoint 2: Side-by-side editor/preview
│   ├── SubjectReview.tsx       # Checkpoint 3: Radio cards for subject lines
│   ├── FinalApproval.tsx       # Checkpoint 4: Full preview, schedule option
│   ├── WorkflowHistory.tsx     # Timeline of execution steps
│   ├── ApprovalActions.tsx     # Approve/Edit/Reject buttons
│   └── index.ts                # Exports
```

### UI Components Added
```
frontend/src/components/ui/
├── slider.tsx                  # Range slider for max articles
└── use-toast.ts                # Toast hook compatible with notification store
```

### Routes Updated
```
frontend/src/App.tsx            # Added newsletter sub-routes
frontend/src/utils/constants.ts # Added route constants
```

## HITL Workflow UI

### Workflow Tracker
```
●────────●────────◉────────○────────○
Research  Review   Generate  Content  Final
✓         ✓        ⏳        ...      ...
```

### Checkpoint Panel Features
- Header with title, description, step indicator
- Content area for checkpoint-specific UI
- Footer with approval actions and optional feedback
- Loading states for all actions

## Checkpoint-Specific UI

| Checkpoint | Component | Features |
|------------|-----------|----------|
| Article Review | `ArticleReview.tsx` | Checkbox selection, score badges, expand/collapse details |
| Content Review | `ContentReview.tsx` | Format tabs (HTML/Text/Markdown), word count, edit mode |
| Subject Review | `SubjectReview.tsx` | Radio cards, style badges, custom input option |
| Final Approval | `FinalApproval.tsx` | Stats summary, preview, schedule picker |

## Real-time Updates
- SSE connection via `useWorkflowSSE` hook
- Toast notifications for checkpoint arrival
- React Query cache updates on approval/rejection
- Auto-reconnection on connection loss

## Pages Overview

| Page | Route | Features |
|------|-------|----------|
| CampaignsPage | `/apps/newsletter/campaigns` | List, filter, search campaigns |
| CampaignDetailPage | `/apps/newsletter/campaigns/:id` | Stats, preview, activity log |
| SubscribersPage | `/apps/newsletter/subscribers` | List, add, import, bulk actions |
| TemplatesPage | `/apps/newsletter/templates` | Template grid, category filter |
| AnalyticsPage | `/apps/newsletter/analytics` | Metrics cards, engagement charts |
| WorkflowPage | `/apps/newsletter/workflow/:id` | Full workflow management |

## Dependencies
- Phase 12 (Types, API, Hooks) ✅
- React, TypeScript
- Tailwind CSS, shadcn/ui components
- React Query for server state
- Zustand for client state
- date-fns for date formatting

## Verification
- [x] All pages render correctly (TypeScript compiles)
- [x] HITL workflow UI components complete
- [x] Real-time updates via SSE hook
- [x] Responsive design with grid layouts
- [ ] Integration tests (deferred to Phase 14)

## Notes
- Some components from spec (CampaignForm, TemplateEditor, etc.) are implicitly included in the page components
- Analytics charts use placeholder content (real charts can be added with recharts/visx)
- The main NewsletterApp integrates all views: Dashboard, Generate, Manual Mode, and Workflow
