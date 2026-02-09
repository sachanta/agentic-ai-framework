/**
 * Newsletter Analytics Page
 *
 * Analytics dashboard showing newsletter performance metrics
 */
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  Eye,
  MousePointer,
  Users,
  Mail,
  Send,
  BarChart3,
  LineChart,
  Calendar,
} from 'lucide-react';
import { useDashboard } from '@/hooks/useNewsletter';

export function AnalyticsPage() {
  const { data: dashboard } = useDashboard();

  const metrics = [
    {
      label: 'Total Newsletters',
      value: dashboard?.newsletters?.total || 0,
      change: dashboard?.newsletters?.growth_rate || 0,
      icon: Mail,
    },
    {
      label: 'Campaigns Sent',
      value: dashboard?.campaigns?.sent_this_month || 0,
      change: null,
      subtitle: 'this month',
      icon: Send,
    },
    {
      label: 'Active Subscribers',
      value: dashboard?.subscribers?.active || 0,
      change: dashboard?.subscribers?.new_this_month || 0,
      changeLabel: 'new',
      icon: Users,
    },
    {
      label: 'Avg Open Rate',
      value: dashboard?.engagement?.avg_open_rate
        ? `${(dashboard.engagement.avg_open_rate * 100).toFixed(1)}%`
        : '-',
      change: null,
      icon: Eye,
    },
    {
      label: 'Avg Click Rate',
      value: dashboard?.engagement?.avg_click_rate
        ? `${(dashboard.engagement.avg_click_rate * 100).toFixed(1)}%`
        : '-',
      change: null,
      icon: MousePointer,
    },
  ];

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
          <h1 className="text-2xl font-bold">Analytics</h1>
          <p className="text-muted-foreground">Newsletter performance metrics</p>
        </div>
        <Select defaultValue="30d">
          <SelectTrigger className="w-40">
            <Calendar className="h-4 w-4 mr-2" />
            <SelectValue placeholder="Period" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7d">Last 7 days</SelectItem>
            <SelectItem value="30d">Last 30 days</SelectItem>
            <SelectItem value="90d">Last 90 days</SelectItem>
            <SelectItem value="year">This year</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Key metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        {metrics.map((metric) => (
          <Card key={metric.label}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">{metric.label}</CardTitle>
              <metric.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metric.value}</div>
              {metric.change !== null && (
                <p className="text-xs text-muted-foreground flex items-center gap-1">
                  {metric.change >= 0 ? (
                    <TrendingUp className="h-3 w-3 text-green-500" />
                  ) : (
                    <TrendingDown className="h-3 w-3 text-red-500" />
                  )}
                  <span className={metric.change >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {metric.change >= 0 ? '+' : ''}{metric.change}
                  </span>
                  {metric.changeLabel || 'vs last month'}
                </p>
              )}
              {metric.subtitle && (
                <p className="text-xs text-muted-foreground">{metric.subtitle}</p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts */}
      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="engagement" className="flex items-center gap-2">
            <LineChart className="h-4 w-4" />
            Engagement
          </TabsTrigger>
          <TabsTrigger value="subscribers" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Subscribers
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6">
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Campaign performance */}
            <Card>
              <CardHeader>
                <CardTitle>Campaign Performance</CardTitle>
                <CardDescription>Open and click rates over time</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                  <div className="text-center">
                    <LineChart className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Campaign performance chart</p>
                    <p className="text-sm">Data visualization coming soon</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Recent campaigns table */}
            <Card>
              <CardHeader>
                <CardTitle>Top Performing Campaigns</CardTitle>
                <CardDescription>By open rate</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    { name: 'Weekly Digest #42', openRate: 0.58, clickRate: 0.12 },
                    { name: 'Product Launch', openRate: 0.52, clickRate: 0.18 },
                    { name: 'Monthly Update', openRate: 0.45, clickRate: 0.08 },
                    { name: 'Holiday Special', openRate: 0.42, clickRate: 0.15 },
                    { name: 'Q4 Recap', openRate: 0.38, clickRate: 0.09 },
                  ].map((campaign, i) => (
                    <div key={i} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium truncate">{campaign.name}</span>
                        <span className="text-muted-foreground">
                          {(campaign.openRate * 100).toFixed(0)}% open
                        </span>
                      </div>
                      <div className="flex gap-2">
                        <Progress value={campaign.openRate * 100} className="h-2 flex-1" />
                        <Progress value={campaign.clickRate * 100} className="h-2 w-16" />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="engagement" className="mt-6">
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Open rate trend */}
            <Card>
              <CardHeader>
                <CardTitle>Open Rate Trend</CardTitle>
                <CardDescription>Average open rate over time</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                  <div className="text-center">
                    <TrendingUp className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Open rate trend chart</p>
                    <p className="text-sm">Data visualization coming soon</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Click rate trend */}
            <Card>
              <CardHeader>
                <CardTitle>Click Rate Trend</CardTitle>
                <CardDescription>Average click rate over time</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                  <div className="text-center">
                    <MousePointer className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Click rate trend chart</p>
                    <p className="text-sm">Data visualization coming soon</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Engagement by day */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Best Performing Days</CardTitle>
                <CardDescription>Open rates by day of week</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-7 gap-2">
                  {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, i) => {
                    const rate = [0.42, 0.48, 0.45, 0.52, 0.38, 0.25, 0.22][i];
                    return (
                      <div key={day} className="text-center">
                        <div className="text-xs text-muted-foreground mb-2">{day}</div>
                        <div
                          className="mx-auto bg-primary rounded"
                          style={{
                            width: '32px',
                            height: `${rate * 150}px`,
                            opacity: 0.3 + rate,
                          }}
                        />
                        <div className="text-xs mt-2 font-medium">
                          {(rate * 100).toFixed(0)}%
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="subscribers" className="mt-6">
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Subscriber growth */}
            <Card>
              <CardHeader>
                <CardTitle>Subscriber Growth</CardTitle>
                <CardDescription>New subscribers over time</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                  <div className="text-center">
                    <Users className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Subscriber growth chart</p>
                    <p className="text-sm">Data visualization coming soon</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Subscriber breakdown */}
            <Card>
              <CardHeader>
                <CardTitle>Subscriber Status</CardTitle>
                <CardDescription>Breakdown by status</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>Active</span>
                      <span className="font-medium">{dashboard?.subscribers?.active || 0}</span>
                    </div>
                    <Progress value={100} className="h-2 bg-green-100" />
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>Unsubscribed</span>
                      <span className="font-medium">-</span>
                    </div>
                    <Progress value={10} className="h-2 bg-muted" />
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>Bounced</span>
                      <span className="font-medium">-</span>
                    </div>
                    <Progress value={5} className="h-2 bg-red-100" />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Acquisition sources */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Acquisition Sources</CardTitle>
                <CardDescription>Where subscribers come from</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[200px] flex items-center justify-center text-muted-foreground">
                  <div className="text-center">
                    <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Acquisition sources chart</p>
                    <p className="text-sm">Data visualization coming soon</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default AnalyticsPage;
