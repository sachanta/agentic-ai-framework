import { useState } from 'react';
import { Pencil, Play, Trash2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { AgentForm } from './AgentForm';
import { AgentToolAssignment } from './AgentToolAssignment';
import { formatDateTime, formatPercentage, formatNumber } from '@/utils/format';
import { useDeleteAgent, useExecuteAgent } from '@/hooks/useAgents';
import { useNavigate } from 'react-router-dom';
import type { Agent } from '@/types/agent';

interface AgentDetailProps {
  agent: Agent;
}

export function AgentDetail({ agent }: AgentDetailProps) {
  const [isEditOpen, setIsEditOpen] = useState(false);
  const navigate = useNavigate();
  const deleteMutation = useDeleteAgent();
  const executeMutation = useExecuteAgent();

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'inactive':
        return 'secondary';
      case 'error':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  const handleDelete = async () => {
    if (confirm('Are you sure you want to delete this agent?')) {
      await deleteMutation.mutateAsync(agent.id);
      navigate('/agents');
    }
  };

  const handleExecute = () => {
    executeMutation.mutate({ id: agent.id, input: {} });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold">{agent.name}</h1>
          <p className="text-muted-foreground mt-1">{agent.description}</p>
          <Badge variant={getStatusVariant(agent.status)} className="mt-2">
            {agent.status}
          </Badge>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleExecute} disabled={agent.status !== 'active'}>
            <Play className="mr-2 h-4 w-4" />
            Execute
          </Button>
          <Button variant="outline" onClick={() => setIsEditOpen(true)}>
            <Pencil className="mr-2 h-4 w-4" />
            Edit
          </Button>
          <Button variant="destructive" onClick={handleDelete}>
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </Button>
        </div>
      </div>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="tools">Tools</TabsTrigger>
          <TabsTrigger value="config">Configuration</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Total Executions</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{formatNumber(agent.executionCount)}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{formatPercentage(agent.successRate)}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Tools Assigned</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{agent.tools.length}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Created</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm">{formatDateTime(agent.createdAt)}</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="tools">
          <AgentToolAssignment agent={agent} />
        </TabsContent>

        <TabsContent value="config">
          <Card>
            <CardHeader>
              <CardTitle>Configuration</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm text-muted-foreground">Model</dt>
                  <dd className="font-medium">{agent.config.model}</dd>
                </div>
                <div>
                  <dt className="text-sm text-muted-foreground">Temperature</dt>
                  <dd className="font-medium">{agent.config.temperature ?? 'Default'}</dd>
                </div>
                <div>
                  <dt className="text-sm text-muted-foreground">Max Tokens</dt>
                  <dd className="font-medium">{agent.config.maxTokens ?? 'Default'}</dd>
                </div>
                <div>
                  <dt className="text-sm text-muted-foreground">Timeout</dt>
                  <dd className="font-medium">{agent.config.timeout ?? 'Default'}ms</dd>
                </div>
                <div className="col-span-2">
                  <dt className="text-sm text-muted-foreground">System Prompt</dt>
                  <dd className="font-medium whitespace-pre-wrap bg-muted p-3 rounded-md mt-1">
                    {agent.config.systemPrompt || 'No system prompt configured'}
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Agent</DialogTitle>
          </DialogHeader>
          <AgentForm agent={agent} onSuccess={() => setIsEditOpen(false)} />
        </DialogContent>
      </Dialog>
    </div>
  );
}
