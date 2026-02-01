import { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { formatDateTime } from '@/utils/format';
import type { LogEntry as LogEntryType } from '@/api/logs';

interface LogEntryProps {
  log: LogEntryType;
}

export function LogEntry({ log }: LogEntryProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'error':
      case 'critical':
        return 'text-red-500 bg-red-50';
      case 'warning':
        return 'text-yellow-600 bg-yellow-50';
      case 'info':
        return 'text-blue-500 bg-blue-50';
      case 'debug':
        return 'text-gray-500 bg-gray-50';
      default:
        return 'text-gray-500 bg-gray-50';
    }
  };

  const getLevelBadgeVariant = (level: string) => {
    switch (level) {
      case 'error':
      case 'critical':
        return 'destructive';
      case 'warning':
        return 'warning';
      case 'info':
        return 'default';
      case 'debug':
        return 'secondary';
      default:
        return 'secondary';
    }
  };

  const hasDetails = log.details && Object.keys(log.details).length > 0;

  return (
    <div className={`font-mono text-sm rounded p-2 ${getLevelColor(log.level)}`}>
      <div className="flex items-start gap-2">
        {hasDetails && (
          <Button
            variant="ghost"
            size="icon"
            className="h-5 w-5 p-0"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
          </Button>
        )}
        <span className="text-muted-foreground whitespace-nowrap">
          {formatDateTime(log.timestamp)}
        </span>
        <Badge variant={getLevelBadgeVariant(log.level)} className="h-5 text-xs">
          {log.level.toUpperCase()}
        </Badge>
        <span className="text-muted-foreground">[{log.source}]</span>
        <span className="flex-1">{log.message}</span>
      </div>
      {isExpanded && hasDetails && (
        <pre className="mt-2 ml-7 p-2 bg-background rounded text-xs overflow-auto">
          {JSON.stringify(log.details, null, 2)}
        </pre>
      )}
    </div>
  );
}
