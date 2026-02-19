# Phase 12: Frontend Infrastructure - Detailed Implementation Plan

## Overview

Phase 12 establishes the frontend infrastructure for the newsletter platform, including TypeScript types, API client, React Query hooks, and Zustand store. This foundation enables Phase 13 (UI components) and Phase 14 (pages).

**Dependencies:** Phase 11 (Backend API Endpoints)

---

## Architecture

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Newsletter Platform UI                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────┐    ┌──────────────────────┐                  │
│  │   React Components   │◄───│   Custom Hooks       │                  │
│  │                      │    │   (useNewsletter)    │                  │
│  └──────────────────────┘    └──────────┬───────────┘                  │
│                                         │                               │
│            ┌────────────────────────────┼────────────────────┐         │
│            │                            │                    │         │
│            ▼                            ▼                    ▼         │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐ │
│  │  React Query     │    │  Zustand Store   │    │  SSE Connection  │ │
│  │  (Server State)  │    │  (Client State)  │    │  (Real-time)     │ │
│  └────────┬─────────┘    └──────────────────┘    └────────┬─────────┘ │
│           │                                               │           │
│           ▼                                               ▼           │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                      API Client (newsletterApi)                  │ │
│  └──────────────────────────────────┬───────────────────────────────┘ │
│                                     │                                  │
└─────────────────────────────────────┼──────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Backend API (/api/v1/platforms/newsletter)       │
├─────────────────────────────────────────────────────────────────────────┤
│  /newsletters  /workflows  /campaigns  /subscribers  /templates        │
│  /analytics    /research   /writing    /preference                     │
└─────────────────────────────────────────────────────────────────────────┘
```

### State Management Strategy

| State Type | Technology | Use Case |
|------------|------------|----------|
| Server State | React Query | Newsletters, campaigns, subscribers, templates, analytics |
| Client State | Zustand | Active workflow, UI state, form drafts |
| Real-time | SSE + Zustand | Workflow progress, checkpoint notifications |
| URL State | React Router | Filters, pagination, selected items |

---

## File Structure

```
frontend/src/
├── types/
│   └── newsletter.ts          # Extended with all entity types
│
├── api/
│   └── newsletter.ts          # Dedicated newsletter API client (NEW)
│
├── hooks/
│   ├── useNewsletter.ts       # Extended with all hooks
│   └── useWorkflowSSE.ts      # SSE hook for workflow streaming (NEW)
│
└── store/
    └── newsletterStore.ts     # Zustand store for workflow state (NEW)
```

---

## TypeScript Types

### File: `frontend/src/types/newsletter.ts`

The existing file has research and writing types. Extend with the following:

```typescript
// ============================================================================
// ENUMS & CONSTANTS
// ============================================================================

export type NewsletterStatus = 'draft' | 'pending_review' | 'approved' | 'sent' | 'archived';
export type CampaignStatus = 'draft' | 'scheduled' | 'sending' | 'sent' | 'failed';
export type SubscriberStatus = 'active' | 'unsubscribed' | 'bounced' | 'pending';
export type TemplateCategory = 'newsletter' | 'campaign' | 'transactional' | 'custom';
export type WorkflowStepStatus = 'running' | 'awaiting_approval' | 'completed' | 'cancelled' | 'failed';

// ============================================================================
// NEWSLETTER ENTITY (Phase 11)
// ============================================================================

export interface Newsletter {
  id: string;
  user_id: string;
  title: string;
  content: string;
  html_content: string;
  status: NewsletterStatus;
  topics_covered: string[];
  tone_used: string;
  word_count: number;
  source_articles: Article[];
  analytics?: NewsletterAnalytics;
  created_at: string;
  updated_at: string;
  published_at?: string;
}

export interface NewsletterAnalytics {
  views: number;
  unique_views: number;
  avg_read_time: number;
  share_count: number;
}

export interface NewsletterListResponse {
  items: Newsletter[];
  total: number;
}

export interface NewsletterUpdateRequest {
  title?: string;
  content?: string;
  html_content?: string;
  status?: NewsletterStatus;
}

// ============================================================================
// WORKFLOW ENTITY (Phase 11 HITL)
// ============================================================================

