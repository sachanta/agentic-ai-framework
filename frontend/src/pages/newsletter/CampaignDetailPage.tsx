/**
 * Campaign Detail Page
 *
 * View and manage a single campaign
 */
import { useParams, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import {
  ArrowLeft,
  Send,
  Calendar,
  Users,
  Mail,
  MousePointer,
  Eye,
  Clock,
  Edit,
  Copy,
  Trash2,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import { format } from 'date-fns';
import { useCampaign, useCampaignStats } from '@/hooks/useNewsletter';
import type { CampaignStatus } from '@/types/newsletter';

export function CampaignDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: campaign, isLoading } = useCampaign(id || '');
  const { data: stats } = useCampaignStats(id || '');

  const getStatusBadge = (status: CampaignStatus) => {
    const variants: Record<CampaignStatus, 'default' | 'secondary' | 'outline' | 'destructive'> = {
      sent: 'default',
      scheduled: 'outline',
      draft: 'secondary',
      sending: 'default',
      failed: 'destructive',
      cancelled: 'secondary',
    };
    const labels: Record<CampaignStatus, string> = {
      sent: 'Sent',
      scheduled: 'Scheduled',
      draft: 'Draft',
      sending: 'Sending',
      failed: 'Failed',
      cancelled: 'Cancelled',
    };
    return <Badge variant={variants[status]}>{labels[status]}</Badge>;
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-40" />
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (!campaign) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" asChild>
          <Link to="/apps/newsletter/campaigns">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Campaigns
          </Link>
        </Button>
        <Card>
          <CardContent className="py-12 text-center">
            <XCircle className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-lg font-medium">Campaign not found</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const openRate = stats?.sent && stats.opened ? (stats.opened / stats.sent) * 100 : 0;
  const clickRate = stats?.opened && stats.clicked ? (stats.clicked / stats.opened) * 100 : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link to="/apps/newsletter/campaigns">
            <ArrowLeft className="h-5 w-5" />
          </Link>
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{campaign.name}</h1>
            {getStatusBadge(campaign.status)}
          </div>
          <p className="text-muted-foreground">{campaign.subject}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon">
            <Edit className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon">
            <Copy className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon">
            <Trash2 className="h-4 w-4" />
          </Button>
          {campaign.status === 'draft' && (
            <Button>
              <Send className="h-4 w-4 mr-2" />
              Send Campaign
            </Button>
          )}
        </div>
      </div>

      {/* Stats cards */}
      {campaign.status === 'sent' && stats && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Sent</CardTitle>
              <Send className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.sent.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">Total recipients</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Opened</CardTitle>
              <Eye className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.opened.toLocaleString()}</div>
              <div className="flex items-center gap-2 mt-2">
                <Progress value={openRate} className="h-2 flex-1" />
                <span className="text-xs text-muted-foreground">{openRate.toFixed(1)}%</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Clicked</CardTitle>
              <MousePointer className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.clicked.toLocaleString()}</div>
              <div className="flex items-center gap-2 mt-2">
                <Progress value={clickRate} className="h-2 flex-1" />
                <span className="text-xs text-muted-foreground">{clickRate.toFixed(1)}%</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Bounced</CardTitle>
              <XCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.bounced.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">
                {stats.sent ? ((stats.bounced / stats.sent) * 100).toFixed(1) : 0}% bounce rate
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Campaign details tabs */}
      <Tabs defaultValue="details">
        <TabsList>
          <TabsTrigger value="details">Details</TabsTrigger>
          <TabsTrigger value="preview">Preview</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
        </TabsList>

        <TabsContent value="details" className="mt-6">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Campaign Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Status</span>
                  {getStatusBadge(campaign.status)}
                </div>
                <Separator />
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Subject Line</span>
                  <span className="font-medium">{campaign.subject}</span>
                </div>
                <Separator />
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Recipients</span>
                  <span className="flex items-center gap-2">
                    <Users className="h-4 w-4" />
                    {campaign.recipient_count.toLocaleString()}
                  </span>
                </div>
                <Separator />
                {campaign.scheduled_at && (
                  <>
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Scheduled For</span>
                      <span className="flex items-center gap-2">
                        <Calendar className="h-4 w-4" />
                        {format(new Date(campaign.scheduled_at), 'MMM d, yyyy h:mm a')}
                      </span>
                    </div>
                    <Separator />
                  </>
                )}
                {campaign.sent_at && (
                  <>
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Sent At</span>
                      <span className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        {format(new Date(campaign.sent_at), 'MMM d, yyyy h:mm a')}
                      </span>
                    </div>
                    <Separator />
                  </>
                )}
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Created</span>
                  <span>{format(new Date(campaign.created_at), 'MMM d, yyyy')}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Newsletter</CardTitle>
                <CardDescription>Associated newsletter content</CardDescription>
              </CardHeader>
              <CardContent>
                {campaign.newsletter_id ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 p-3 rounded-lg border">
                      <Mail className="h-5 w-5 text-primary" />
                      <div className="flex-1">
                        <p className="font-medium">Newsletter #{campaign.newsletter_id.slice(0, 8)}</p>
                        <p className="text-sm text-muted-foreground">
                          Click to view newsletter content
                        </p>
                      </div>
                      <Button variant="outline" size="sm" asChild>
                        <Link to={`/apps/newsletter/newsletters/${campaign.newsletter_id}`}>
                          View
                        </Link>
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <Mail className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>No newsletter associated</p>
                    <Button variant="link" size="sm" className="mt-2">
                      Select Newsletter
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="preview" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Email Preview</CardTitle>
              <CardDescription>Preview how the email will appear to recipients</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="border rounded-lg overflow-hidden">
                <div className="bg-muted p-4 border-b">
                  <div className="space-y-1 text-sm">
                    <div className="flex gap-2">
                      <span className="text-muted-foreground w-16">From:</span>
                      <span>Newsletter &lt;newsletter@example.com&gt;</span>
                    </div>
                    <div className="flex gap-2">
                      <span className="text-muted-foreground w-16">Subject:</span>
                      <span className="font-medium">{campaign.subject}</span>
                    </div>
                  </div>
                </div>
                <div className="p-6 bg-white min-h-[400px]">
                  <p className="text-muted-foreground text-center py-12">
                    Email content preview would appear here
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="activity" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>Campaign activity log</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center gap-3 text-sm">
                  <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center">
                    <Clock className="h-4 w-4" />
                  </div>
                  <div className="flex-1">
                    <p>Campaign created</p>
                    <p className="text-muted-foreground text-xs">
                      {format(new Date(campaign.created_at), 'MMM d, yyyy h:mm a')}
                    </p>
                  </div>
                </div>
                {campaign.sent_at && (
                  <div className="flex items-center gap-3 text-sm">
                    <div className="h-8 w-8 rounded-full bg-green-100 flex items-center justify-center">
                      <Send className="h-4 w-4 text-green-600" />
                    </div>
                    <div className="flex-1">
                      <p>Campaign sent</p>
                      <p className="text-muted-foreground text-xs">
                        {format(new Date(campaign.sent_at), 'MMM d, yyyy h:mm a')}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default CampaignDetailPage;
