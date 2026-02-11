/**
 * Newsletter Platform types
 */

// Research request/response types
export interface ResearchRequest {
  topics: string[];
  max_results?: number;
  include_summaries?: boolean;
  days_back?: number;
}

export interface CustomResearchRequest {
  prompt: string;
  max_results?: number;
  include_summaries?: boolean;
}

export interface Article {
  title: string;
  url: string;
  source: string;
  content?: string;
  summary?: string;
  key_takeaway?: string;
  published_date?: string;
  score: number;
  relevance_score: number;
  quality_score: number;
  recency_boost: number;
}

export interface ResearchMetadata {
  topics: string[];
  total_found: number;
  after_filter: number;
  source: string;
  cached: boolean;
  message?: string;
}

export interface ResearchResponse {
  success: boolean;
  articles: Article[];
  metadata: ResearchMetadata;
  error?: string;
}

// Platform status types
export interface NewsletterStatus {
  platform_id: string;
  name: string;
  status: string;
  agents: string[];
  version: string;
  llm_provider: string;
  llm_model: string;
}

export interface NewsletterAgent {
  id: string;
  name: string;
  description: string;
  status: string;
}

// Writing request/response types (Phase 7)
export interface GenerateRequest {
  articles: Article[];
  tone: string;
  user_id?: string;
  include_rag?: boolean;
}

export interface SubjectLine {
  text: string;
  style: string;
}

export interface NewsletterContent {
  content: string;
  word_count: number;
}

export interface NewsletterFormats {
  html: string;
  text: string;
  markdown: string;
}

export interface NewsletterSummary {
  bullets: string[];
  raw?: string;
}

export interface GenerateMetadata {
  article_count: number;
  topics: string[];
  tone: string;
  generated_at: string;
  rag_examples_used?: number;
}

export interface GenerateResponse {
  success: boolean;
  newsletter?: NewsletterContent;
  subject_lines: SubjectLine[];
  summary?: NewsletterSummary;
  formats?: NewsletterFormats;
  metadata?: GenerateMetadata;
  error?: string;
}

export type WritingTone = 'professional' | 'casual' | 'formal' | 'enthusiastic';

// ============================================================================
// ENUMS & STATUS TYPES (Phase 12)
// ============================================================================

export type NewsletterEntityStatus = 'draft' | 'pending_review' | 'approved' | 'sent' | 'archived';
export type CampaignStatus = 'draft' | 'scheduled' | 'sending' | 'sent' | 'failed' | 'cancelled';
export type SubscriberStatus = 'active' | 'unsubscribed' | 'bounced' | 'pending';
export type TemplateCategory = 'newsletter' | 'campaign' | 'transactional' | 'custom';
export type WorkflowStepStatus = 'running' | 'awaiting_approval' | 'completed' | 'cancelled' | 'failed';
export type CheckpointAction = 'approve' | 'edit' | 'reject';

// ============================================================================
// NEWSLETTER ENTITY (Phase 11/12)
// ============================================================================

export interface Newsletter {
  id: string;
  user_id: string;
  title: string;
  content: string;
  html_content: string;
  status: NewsletterEntityStatus;
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
  status?: NewsletterEntityStatus;
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
  checkpoint_type: 'research_review' | 'content_review' | 'subject_review' | 'final_review';
  title: string;
  description: string;
  data: CheckpointData;
  actions: CheckpointAction[];
  metadata: Record<string, unknown>;
}

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

export interface EditCheckpointRequest {
  checkpoint_id: string;
  modifications: Record<string, unknown>;
  feedback?: string;
}

export interface RejectCheckpointRequest {
  checkpoint_id: string;
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
  scheduled_at: string;
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

export interface SubscriberAnalyticsData {
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
  offset?: number; // alias for skip
  limit?: number;
  status?: string;
}

export interface SubscriberListParams extends ListParams {
  tag?: string;
  group?: string;
}

export interface CampaignStats {
  sent: number;
  delivered: number;
  opened: number;
  clicked: number;
  bounced: number;
  unsubscribed: number;
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
