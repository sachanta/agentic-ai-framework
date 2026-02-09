/**
 * Workflow Detail Page
 *
 * View and manage a specific workflow
 */
import { useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/components/ui/use-toast';
import {
  ArrowLeft,
  X,
  Wand2,
} from 'lucide-react';
import {
  useWorkflow,
  useWorkflowCheckpoint,
  useWorkflowHistory,
  useApproveCheckpoint,
  useRejectCheckpoint,
  useCancelWorkflow,
} from '@/hooks/useNewsletter';
import { useWorkflowSSE } from '@/hooks/useWorkflowSSE';
import { useWorkflowState } from '@/store/newsletterStore';
import {
  WorkflowTracker,
  ArticleReview,
  ContentReview,
  FinalApproval,
  WorkflowHistory,
} from '@/components/apps/newsletter/workflow';
import type { Article, CheckpointAction } from '@/types/newsletter';
import { useState } from 'react';

export function WorkflowPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  // Workflow state from store
  const { setWorkflowStatus, setCheckpointData, clearWorkflowState } = useWorkflowState();
  const [loadingAction, setLoadingAction] = useState<CheckpointAction | null>(null);

  // Queries
  const { data: workflowData, isLoading } = useWorkflow(id || '');
  const { data: checkpoint } = useWorkflowCheckpoint(id || '');
  const { data: history } = useWorkflowHistory(id || '');

  // Mutations
  const approveMutation = useApproveCheckpoint();
  const rejectMutation = useRejectCheckpoint();
  const cancelMutation = useCancelWorkflow();

  // SSE connection for real-time updates
  useWorkflowSSE(id ?? null, {
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
      clearWorkflowState();
      navigate('/apps/newsletter');
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

  const handleApproveCheckpoint = (data?: Record<string, unknown>, feedback?: string) => {
    if (!id || !checkpoint) return;

    setLoadingAction('approve');
    approveMutation.mutate(
      {
        workflowId: id,
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
    if (!id || !checkpoint) return;

    setLoadingAction('reject');
    rejectMutation.mutate(
      {
        workflowId: id,
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
    if (!id) return;

    cancelMutation.mutate(id, {
      onSuccess: () => {
        clearWorkflowState();
        navigate('/apps/newsletter');
        toast({
          title: 'Workflow Cancelled',
          description: 'The newsletter generation has been cancelled.',
        });
      },
    });
  };

  const isWorkflowLoading = approveMutation.isPending || rejectMutation.isPending;

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
            content={checkpointData.newsletter as any || { content: '', word_count: 0 }}
            formats={checkpointData.formats as any}
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

      case 'final_review':
        return (
          <FinalApproval
            checkpoint={checkpoint}
            subject={String(checkpointData.subject || '')}
            content={String(checkpointData.content || '')}
            formats={checkpointData.formats as any}
            articleCount={workflowData.article_count}
            onApprove={(scheduleAt, feedback) => {
              handleApproveCheckpoint({ schedule_at: scheduleAt }, feedback);
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

  const getStatusBadge = (status: string | undefined) => {
    if (!status) return null;
    const variants: Record<string, 'default' | 'secondary' | 'outline' | 'destructive'> = {
      running: 'default',
      awaiting_approval: 'outline',
      completed: 'default',
      cancelled: 'secondary',
      failed: 'destructive',
    };
    return <Badge variant={variants[status] || 'secondary'}>{status}</Badge>;
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-40" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!workflowData) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" asChild>
          <Link to="/apps/newsletter">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Link>
        </Button>
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-lg font-medium">Workflow not found</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link to="/apps/newsletter">
            <ArrowLeft className="h-5 w-5" />
          </Link>
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">
              Workflow {id?.slice(0, 8)}...
            </h1>
            {getStatusBadge(workflowData.status)}
          </div>
          <p className="text-muted-foreground">
            {workflowData.topics?.join(', ') || 'Newsletter generation'}
          </p>
        </div>
        {(workflowData.status === 'running' || workflowData.status === 'awaiting_approval') && (
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

      {/* Workflow tracker */}
      <Card>
        <CardContent className="pt-6">
          <WorkflowTracker
            currentStep={workflowData.current_step || null}
            completedSteps={workflowData.checkpoints_completed || []}
            status={workflowData.status || null}
          />
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Checkpoint UI */}
        <div className="lg:col-span-2">
          {workflowData.status === 'awaiting_approval' && checkpoint ? (
            renderCheckpointUI()
          ) : workflowData.status === 'running' ? (
            <Card>
              <CardContent className="py-12 text-center">
                <div className="animate-pulse">
                  <Wand2 className="h-12 w-12 mx-auto text-primary mb-4" />
                  <p className="text-lg font-medium">Processing...</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    {workflowData.current_step?.replace(/_/g, ' ') || 'Starting workflow'}
                  </p>
                </div>
              </CardContent>
            </Card>
          ) : workflowData.status === 'completed' ? (
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-lg font-medium text-green-600">Workflow completed!</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Your newsletter has been generated.
                </p>
                <Button className="mt-4" asChild>
                  <Link to="/apps/newsletter">Back to Dashboard</Link>
                </Button>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                Workflow status: {workflowData.status}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <WorkflowHistory history={history?.history || []} />

          {/* Workflow info */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Workflow Details</CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              <div className="flex justify-between">
                <span className="text-muted-foreground">ID</span>
                <span className="font-mono text-xs">{id?.slice(0, 12)}...</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Topics</span>
                <span>{workflowData.topics?.length || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Tone</span>
                <span className="capitalize">{workflowData.tone || '-'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Articles</span>
                <span>{workflowData.article_count || 0}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default WorkflowPage;
