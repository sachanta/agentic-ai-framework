/**
 * Workflow execution history component
 *
 * Displays a timeline of workflow steps with status and timestamps
 */
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Check,
  X,
  Clock,
  AlertCircle,
  Loader2,
  History,
} from 'lucide-react';
import type { WorkflowHistoryItem } from '@/types/newsletter';
import { formatDistanceToNow } from 'date-fns';

interface WorkflowHistoryProps {
  history: WorkflowHistoryItem[];
  className?: string;
}

export function WorkflowHistory({ history, className }: WorkflowHistoryProps) {
  const getStepIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <Check className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <X className="h-4 w-4 text-destructive" />;
      case 'running':
        return <Loader2 className="h-4 w-4 text-primary animate-spin" />;
      case 'awaiting_approval':
        return <AlertCircle className="h-4 w-4 text-amber-500" />;
      default:
        return <Clock className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="default" className="bg-green-500">Completed</Badge>;
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>;
      case 'running':
        return <Badge variant="default">Running</Badge>;
      case 'awaiting_approval':
        return <Badge variant="outline" className="text-amber-600 border-amber-600">Awaiting</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const formatStepName = (step: string) => {
    return step
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase());
  };

  if (history.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="py-8 text-center text-muted-foreground">
          <History className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>No history yet</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <History className="h-4 w-4" />
          Execution History
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <ScrollArea className="h-[300px] pr-4">
          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-[11px] top-2 bottom-2 w-0.5 bg-muted" />

            {/* History items */}
            <div className="space-y-4">
              {history.map((item, index) => (
                <div key={index} className="relative flex gap-3">
                  {/* Icon */}
                  <div className="relative z-10 flex h-6 w-6 items-center justify-center rounded-full bg-background border">
                    {getStepIcon(item.status)}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0 pb-4">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-medium text-sm">
                        {formatStepName(item.step)}
                      </span>
                      {getStatusBadge(item.status)}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      {formatDistanceToNow(new Date(item.timestamp), { addSuffix: true })}
                    </div>
                    {item.data && Object.keys(item.data).length > 0 && (() => {
                      const msg = item.data.message;
                      const count = item.data.article_count;
                      const err = item.data.error;
                      return (
                        <div className="mt-2 text-xs text-muted-foreground bg-muted rounded p-2">
                          {msg != null && <p>{String(msg)}</p>}
                          {count != null && <p>Articles: {String(count)}</p>}
                          {err != null && (
                            <p className="text-destructive">Error: {String(err)}</p>
                          )}
                        </div>
                      );
                    })()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

export default WorkflowHistory;
