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
  NewsletterUpdateRequest,
  ListParams,
  // Workflow
  WorkflowState,
  ApproveCheckpointRequest,
  EditCheckpointRequest,
  RejectCheckpointRequest,
  GenerateWorkflowRequest,
  GenerateWorkflowResponse,
  // Campaign
  Campaign,
  CreateCampaignRequest,
  UpdateCampaignRequest,
  ScheduleCampaignRequest,
  // Subscriber
  Subscriber,
  CreateSubscriberRequest,
  UpdateSubscriberRequest,
  BulkImportRequest,
  ImportResult,
  SubscriberListParams,
  // Template
  Template,
  CreateTemplateRequest,
  UpdateTemplateRequest,
  TemplatePreviewRequest,
  TemplatePreviewResponse,
  TemplateListParams,
  // Analytics
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

/**
 * Hook to fetch Newsletter platform status
 */
export function useNewsletterStatus() {
  return useQuery({
    queryKey: newsletterKeys.status(),
    queryFn: newsletterApi.getStatus,
    staleTime: 30000,
  });
}

/**
 * Hook to fetch Newsletter agents
 */
export function useNewsletterAgents() {
  return useQuery({
    queryKey: newsletterKeys.agents(),
    queryFn: newsletterApi.getAgents,
  });
}

// ============================================================================
// RESEARCH HOOKS (Phase 6)
// ============================================================================

/**
 * Hook to research content by topics
 */
export function useResearch() {
  return useMutation<ResearchResponse, Error, ResearchRequest>({
    mutationFn: newsletterApi.research,
  });
}

/**
 * Hook to research content using custom prompt
 */
export function useResearchCustom() {
  return useMutation<ResearchResponse, Error, CustomResearchRequest>({
    mutationFn: newsletterApi.researchCustom,
  });
}

/**
 * Hook to get trending content
 */
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

/**
 * Hook to generate newsletter content from articles
 */
export function useGenerateContent() {
  return useMutation<GenerateResponse, Error, GenerateRequest>({
    mutationFn: newsletterApi.generateContent,
  });
}

// Legacy alias for backward compatibility
export const useGenerateNewsletter = useGenerateContent;

// ============================================================================
// NEWSLETTER HOOKS (Phase 11)
// ============================================================================

/**
 * Hook to list newsletters with pagination
 */
export function useNewsletters(params?: ListParams) {
  return useQuery({
    queryKey: newsletterKeys.newslettersList(params),
    queryFn: () => newsletterApi.listNewsletters(params),
  });
}

/**
 * Hook to get a single newsletter by ID
 */
export function useNewsletter(id: string) {
  return useQuery({
    queryKey: newsletterKeys.newsletterDetail(id),
    queryFn: () => newsletterApi.getNewsletter(id),
    enabled: !!id,
  });
}

/**
 * Hook to update a newsletter
 */
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

/**
 * Hook to delete a newsletter
 */
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

/**
 * Hook to start a new newsletter generation workflow
 */
export function useGenerateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation<GenerateWorkflowResponse, Error, GenerateWorkflowRequest>({
    mutationFn: newsletterApi.generateNewsletter,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.workflows() });
    },
  });
}

/**
 * Hook to list workflows with optional status filter
 */
export function useWorkflows(status?: string) {
  return useQuery({
    queryKey: newsletterKeys.workflowsList(status),
    queryFn: () => newsletterApi.listWorkflows(status),
  });
}

/**
 * Hook to get a single workflow by ID with auto-polling when running
 */
export function useWorkflow(workflowId: string) {
  return useQuery({
    queryKey: newsletterKeys.workflowDetail(workflowId),
    queryFn: () => newsletterApi.getWorkflow(workflowId),
    enabled: !!workflowId,
    refetchInterval: (query) => {
      // Poll every 2 seconds while workflow is running
      const data = query.state.data;
      if (data?.status === 'running') return 2000;
      return false;
    },
  });
}

/**
 * Hook to get the current checkpoint for a workflow
 */
export function useWorkflowCheckpoint(workflowId: string) {
  return useQuery({
    queryKey: newsletterKeys.workflowCheckpoint(workflowId),
    queryFn: () => newsletterApi.getCheckpoint(workflowId),
    enabled: !!workflowId,
    retry: false, // Don't retry on 404 (no checkpoint)
  });
}

