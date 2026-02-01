import { Link } from 'react-router-dom';
import { MoreVertical, Power, PowerOff, Trash2, Play } from 'lucide-react';
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
import { formatNumber, formatDuration } from '@/utils/format';
import { useEnableTool, useDisableTool, useDeleteTool } from '@/hooks/useTools';
import type { Tool } from '@/types/tool';

interface ToolCardProps {
  tool: Tool;
}

export function ToolCard({ tool }: ToolCardProps) {
  const enableMutation = useEnableTool();
  const disableMutation = useDisableTool();
  const deleteMutation = useDeleteTool();

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'function':
        return 'bg-blue-100 text-blue-800';
      case 'api':
        return 'bg-green-100 text-green-800';
      case 'database':
        return 'bg-purple-100 text-purple-800';
      case 'file':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const handleToggleEnabled = () => {
    if (tool.enabled) {
      disableMutation.mutate(tool.id);
    } else {
      enableMutation.mutate(tool.id);
    }
  };

  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this tool?')) {
      deleteMutation.mutate(tool.id);
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between space-y-0">
        <div className="space-y-1">
          <Link to={`/tools/${tool.id}`}>
            <CardTitle className="hover:underline">{tool.name}</CardTitle>
          </Link>
          <div className="flex gap-2">
            <Badge className={getTypeColor(tool.type)}>{tool.type}</Badge>
            <Badge variant={tool.enabled ? 'success' : 'secondary'}>
              {tool.enabled ? 'Enabled' : 'Disabled'}
            </Badge>
          </div>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem asChild>
              <Link to={`/tools/${tool.id}`}>
                <Play className="mr-2 h-4 w-4" />
                Test Tool
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={handleToggleEnabled}>
              {tool.enabled ? (
                <>
                  <PowerOff className="mr-2 h-4 w-4" />
                  Disable
                </>
              ) : (
                <>
                  <Power className="mr-2 h-4 w-4" />
                  Enable
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
        <p className="text-sm text-muted-foreground line-clamp-2 mb-4">{tool.description}</p>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-muted-foreground">Parameters</p>
            <p className="font-medium">{tool.schema.parameters.length}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Version</p>
            <p className="font-medium">{tool.version}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Usage</p>
            <p className="font-medium">{formatNumber(tool.usageCount)}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Avg Time</p>
            <p className="font-medium">
              {tool.avgExecutionTime ? formatDuration(tool.avgExecutionTime) : '-'}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
