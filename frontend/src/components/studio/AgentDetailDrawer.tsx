import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Skeleton } from '@/components/ui/skeleton';
import { useStudioAgent } from '@/hooks/useStudio';
import type { StudioAgentSummary } from '@/types/studio';

interface AgentDetailDrawerProps {
  agent: StudioAgentSummary | null;
  open: boolean;
  onClose: () => void;
}

export function AgentDetailDrawer({
  agent,
  open,
  onClose,
}: AgentDetailDrawerProps) {
  const { data: detail, isLoading } = useStudioAgent(
    agent?.platform_id ?? '',
    agent?.name ?? '',
  );

  if (!agent) return null;

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-2xl max-h-[85vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="text-xl">{agent.display_name}</DialogTitle>
          <div className="flex gap-2 mt-1">
            <Badge variant="outline">{agent.platform_name}</Badge>
            <Badge variant="secondary">{agent.agent_class}</Badge>
          </div>
        </DialogHeader>

        {isLoading ? (
          <div className="space-y-4 py-4">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-4 w-1/2" />
          </div>
        ) : detail ? (
          <Tabs defaultValue="overview" className="mt-2 flex-1 min-h-0">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="config">Config</TabsTrigger>
              <TabsTrigger value="prompt">Prompt</TabsTrigger>
              <TabsTrigger value="tools">
                Tools ({detail.tool_count})
              </TabsTrigger>
            </TabsList>

            <ScrollArea className="h-[55vh] mt-4">
              <TabsContent value="overview" className="space-y-4 mt-0">
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground">
                    Description
                  </h4>
                  <p className="mt-1">{detail.description}</p>
                </div>
                <Separator />
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-sm font-medium text-muted-foreground">
                      Platform
                    </h4>
                    <p className="mt-1">{detail.platform_name}</p>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-muted-foreground">
                      Agent Class
                    </h4>
                    <p className="mt-1 font-mono text-sm">
                      {detail.agent_class}
                    </p>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-muted-foreground">
                      Agent ID
                    </h4>
                    <p className="mt-1 font-mono text-sm">{detail.agent_id}</p>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-muted-foreground">
                      Status
                    </h4>
                    <p className="mt-1 capitalize">{detail.status}</p>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="config" className="space-y-4 mt-0">
                <dl className="grid grid-cols-2 gap-4">
                  <div>
                    <dt className="text-sm text-muted-foreground">Provider</dt>
                    <dd className="font-medium mt-1">
                      {detail.llm_config.provider ?? 'Default'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm text-muted-foreground">Model</dt>
                    <dd className="font-medium mt-1">
                      {detail.llm_config.model ?? 'Default'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm text-muted-foreground">
                      Temperature
                    </dt>
                    <dd className="font-medium mt-1">
                      {detail.llm_config.temperature != null
                        ? String(detail.llm_config.temperature)
                        : 'Default'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm text-muted-foreground">
                      Max Tokens
                    </dt>
                    <dd className="font-medium mt-1">
                      {detail.llm_config.max_tokens != null
                        ? String(detail.llm_config.max_tokens)
                        : 'Default'}
                    </dd>
                  </div>
                </dl>
                {detail.parameters &&
                  Object.keys(detail.parameters).length > 0 && (
                    <>
                      <Separator />
                      <div>
                        <h4 className="text-sm font-medium text-muted-foreground mb-2">
                          All Parameters
                        </h4>
                        <pre className="text-sm bg-muted p-3 rounded-md overflow-x-auto">
                          {JSON.stringify(detail.parameters, null, 2)}
                        </pre>
                      </div>
                    </>
                  )}
              </TabsContent>

              <TabsContent value="prompt" className="mt-0">
                {detail.system_prompt ? (
                  <div className="bg-muted p-4 rounded-md">
                    <pre className="whitespace-pre-wrap text-sm font-mono">
                      {detail.system_prompt}
                    </pre>
                  </div>
                ) : (
                  <p className="text-muted-foreground py-4">
                    No system prompt configured.
                  </p>
                )}
              </TabsContent>

              <TabsContent value="tools" className="space-y-3 mt-0">
                {detail.tools.length === 0 ? (
                  <p className="text-muted-foreground py-4">
                    No tools registered.
                  </p>
                ) : (
                  detail.tools.map((tool) => (
                    <div key={tool.name} className="border rounded-md p-3">
                      <h4 className="font-medium">{tool.name}</h4>
                      <p className="text-sm text-muted-foreground mt-1">
                        {tool.description}
                      </p>
                      {Object.keys(tool.parameters).length > 0 && (
                        <pre className="mt-2 text-xs bg-muted p-2 rounded overflow-x-auto">
                          {JSON.stringify(tool.parameters, null, 2)}
                        </pre>
                      )}
                    </div>
                  ))
                )}
              </TabsContent>
            </ScrollArea>
          </Tabs>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
