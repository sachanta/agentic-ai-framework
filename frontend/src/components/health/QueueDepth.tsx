import { Layers } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

interface QueueDepthProps {
  pending?: number;
  processing?: number;
  completed?: number;
  failed?: number;
  isLoading?: boolean;
}

export function QueueDepth({
  pending,
  processing,
  completed,
  failed,
  isLoading,
}: QueueDepthProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Layers className="h-4 w-4" />
            Queue Depth
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-32 w-full" />
        </CardContent>
      </Card>
    );
  }

  const data = [
    { name: 'Pending', value: pending || 0, fill: '#f59e0b' },
    { name: 'Processing', value: processing || 0, fill: '#3b82f6' },
    { name: 'Completed', value: completed || 0, fill: '#22c55e' },
    { name: 'Failed', value: failed || 0, fill: '#ef4444' },
  ];

  const total = (pending || 0) + (processing || 0);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Layers className="h-4 w-4" />
          Queue Depth
          <span className="text-muted-foreground font-normal">({total} active)</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={120}>
          <BarChart data={data} layout="vertical">
            <XAxis type="number" hide />
            <YAxis type="category" dataKey="name" width={80} />
            <Tooltip />
            <Bar dataKey="value" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
