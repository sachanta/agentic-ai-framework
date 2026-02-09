/**
 * Newsletter Dashboard Component
 *
 * Main dashboard view showing:
 * - Quick stats (newsletters, campaigns, subscribers)
 * - Active workflows
 * - Recent newsletters
 * - Quick actions
 */
import { Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Newspaper,
  Send,
  Users,
  TrendingUp,
  Plus,
  ArrowRight,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import {
  useDashboard,
  useNewsletters,
  useWorkflows,
} from '@/hooks/useNewsletter';
import type { WorkflowStepStatus } from '@/types/newsletter';

interface NewsletterDashboardProps {
  onStartGeneration: () => void;
}

export function NewsletterDashboard({ onStartGeneration }: NewsletterDashboardProps) {
  const { data: dashboard, isLoading: dashboardLoading } = useDashboard();
  const { data: newsletters, isLoading: newslettersLoading } = useNewsletters({ limit: 5 });
  const { data: workflows, isLoading: workflowsLoading } = useWorkflows();

  // Active workflows (not completed/cancelled/failed)
  const activeWorkflows = workflows?.items.filter(
    (w) => w.status === 'running' || w.status === 'awaiting_approval'
  ) || [];

  return (
    <div className="space-y-6">
      {/* Stats cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Total Newsletters"
          value={dashboard?.newsletters?.total}
          change={dashboard?.newsletters?.growth_rate}
          icon={Newspaper}
          loading={dashboardLoading}
        />
        <StatsCard
          title="Campaigns Sent"
          value={dashboard?.campaigns?.sent_this_month}
          subtitle="this month"
          icon={Send}
          loading={dashboardLoading}
        />
        <StatsCard
          title="Active Subscribers"
          value={dashboard?.subscribers?.active}
          change={dashboard?.subscribers?.new_this_month}
          changeLabel="new"
          icon={Users}
          loading={dashboardLoading}
        />
        <StatsCard
          title="Avg Open Rate"
          value={dashboard?.engagement?.avg_open_rate ? `${(dashboard.engagement.avg_open_rate * 100).toFixed(1)}%` : undefined}
          icon={TrendingUp}
          loading={dashboardLoading}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Active workflows */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle className="text-base">Active Workflows</CardTitle>
              <CardDescription>Newsletters in progress</CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={onStartGeneration}>
              <Plus className="h-4 w-4 mr-1" />
              New
            </Button>
          </CardHeader>
          <CardContent>
            {workflowsLoading ? (
              <div className="space-y-3">
                {[1, 2].map((i) => (
                  <Skeleton key={i} className="h-16 w-full" />
                ))}
              </div>
            ) : activeWorkflows.length > 0 ? (
              <ScrollArea className="h-[200px]">
                <div className="space-y-3">
                  {activeWorkflows.map((workflow) => (
                    <WorkflowCard
                      key={workflow.workflow_id}
                      workflowId={workflow.workflow_id}
                      status={workflow.status}
                      currentStep={workflow.current_step}
                      updatedAt={workflow.updated_at}
                    />
                  ))}
                </div>
              </ScrollArea>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Newspaper className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No active workflows</p>
                <Button
                  variant="link"
                  size="sm"
                  className="mt-2"
                  onClick={onStartGeneration}
                >
                  Start generating a newsletter
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent newsletters */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle className="text-base">Recent Newsletters</CardTitle>
              <CardDescription>Your latest newsletters</CardDescription>
            </div>
            <Button variant="ghost" size="sm" asChild>
              <Link to="/apps/newsletter/newsletters">
                View all
                <ArrowRight className="h-4 w-4 ml-1" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            {newslettersLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : newsletters?.items && newsletters.items.length > 0 ? (
              <ScrollArea className="h-[200px]">
                <div className="space-y-2">
                  {newsletters.items.map((newsletter) => (
                    <div
                      key={newsletter.id}
                      className="flex items-center justify-between p-2 rounded-lg hover:bg-muted transition-colors"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm truncate">
                          {newsletter.title}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {formatDistanceToNow(new Date(newsletter.created_at), { addSuffix: true })}
                        </p>
                      </div>
                      <Badge variant={newsletter.status === 'sent' ? 'default' : 'secondary'}>
                        {newsletter.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Newspaper className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No newsletters yet</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick actions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            <Button variant="outline" className="justify-start" onClick={onStartGeneration}>
              <Plus className="h-4 w-4 mr-2" />
              Generate Newsletter
            </Button>
            <Button variant="outline" className="justify-start" asChild>
              <Link to="/apps/newsletter/campaigns">
                <Send className="h-4 w-4 mr-2" />
                Create Campaign
              </Link>
            </Button>
            <Button variant="outline" className="justify-start" asChild>
              <Link to="/apps/newsletter/subscribers">
                <Users className="h-4 w-4 mr-2" />
                Manage Subscribers
              </Link>
            </Button>
            <Button variant="outline" className="justify-start" asChild>
              <Link to="/apps/newsletter/analytics">
                <TrendingUp className="h-4 w-4 mr-2" />
                View Analytics
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Stats card component
interface StatsCardProps {
  title: string;
  value?: number | string;
  change?: number;
  changeLabel?: string;
  subtitle?: string;
  icon: React.ComponentType<{ className?: string }>;
  loading?: boolean;
}

function StatsCard({
  title,
  value,
  change,
  changeLabel = 'vs last month',
  subtitle,
  icon: Icon,
  loading,
}: StatsCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-8 w-20" />
        ) : (
          <>
            <div className="text-2xl font-bold">{value ?? '-'}</div>
            {(change !== undefined || subtitle) && (
              <p className="text-xs text-muted-foreground">
                {change !== undefined ? (
                  <>
                    <span className={change >= 0 ? 'text-green-600' : 'text-red-600'}>
                      {change >= 0 ? '+' : ''}{change}
                    </span>
                    {' '}{changeLabel}
                  </>
                ) : (
                  subtitle
                )}
              </p>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

// Workflow card component
interface WorkflowCardProps {
  workflowId: string;
  status: WorkflowStepStatus;
  currentStep: string | null;
  updatedAt: string;
}

function WorkflowCard({ workflowId, status, currentStep, updatedAt }: WorkflowCardProps) {
  const getStatusIcon = () => {
    switch (status) {
      case 'running':
        return <Loader2 className="h-4 w-4 text-primary animate-spin" />;
      case 'awaiting_approval':
        return <AlertCircle className="h-4 w-4 text-amber-500" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      default:
        return <Clock className="h-4 w-4 text-muted-foreground" />;
    }
  };

  return (
    <Link
      to={`/apps/newsletter/workflow/${workflowId}`}
      className="flex items-center gap-3 p-3 rounded-lg border hover:bg-muted transition-colors"
    >
      {getStatusIcon()}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm truncate">
            Workflow {workflowId.slice(0, 8)}...
          </span>
          <Badge
            variant={status === 'awaiting_approval' ? 'outline' : 'secondary'}
            className={status === 'awaiting_approval' ? 'text-amber-600 border-amber-600' : ''}
          >
            {status === 'awaiting_approval' ? 'Needs Review' : status}
          </Badge>
        </div>
        <p className="text-xs text-muted-foreground">
          {currentStep ? `Step: ${currentStep.replace(/_/g, ' ')}` : 'Starting...'} •{' '}
          {formatDistanceToNow(new Date(updatedAt), { addSuffix: true })}
        </p>
      </div>
      <ArrowRight className="h-4 w-4 text-muted-foreground" />
    </Link>
  );
}

export default NewsletterDashboard;
