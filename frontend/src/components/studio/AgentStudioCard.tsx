import { Bot, Wrench, MessageSquare, Cpu } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { StudioAgentSummary } from '@/types/studio';

interface AgentStudioCardProps {
  agent: StudioAgentSummary;
  onSelect: (agent: StudioAgentSummary) => void;
}

export function AgentStudioCard({ agent, onSelect }: AgentStudioCardProps) {
  return (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow"
      onClick={() => onSelect(agent)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <CardTitle className="text-lg">{agent.display_name}</CardTitle>
            <Badge variant="outline">{agent.platform_name}</Badge>
          </div>
          <Bot className="h-5 w-5 text-muted-foreground" />
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground line-clamp-2 mb-4">
          {agent.description}
        </p>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="flex items-center gap-1.5">
            <Cpu className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="truncate">
              {agent.llm_config.model ?? 'Default'}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <Wrench className="h-3.5 w-3.5 text-muted-foreground" />
            <span>{agent.tool_count} tools</span>
          </div>
          <div className="flex items-center gap-1.5">
            <MessageSquare className="h-3.5 w-3.5 text-muted-foreground" />
            <span>{agent.has_system_prompt ? 'Has prompt' : 'No prompt'}</span>
          </div>
          <div>
            <span className="text-xs text-muted-foreground font-mono">
              {agent.agent_class}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
