import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { StudioToolInfo } from '@/types/studio';

interface ToolsPanelProps {
  tools: StudioToolInfo[];
}

export function ToolsPanel({ tools }: ToolsPanelProps) {
  if (tools.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">No tools registered for this agent.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {tools.map((tool) => {
        const paramCount = Object.keys(tool.parameters).length;
        return (
          <Card key={tool.name}>
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <CardTitle className="text-base">{tool.name}</CardTitle>
                <Badge variant="outline">
                  {paramCount} param{paramCount !== 1 ? 's' : ''}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-2">
                {tool.description}
              </p>
              {paramCount > 0 && (
                <pre className="text-xs font-mono bg-muted p-3 rounded-md overflow-x-auto">
                  {JSON.stringify(tool.parameters, null, 2)}
                </pre>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
