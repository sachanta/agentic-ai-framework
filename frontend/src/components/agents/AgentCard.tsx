import { Link } from 'react-router-dom';
import { MoreVertical, Play, Pause, Trash2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { formatTimeAgo, formatPercentage } from '@/utils/format';
import { useActivateAgent, useDeactivateAgent, useDeleteAgent } from '@/hooks/useAgents';
import type { Agent } from '@/types/agent';

interface AgentCardProps {
  agent: Agent;
}

export function AgentCard({ agent }: AgentCardProps) {
  const activateMutation = useActivateAgent();
  const deactivateMutation = useDeactivateAgent();
  const deleteMutation = useDeleteAgent();

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

  const handleToggleStatus = () => {
    if (agent.status === 'active') {
      deactivateMutation.mutate(agent.id);
    } else {
      activateMutation.mutate(agent.id);
    }
  };

  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this agent?')) {
      deleteMutation.mutate(agent.id);
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between space-y-0">
        <div className="space-y-1">
          <Link to={`/agents/${agent.id}`}>
            <CardTitle className="hover:underline">{agent.name}</CardTitle>
          </Link>
          <Badge variant={getStatusVariant(agent.status)}>{agent.status}</Badge>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={handleToggleStatus}>
              {agent.status === 'active' ? (
                <>
                  <Pause className="mr-2 h-4 w-4" />
                  Deactivate
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Activate
                </>
              )}
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleDelete} className="text-destructive">
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground line-clamp-2 mb-4">{agent.description}</p>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-muted-foreground">Model</p>
            <p className="font-medium">{agent.config.model}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Tools</p>
            <p className="font-medium">{agent.tools.length}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Executions</p>
            <p className="font-medium">{agent.executionCount}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Success Rate</p>
            <p className="font-medium">{formatPercentage(agent.successRate)}</p>
          </div>
        </div>
        {agent.lastExecutedAt && (
          <p className="text-xs text-muted-foreground mt-4">
            Last executed {formatTimeAgo(agent.lastExecutedAt)}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
