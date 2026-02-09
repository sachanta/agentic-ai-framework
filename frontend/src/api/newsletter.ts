/**
 * Newsletter Platform API Client
 *
 * Complete API client for newsletter platform operations.
 * Covers all Phase 11 endpoints with proper typing.
 */
import { apiClient } from './client';
import type {
  // Research & Writing (existing)
  ResearchRequest,
  CustomResearchRequest,
  ResearchResponse,
  GenerateRequest,
  GenerateResponse,
  NewsletterStatus,
  NewsletterAgent,
  // Newsletter entity
  Newsletter,
  NewsletterListResponse,
  NewsletterUpdateRequest,
  // Workflow
  WorkflowState,
  WorkflowListResponse,
  Checkpoint,
  ApproveCheckpointRequest,
  EditCheckpointRequest,
  RejectCheckpointRequest,
  WorkflowHistoryResponse,
  GenerateWorkflowRequest,
  GenerateWorkflowResponse,
  // Campaign
  Campaign,
  CampaignListResponse,
  CreateCampaignRequest,
  UpdateCampaignRequest,
  ScheduleCampaignRequest,
  CampaignAnalytics,
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
  EngagementMetrics,
  SubscriberAnalyticsData,
  AnalyticsExportRequest,
  // Common
  ListParams,
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

  getStatus: async (): Promise<NewsletterStatus> => {
    const response = await apiClient.get<NewsletterStatus>(`${BASE_PATH}/status`);
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
    request: EditCheckpointRequest
  ): Promise<WorkflowState> => {
    const response = await apiClient.post<WorkflowState>(
      `${BASE_PATH}/workflows/${workflowId}/edit`,
      request
    );
    return response.data;
  },

  rejectCheckpoint: async (
    workflowId: string,
    request: RejectCheckpointRequest
  ): Promise<WorkflowState> => {
    const response = await apiClient.post<WorkflowState>(
      `${BASE_PATH}/workflows/${workflowId}/reject`,
      request
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
   * Note: Returns full URL for EventSource usage
   */
  getWorkflowStreamUrl: (workflowId: string): string => {
    const baseUrl = apiClient.defaults.baseURL || '';
    return `${baseUrl}${BASE_PATH}/workflows/${workflowId}/stream`;
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

  getSubscriberAnalytics: async (): Promise<SubscriberAnalyticsData> => {
    const response = await apiClient.get<SubscriberAnalyticsData>(
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

export default newsletterApi;
