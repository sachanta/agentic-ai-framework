import { X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useAgents } from '@/hooks/useAgents';
import { useTools } from '@/hooks/useTools';
import type { WorkflowStep } from '@/types/workflow';

interface StepEditorProps {
  step: WorkflowStep;
  onClose: () => void;
}

export function StepEditor({ step, onClose }: StepEditorProps) {
  const { data: agentsData } = useAgents();
  const { data: toolsData } = useTools();

  const agents = agentsData?.items ?? [];
  const tools = toolsData?.items ?? [];

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm">Edit Step</CardTitle>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label>Name</Label>
          <Input defaultValue={step.name} />
        </div>

        <div className="space-y-2">
          <Label>Type</Label>
          <Input value={step.type} disabled />
        </div>

        {step.type === 'agent' && (
          <div className="space-y-2">
            <Label>Agent</Label>
            <Select defaultValue={step.config.agentId}>
              <SelectTrigger>
                <SelectValue placeholder="Select agent" />
              </SelectTrigger>
              <SelectContent>
                {agents.map((agent) => (
                  <SelectItem key={agent.id} value={agent.id}>
                    {agent.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {step.type === 'tool' && (
          <div className="space-y-2">
            <Label>Tool</Label>
            <Select defaultValue={step.config.toolId}>
              <SelectTrigger>
                <SelectValue placeholder="Select tool" />
              </SelectTrigger>
              <SelectContent>
                {tools.map((tool) => (
                  <SelectItem key={tool.id} value={tool.id}>
                    {tool.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {step.type === 'condition' && (
          <div className="space-y-2">
            <Label>Condition</Label>
            <Input
              defaultValue={step.config.condition}
              placeholder="e.g., result.success === true"
            />
          </div>
        )}

        <div className="space-y-2">
          <Label>On Error</Label>
          <Select defaultValue={step.onError || 'stop'}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="stop">Stop Workflow</SelectItem>
              <SelectItem value="continue">Continue</SelectItem>
              <SelectItem value="retry">Retry</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>
  );
}
