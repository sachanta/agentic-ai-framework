# Phase 13: Frontend Pages & Components

## Overview

Phase 13 implements the complete Newsletter UI with HITL (Human-in-the-Loop) workflow support. This includes all pages for managing newsletters, campaigns, subscribers, and templates, plus the workflow components for the approval process.

## File Structure

```
frontend/src/
├── pages/newsletter/
│   ├── CampaignsPage.tsx        # Campaign list with search/filter
│   ├── CampaignDetailPage.tsx   # Single campaign view with stats
│   ├── SubscribersPage.tsx      # Subscriber management
│   ├── TemplatesPage.tsx        # Template gallery
│   ├── AnalyticsPage.tsx        # Performance metrics dashboard
│   ├── WorkflowPage.tsx         # Standalone workflow management
│   └── index.ts                 # Exports
│
├── components/apps/newsletter/
│   ├── NewsletterApp.tsx        # Main app with tabs (Dashboard/Generate/Manual)
│   ├── NewsletterDashboard.tsx  # Stats, active workflows, recent items
│   ├── GeneratePanel.tsx        # Workflow generation form
│   ├── ResearchPanel.tsx        # Manual research form
│   ├── ArticleResults.tsx       # Article list display
│   ├── WritingPanel.tsx         # Manual writing controls
│   ├── NewsletterPreview.tsx    # Newsletter preview
│   │
│   └── workflow/                # HITL Workflow Components
│       ├── WorkflowTracker.tsx  # Visual step progress
│       ├── CheckpointPanel.tsx  # Generic checkpoint container
│       ├── ArticleReview.tsx    # Checkpoint 1: Article selection
│       ├── ContentReview.tsx    # Checkpoint 2: Content editing
│       ├── SubjectReview.tsx    # Checkpoint 3: Subject line selection
│       ├── FinalApproval.tsx    # Checkpoint 4: Send approval
│       ├── WorkflowHistory.tsx  # Execution timeline
│       ├── ApprovalActions.tsx  # Approve/Edit/Reject buttons
│       └── index.ts             # Exports
│
└── components/ui/
    ├── slider.tsx               # Range slider component
    └── use-toast.ts             # Toast hook wrapper
```

## Routes

| Route | Component | Description |
|-------|-----------|-------------|
| `/apps/newsletter` | `NewsletterPage` | Main newsletter app |
| `/apps/newsletter/campaigns` | `CampaignsPage` | Campaign list |
| `/apps/newsletter/campaigns/:id` | `CampaignDetailPage` | Campaign detail |
| `/apps/newsletter/subscribers` | `SubscribersPage` | Subscriber management |
| `/apps/newsletter/templates` | `TemplatesPage` | Template gallery |
| `/apps/newsletter/analytics` | `AnalyticsPage` | Performance metrics |
| `/apps/newsletter/workflow/:id` | `WorkflowPage` | Workflow detail |

Route constants are defined in `frontend/src/utils/constants.ts`.

## HITL Workflow UI

### Visual Progress Tracker

The workflow UI guides users through the newsletter generation process with visual progress indication:

```
●────────●────────◉────────○────────○
Research  Review   Generate  Content  Final
   ✓        ✓        ⏳       ...      ...
```

### Workflow Steps

1. **Research** - AI discovers relevant articles using Tavily search
2. **Review Articles** - User selects and reorders articles (Checkpoint 1)
3. **Generate** - AI writes newsletter content using selected articles
4. **Review Content** - User edits and approves content (Checkpoint 2)
5. **Final Review** - User approves and optionally schedules (Checkpoint 3)

### Checkpoint Components

| Component | Checkpoint Type | Features |
|-----------|-----------------|----------|
| `ArticleReview` | `research_review` | Checkbox selection, relevance scores, expand/collapse details, article count |
| `ContentReview` | `content_review` | Format tabs (HTML/Text/Markdown), word count, reading time, inline editing |
| `SubjectReview` | `subject_review` | Radio card selection, style badges, custom subject input option |
| `FinalApproval` | `final_review` | Full preview, stats summary, schedule picker, recipient count |

## Component Details

### NewsletterApp

The main application component with four view modes:

```tsx
type AppView = 'dashboard' | 'generate' | 'manual' | 'workflow';
```

- **Dashboard**: Stats cards, active workflows, recent newsletters, quick actions
- **Generate**: Form to start new workflow with topics, tone, max articles
- **Manual Mode**: Step-by-step research and writing without workflow
- **Workflow**: Full-screen workflow management with checkpoints

### NewsletterDashboard

Overview dashboard showing:
- Quick stats (total newsletters, campaigns sent, active subscribers, open rate)
- Active workflows list with status and progress
- Recent newsletters with status badges
- Quick action buttons

### GeneratePanel

Form for initiating a new workflow:
- Topic input with tag-style chips
- Custom prompt toggle with textarea
- Writing tone selection (Professional, Casual, Formal, Enthusiastic)
- Max articles slider (3-20)
- RAG examples toggle

### WorkflowTracker

Visual step indicator component:
- Shows completed steps with checkmark
- Current step with spinning loader
- Pending steps with empty circle
- Error state with exclamation mark
- Compact version available for sidebars

### CheckpointPanel

Generic container for checkpoint UIs:
- Header with title, description, step indicator
- Scrollable content area
- Footer with approval actions
- Collapsible feedback textarea

### ApprovalActions

Standardized approval buttons:
- Approve (primary action)
- Edit (secondary, opens edit mode)
- Reject (destructive, requires feedback)
- Loading states per action
- Disabled states during mutations