/**
 * Hook to get workflow execution history
 */
export function useWorkflowHistory(workflowId: string) {
  return useQuery({
    queryKey: newsletterKeys.workflowHistory(workflowId),
    queryFn: () => newsletterApi.getWorkflowHistory(workflowId),
    enabled: !!workflowId,
  });
}

/**
 * Hook to approve a checkpoint
 */
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

/**
 * Hook to edit checkpoint data and continue
 */
export function useEditCheckpoint() {
  const queryClient = useQueryClient();

  return useMutation<WorkflowState, Error, { workflowId: string; request: EditCheckpointRequest }>({
    mutationFn: ({ workflowId, request }) => newsletterApi.editCheckpoint(workflowId, request),
    onSuccess: (workflow) => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.workflowDetail(workflow.workflow_id) });
      queryClient.invalidateQueries({ queryKey: newsletterKeys.workflowCheckpoint(workflow.workflow_id) });
    },
  });
}

/**
 * Hook to reject checkpoint and re-run
 */
export function useRejectCheckpoint() {
  const queryClient = useQueryClient();

  return useMutation<WorkflowState, Error, { workflowId: string; request: RejectCheckpointRequest }>({
    mutationFn: ({ workflowId, request }) => newsletterApi.rejectCheckpoint(workflowId, request),
    onSuccess: (workflow) => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.workflowDetail(workflow.workflow_id) });
      queryClient.invalidateQueries({ queryKey: newsletterKeys.workflowCheckpoint(workflow.workflow_id) });
    },
  });
}

/**
 * Hook to cancel a running workflow
 */
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

/**
 * Hook to list campaigns with pagination
 */
export function useCampaigns(params?: ListParams) {
  return useQuery({
    queryKey: newsletterKeys.campaignsList(params),
    queryFn: () => newsletterApi.listCampaigns(params),
  });
}

/**
 * Hook to get a single campaign by ID
 */
export function useCampaign(id: string) {
  return useQuery({
    queryKey: newsletterKeys.campaignDetail(id),
    queryFn: () => newsletterApi.getCampaign(id),
    enabled: !!id,
  });
}

/**
 * Hook to get campaign stats/analytics
 */
export function useCampaignStats(id: string) {
  return useQuery({
    queryKey: newsletterKeys.campaignAnalytics(id),
    queryFn: async () => {
      // Use the campaign's own analytics from the detail endpoint
      const campaign = await newsletterApi.getCampaign(id);
      return campaign.analytics;
    },
    enabled: !!id,
  });
}

/**
 * Hook to create a new campaign
 */
export function useCreateCampaign() {
  const queryClient = useQueryClient();

  return useMutation<Campaign, Error, CreateCampaignRequest>({
    mutationFn: newsletterApi.createCampaign,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.campaigns() });
    },
  });
}

/**
 * Hook to update a campaign
 */
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

/**
 * Hook to delete a campaign
 */
export function useDeleteCampaign() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: newsletterApi.deleteCampaign,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.campaigns() });
    },
  });
}

/**
 * Hook to send a campaign immediately
 */
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

/**
 * Hook to schedule a campaign
 */
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

/**
 * Hook to list subscribers with pagination and filters
 */
export function useSubscribers(params?: SubscriberListParams) {
  return useQuery({
    queryKey: newsletterKeys.subscribersList(params),
    queryFn: () => newsletterApi.listSubscribers(params),
  });
}

/**
 * Hook to get a single subscriber by ID
 */
export function useSubscriber(id: string) {
  return useQuery({
    queryKey: newsletterKeys.subscriberDetail(id),
    queryFn: () => newsletterApi.getSubscriber(id),
    enabled: !!id,
  });
}

/**
 * Hook to create a new subscriber
 */
export function useCreateSubscriber() {
  const queryClient = useQueryClient();

  return useMutation<Subscriber, Error, CreateSubscriberRequest>({
    mutationFn: newsletterApi.createSubscriber,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.subscribers() });
    },
  });
}

/**
 * Hook to update a subscriber
 */
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

/**
 * Hook to delete a subscriber
 */
