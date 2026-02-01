import { CheckCircle, Circle, XCircle, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatDuration } from '@/utils/format';
import type { Execution } from '@/types/execution';

interface ExecutionProgressProps {
  execution: Execution;
}

export function ExecutionProgress({ execution }: ExecutionProgressProps) {
  const getStepIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'running':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Circle className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStepBadgeVariant = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'running':
        return 'default';
      case 'failed':
        return 'destructive';
      default:
        return 'secondary';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Execution Steps</CardTitle>
      </CardHeader>
      <CardContent>
        {execution.steps.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-8">
            No steps to display
          </p>
        ) : (
          <div className="space-y-4">
            {execution.steps.map((step, index) => (
              <div
                key={step.id}
                className="flex items-start gap-4 p-4 border rounded-lg"
              >
                <div className="flex flex-col items-center">
                  {getStepIcon(step.status)}
                  {index < execution.steps.length - 1 && (
                    <div className="w-px h-8 bg-border mt-2" />
                  )}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium">{step.stepName}</h4>
                    <Badge variant={getStepBadgeVariant(step.status)}>{step.status}</Badge>
                  </div>
                  {step.duration && (
                    <p className="text-sm text-muted-foreground mt-1">
                      Duration: {formatDuration(step.duration)}
                    </p>
                  )}
                  {step.error && (
                    <p className="text-sm text-destructive mt-2">{step.error}</p>
                  )}
                  {step.output && (
                    <details className="mt-2">
                      <summary className="text-sm text-muted-foreground cursor-pointer">
                        View Output
                      </summary>
                      <pre className="mt-2 p-2 bg-muted rounded text-xs overflow-auto max-h-32">
                        {JSON.stringify(step.output, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
