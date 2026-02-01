import { useState } from 'react';
import { Pencil, Trash2, Power, PowerOff } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
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
import { ToolForm } from './ToolForm';
import { ToolTester } from './ToolTester';
import { SchemaViewer } from './SchemaViewer';
import { formatDateTime, formatNumber, formatDuration } from '@/utils/format';
import { useDeleteTool, useEnableTool, useDisableTool } from '@/hooks/useTools';
import type { Tool } from '@/types/tool';

interface ToolDetailProps {
  tool: Tool;
}

export function ToolDetail({ tool }: ToolDetailProps) {
  const [isEditOpen, setIsEditOpen] = useState(false);
  const navigate = useNavigate();
  const deleteMutation = useDeleteTool();
  const enableMutation = useEnableTool();
  const disableMutation = useDisableTool();

  const handleDelete = async () => {
    if (confirm('Are you sure you want to delete this tool?')) {
      await deleteMutation.mutateAsync(tool.id);
      navigate('/tools');
    }
  };

  const handleToggleEnabled = () => {
    if (tool.enabled) {
      disableMutation.mutate(tool.id);
    } else {
      enableMutation.mutate(tool.id);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold">{tool.name}</h1>
          <p className="text-muted-foreground mt-1">{tool.description}</p>
          <div className="flex gap-2 mt-2">
            <Badge>{tool.type}</Badge>
            <Badge variant={tool.enabled ? 'success' : 'secondary'}>
              {tool.enabled ? 'Enabled' : 'Disabled'}
            </Badge>
            <Badge variant="outline">v{tool.version}</Badge>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleToggleEnabled}>
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

      <Tabs defaultValue="test">
        <TabsList>
          <TabsTrigger value="test">Test</TabsTrigger>
          <TabsTrigger value="schema">Schema</TabsTrigger>
          <TabsTrigger value="stats">Statistics</TabsTrigger>
        </TabsList>

        <TabsContent value="test">
          <ToolTester tool={tool} />
        </TabsContent>

        <TabsContent value="schema">
          <SchemaViewer schema={tool.schema} />
        </TabsContent>

        <TabsContent value="stats" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Total Usage</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{formatNumber(tool.usageCount)}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Avg Execution Time</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">
                  {tool.avgExecutionTime ? formatDuration(tool.avgExecutionTime) : '-'}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Parameters</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{tool.schema.parameters.length}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Created</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm">{formatDateTime(tool.createdAt)}</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Tool</DialogTitle>
          </DialogHeader>
          <ToolForm tool={tool} onSuccess={() => setIsEditOpen(false)} />
        </DialogContent>
      </Dialog>
    </div>
  );
}
