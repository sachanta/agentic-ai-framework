import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { useStudioAgent } from '@/hooks/useStudio';
import { LLMConfigEditor } from '@/components/studio/LLMConfigEditor';
import { PromptEditor } from '@/components/studio/PromptEditor';
import { TryItPanel } from '@/components/studio/TryItPanel';
import { ToolsPanel } from '@/components/studio/ToolsPanel';

export function AgentInspectorPage() {
  const { platformId, agentName } = useParams<{
    platformId: string;
    agentName: string;
  }>();
  const navigate = useNavigate();
  const { data: detail, isLoading } = useStudioAgent(
    platformId ?? '',
    agentName ?? '',
  );

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-[400px] w-full" />
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/studio')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Studio
        </Button>
        <div className="text-center py-12">
          <p className="text-muted-foreground">Agent not found.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/studio')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <div>
          <h1 className="text-2xl font-bold">{detail.display_name}</h1>
          <div className="flex gap-2 mt-1">
            <Badge variant="outline">{detail.platform_name}</Badge>
            <Badge variant="secondary">{detail.agent_class}</Badge>
            <Badge variant="secondary">
              {detail.tool_count} tool{detail.tool_count !== 1 ? 's' : ''}
            </Badge>
          </div>
        </div>
      </div>

      {detail.description && (
        <p className="text-muted-foreground">{detail.description}</p>
      )}

      <Tabs defaultValue="config">
        <TabsList>
          <TabsTrigger value="config">LLM Config</TabsTrigger>
          <TabsTrigger value="prompt">System Prompt</TabsTrigger>
          <TabsTrigger value="try">Try It</TabsTrigger>
          <TabsTrigger value="tools">
            Tools ({detail.tool_count})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="config" className="mt-4">
          <LLMConfigEditor
            platformId={platformId!}
            agentName={agentName!}
            detail={detail}
          />
        </TabsContent>

        <TabsContent value="prompt" className="mt-4">
          <PromptEditor
            platformId={platformId!}
            agentName={agentName!}
            detail={detail}
          />
        </TabsContent>

        <TabsContent value="try" className="mt-4">
          <TryItPanel
            platformId={platformId!}
            agentName={agentName!}
          />
        </TabsContent>

        <TabsContent value="tools" className="mt-4">
          <ToolsPanel tools={detail.tools} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default AgentInspectorPage;