export interface WorkflowState {
  workflow_id: string;
  user_id: string;
  status: WorkflowStepStatus;
  current_step: string | null;
  current_checkpoint: Checkpoint | null;
  topics: string[];
  tone: string;
  article_count: number;
  newsletter_id: string | null;
  checkpoints_completed: string[];
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface WorkflowListItem {
  workflow_id: string;
  status: WorkflowStepStatus;
  current_step: string | null;
  created_at: string;
  updated_at: string;
}

export interface WorkflowListResponse {
  items: WorkflowListItem[];
  total: number;
}

export interface Checkpoint {
  checkpoint_id: string;
  checkpoint_type: 'research_review' | 'content_review' | 'final_review';
  title: string;
  description: string;
  data: CheckpointData;
  actions: CheckpointAction[];
  metadata: Record<string, unknown>;
}

export type CheckpointAction = 'approve' | 'edit' | 'reject';

export interface CheckpointData {
  articles?: Article[];
  newsletter?: NewsletterContent;
  subject_lines?: SubjectLine[];
  [key: string]: unknown;
}

export interface ApproveCheckpointRequest {
  checkpoint_id: string;
  action: CheckpointAction;
  modifications?: Record<string, unknown>;
  feedback?: string;
}

export interface WorkflowHistoryItem {
  step: string;
  status: string;
  timestamp: string;
  data: Record<string, unknown>;
}

export interface WorkflowHistoryResponse {
  workflow_id: string;
  history: WorkflowHistoryItem[];
}

// ============================================================================
// CAMPAIGN ENTITY (Phase 11)
// ============================================================================

export interface Campaign {
  id: string;
  user_id: string;
  name: string;
  subject: string;
  status: CampaignStatus;
  newsletter_id?: string;
  template_id?: string;
  scheduled_at?: string;
  sent_at?: string;
  recipient_count: number;
  analytics: CampaignAnalytics;
  created_at: string;
  updated_at: string;
}

export interface CampaignAnalytics {
  sent: number;
  delivered: number;
  opened: number;
  clicked: number;
  bounced: number;
  unsubscribed: number;
  open_rate: number;
  click_rate: number;
}

export interface CampaignListResponse {
  items: Campaign[];
  total: number;
}

export interface CreateCampaignRequest {
  name: string;
  subject: string;
  newsletter_id?: string;
  template_id?: string;
}

export interface UpdateCampaignRequest {
  name?: string;
  subject?: string;
  newsletter_id?: string;
  template_id?: string;
}

export interface ScheduleCampaignRequest {
  scheduled_at: string;  // ISO 8601 datetime
}

// ============================================================================
// SUBSCRIBER ENTITY (Phase 11)
// ============================================================================

export interface Subscriber {
  id: string;
  user_id: string;
  email: string;
  name?: string;
  status: SubscriberStatus;
  tags: string[];
  groups: string[];
  preferences: SubscriberPreferences;
  engagement: SubscriberEngagement;
  subscribed_at: string;
  unsubscribed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface SubscriberPreferences {
  frequency: 'daily' | 'weekly' | 'monthly';
  topics: string[];
  format: 'html' | 'text';
}

export interface SubscriberEngagement {
  emails_received: number;
  emails_opened: number;
  links_clicked: number;
  last_opened?: string;
  last_clicked?: string;
  engagement_score: number;
}

export interface SubscriberListResponse {
  items: Subscriber[];
  total: number;
}

export interface CreateSubscriberRequest {
  email: string;
  name?: string;
  tags?: string[];
  groups?: string[];
  preferences?: Partial<SubscriberPreferences>;
}

export interface UpdateSubscriberRequest {
  name?: string;
  tags?: string[];
  groups?: string[];
  preferences?: Partial<SubscriberPreferences>;
}

export interface BulkImportRequest {
  subscribers: CreateSubscriberRequest[];
  send_welcome?: boolean;
}

export interface ImportResult {
  imported: number;
  skipped: number;
  errors: string[];
}

// ============================================================================
// TEMPLATE ENTITY (Phase 11)
// ============================================================================

export interface Template {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  category: TemplateCategory;
  subject_template: string;
  html_template: string;
  text_template?: string;
  variables: TemplateVariable[];
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface TemplateVariable {
  name: string;
  description?: string;
  default_value?: string;
  required: boolean;
}

export interface TemplateListResponse {
  items: Template[];
  total: number;
}

export interface CreateTemplateRequest {
  name: string;
  description?: string;
  category: TemplateCategory;
  subject_template: string;
  html_template: string;
  text_template?: string;
  variables?: TemplateVariable[];
}

export interface UpdateTemplateRequest {
  name?: string;
  description?: string;
  category?: TemplateCategory;
  subject_template?: string;
  html_template?: string;
  text_template?: string;
  variables?: TemplateVariable[];
}

export interface TemplatePreviewRequest {
  variables: Record<string, string>;
}

export interface TemplatePreviewResponse {
  subject: string;
  html: string;
  text?: string;
}

// ============================================================================
// ANALYTICS (Phase 11)
// ============================================================================

export interface DashboardMetrics {
  newsletters: {
    total: number;
    this_month: number;
    growth_rate: number;
  };
  campaigns: {
    total: number;
    sent_this_month: number;
    avg_open_rate: number;
    avg_click_rate: number;
  };
  subscribers: {
    total: number;
    active: number;
    new_this_month: number;
    churn_rate: number;
  };
  engagement: {
    avg_open_rate: number;
    avg_click_rate: number;
    avg_read_time: number;
  };
}

export interface EngagementMetrics {
  period: string;
  opens: number;
  clicks: number;
  unsubscribes: number;
  bounces: number;
  open_rate: number;
  click_rate: number;
}

export interface SubscriberAnalytics {
  total_subscribers: number;
  active_subscribers: number;
  growth_data: Array<{ date: string; count: number }>;
  top_engaged: Subscriber[];
  by_status: Record<SubscriberStatus, number>;
  by_source: Record<string, number>;
}

export interface AnalyticsExportRequest {
  type: 'newsletters' | 'campaigns' | 'subscribers' | 'all';
  format: 'csv' | 'json';
  date_from?: string;
  date_to?: string;
}

// ============================================================================
// SSE EVENTS (Phase 11 Workflow Streaming)
// ============================================================================

export type SSEEventType = 'status' | 'checkpoint' | 'complete' | 'error' | 'done';

export interface SSEStatusEvent {
  workflow_id: string;
  status: WorkflowStepStatus;
  current_step: string | null;
  checkpoint: Checkpoint | null;
}

export interface SSECheckpointEvent {
  checkpoint_id: string;
  checkpoint_type: string;
  title: string;
  data: Record<string, unknown>;
}

export interface SSECompleteEvent {
  status: 'completed' | 'cancelled' | 'failed';
  newsletter_id?: string;
}

export interface SSEErrorEvent {
  error: string;
}

// ============================================================================
// LIST PARAMETERS (Common)
// ============================================================================

export interface ListParams {
  skip?: number;
  limit?: number;
  status?: string;
}

export interface SubscriberListParams extends ListParams {
  tag?: string;
  group?: string;
}

export interface TemplateListParams extends ListParams {
  category?: TemplateCategory;
}

// ============================================================================
// GENERATE WORKFLOW REQUEST (Phase 11)
// ============================================================================

export interface GenerateWorkflowRequest {
  topics: string[];
  tone?: string;
  max_articles?: number;
  include_rag?: boolean;
  auto_approve?: boolean;
}

export interface GenerateWorkflowResponse {
  workflow_id: string;
  status: WorkflowStepStatus;
  message: string;
}
```

---

## API Client

### File: `frontend/src/api/newsletter.ts` (NEW)

Dedicated API client for newsletter platform with all Phase 11 endpoints.

```typescript
/**
 * Newsletter Platform API Client
 *
 * Complete API client for newsletter platform operations.
 * Covers all Phase 11 endpoints with proper typing.
 */
import { apiClient } from './client';
import type {
  // Existing types
  ResearchRequest,
  CustomResearchRequest,
  ResearchResponse,
  GenerateRequest,
  GenerateResponse,
  NewsletterStatus as PlatformStatus,
  NewsletterAgent,
  // New Phase 12 types
  Newsletter,
  NewsletterListResponse,
  NewsletterUpdateRequest,
  WorkflowState,
  WorkflowListResponse,
  Checkpoint,
  ApproveCheckpointRequest,
  WorkflowHistoryResponse,
  Campaign,
  CampaignListResponse,
  CreateCampaignRequest,
  UpdateCampaignRequest,
  ScheduleCampaignRequest,
  Subscriber,
  SubscriberListResponse,
  CreateSubscriberRequest,
  UpdateSubscriberRequest,
  BulkImportRequest,
  ImportResult,
  Template,
  TemplateListResponse,
  CreateTemplateRequest,
  UpdateTemplateRequest,
  TemplatePreviewRequest,
  TemplatePreviewResponse,
  DashboardMetrics,
  CampaignAnalytics,
  EngagementMetrics,
  SubscriberAnalytics,
  AnalyticsExportRequest,
  ListParams,
  SubscriberListParams,
  TemplateListParams,
  GenerateWorkflowRequest,
  GenerateWorkflowResponse,
} from '@/types/newsletter';

const BASE_PATH = '/api/v1/platforms/newsletter';

// Timeout configurations
const TIMEOUTS = {
  DEFAULT: 30000,
  RESEARCH: 180000,     // 3 minutes for research operations
  GENERATION: 300000,   // 5 minutes for newsletter generation
  EXPORT: 120000,       // 2 minutes for analytics export
};

/**
 * Newsletter Platform API
 */
export const newsletterApi = {
  // ==========================================================================
  // PLATFORM STATUS
  // ==========================================================================

  getStatus: async (): Promise<PlatformStatus> => {
    const response = await apiClient.get<PlatformStatus>(`${BASE_PATH}/status`);
    return response.data;
  },

  getAgents: async (): Promise<NewsletterAgent[]> => {
    const response = await apiClient.get<NewsletterAgent[]>(`${BASE_PATH}/agents`);
    return response.data;
  },

  // ==========================================================================
  // RESEARCH (Phase 6)
  // ==========================================================================

  research: async (request: ResearchRequest): Promise<ResearchResponse> => {
    const response = await apiClient.post<ResearchResponse>(
      `${BASE_PATH}/research`,
      request,
      { timeout: TIMEOUTS.RESEARCH }
    );
    return response.data;
  },

  researchCustom: async (request: CustomResearchRequest): Promise<ResearchResponse> => {
    const response = await apiClient.post<ResearchResponse>(
      `${BASE_PATH}/research/custom`,
      request,
      { timeout: TIMEOUTS.RESEARCH }
    );
    return response.data;
  },

  getTrending: async (topics: string[], maxResults = 10): Promise<ResearchResponse> => {
    const response = await apiClient.get<ResearchResponse>(
      `${BASE_PATH}/research/trending`,
      {
        params: { topics: topics.join(','), max_results: maxResults },
        timeout: TIMEOUTS.RESEARCH,
      }
    );
    return response.data;
  },

  // ==========================================================================
  // WRITING (Phase 7)
  // ==========================================================================

  generateContent: async (request: GenerateRequest): Promise<GenerateResponse> => {
    const response = await apiClient.post<GenerateResponse>(
      `${BASE_PATH}/writing/generate`,
      request,
      { timeout: TIMEOUTS.GENERATION }
    );
    return response.data;
  },

  // ==========================================================================
  // NEWSLETTERS (Phase 11)
  // ==========================================================================

  listNewsletters: async (params?: ListParams): Promise<NewsletterListResponse> => {
    const response = await apiClient.get<NewsletterListResponse>(
      `${BASE_PATH}/newsletters`,
      { params }
    );
    return response.data;
  },

  getNewsletter: async (id: string): Promise<Newsletter> => {
    const response = await apiClient.get<Newsletter>(`${BASE_PATH}/newsletters/${id}`);
    return response.data;
  },

  updateNewsletter: async (id: string, data: NewsletterUpdateRequest): Promise<Newsletter> => {
    const response = await apiClient.patch<Newsletter>(
      `${BASE_PATH}/newsletters/${id}`,
      data
    );
    return response.data;
  },

  deleteNewsletter: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/newsletters/${id}`);
  },

  // ==========================================================================
  // WORKFLOWS (Phase 11 HITL)
  // ==========================================================================

  /**
   * Start a new newsletter generation workflow
   */
  generateNewsletter: async (request: GenerateWorkflowRequest): Promise<GenerateWorkflowResponse> => {
    const response = await apiClient.post<GenerateWorkflowResponse>(
      `${BASE_PATH}/generate`,
      request,
      { timeout: TIMEOUTS.GENERATION }
    );
    return response.data;
  },

  listWorkflows: async (status?: string, limit = 20): Promise<WorkflowListResponse> => {
    const response = await apiClient.get<WorkflowListResponse>(
      `${BASE_PATH}/workflows`,
      { params: { status, limit } }
    );
    return response.data;
  },

  getWorkflow: async (workflowId: string): Promise<WorkflowState> => {
    const response = await apiClient.get<WorkflowState>(
      `${BASE_PATH}/workflows/${workflowId}`
    );
    return response.data;
  },

  getCheckpoint: async (workflowId: string): Promise<Checkpoint> => {
    const response = await apiClient.get<Checkpoint>(
      `${BASE_PATH}/workflows/${workflowId}/checkpoint`
    );
    return response.data;
  },

  approveCheckpoint: async (
    workflowId: string,
    request: ApproveCheckpointRequest
  ): Promise<WorkflowState> => {
    const response = await apiClient.post<WorkflowState>(
      `${BASE_PATH}/workflows/${workflowId}/approve`,
      request
    );
    return response.data;
  },

  editCheckpoint: async (
    workflowId: string,
    checkpointId: string,
    modifications: Record<string, unknown>,
    feedback?: string
  ): Promise<WorkflowState> => {
    const response = await apiClient.post<WorkflowState>(
      `${BASE_PATH}/workflows/${workflowId}/edit`,
      { checkpoint_id: checkpointId, modifications, feedback }
    );
    return response.data;
  },

  rejectCheckpoint: async (
    workflowId: string,
    checkpointId: string,
    feedback?: string
  ): Promise<WorkflowState> => {
    const response = await apiClient.post<WorkflowState>(
      `${BASE_PATH}/workflows/${workflowId}/reject`,
      { checkpoint_id: checkpointId, feedback }
    );
    return response.data;
  },

  cancelWorkflow: async (workflowId: string): Promise<WorkflowState> => {
    const response = await apiClient.post<WorkflowState>(
      `${BASE_PATH}/workflows/${workflowId}/cancel`
    );
    return response.data;
  },

  getWorkflowHistory: async (workflowId: string): Promise<WorkflowHistoryResponse> => {
    const response = await apiClient.get<WorkflowHistoryResponse>(
      `${BASE_PATH}/workflows/${workflowId}/history`
    );
    return response.data;
  },

  /**
   * Get SSE endpoint URL for workflow streaming
   * (Used by useWorkflowSSE hook)
   */
  getWorkflowStreamUrl: (workflowId: string): string => {
    return `${BASE_PATH}/workflows/${workflowId}/stream`;
  },

  // ==========================================================================
  // CAMPAIGNS (Phase 11)
  // ==========================================================================

  listCampaigns: async (params?: ListParams): Promise<CampaignListResponse> => {
    const response = await apiClient.get<CampaignListResponse>(
      `${BASE_PATH}/campaigns`,
      { params }
    );
    return response.data;
  },

  getCampaign: async (id: string): Promise<Campaign> => {
    const response = await apiClient.get<Campaign>(`${BASE_PATH}/campaigns/${id}`);
    return response.data;
  },

  createCampaign: async (data: CreateCampaignRequest): Promise<Campaign> => {
    const response = await apiClient.post<Campaign>(`${BASE_PATH}/campaigns`, data);
    return response.data;
  },

  updateCampaign: async (id: string, data: UpdateCampaignRequest): Promise<Campaign> => {
    const response = await apiClient.put<Campaign>(
      `${BASE_PATH}/campaigns/${id}`,
      data
    );
    return response.data;
  },

  deleteCampaign: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/campaigns/${id}`);
  },

