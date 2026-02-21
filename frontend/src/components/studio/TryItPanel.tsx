import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import { useTryAgent } from '@/hooks/useStudio';
import type { StudioTryResponse } from '@/types/studio';

interface TryItPanelProps {
  platformId: string;
  agentName: string;
}

function getDefaultInput(agentName: string): string {
  const defaults: Record<string, object> = {
    greeter: { name: 'World' },
    research: { topic: 'AI agents', max_results: 3 },
    writing: { topic: 'AI agents', articles: [] },
    preference: { content: 'Sample newsletter content', preferences: {} },
    custom_prompt: { content: 'Sample content', prompt: 'Summarize this' },
  };
  return JSON.stringify(defaults[agentName] ?? { message: 'Hello' }, null, 2);
}

export function TryItPanel({ platformId, agentName }: TryItPanelProps) {
  const { toast } = useToast();
  const tryAgent = useTryAgent();
  const [input, setInput] = useState(() => getDefaultInput(agentName));
  const [result, setResult] = useState<StudioTryResponse | null>(null);

  const handleRun = () => {
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(input);
    } catch {
      toast({
        variant: 'destructive',
        title: 'Invalid JSON',
        description: 'Input must be valid JSON.',
      });
      return;
    }

    tryAgent.mutate(
      {
        platformId,
        agentName,
        data: { input: parsed },
      },
      {
        onSuccess: (data) => setResult(data),
        onError: (err) => {
          toast({ variant: 'destructive', title: 'Error', description: String(err) });
        },
      },
    );
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* Input */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Input</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            rows={12}
            className="font-mono text-sm"
            placeholder='{"message": "Hello"}'
          />
          <Button onClick={handleRun} disabled={tryAgent.isPending}>
            {tryAgent.isPending ? 'Running...' : 'Run'}
          </Button>
        </CardContent>
      </Card>

      {/* Output */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Output</CardTitle>
        </CardHeader>
        <CardContent>
          {tryAgent.isPending ? (
            <p className="text-muted-foreground py-4">Running agent...</p>
          ) : result ? (
            <div className="space-y-3">
              <div className="flex gap-2">
                <Badge variant={result.success ? 'default' : 'destructive'}>
                  {result.success ? 'Success' : 'Error'}
                </Badge>
                <Badge variant="outline">
                  {result.duration_ms.toFixed(0)} ms
                </Badge>
              </div>
              {result.error && (
                <p className="text-sm text-destructive">{result.error}</p>
              )}
              {result.output && (
                <pre className="text-sm font-mono bg-muted p-4 rounded-md overflow-x-auto whitespace-pre-wrap">
                  {JSON.stringify(result.output, null, 2)}
                </pre>
              )}
            </div>
          ) : (
            <p className="text-muted-foreground py-4">
              Click Run to execute the agent.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
