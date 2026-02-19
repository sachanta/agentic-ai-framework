/**
 * Main Newsletter app component
 *
 * Integrates dashboard, generation panel, and HITL workflow UI
 */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';
import { AppStatusBadge } from '../AppStatusBadge';
import { NewsletterDashboard } from './NewsletterDashboard';
import { GeneratePanel } from './GeneratePanel';
import { ResearchPanel } from './ResearchPanel';
import { ArticleResults } from './ArticleResults';
import { WritingPanel } from './WritingPanel';
import { NewsletterPreview } from './NewsletterPreview';
import {
  WorkflowTracker,
  ArticleReview,
  ContentReview,
  SubjectReview,
  FinalApproval,
  WorkflowHistory,
} from './workflow';
import {
  useNewsletterStatus,
  useNewsletterAgents,
  useResearch,
  useResearchCustom,
  useGenerateContent,
  useGenerateWorkflow,
  useWorkflow,
  useWorkflowCheckpoint,
  useWorkflowHistory,
  useApproveCheckpoint,
  useRejectCheckpoint,
  useCancelWorkflow,
} from '@/hooks/useNewsletter';
import { useWorkflowSSE } from '@/hooks/useWorkflowSSE';
import { useWorkflowState, useArticleSelection } from '@/store/newsletterStore';
import {
  ArrowLeft,
  Newspaper,
  Bot,
  Info,
  LayoutDashboard,
  Wand2,
  FileText,
  GitBranch,
  X,
} from 'lucide-react';
import type { Article, ResearchResponse, GenerateResponse, WritingTone, CheckpointAction } from '@/types/newsletter';

type AppView = 'dashboard' | 'generate' | 'manual' | 'workflow';
type ManualPhase = 'research' | 'writing' | 'preview';