  sendCampaign: async (id: string): Promise<Campaign> => {
    const response = await apiClient.post<Campaign>(
      `${BASE_PATH}/campaigns/${id}/send`
    );
    return response.data;
  },

  scheduleCampaign: async (id: string, data: ScheduleCampaignRequest): Promise<Campaign> => {
    const response = await apiClient.post<Campaign>(
      `${BASE_PATH}/campaigns/${id}/schedule`,
      data
    );
    return response.data;
  },

  // ==========================================================================
  // SUBSCRIBERS (Phase 11)
  // ==========================================================================

  listSubscribers: async (params?: SubscriberListParams): Promise<SubscriberListResponse> => {
    const response = await apiClient.get<SubscriberListResponse>(
      `${BASE_PATH}/subscribers`,
      { params }
    );
    return response.data;
  },

  getSubscriber: async (id: string): Promise<Subscriber> => {
    const response = await apiClient.get<Subscriber>(`${BASE_PATH}/subscribers/${id}`);
    return response.data;
  },

  createSubscriber: async (data: CreateSubscriberRequest): Promise<Subscriber> => {
    const response = await apiClient.post<Subscriber>(`${BASE_PATH}/subscribers`, data);
    return response.data;
  },

  updateSubscriber: async (id: string, data: UpdateSubscriberRequest): Promise<Subscriber> => {
    const response = await apiClient.put<Subscriber>(
      `${BASE_PATH}/subscribers/${id}`,
      data
    );
    return response.data;
  },

