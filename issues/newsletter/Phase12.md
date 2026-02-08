# Phase 12: Frontend - Types, API Client, Hooks

## Goal
Frontend infrastructure for newsletter platform

## Status
- [ ] Not Started

## Files to Create
```
frontend/src/types/newsletter.ts
frontend/src/api/newsletter.ts
frontend/src/hooks/useNewsletter.ts
frontend/src/store/newsletterStore.ts
```

## Types
```typescript
// newsletter.ts
interface Newsletter {
  id: string;
  user_id: string;
  title: string;
  content: string;
  html_content: string;
  status: NewsletterStatus;
  topics_covered: string[];
  tone_used: string;
  word_count: number;
  created_at: string;
}

interface Campaign {
  id: string;
  name: string;
  subject: string;
  status: CampaignStatus;
  newsletter_id?: string;
  analytics: CampaignAnalytics;
}

interface Subscriber {
  id: string;
  email: string;
  name?: string;
  status: SubscriberStatus;
  preferences: SubscriberPreferences;
  engagement: EngagementMetrics;
}

interface WorkflowStatus {
  workflow_id: string;
  status: 'running' | 'awaiting_approval' | 'completed' | 'cancelled' | 'failed';
  current_checkpoint?: string;
  checkpoint_data?: Record<string, any>;
}
```

## API Client Methods
```typescript
// newsletter.ts
const newsletterApi = {
  // Newsletters
  generateNewsletter: (request: GenerateRequest) => Promise<WorkflowStatus>,
  getNewsletters: (params?: ListParams) => Promise<Newsletter[]>,
  getNewsletter: (id: string) => Promise<Newsletter>,
  deleteNewsletter: (id: string) => Promise<void>,

  // Workflows
  getWorkflowStatus: (id: string) => Promise<WorkflowStatus>,
  approveCheckpoint: (id: string, data: ApproveRequest) => Promise<WorkflowStatus>,
  cancelWorkflow: (id: string) => Promise<void>,

  // Campaigns, Subscribers, Templates...
};
```

## Hooks
```typescript
// useNewsletter.ts
const useNewsletters = () => useQuery(['newsletters'], ...);
const useNewsletter = (id: string) => useQuery(['newsletter', id], ...);
const useGenerateNewsletter = () => useMutation(...);
const useWorkflowStatus = (id: string) => useQuery(['workflow', id], ...);
const useApproveCheckpoint = () => useMutation(...);
```

## Store (Zustand)
```typescript
// newsletterStore.ts
interface NewsletterStore {
  activeWorkflowId: string | null;
  setActiveWorkflow: (id: string | null) => void;
  checkpointData: Record<string, any> | null;
  setCheckpointData: (data: Record<string, any> | null) => void;
}
```

## Dependencies
- Phase 11 (Backend API)
- React Query (for data fetching)
- Zustand (for state management)

## Verification
- [ ] All types match backend schemas
- [ ] API client methods work
- [ ] Hooks fetch data correctly
- [ ] Store manages workflow state
- [ ] Tests passing