export function NewsletterApp() {
  const { toast } = useToast();

  // Workflow state from store (read first so we can set initial view)
  const {
    activeWorkflowId,
    setActiveWorkflow,
    setWorkflowStatus,
    setCheckpointData,
    clearWorkflowState,
  } = useWorkflowState();

  // View management — auto-open workflow tab if a workflow was active before refresh
  const [view, setView] = useState<AppView>(activeWorkflowId ? 'workflow' : 'dashboard');
  const [manualPhase, setManualPhase] = useState<ManualPhase>('research');

  // Article selection from store
  const { selectedArticles, setSelectedArticles, clearSelectedArticles } = useArticleSelection();

  // Manual mode state
  const [researchResult, setResearchResult] = useState<ResearchResponse | null>(null);
  const [tone, setTone] = useState<WritingTone>('professional');
  const [generatedNewsletter, setGeneratedNewsletter] = useState<GenerateResponse | null>(null);

  // Loading action tracking
  const [loadingAction, setLoadingAction] = useState<CheckpointAction | null>(null);

  // Queries and mutations
  const { data: status } = useNewsletterStatus();
  const { data: agents } = useNewsletterAgents();

  // Manual mode mutations
  const researchMutation = useResearch();
  const researchCustomMutation = useResearchCustom();
  const generateContentMutation = useGenerateContent();

  // Workflow mutations
  const generateWorkflowMutation = useGenerateWorkflow();
  const approveMutation = useApproveCheckpoint();
  const rejectMutation = useRejectCheckpoint();
  const cancelMutation = useCancelWorkflow();

  // Workflow queries (only when workflow is active)
  const { data: workflowData } = useWorkflow(activeWorkflowId || '');
  const { data: checkpoint } = useWorkflowCheckpoint(activeWorkflowId || '');
  const { data: history } = useWorkflowHistory(activeWorkflowId || '');

  // SSE connection for real-time updates
  useWorkflowSSE(activeWorkflowId, {
    onStatus: (event) => {
      setWorkflowStatus(event.status);
    },
    onCheckpoint: (event) => {
      setCheckpointData(event);
      toast({
        title: 'Checkpoint Ready',
        description: `${event.title} - Your review is needed`,
      });
    },
    onComplete: (event) => {
      if (event.status === 'completed') {
        toast({
          title: 'Newsletter Complete!',
          description: 'Your newsletter has been generated successfully.',
        });
      }
      setView('dashboard');
      clearWorkflowState();
    },
    onError: (event) => {
      toast({
        title: 'Workflow Error',
        description: event.error,
        variant: 'destructive',
      });
    },
  });

  // Update workflow status when data changes
  useEffect(() => {
    if (workflowData) {
      setWorkflowStatus(workflowData.status);
    }
  }, [workflowData, setWorkflowStatus]);

  const isResearching = researchMutation.isPending || researchCustomMutation.isPending;
  const isGenerating = generateContentMutation.isPending;
  const isWorkflowLoading = generateWorkflowMutation.isPending || approveMutation.isPending || rejectMutation.isPending;

  // ============================================================================
  // WORKFLOW MODE HANDLERS
  // ============================================================================

  const handleStartWorkflow = (options: {
    topics: string[];
    tone: string;
    maxArticles: number;
    customPrompt?: string;
    includeRag: boolean;
  }) => {
    generateWorkflowMutation.mutate(
      {
        topics: options.topics,
        tone: options.tone,
        max_articles: options.maxArticles,
        include_rag: options.includeRag,
      },
      {
        onSuccess: (data) => {
          setActiveWorkflow(data.workflow_id);
          setView('workflow');
          toast({
            title: 'Workflow Started',
            description: 'Newsletter generation is in progress...',
          });
        },
        onError: (error) => {
          toast({
            title: 'Failed to Start',
            description: error.message,
            variant: 'destructive',
          });
        },
      }
    );
  };

  const handleApproveCheckpoint = (data?: Record<string, unknown>, feedback?: string) => {
    if (!activeWorkflowId || !checkpoint) return;

    setLoadingAction('approve');
    approveMutation.mutate(
      {
        workflowId: activeWorkflowId,
        request: {
          checkpoint_id: checkpoint.checkpoint_id,
          action: 'approve',
          modifications: data,
          feedback,
        },
      },
      {
        onSuccess: () => {
          setLoadingAction(null);
        },
        onError: (error) => {
          setLoadingAction(null);
          toast({
            title: 'Approval Failed',
            description: error.message,
            variant: 'destructive',
          });
        },
      }
    );
  };

  const handleRejectCheckpoint = (feedback?: string) => {
    if (!activeWorkflowId || !checkpoint) return;

    setLoadingAction('reject');
    rejectMutation.mutate(
      {
        workflowId: activeWorkflowId,
        request: {
          checkpoint_id: checkpoint.checkpoint_id,
          feedback,
        },
      },
      {
        onSuccess: () => {
          setLoadingAction(null);
        },
        onError: (error) => {
          setLoadingAction(null);
          toast({
            title: 'Rejection Failed',
            description: error.message,
            variant: 'destructive',
          });
        },
      }
    );
  };

  const handleCancelWorkflow = () => {
    if (!activeWorkflowId) return;

    cancelMutation.mutate(activeWorkflowId, {
      onSuccess: () => {
        clearWorkflowState();
        setView('dashboard');
        toast({
          title: 'Workflow Cancelled',
          description: 'The newsletter generation has been cancelled.',
        });
      },
    });
  };

  // ============================================================================
  // MANUAL MODE HANDLERS
  // ============================================================================

  const handleResearch = (
    topics: string[],
    customPrompt: string | null,
    maxResults: number,
    includeSummaries: boolean
  ) => {
    setResearchResult(null);
    clearSelectedArticles();
    setGeneratedNewsletter(null);
    setManualPhase('research');

    const mutation = customPrompt ? researchCustomMutation : researchMutation;
    const request = customPrompt
      ? { prompt: customPrompt, max_results: maxResults, include_summaries: includeSummaries }
      : { topics, max_results: maxResults, include_summaries: includeSummaries };

    mutation.mutate(request as any, {
      onSuccess: (data) => setResearchResult(data),
    });
  };

  const handleArticleSelect = (article: Article, selected: boolean) => {
    if (selected) {
      setSelectedArticles([...selectedArticles, article]);
    } else {
      setSelectedArticles(selectedArticles.filter((a) => a.url !== article.url));
    }
  };

  const handleGenerate = () => {
    generateContentMutation.mutate(
      {
        articles: selectedArticles,
        tone,
        include_rag: true,
      },
      {
        onSuccess: (data) => {
          setGeneratedNewsletter(data);
          if (data.success) {
            setManualPhase('preview');
          }
        },
      }
    );
  };

  // ============================================================================
  // RENDER HELPERS
  // ============================================================================

  const renderCheckpointUI = () => {
    if (!checkpoint || !workflowData) return null;

    const checkpointType = checkpoint.checkpoint_type;
    const checkpointData = checkpoint.data;

    switch (checkpointType) {
      case 'research_review':
        return (
          <ArticleReview
            checkpoint={checkpoint}
            articles={(checkpointData.articles as Article[]) || []}
            onApprove={(articles, feedback) => {
              handleApproveCheckpoint({ articles }, feedback);
            }}
            onReject={handleRejectCheckpoint}
            isLoading={isWorkflowLoading}
            loadingAction={loadingAction}
          />
        );

      case 'content_review':
        return (
          <ContentReview
            checkpoint={checkpoint}
            content={(checkpointData.newsletter as any) || {
              content: String(checkpointData.content || ''),
              word_count: Number(checkpointData.word_count || 0),
            }}
            formats={(checkpointData.formats as any) || (checkpointData.html_preview ? { html: String(checkpointData.html_preview) } : undefined)}
            onApprove={(content, feedback) => {
              handleApproveCheckpoint({ content }, feedback);
            }}
            onEdit={(content, feedback) => {
              handleApproveCheckpoint({ content, action: 'edit' }, feedback);
            }}
            onReject={handleRejectCheckpoint}
            isLoading={isWorkflowLoading}
            loadingAction={loadingAction}
          />
        );

      case 'subject_review':
        return (
          <SubjectReview
            checkpoint={checkpoint}
            subjectLines={((checkpointData.subject_lines as any[]) || []).map((s: any) =>
              typeof s === 'string' ? { text: s, style: 'professional' } : { text: s.text || String(s), style: s.style || s.angle || 'professional' }
            )}
            onApprove={(subject, feedback) => {
              handleApproveCheckpoint({ selected_subject: subject }, feedback);
            }}
            onReject={handleRejectCheckpoint}
            isLoading={isWorkflowLoading}
            loadingAction={loadingAction}
          />
        );

      case 'final_review':
        return (
          <FinalApproval
            checkpoint={checkpoint}
            subject={String(checkpointData.subject || '')}
            content={String(checkpointData.preview_html || checkpointData.content || '')}
            formats={(checkpointData.formats as any) || (checkpointData.preview_html ? { html: String(checkpointData.preview_html) } : undefined)}
            articleCount={Number(checkpointData.word_count || workflowData.article_count || 0)}
            recipientCount={Number(checkpointData.recipient_count || 0)}
            onApprove={(scheduleAt, feedback, testRecipients) => {
              handleApproveCheckpoint({ schedule_at: scheduleAt, test_recipients: testRecipients }, feedback);
            }}
            onReject={handleRejectCheckpoint}
            isLoading={isWorkflowLoading}
            loadingAction={loadingAction}
          />
        );

      default:
        return (
          <Card>
            <CardContent className="py-8 text-center">
              <p className="text-muted-foreground">
                Unknown checkpoint type: {checkpointType}
              </p>
            </CardContent>
          </Card>
        );
    }
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link to="/apps">
            <ArrowLeft className="h-5 w-5" />
          </Link>
        </Button>
        <div className="flex items-center gap-4 flex-1">
          <div className="p-3 rounded-lg bg-primary/10">
            <Newspaper className="h-8 w-8 text-primary" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">Newsletter</h1>
              {status && <AppStatusBadge status={status.status} />}
            </div>
            <p className="text-muted-foreground">
              AI-powered newsletter generation with human-in-the-loop
            </p>
          </div>

          {/* Cancel workflow button */}
          {view === 'workflow' && activeWorkflowId && (
            <Button
              variant="outline"
              onClick={handleCancelWorkflow}
              disabled={cancelMutation.isPending}
            >
              <X className="h-4 w-4 mr-2" />
              Cancel Workflow
            </Button>
          )}
        </div>
      </div>

      {/* Dashboard / Generate / Manual / Workflow views */}
      <Tabs value={view} onValueChange={(v) => setView(v as AppView)} className="w-full">
        <TabsList>
          <TabsTrigger value="dashboard" className="flex items-center gap-2">
            <LayoutDashboard className="h-4 w-4" />
            Dashboard
          </TabsTrigger>
          <TabsTrigger value="generate" className="flex items-center gap-2">
            <Wand2 className="h-4 w-4" />
            Generate
          </TabsTrigger>
          <TabsTrigger value="manual" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Manual Mode
          </TabsTrigger>
          <TabsTrigger value="workflow" className="flex items-center gap-2">
            <GitBranch className="h-4 w-4" />
            Workflow
          </TabsTrigger>
        </TabsList>

          <TabsContent value="dashboard" className="mt-6">
            <NewsletterDashboard onStartGeneration={() => setView('generate')} />
          </TabsContent>

          <TabsContent value="generate" className="mt-6">
            <div className="grid gap-6 lg:grid-cols-3">
              <div className="lg:col-span-2">
                <GeneratePanel
                  onGenerate={handleStartWorkflow}
                  isLoading={generateWorkflowMutation.isPending}
                />
              </div>
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Info className="h-4 w-4" />
                      How It Works
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="text-sm text-muted-foreground space-y-3">
                    <div className="space-y-2">
                      <p className="font-medium text-foreground">1. Configure</p>
                      <p>Set topics, tone, and preferences for your newsletter.</p>
                    </div>
                    <div className="space-y-2">
                      <p className="font-medium text-foreground">2. Review</p>
                      <p>AI researches and you approve selected articles.</p>
                    </div>
                    <div className="space-y-2">
                      <p className="font-medium text-foreground">3. Generate</p>
                      <p>AI writes content, you review and edit.</p>
                    </div>
                    <div className="space-y-2">
                      <p className="font-medium text-foreground">4. Send</p>
                      <p>Final approval and send or schedule.</p>
                    </div>
                  </CardContent>
                </Card>

                {/* LLM Info */}
                {status && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-base">
                        <Bot className="h-4 w-4" />
                        LLM Configuration
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="text-sm">
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Provider</span>
                          <span className="font-medium">{status.llm_provider}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Model</span>
                          <span className="font-medium">{status.llm_model}</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          </TabsContent>

          <TabsContent value="manual" className="mt-6">
            {/* Manual mode - existing research/writing flow */}
            {manualPhase === 'preview' && generatedNewsletter ? (
              <div className="space-y-6">
                <Button variant="outline" onClick={() => setManualPhase('research')}>
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Research
                </Button>
                <NewsletterPreview
                  result={generatedNewsletter}
                  onRegenerate={handleGenerate}
                  isRegenerating={isGenerating}
                />
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                  <ResearchPanel onResearch={handleResearch} isLoading={isResearching} />
                  <WritingPanel
                    selectedArticles={selectedArticles}
                    tone={tone}
                    onToneChange={setTone}
                    onGenerate={handleGenerate}
                    onClearSelection={clearSelectedArticles}
                    isGenerating={isGenerating}
                  />
                  <ArticleResults
                    articles={researchResult?.articles || null}
                    metadata={researchResult?.metadata || null}
                    isLoading={isResearching}
                    error={researchResult?.error}
                    selectedArticles={selectedArticles}
                    onArticleSelect={handleArticleSelect}
                    onSelectAll={() => researchResult?.articles && setSelectedArticles([...researchResult.articles])}
                    onClearSelection={clearSelectedArticles}
                  />
                </div>
                <div className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-base">
                        <Bot className="h-4 w-4" />
                        Agents
                      </CardTitle>
                      <CardDescription>Agents powering this platform</CardDescription>
                    </CardHeader>
                    <CardContent>
                      {agents && agents.length > 0 ? (
                        <div className="space-y-3">
                          {agents.map((agent, index) => (
                            <div key={agent.id}>
                              {index > 0 && <Separator className="my-3" />}
                              <div>
                                <div className="flex items-center justify-between">
                                  <span className="font-medium text-sm">{agent.name}</span>
                                  <AppStatusBadge status={agent.status} size="sm" />
                                </div>
                                <p className="text-xs text-muted-foreground mt-1">
                                  {agent.description}
                                </p>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-muted-foreground text-center py-2">
                          Loading agents...
                        </p>
                      )}
                    </CardContent>
                  </Card>
                </div>
              </div>
            )}
          </TabsContent>

          <TabsContent value="workflow" className="mt-6">
            {activeWorkflowId ? (
              <div className="space-y-6">
                {/* Workflow tracker */}
                <Card>
                  <CardContent className="pt-6">
                    <WorkflowTracker
                      currentStep={workflowData?.current_step || null}
                      completedSteps={workflowData?.checkpoints_completed || []}
                      status={workflowData?.status || null}
                    />
                  </CardContent>
                </Card>

                {/* Workflow info bar */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Card>
                    <CardContent className="p-3 flex items-center justify-between">
                      <span className="text-xs text-muted-foreground">ID</span>
                      <span className="font-mono text-xs">{activeWorkflowId.slice(0, 12)}...</span>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-3 flex items-center justify-between">
                      <span className="text-xs text-muted-foreground">Topics</span>
                      <span className="text-sm font-medium">{workflowData?.topics?.length || 0}</span>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-3 flex items-center justify-between">
                      <span className="text-xs text-muted-foreground">Tone</span>
                      <span className="text-sm font-medium capitalize">{workflowData?.tone || '-'}</span>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-3 flex items-center justify-between">
                      <span className="text-xs text-muted-foreground">Articles</span>
                      <span className="text-sm font-medium">{workflowData?.article_count || 0}</span>
                    </CardContent>
                  </Card>
                </div>

                {/* Checkpoint UI — full width */}
                <div className="w-full">
                  {workflowData?.status === 'awaiting_approval' && checkpoint ? (
                    renderCheckpointUI()
                  ) : workflowData?.status === 'running' ? (
                    <Card>
                      <CardContent className="py-12 text-center">
                        <div className="animate-pulse">
                          <Wand2 className="h-12 w-12 mx-auto text-primary mb-4" />
                          <p className="text-lg font-medium">Processing...</p>
                          <p className="text-sm text-muted-foreground mt-1">
                            {workflowData?.current_step?.replace(/_/g, ' ') || 'Starting workflow'}
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  ) : (
                    <Card>
                      <CardContent className="py-8 text-center text-muted-foreground">
                        Workflow status: {workflowData?.status || 'Loading...'}
                      </CardContent>
                    </Card>
                  )}
                </div>

                {/* History — full width, collapsed */}
                <WorkflowHistory history={history?.history || []} />
              </div>
            ) : (
              <Card>
                <CardContent className="py-12 text-center">
                  <GitBranch className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-lg font-medium">No Active Workflow</p>
                  <p className="text-sm text-muted-foreground mt-1 mb-4">
                    Start a new workflow from the Generate tab to begin newsletter creation.
                  </p>
                  <Button variant="outline" onClick={() => setView('generate')}>
                    <Wand2 className="h-4 w-4 mr-2" />
                    Go to Generate
                  </Button>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
    </div>
  );
}

export default NewsletterApp;
