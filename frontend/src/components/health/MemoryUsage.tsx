import { HardDrive } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { formatBytes } from '@/utils/format';

interface MemoryUsageProps {
  used?: number;
  total?: number;
  percentage?: number;
  isLoading?: boolean;
}

export function MemoryUsage({ used, total, percentage, isLoading }: MemoryUsageProps) {
  const getProgressColor = (pct?: number) => {
    if (pct === undefined) return '';
    if (pct >= 90) return 'bg-red-500';
    if (pct >= 70) return 'bg-yellow-500';
    return '';
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <HardDrive className="h-4 w-4" />
            Memory Usage
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-32" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <HardDrive className="h-4 w-4" />
          Memory Usage
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold">{percentage?.toFixed(1)}%</span>
            <span className="text-sm text-muted-foreground">
              {used !== undefined && total !== undefined
                ? `${formatBytes(used)} / ${formatBytes(total)}`
                : '-'}
            </span>
          </div>
          <Progress value={percentage || 0} className={getProgressColor(percentage)} />
        </div>
      </CardContent>
    </Card>
  );
}