  deleteSubscriber: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/subscribers/${id}`);
  },

  importSubscribers: async (data: BulkImportRequest): Promise<ImportResult> => {
    const response = await apiClient.post<ImportResult>(
      `${BASE_PATH}/subscribers/import`,
      data
    );
    return response.data;
  },

  importSubscribersCSV: async (file: File, sendWelcome = false): Promise<ImportResult> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post<ImportResult>(
      `${BASE_PATH}/subscribers/import/csv`,
      formData,
      {
        params: { send_welcome: sendWelcome },
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );
    return response.data;
  },

  unsubscribe: async (id: string): Promise<Subscriber> => {
    const response = await apiClient.post<Subscriber>(
      `${BASE_PATH}/subscribers/${id}/unsubscribe`
    );
    return response.data;
  },

  resubscribe: async (id: string): Promise<Subscriber> => {
    const response = await apiClient.post<Subscriber>(
      `${BASE_PATH}/subscribers/${id}/resubscribe`
    );
    return response.data;
  },

  // ==========================================================================
  // TEMPLATES (Phase 11)
  // ==========================================================================

  listTemplates: async (params?: TemplateListParams): Promise<TemplateListResponse> => {
    const response = await apiClient.get<TemplateListResponse>(
      `${BASE_PATH}/templates`,
      { params }
    );
    return response.data;
  },

  getTemplate: async (id: string): Promise<Template> => {
    const response = await apiClient.get<Template>(`${BASE_PATH}/templates/${id}`);
    return response.data;
  },

  createTemplate: async (data: CreateTemplateRequest): Promise<Template> => {
    const response = await apiClient.post<Template>(`${BASE_PATH}/templates`, data);
    return response.data;
  },

  updateTemplate: async (id: string, data: UpdateTemplateRequest): Promise<Template> => {
    const response = await apiClient.put<Template>(
      `${BASE_PATH}/templates/${id}`,
      data
    );
    return response.data;
  },

  deleteTemplate: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/templates/${id}`);
  },

  duplicateTemplate: async (id: string): Promise<Template> => {
    const response = await apiClient.post<Template>(
      `${BASE_PATH}/templates/${id}/duplicate`
    );
    return response.data;
  },

  setDefaultTemplate: async (id: string): Promise<Template> => {
    const response = await apiClient.post<Template>(
      `${BASE_PATH}/templates/${id}/set-default`
    );
    return response.data;
  },

  previewTemplate: async (
    id: string,
    data: TemplatePreviewRequest
  ): Promise<TemplatePreviewResponse> => {
    const response = await apiClient.post<TemplatePreviewResponse>(
      `${BASE_PATH}/templates/${id}/preview`,
      data
    );
    return response.data;
  },

  // ==========================================================================
  // ANALYTICS (Phase 11)
  // ==========================================================================

  getDashboard: async (): Promise<DashboardMetrics> => {
    const response = await apiClient.get<DashboardMetrics>(
      `${BASE_PATH}/analytics/dashboard`
    );
    return response.data;
  },

  getCampaignAnalytics: async (campaignId: string): Promise<CampaignAnalytics> => {
    const response = await apiClient.get<CampaignAnalytics>(
      `${BASE_PATH}/analytics/campaigns/${campaignId}`
    );
    return response.data;
  },

  getEngagementMetrics: async (
    period: 'day' | 'week' | 'month' = 'week'
  ): Promise<EngagementMetrics[]> => {
    const response = await apiClient.get<EngagementMetrics[]>(
      `${BASE_PATH}/analytics/engagement`,
      { params: { period } }
    );
    return response.data;
  },

  getSubscriberAnalytics: async (): Promise<SubscriberAnalytics> => {
    const response = await apiClient.get<SubscriberAnalytics>(
      `${BASE_PATH}/analytics/subscribers`
    );
    return response.data;
  },

  exportAnalytics: async (request: AnalyticsExportRequest): Promise<Blob> => {
    const response = await apiClient.get(`${BASE_PATH}/analytics/export`, {
      params: request,
      responseType: 'blob',
      timeout: TIMEOUTS.EXPORT,
    });
    return response.data;
  },
};
```

---

## React Query Hooks

### File: `frontend/src/hooks/useNewsletter.ts` (EXTENDED)

Extend the existing file with comprehensive hooks for all entities.

```typescript
/**
 * React Query hooks for Newsletter platform
 *
 * Complete hook library covering all Phase 11 API endpoints.
 * Follows existing codebase patterns from useAgents.ts, useWorkflows.ts.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { newsletterApi } from '@/api/newsletter';
import type {
  // Research & Writing
  ResearchRequest,
  CustomResearchRequest,
  ResearchResponse,
  GenerateRequest,
  GenerateResponse,
  // Newsletter
  Newsletter,
  NewsletterListResponse,
  NewsletterUpdateRequest,
  ListParams,
  // Workflow
  WorkflowState,
  WorkflowListResponse,
  Checkpoint,
  ApproveCheckpointRequest,
  WorkflowHistoryResponse,
  GenerateWorkflowRequest,
  GenerateWorkflowResponse,
  // Campaign
  Campaign,
  CampaignListResponse,
  CreateCampaignRequest,
  UpdateCampaignRequest,
  ScheduleCampaignRequest,
  // Subscriber
  Subscriber,
  SubscriberListResponse,
  CreateSubscriberRequest,
  UpdateSubscriberRequest,
  BulkImportRequest,
  ImportResult,
  SubscriberListParams,
  // Template
  Template,
  TemplateListResponse,
  CreateTemplateRequest,
  UpdateTemplateRequest,
  TemplatePreviewRequest,
  TemplatePreviewResponse,
  TemplateListParams,
  // Analytics
  DashboardMetrics,
  CampaignAnalytics,
  EngagementMetrics,
  SubscriberAnalytics,
  AnalyticsExportRequest,
} from '@/types/newsletter';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const newsletterKeys = {
  all: ['newsletter'] as const,

  // Platform
  status: () => [...newsletterKeys.all, 'status'] as const,
  agents: () => [...newsletterKeys.all, 'agents'] as const,

  // Research
  research: () => [...newsletterKeys.all, 'research'] as const,
  trending: (topics: string[]) => [...newsletterKeys.all, 'trending', topics] as const,

  // Newsletters
  newsletters: () => [...newsletterKeys.all, 'newsletters'] as const,
  newslettersList: (params?: ListParams) => [...newsletterKeys.newsletters(), 'list', params] as const,
  newsletterDetail: (id: string) => [...newsletterKeys.newsletters(), 'detail', id] as const,

  // Workflows
  workflows: () => [...newsletterKeys.all, 'workflows'] as const,
  workflowsList: (status?: string) => [...newsletterKeys.workflows(), 'list', status] as const,
  workflowDetail: (id: string) => [...newsletterKeys.workflows(), 'detail', id] as const,
  workflowCheckpoint: (id: string) => [...newsletterKeys.workflows(), 'checkpoint', id] as const,
  workflowHistory: (id: string) => [...newsletterKeys.workflows(), 'history', id] as const,

  // Campaigns
  campaigns: () => [...newsletterKeys.all, 'campaigns'] as const,
  campaignsList: (params?: ListParams) => [...newsletterKeys.campaigns(), 'list', params] as const,
  campaignDetail: (id: string) => [...newsletterKeys.campaigns(), 'detail', id] as const,

  // Subscribers
  subscribers: () => [...newsletterKeys.all, 'subscribers'] as const,
  subscribersList: (params?: SubscriberListParams) => [...newsletterKeys.subscribers(), 'list', params] as const,
  subscriberDetail: (id: string) => [...newsletterKeys.subscribers(), 'detail', id] as const,

  // Templates
  templates: () => [...newsletterKeys.all, 'templates'] as const,
  templatesList: (params?: TemplateListParams) => [...newsletterKeys.templates(), 'list', params] as const,
  templateDetail: (id: string) => [...newsletterKeys.templates(), 'detail', id] as const,

  // Analytics
  analytics: () => [...newsletterKeys.all, 'analytics'] as const,
  dashboard: () => [...newsletterKeys.analytics(), 'dashboard'] as const,
  campaignAnalytics: (id: string) => [...newsletterKeys.analytics(), 'campaign', id] as const,
  engagement: (period: string) => [...newsletterKeys.analytics(), 'engagement', period] as const,
  subscriberAnalytics: () => [...newsletterKeys.analytics(), 'subscribers'] as const,
};

// ============================================================================
// PLATFORM HOOKS
// ============================================================================

export function useNewsletterStatus() {
  return useQuery({
    queryKey: newsletterKeys.status(),
    queryFn: newsletterApi.getStatus,
    staleTime: 30000,
  });
}

export function useNewsletterAgents() {
  return useQuery({
    queryKey: newsletterKeys.agents(),
    queryFn: newsletterApi.getAgents,
  });
}

// ============================================================================
// RESEARCH HOOKS (Phase 6)
// ============================================================================

export function useResearch() {
  return useMutation<ResearchResponse, Error, ResearchRequest>({
    mutationFn: newsletterApi.research,
  });
}

export function useResearchCustom() {
  return useMutation<ResearchResponse, Error, CustomResearchRequest>({
    mutationFn: newsletterApi.researchCustom,
  });
}

export function useTrending(topics: string[], maxResults = 10) {
  return useQuery({
    queryKey: newsletterKeys.trending(topics),
    queryFn: () => newsletterApi.getTrending(topics, maxResults),
    enabled: topics.length > 0,
    staleTime: 60000,
  });
}

// ============================================================================
// WRITING HOOKS (Phase 7)
// ============================================================================

export function useGenerateContent() {
  return useMutation<GenerateResponse, Error, GenerateRequest>({
    mutationFn: newsletterApi.generateContent,
  });
}

// ============================================================================
// NEWSLETTER HOOKS (Phase 11)
// ============================================================================

export function useNewsletters(params?: ListParams) {
  return useQuery({
    queryKey: newsletterKeys.newslettersList(params),
    queryFn: () => newsletterApi.listNewsletters(params),
  });
}

export function useNewsletter(id: string) {
  return useQuery({
    queryKey: newsletterKeys.newsletterDetail(id),
    queryFn: () => newsletterApi.getNewsletter(id),
    enabled: !!id,
  });
}

export function useUpdateNewsletter() {
  const queryClient = useQueryClient();

  return useMutation<Newsletter, Error, { id: string; data: NewsletterUpdateRequest }>({
    mutationFn: ({ id, data }) => newsletterApi.updateNewsletter(id, data),
    onSuccess: (newsletter) => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.newsletters() });
      queryClient.setQueryData(newsletterKeys.newsletterDetail(newsletter.id), newsletter);
    },
  });
}

export function useDeleteNewsletter() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: newsletterApi.deleteNewsletter,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.newsletters() });
    },
  });
}

// ============================================================================
// WORKFLOW HOOKS (Phase 11 HITL)
// ============================================================================

export function useGenerateNewsletter() {
  const queryClient = useQueryClient();

  return useMutation<GenerateWorkflowResponse, Error, GenerateWorkflowRequest>({
    mutationFn: newsletterApi.generateNewsletter,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.workflows() });
    },
  });
}

export function useWorkflows(status?: string) {
  return useQuery({
    queryKey: newsletterKeys.workflowsList(status),
    queryFn: () => newsletterApi.listWorkflows(status),
  });
}

export function useWorkflow(workflowId: string) {
  return useQuery({
    queryKey: newsletterKeys.workflowDetail(workflowId),
    queryFn: () => newsletterApi.getWorkflow(workflowId),
    enabled: !!workflowId,
    refetchInterval: (data) => {
      // Poll every 2 seconds while workflow is running
      if (data?.status === 'running') return 2000;
      return false;
    },
  });
}

export function useWorkflowCheckpoint(workflowId: string) {
  return useQuery({
    queryKey: newsletterKeys.workflowCheckpoint(workflowId),
    queryFn: () => newsletterApi.getCheckpoint(workflowId),
    enabled: !!workflowId,
    retry: false, // Don't retry on 404 (no checkpoint)
  });
}

export function useWorkflowHistory(workflowId: string) {
  return useQuery({
    queryKey: newsletterKeys.workflowHistory(workflowId),
    queryFn: () => newsletterApi.getWorkflowHistory(workflowId),
    enabled: !!workflowId,
  });
}

export function useApproveCheckpoint() {
  const queryClient = useQueryClient();

  return useMutation<WorkflowState, Error, { workflowId: string; request: ApproveCheckpointRequest }>({
    mutationFn: ({ workflowId, request }) => newsletterApi.approveCheckpoint(workflowId, request),
    onSuccess: (workflow) => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.workflowDetail(workflow.workflow_id) });
      queryClient.invalidateQueries({ queryKey: newsletterKeys.workflowCheckpoint(workflow.workflow_id) });
    },
  });
}

export function useCancelWorkflow() {
  const queryClient = useQueryClient();

  return useMutation<WorkflowState, Error, string>({
    mutationFn: newsletterApi.cancelWorkflow,
    onSuccess: (workflow) => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.workflows() });
      queryClient.setQueryData(newsletterKeys.workflowDetail(workflow.workflow_id), workflow);
    },
  });
}

// ============================================================================
// CAMPAIGN HOOKS (Phase 11)
// ============================================================================

export function useCampaigns(params?: ListParams) {
  return useQuery({
    queryKey: newsletterKeys.campaignsList(params),
    queryFn: () => newsletterApi.listCampaigns(params),
  });
}

export function useCampaign(id: string) {
  return useQuery({
    queryKey: newsletterKeys.campaignDetail(id),
    queryFn: () => newsletterApi.getCampaign(id),
    enabled: !!id,
  });
}

export function useCreateCampaign() {
  const queryClient = useQueryClient();

  return useMutation<Campaign, Error, CreateCampaignRequest>({
    mutationFn: newsletterApi.createCampaign,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.campaigns() });
    },
  });
}

export function useUpdateCampaign() {
  const queryClient = useQueryClient();

  return useMutation<Campaign, Error, { id: string; data: UpdateCampaignRequest }>({
    mutationFn: ({ id, data }) => newsletterApi.updateCampaign(id, data),
    onSuccess: (campaign) => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.campaigns() });
      queryClient.setQueryData(newsletterKeys.campaignDetail(campaign.id), campaign);
    },
  });
}

export function useDeleteCampaign() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: newsletterApi.deleteCampaign,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.campaigns() });
    },
  });
}

export function useSendCampaign() {
  const queryClient = useQueryClient();

  return useMutation<Campaign, Error, string>({
    mutationFn: newsletterApi.sendCampaign,
    onSuccess: (campaign) => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.campaigns() });
      queryClient.setQueryData(newsletterKeys.campaignDetail(campaign.id), campaign);
    },
  });
}

export function useScheduleCampaign() {
  const queryClient = useQueryClient();

  return useMutation<Campaign, Error, { id: string; data: ScheduleCampaignRequest }>({
    mutationFn: ({ id, data }) => newsletterApi.scheduleCampaign(id, data),
    onSuccess: (campaign) => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.campaigns() });
      queryClient.setQueryData(newsletterKeys.campaignDetail(campaign.id), campaign);
    },
  });
}

// ============================================================================
// SUBSCRIBER HOOKS (Phase 11)
// ============================================================================

export function useSubscribers(params?: SubscriberListParams) {
  return useQuery({
    queryKey: newsletterKeys.subscribersList(params),
    queryFn: () => newsletterApi.listSubscribers(params),
  });
}

export function useSubscriber(id: string) {
  return useQuery({
    queryKey: newsletterKeys.subscriberDetail(id),
    queryFn: () => newsletterApi.getSubscriber(id),
    enabled: !!id,
  });
}

export function useCreateSubscriber() {
  const queryClient = useQueryClient();

  return useMutation<Subscriber, Error, CreateSubscriberRequest>({
    mutationFn: newsletterApi.createSubscriber,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.subscribers() });
    },
  });
}

export function useUpdateSubscriber() {
  const queryClient = useQueryClient();

  return useMutation<Subscriber, Error, { id: string; data: UpdateSubscriberRequest }>({
    mutationFn: ({ id, data }) => newsletterApi.updateSubscriber(id, data),
    onSuccess: (subscriber) => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.subscribers() });
      queryClient.setQueryData(newsletterKeys.subscriberDetail(subscriber.id), subscriber);
    },
  });
}

export function useDeleteSubscriber() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: newsletterApi.deleteSubscriber,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.subscribers() });
    },
  });
}

export function useImportSubscribers() {
  const queryClient = useQueryClient();

  return useMutation<ImportResult, Error, BulkImportRequest>({
    mutationFn: newsletterApi.importSubscribers,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.subscribers() });
    },
  });
}

export function useImportSubscribersCSV() {
  const queryClient = useQueryClient();

  return useMutation<ImportResult, Error, { file: File; sendWelcome?: boolean }>({
    mutationFn: ({ file, sendWelcome }) => newsletterApi.importSubscribersCSV(file, sendWelcome),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.subscribers() });
    },
  });
}

export function useUnsubscribe() {
  const queryClient = useQueryClient();

  return useMutation<Subscriber, Error, string>({
    mutationFn: newsletterApi.unsubscribe,
    onSuccess: (subscriber) => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.subscribers() });
      queryClient.setQueryData(newsletterKeys.subscriberDetail(subscriber.id), subscriber);
    },
  });
}

export function useResubscribe() {
  const queryClient = useQueryClient();

  return useMutation<Subscriber, Error, string>({
    mutationFn: newsletterApi.resubscribe,
    onSuccess: (subscriber) => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.subscribers() });
      queryClient.setQueryData(newsletterKeys.subscriberDetail(subscriber.id), subscriber);
    },
  });
}

// ============================================================================
// TEMPLATE HOOKS (Phase 11)
// ============================================================================

export function useTemplates(params?: TemplateListParams) {
  return useQuery({
    queryKey: newsletterKeys.templatesList(params),
    queryFn: () => newsletterApi.listTemplates(params),
  });
}

export function useTemplate(id: string) {
  return useQuery({
    queryKey: newsletterKeys.templateDetail(id),
    queryFn: () => newsletterApi.getTemplate(id),
    enabled: !!id,
  });
}

export function useCreateTemplate() {
  const queryClient = useQueryClient();

  return useMutation<Template, Error, CreateTemplateRequest>({
    mutationFn: newsletterApi.createTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.templates() });
    },
  });
}

export function useUpdateTemplate() {
  const queryClient = useQueryClient();

  return useMutation<Template, Error, { id: string; data: UpdateTemplateRequest }>({
    mutationFn: ({ id, data }) => newsletterApi.updateTemplate(id, data),
    onSuccess: (template) => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.templates() });
      queryClient.setQueryData(newsletterKeys.templateDetail(template.id), template);
    },
  });
}

export function useDeleteTemplate() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: newsletterApi.deleteTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.templates() });
    },
  });
}

export function useDuplicateTemplate() {
  const queryClient = useQueryClient();

  return useMutation<Template, Error, string>({
    mutationFn: newsletterApi.duplicateTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.templates() });
    },
  });
}

export function useSetDefaultTemplate() {
  const queryClient = useQueryClient();

  return useMutation<Template, Error, string>({
    mutationFn: newsletterApi.setDefaultTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.templates() });
    },
  });
}

export function usePreviewTemplate() {
  return useMutation<TemplatePreviewResponse, Error, { id: string; data: TemplatePreviewRequest }>({
    mutationFn: ({ id, data }) => newsletterApi.previewTemplate(id, data),
  });
}

// ============================================================================
// ANALYTICS HOOKS (Phase 11)
// ============================================================================

export function useDashboard() {
  return useQuery({
    queryKey: newsletterKeys.dashboard(),
    queryFn: newsletterApi.getDashboard,
    staleTime: 60000, // 1 minute
  });
}

export function useCampaignAnalytics(campaignId: string) {
  return useQuery({
    queryKey: newsletterKeys.campaignAnalytics(campaignId),
    queryFn: () => newsletterApi.getCampaignAnalytics(campaignId),
    enabled: !!campaignId,
  });
}

export function useEngagementMetrics(period: 'day' | 'week' | 'month' = 'week') {
  return useQuery({
    queryKey: newsletterKeys.engagement(period),
    queryFn: () => newsletterApi.getEngagementMetrics(period),
  });
}

export function useSubscriberAnalytics() {
  return useQuery({
    queryKey: newsletterKeys.subscriberAnalytics(),
    queryFn: newsletterApi.getSubscriberAnalytics,
  });
}

export function useExportAnalytics() {
  return useMutation<Blob, Error, AnalyticsExportRequest>({
    mutationFn: newsletterApi.exportAnalytics,
  });
}
```

---

## SSE Hook for Workflow Streaming

### File: `frontend/src/hooks/useWorkflowSSE.ts` (NEW)

```typescript
/**
 * SSE Hook for real-time workflow updates
 *
 * Connects to the workflow stream endpoint and updates the store
 * in real-time as the workflow progresses.
 */
import { useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useNewsletterStore } from '@/store/newsletterStore';
import { newsletterKeys } from '@/hooks/useNewsletter';
import { newsletterApi } from '@/api/newsletter';
import type {
  SSEEventType,
  SSEStatusEvent,
  SSECheckpointEvent,
  SSECompleteEvent,
  SSEErrorEvent,
  WorkflowStepStatus,
} from '@/types/newsletter';

interface UseWorkflowSSEOptions {
  onStatus?: (event: SSEStatusEvent) => void;
  onCheckpoint?: (event: SSECheckpointEvent) => void;
  onComplete?: (event: SSECompleteEvent) => void;
  onError?: (event: SSEErrorEvent) => void;
}

export function useWorkflowSSE(
  workflowId: string | null,
  options: UseWorkflowSSEOptions = {}
) {
  const eventSourceRef = useRef<EventSource | null>(null);
  const queryClient = useQueryClient();
  const { setCheckpointData, setWorkflowStatus } = useNewsletterStore();

  const connect = useCallback(() => {
    if (!workflowId) return;

    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const url = newsletterApi.getWorkflowStreamUrl(workflowId);
    const eventSource = new EventSource(url, { withCredentials: true });
    eventSourceRef.current = eventSource;

    eventSource.addEventListener('status', (event) => {
      try {
        const data: SSEStatusEvent = JSON.parse(event.data);
        setWorkflowStatus(data.status);

        // Update React Query cache
        queryClient.setQueryData(newsletterKeys.workflowDetail(workflowId), (old: any) => ({
          ...old,
          status: data.status,
          current_step: data.current_step,
        }));

        options.onStatus?.(data);
      } catch (e) {
        console.error('Failed to parse SSE status event:', e);
      }
    });

    eventSource.addEventListener('checkpoint', (event) => {
      try {
        const data: SSECheckpointEvent = JSON.parse(event.data);
        setCheckpointData(data);

        // Invalidate checkpoint query to trigger refetch
        queryClient.invalidateQueries({
          queryKey: newsletterKeys.workflowCheckpoint(workflowId),
        });

        options.onCheckpoint?.(data);
      } catch (e) {
        console.error('Failed to parse SSE checkpoint event:', e);
      }
    });

    eventSource.addEventListener('complete', (event) => {
      try {
        const data: SSECompleteEvent = JSON.parse(event.data);
        setWorkflowStatus(data.status as WorkflowStepStatus);
        setCheckpointData(null);

        // Invalidate queries to refresh data
        queryClient.invalidateQueries({ queryKey: newsletterKeys.workflows() });
        queryClient.invalidateQueries({ queryKey: newsletterKeys.newsletters() });

        options.onComplete?.(data);

        // Close connection on completion
        eventSource.close();
      } catch (e) {
        console.error('Failed to parse SSE complete event:', e);
      }
    });

    eventSource.addEventListener('error', (event) => {
      try {
        const data: SSEErrorEvent = JSON.parse((event as MessageEvent).data || '{}');
        options.onError?.(data);
      } catch (e) {
        // Connection error
        console.error('SSE connection error:', e);
      }
    });

    eventSource.addEventListener('done', () => {
      eventSource.close();
    });

    eventSource.onerror = () => {
      // Attempt reconnection after 3 seconds
      setTimeout(() => {
        if (eventSourceRef.current === eventSource) {
          connect();
        }
      }, 3000);
    };
  }, [workflowId, queryClient, setCheckpointData, setWorkflowStatus, options]);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return {
    connect,
    disconnect,
    isConnected: eventSourceRef.current?.readyState === EventSource.OPEN,
  };
}
```

---

## Zustand Store

### File: `frontend/src/store/newsletterStore.ts` (NEW)

```typescript
/**
 * Zustand store for Newsletter platform state
 *
 * Manages client-side state for:
 * - Active workflow tracking
 * - Checkpoint data
 * - UI state (selected articles, form drafts)
 * - Real-time status updates
 */
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type {
  Article,
  WorkflowStepStatus,
  Checkpoint,
  SSECheckpointEvent,
} from '@/types/newsletter';

