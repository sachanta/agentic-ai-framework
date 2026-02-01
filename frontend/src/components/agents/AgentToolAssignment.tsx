import { useState } from 'react';
import { Plus, X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useTools } from '@/hooks/useTools';
import { useAssignTools } from '@/hooks/useAgents';
import type { Agent } from '@/types/agent';

interface AgentToolAssignmentProps {
  agent: Agent;
}

export function AgentToolAssignment({ agent }: AgentToolAssignmentProps) {
  const [selectedTool, setSelectedTool] = useState<string>('');
  const { data: toolsData } = useTools();
  const assignMutation = useAssignTools();

  const tools = toolsData?.items ?? [];
  const assignedToolIds = agent.tools;
  const availableTools = tools.filter((tool) => !assignedToolIds.includes(tool.id));

  const handleAssign = () => {
    if (selectedTool) {
      assignMutation.mutate({
        id: agent.id,
        toolIds: [...assignedToolIds, selectedTool],
      });
      setSelectedTool('');
    }
  };

  const handleRemove = (toolId: string) => {
    assignMutation.mutate({
      id: agent.id,
      toolIds: assignedToolIds.filter((id) => id !== toolId),
    });
  };

  const assignedTools = tools.filter((tool) => assignedToolIds.includes(tool.id));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Assigned Tools</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Select value={selectedTool} onValueChange={setSelectedTool}>
            <SelectTrigger className="flex-1">
              <SelectValue placeholder="Select a tool to assign" />
            </SelectTrigger>
            <SelectContent>
              {availableTools.map((tool) => (
                <SelectItem key={tool.id} value={tool.id}>
                  {tool.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button onClick={handleAssign} disabled={!selectedTool || assignMutation.isPending}>
            <Plus className="mr-2 h-4 w-4" />
            Assign
          </Button>
        </div>

        {assignedTools.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">
            No tools assigned to this agent
          </p>
        ) : (
          <div className="space-y-2">
            {assignedTools.map((tool) => (
              <div
                key={tool.id}
                className="flex items-center justify-between p-3 border rounded-md"
              >
                <div>
                  <p className="font-medium">{tool.name}</p>
                  <p className="text-sm text-muted-foreground">{tool.description}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={tool.enabled ? 'success' : 'secondary'}>
                    {tool.enabled ? 'Enabled' : 'Disabled'}
                  </Badge>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleRemove(tool.id)}
                    disabled={assignMutation.isPending}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