## State Management

### Zustand Store

Client-side state in `store/newsletterStore.ts`:

```tsx
// Workflow state
const { activeWorkflowId, setActiveWorkflow, clearWorkflowState } = useWorkflowState();

// Article selection for ArticleReview
const { selectedArticles, setSelectedArticles, toggleArticle } = useArticleSelection();

// Form draft persistence
const { topics, tone, maxArticles, setSelectedTone } = useFormDraft();
```

### React Query Integration

Server state managed via hooks in `hooks/useNewsletter.ts`:

```tsx
// Queries
const { data: workflow } = useWorkflow(workflowId);
const { data: checkpoint } = useWorkflowCheckpoint(workflowId);
const { data: history } = useWorkflowHistory(workflowId);

// Mutations
const approveMutation = useApproveCheckpoint();
const rejectMutation = useRejectCheckpoint();
const cancelMutation = useCancelWorkflow();
```

### SSE Integration

Real-time updates via `hooks/useWorkflowSSE.ts`:

```tsx
useWorkflowSSE(workflowId, {
  onStatus: (event) => {
    // Update workflow status in store
    setWorkflowStatus(event.status);
  },
  onCheckpoint: (event) => {
    // Store checkpoint data and notify user
    setCheckpointData(event);
    toast({ title: 'Checkpoint Ready', description: event.title });
  },
  onComplete: (event) => {
    // Handle workflow completion
    toast({ title: 'Newsletter Complete!' });
    navigate('/apps/newsletter');
  },
  onError: (event) => {
    toast({ title: 'Error', description: event.error, variant: 'destructive' });
  },
});
```

## Pages Overview

### CampaignsPage

Campaign management with:
- Search by name or subject
- Filter by status (draft, scheduled, sending, sent, failed)
- Pagination (20 per page)
- Quick actions dropdown (edit, duplicate, delete)
- Status badges with icons

### CampaignDetailPage

Single campaign view with:
- Stats cards (sent, opened, clicked, bounced)
- Progress bars for open/click rates
- Campaign information panel
- Email preview tab
- Activity log tab

### SubscribersPage

Subscriber management with:
- Search by email or name
- Filter by status (active, unsubscribed, bounced)
- Multi-select with checkboxes
- Bulk delete action
- Add subscriber dialog
- Import CSV button (placeholder)
- Export button

### TemplatesPage

Template gallery with:
- Grid layout with preview thumbnails
- Search by name
- Category filter (newsletter, promotional, announcement, digest)
- Default template badge
- Quick actions (preview, edit, duplicate, set default, delete)

### AnalyticsPage

Metrics dashboard with:
- Key metrics cards (newsletters, campaigns, subscribers, rates)
- Time period selector (7d, 30d, 90d, year)
- Overview tab with campaign performance
- Engagement tab with trend charts
- Subscribers tab with growth data
- Chart placeholders (ready for recharts/visx integration)

### WorkflowPage

Standalone workflow management:
- Same functionality as workflow view in NewsletterApp
- Direct URL access via `/apps/newsletter/workflow/:id`
- SSE connection for real-time updates
- Full checkpoint UI rendering

## UI Patterns

### Loading States

```tsx
{isLoading ? (
  <Skeleton className="h-20 w-full" />
) : data ? (
  <DataDisplay data={data} />
) : (
  <EmptyState message="No data" />
)}
```

### Form Validation

```tsx
const canGenerate = topics.length > 0 || (useCustomPrompt && customPrompt.trim());
<Button disabled={!canGenerate || isLoading}>Start Generation</Button>
```

### Toast Notifications

```tsx
import { useToast } from '@/components/ui/use-toast';

const { toast } = useToast();
toast({
  title: 'Success',
  description: 'Newsletter generated',
  variant: 'default',  // or 'destructive' for errors
});
```

### Responsive Grid

```tsx
<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
  {/* Cards adapt to screen size */}
</div>
```

## Dependencies

### New Packages

```json
{
  "@radix-ui/react-slider": "^1.x.x"
}
```

### UI Components Used

- shadcn/ui: Card, Button, Badge, Tabs, Dialog, Select, Input, Textarea, etc.
- Radix UI primitives: Slider, Radio Group, Switch, Checkbox
- Lucide React: Icons throughout

## Testing

### Development Server

```bash
cd frontend
npm run dev
# Open http://localhost:5173/apps/newsletter
```

### TypeScript Check

```bash
cd frontend
npx tsc --noEmit
```

### Manual Testing Flow

1. Navigate to Newsletter app
2. Go to "Generate" tab
3. Enter topics (e.g., "AI", "Technology")
4. Select tone and max articles
5. Click "Start Generation"
6. Observe workflow progress tracker
7. Approve/reject at each checkpoint
8. Verify completion and navigation

## Common Issues

### SSE Connection

- Ensure backend is running with SSE endpoint
- Check CORS configuration for EventSource
- Auto-reconnection handles temporary disconnections

### Type Errors

- Use `id ?? null` for `useParams` to `useWorkflowSSE`
- Cast `checkpoint.data` fields explicitly when rendering
- Use `String()` wrapper for unknown types in JSX

### State Sync

- SSE events update React Query cache
- Zustand store tracks active workflow
- Clear state on workflow completion/cancellation

## Future Enhancements

- Drag-and-drop article reordering in ArticleReview
- Rich text editor in ContentReview
- Real chart visualizations in AnalyticsPage
- Template editor with live preview
- Bulk subscriber import with validation
- Campaign A/B testing UI