// ============================================================================
// STATE TYPES
// ============================================================================

interface WorkflowUIState {
  activeWorkflowId: string | null;
  workflowStatus: WorkflowStepStatus | null;
  checkpointData: SSECheckpointEvent | Checkpoint | null;
}

interface ArticleSelectionState {
  selectedArticles: Article[];
  articleSortOrder: string[];
}

interface FormDraftState {
  researchTopics: string[];
  selectedTone: string;
  customPrompt: string;
}

interface UIPreferencesState {
  showPreview: boolean;
  previewFormat: 'html' | 'text' | 'markdown';
  listViewMode: 'grid' | 'list';
}

interface NewsletterState extends
  WorkflowUIState,
  ArticleSelectionState,
  FormDraftState,
  UIPreferencesState {
  // Workflow actions
  setActiveWorkflow: (id: string | null) => void;
  setWorkflowStatus: (status: WorkflowStepStatus | null) => void;
  setCheckpointData: (data: SSECheckpointEvent | Checkpoint | null) => void;
  clearWorkflowState: () => void;

  // Article selection actions
  selectArticle: (article: Article) => void;
  deselectArticle: (url: string) => void;
  clearSelectedArticles: () => void;
  reorderArticles: (fromIndex: number, toIndex: number) => void;
  setSelectedArticles: (articles: Article[]) => void;

  // Form draft actions
  setResearchTopics: (topics: string[]) => void;
  addResearchTopic: (topic: string) => void;
  removeResearchTopic: (topic: string) => void;
  setSelectedTone: (tone: string) => void;
  setCustomPrompt: (prompt: string) => void;
  clearFormDraft: () => void;

  // UI preference actions
  togglePreview: () => void;
  setPreviewFormat: (format: 'html' | 'text' | 'markdown') => void;
  setListViewMode: (mode: 'grid' | 'list') => void;
}