export function useDeleteSubscriber() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: newsletterApi.deleteSubscriber,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.subscribers() });
    },
  });
}

/**
 * Hook to bulk import subscribers via JSON
 */
export function useImportSubscribers() {
  const queryClient = useQueryClient();

  return useMutation<ImportResult, Error, BulkImportRequest>({
    mutationFn: newsletterApi.importSubscribers,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.subscribers() });
    },
  });
}

/**
 * Hook to bulk import subscribers via CSV file
 */
export function useImportSubscribersCSV() {
  const queryClient = useQueryClient();

  return useMutation<ImportResult, Error, { file: File; sendWelcome?: boolean }>({
    mutationFn: ({ file, sendWelcome }) => newsletterApi.importSubscribersCSV(file, sendWelcome),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.subscribers() });
    },
  });
}

/**
 * Hook to unsubscribe a subscriber
 */
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

/**
 * Hook to resubscribe a subscriber
 */
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

/**
 * Hook to list templates with pagination and filters
 */
export function useTemplates(params?: TemplateListParams) {
  return useQuery({
    queryKey: newsletterKeys.templatesList(params),
    queryFn: () => newsletterApi.listTemplates(params),
  });
}

/**
 * Hook to get a single template by ID
 */
export function useTemplate(id: string) {
  return useQuery({
    queryKey: newsletterKeys.templateDetail(id),
    queryFn: () => newsletterApi.getTemplate(id),
    enabled: !!id,
  });
}

/**
 * Hook to create a new template
 */
export function useCreateTemplate() {
  const queryClient = useQueryClient();

  return useMutation<Template, Error, CreateTemplateRequest>({
    mutationFn: newsletterApi.createTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.templates() });
    },
  });
}

/**
 * Hook to update a template
 */
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

/**
 * Hook to delete a template
 */
export function useDeleteTemplate() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: newsletterApi.deleteTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.templates() });
    },
  });
}

/**
 * Hook to duplicate a template
 */
export function useDuplicateTemplate() {
  const queryClient = useQueryClient();

  return useMutation<Template, Error, string>({
    mutationFn: newsletterApi.duplicateTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.templates() });
    },
  });
}

/**
 * Hook to set a template as default
 */
export function useSetDefaultTemplate() {
  const queryClient = useQueryClient();

  return useMutation<Template, Error, string>({
    mutationFn: newsletterApi.setDefaultTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: newsletterKeys.templates() });
    },
  });
}

/**
 * Hook to preview a template with variables
 */
export function usePreviewTemplate() {
  return useMutation<TemplatePreviewResponse, Error, { id: string; data: TemplatePreviewRequest }>({
    mutationFn: ({ id, data }) => newsletterApi.previewTemplate(id, data),
  });
}

// ============================================================================
// ANALYTICS HOOKS (Phase 11)
// ============================================================================

/**
 * Hook to get dashboard metrics
 */
export function useDashboard() {
  return useQuery({
    queryKey: newsletterKeys.dashboard(),
    queryFn: newsletterApi.getDashboard,
    staleTime: 60000, // 1 minute
  });
}

/**
 * Hook to get campaign analytics
 */
export function useCampaignAnalytics(campaignId: string) {
  return useQuery({
    queryKey: newsletterKeys.campaignAnalytics(campaignId),
    queryFn: () => newsletterApi.getCampaignAnalytics(campaignId),
    enabled: !!campaignId,
  });
}

/**
 * Hook to get engagement metrics over time
 */
export function useEngagementMetrics(period: 'day' | 'week' | 'month' = 'week') {
  return useQuery({
    queryKey: newsletterKeys.engagement(period),
    queryFn: () => newsletterApi.getEngagementMetrics(period),
  });
}

/**
 * Hook to get subscriber analytics
 */
export function useSubscriberAnalytics() {
  return useQuery({
    queryKey: newsletterKeys.subscriberAnalytics(),
    queryFn: newsletterApi.getSubscriberAnalytics,
  });
}

/**
 * Hook to export analytics data
 */
export function useExportAnalytics() {
  return useMutation<Blob, Error, AnalyticsExportRequest>({
    mutationFn: newsletterApi.exportAnalytics,
  });
}
