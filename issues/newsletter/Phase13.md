# Phase 13: Frontend - Pages & Components

## Goal
Newsletter platform UI with HITL approval workflow

## Status
- [ ] Not Started

## Files to Create

### Pages
```
frontend/src/pages/apps/NewsletterPage.tsx
frontend/src/pages/newsletter/
├── CampaignsPage.tsx
├── CampaignDetailPage.tsx
├── SubscribersPage.tsx
├── TemplatesPage.tsx
├── AnalyticsPage.tsx
└── WorkflowPage.tsx            # Active workflow management
```

### Components
```
frontend/src/components/apps/newsletter/
├── NewsletterApp.tsx           # Main app component
├── NewsletterDashboard.tsx     # Overview dashboard
├── CampaignForm.tsx            # Create/edit campaign
├── CampaignList.tsx            # Campaign listing
├── CampaignCard.tsx            # Campaign card
├── SubscriberManager.tsx       # Subscriber management
├── SubscriberImport.tsx        # Bulk import
├── TemplateEditor.tsx          # Template editing
├── TemplatePreview.tsx         # Template preview
├── NewsletterPreview.tsx       # Newsletter preview
├── GeneratePanel.tsx           # Newsletter generation
├── CustomPromptInput.tsx       # Custom prompt UI
├── AnalyticsCharts.tsx         # Analytics visualization
├── SchedulePanel.tsx           # Scheduling UI
├── PreferencesForm.tsx         # User preferences
│
│   # HITL Workflow Components
├── workflow/
│   ├── WorkflowTracker.tsx     # Visual progress tracker
│   ├── CheckpointPanel.tsx     # Checkpoint approval panel
│   ├── ArticleReview.tsx       # Checkpoint 1: Article selection
│   ├── ContentReview.tsx       # Checkpoint 2: Newsletter content
│   ├── SubjectReview.tsx       # Checkpoint 3: Subject lines
│   ├── FinalApproval.tsx       # Checkpoint 4: Send approval
│   ├── WorkflowHistory.tsx     # Execution history
│   └── ApprovalActions.tsx     # Approve/Edit/Reject buttons
```

## HITL Workflow UI

### Workflow Tracker
```
●────────●────────◉────────○────────○
Prefs    Research  Review   Write    Send
✓        ✓         ⏳       ...      ...
```

### Checkpoint Panel Example
```
┌──────────────────────────────────────────┐
│         CHECKPOINT: Article Review        │
│                                          │
│  Selected 8 articles from 3 topics:       │
│                                          │
│  ☑ AI Breakthrough in Healthcare          │
│    Source: TechCrunch | Score: 0.92       │
│    [Preview] [Remove]                     │
│                                          │
│  ☑ New Climate Tech Funding               │
│    Source: Reuters | Score: 0.88          │
│    [Preview] [Remove]                     │
│                                          │
│  [+ Add Article]  [Reorder]  [Re-search] │
│                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ Approve  │ │   Edit   │ │  Reject  │ │
│  └──────────┘ └──────────┘ └──────────┘ │
└──────────────────────────────────────────┘
```

## Checkpoint-Specific UI

| Checkpoint | Component | Features |
|------------|-----------|----------|
| Article Review | `ArticleReview.tsx` | Drag-to-reorder, remove, add URL, scores |
| Content Review | `ContentReview.tsx` | Rich text editor, side-by-side preview |
| Subject Review | `SubjectReview.tsx` | 5 options as radio cards, custom input |
| Final Approval | `FinalApproval.tsx` | Full preview, recipient count, schedule picker |

## Real-time Updates
- SSE connection for workflow progress
- Toast notifications for checkpoint arrival
- Auto-refresh on approval/rejection

## Dependencies
- Phase 12 (Types, API, Hooks)
- React, TypeScript
- Tailwind CSS (styling)

## Verification
- [ ] All pages render correctly
- [ ] HITL workflow UI functions
- [ ] Real-time updates work
- [ ] Responsive design
- [ ] Tests passing