// ============================================================================
// INITIAL STATE
// ============================================================================

const initialWorkflowState: WorkflowUIState = {
  activeWorkflowId: null,
  workflowStatus: null,
  checkpointData: null,
};

const initialArticleState: ArticleSelectionState = {
  selectedArticles: [],
  articleSortOrder: [],
};

const initialFormState: FormDraftState = {
  researchTopics: [],
  selectedTone: 'professional',
  customPrompt: '',
};

const initialUIPreferences: UIPreferencesState = {
  showPreview: true,
  previewFormat: 'html',
  listViewMode: 'grid',
};

// ============================================================================
// STORE
// ============================================================================

export const useNewsletterStore = create<NewsletterState>()(
  persist(
    (set, get) => ({
      // Initial state
      ...initialWorkflowState,
      ...initialArticleState,
      ...initialFormState,
      ...initialUIPreferences,

      // ========================================================================
      // WORKFLOW ACTIONS
      // ========================================================================

      setActiveWorkflow: (id) => set({ activeWorkflowId: id }),

      setWorkflowStatus: (status) => set({ workflowStatus: status }),

      setCheckpointData: (data) => set({ checkpointData: data }),

      clearWorkflowState: () => set(initialWorkflowState),

      // ========================================================================
      // ARTICLE SELECTION ACTIONS
      // ========================================================================

      selectArticle: (article) => {
        const { selectedArticles, articleSortOrder } = get();
        if (!selectedArticles.find((a) => a.url === article.url)) {
          set({
            selectedArticles: [...selectedArticles, article],
            articleSortOrder: [...articleSortOrder, article.url],
          });
        }
      },

      deselectArticle: (url) => {
        const { selectedArticles, articleSortOrder } = get();
        set({
          selectedArticles: selectedArticles.filter((a) => a.url !== url),
          articleSortOrder: articleSortOrder.filter((u) => u !== url),
        });
      },

      clearSelectedArticles: () => set(initialArticleState),

      reorderArticles: (fromIndex, toIndex) => {
        const { articleSortOrder, selectedArticles } = get();
        const newOrder = [...articleSortOrder];
        const [moved] = newOrder.splice(fromIndex, 1);
        newOrder.splice(toIndex, 0, moved);

        // Reorder selectedArticles to match
        const orderedArticles = newOrder
          .map((url) => selectedArticles.find((a) => a.url === url))
          .filter(Boolean) as Article[];

        set({
          articleSortOrder: newOrder,
          selectedArticles: orderedArticles,
        });
      },

      setSelectedArticles: (articles) => set({
        selectedArticles: articles,
        articleSortOrder: articles.map((a) => a.url),
      }),

      // ========================================================================
      // FORM DRAFT ACTIONS
      // ========================================================================

      setResearchTopics: (topics) => set({ researchTopics: topics }),

      addResearchTopic: (topic) => {
        const { researchTopics } = get();
        if (!researchTopics.includes(topic)) {
          set({ researchTopics: [...researchTopics, topic] });
        }
      },

      removeResearchTopic: (topic) => {
        const { researchTopics } = get();
        set({ researchTopics: researchTopics.filter((t) => t !== topic) });
      },

      setSelectedTone: (tone) => set({ selectedTone: tone }),

      setCustomPrompt: (prompt) => set({ customPrompt: prompt }),

      clearFormDraft: () => set(initialFormState),

      // ========================================================================
      // UI PREFERENCE ACTIONS
      // ========================================================================

      togglePreview: () => set((state) => ({ showPreview: !state.showPreview })),

      setPreviewFormat: (format) => set({ previewFormat: format }),

      setListViewMode: (mode) => set({ listViewMode: mode }),
    }),
    {
      name: 'newsletter-storage',
      storage: createJSONStorage(() => localStorage),
      // Only persist UI preferences and form drafts, not workflow state
      partialize: (state) => ({
        researchTopics: state.researchTopics,
        selectedTone: state.selectedTone,
        showPreview: state.showPreview,
        previewFormat: state.previewFormat,
        listViewMode: state.listViewMode,
      }),
    }
  )
);

