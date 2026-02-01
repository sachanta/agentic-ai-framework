import { useState } from 'react';
import { Play, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { useTestTool } from '@/hooks/useTools';
import { formatDuration } from '@/utils/format';
import type { Tool } from '@/types/tool';

interface ToolTesterProps {
  tool: Tool;
}

export function ToolTester({ tool }: ToolTesterProps) {
  const [parameters, setParameters] = useState<Record<string, string>>({});
  const testMutation = useTestTool();

  const handleTest = () => {
    const parsedParams: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(parameters)) {
      const paramDef = tool.schema.parameters.find((p) => p.name === key);
      if (paramDef) {
        switch (paramDef.type) {
          case 'number':
            parsedParams[key] = parseFloat(value);
            break;
          case 'boolean':
            parsedParams[key] = value === 'true';
            break;
          case 'array':
          case 'object':
            try {
              parsedParams[key] = JSON.parse(value);
            } catch {
              parsedParams[key] = value;
            }
            break;
          default:
            parsedParams[key] = value;
        }
      }
    }

    testMutation.mutate({ toolId: tool.id, parameters: parsedParams });
  };

  return (
    <div className="grid grid-cols-2 gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Test Parameters</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {tool.schema.parameters.length === 0 ? (
            <p className="text-sm text-muted-foreground">This tool has no parameters</p>
          ) : (
            tool.schema.parameters.map((param) => (
              <div key={param.name} className="space-y-2">
                <div className="flex items-center gap-2">
                  <Label htmlFor={param.name}>{param.name}</Label>
                  <Badge variant="outline" className="text-xs">
                    {param.type}
                  </Badge>
                  {param.required && (
                    <Badge variant="destructive" className="text-xs">
                      Required
                    </Badge>
                  )}
                </div>
                <Input
                  id={param.name}
                  placeholder={param.description || `Enter ${param.name}`}
                  value={parameters[param.name] || ''}
                  onChange={(e) =>
                    setParameters((prev) => ({ ...prev, [param.name]: e.target.value }))
                  }
                />
                {param.description && (
                  <p className="text-xs text-muted-foreground">{param.description}</p>
                )}
              </div>
            ))
          )}

          <Button
            onClick={handleTest}
            disabled={testMutation.isPending || !tool.enabled}
            className="w-full"
          >
            {testMutation.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Play className="mr-2 h-4 w-4" />
            )}
            Run Test
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Test Result</CardTitle>
        </CardHeader>
        <CardContent>
          {testMutation.data ? (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Badge variant={testMutation.data.success ? 'success' : 'destructive'}>
                  {testMutation.data.success ? 'Success' : 'Failed'}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  {formatDuration(testMutation.data.executionTime)}
                </span>
              </div>

              {testMutation.data.error && (
                <div className="p-3 bg-destructive/10 rounded-md">
                  <p className="text-sm text-destructive">{testMutation.data.error}</p>
                </div>
              )}

              {testMutation.data.result !== undefined && (
                <div className="space-y-2">
                  <Label>Output</Label>
                  <pre className="p-3 bg-muted rounded-md text-sm overflow-auto max-h-64">
                    {JSON.stringify(testMutation.data.result, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-8">
              Run a test to see results
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