// ============================================================================
// SELECTORS (for performance optimization)
// ============================================================================

export const selectActiveWorkflow = (state: NewsletterState) => state.activeWorkflowId;
export const selectWorkflowStatus = (state: NewsletterState) => state.workflowStatus;
export const selectCheckpointData = (state: NewsletterState) => state.checkpointData;
export const selectSelectedArticles = (state: NewsletterState) => state.selectedArticles;
export const selectSelectedArticleCount = (state: NewsletterState) => state.selectedArticles.length;
export const selectResearchTopics = (state: NewsletterState) => state.researchTopics;
export const selectIsArticleSelected = (url: string) => (state: NewsletterState) =>
  state.selectedArticles.some((a) => a.url === url);
```

---

## Implementation Tasks

### Task Breakdown

| # | Task | Files | Estimated Effort |
|---|------|-------|------------------|
| 1 | Extend newsletter types | `types/newsletter.ts` | Medium |
| 2 | Create newsletter API client | `api/newsletter.ts` (NEW) | Medium |
| 3 | Extend hooks with all entities | `hooks/useNewsletter.ts` | Medium |
| 4 | Create SSE streaming hook | `hooks/useWorkflowSSE.ts` (NEW) | Medium |
| 5 | Create Zustand store | `store/newsletterStore.ts` (NEW) | Medium |
| 6 | Update existing apps.ts (import paths) | `api/apps.ts` | Small |
| 7 | Add MSW mock handlers | `mocks/handlers/newsletter.ts` (NEW) | Medium |
| 8 | Write unit tests | `__tests__/` | Medium |

### Implementation Order

1. **Types first** - All other files depend on correct types
2. **API client** - Foundation for hooks
3. **Hooks** - Depend on API client and types
4. **Store** - Can be developed in parallel with hooks
5. **SSE hook** - Depends on store and API client
6. **Mocks & Tests** - After core implementation

### Testing Strategy

```typescript
// Example test structure

// 1. Type tests (compile-time)
// Ensure types match backend schemas

// 2. API client tests
describe('newsletterApi', () => {
  it('calls correct endpoints', async () => {
    // Mock axios
    // Verify URL, method, params
  });
});

// 3. Hook tests
describe('useNewsletters', () => {
  it('fetches newsletters', async () => {
    // Use React Query test utils
    // Mock API response
  });
});

// 4. Store tests
describe('newsletterStore', () => {
  it('manages article selection', () => {
    // Test Zustand store actions
  });
});

// 5. SSE tests
describe('useWorkflowSSE', () => {
  it('handles status events', () => {
    // Mock EventSource
    // Dispatch events
    // Verify store updates
  });
});
```

---

## Dependencies

### Package Requirements

The following packages are already in the codebase:
- `@tanstack/react-query` - Server state management
- `zustand` - Client state management
- `axios` - HTTP client

No new packages required for Phase 12.

### Backend Dependencies

Phase 12 requires all Phase 11 endpoints to be functional:
- `/newsletters/*` - Newsletter CRUD
- `/workflows/*` - HITL workflow management
- `/campaigns/*` - Campaign management
- `/subscribers/*` - Subscriber management
- `/templates/*` - Template management
- `/analytics/*` - Analytics endpoints

---

## Verification Checklist

- [ ] All TypeScript types compile without errors
- [ ] API client methods match backend endpoints exactly
- [ ] React Query hooks handle loading, error, and success states
- [ ] Zustand store persists UI preferences correctly
- [ ] SSE connection handles reconnection gracefully
- [ ] MSW mocks work for development/testing
- [ ] Unit tests cover critical paths
- [ ] Integration with existing frontend patterns (client.ts, auth)

---

## Notes

### Backend Schema Alignment

Ensure TypeScript types match backend Pydantic schemas exactly. Key mappings:

| Backend (Python) | Frontend (TypeScript) |
|------------------|----------------------|
| `datetime` | `string` (ISO 8601) |
| `Optional[str]` | `string \| undefined` |
| `List[str]` | `string[]` |
| `Dict[str, Any]` | `Record<string, unknown>` |

### SSE Event Format

The backend SSE endpoint uses this format:
```
event: status
data: {"workflow_id": "...", "status": "running", ...}

event: checkpoint
data: {"checkpoint_id": "...", ...}

event: complete
data: {"status": "completed"}

event: done
data: {}
```

### React Query Cache Strategy

- **Newsletters, Campaigns, Subscribers, Templates**: Cached indefinitely, invalidated on mutation
- **Workflows**: Short staleTime (2s) for running workflows, longer for completed
- **Analytics**: 1 minute staleTime for dashboard, longer for historical data

---

## Related Documentation

- [Phase 11: API Endpoints](./phase11-api-endpoints.md)
- [Phase 13: Frontend Components](../issues/newsletter/Phase13.md) (Next)
- [Phase 14: Frontend Pages](../issues/newsletter/Phase14.md)
