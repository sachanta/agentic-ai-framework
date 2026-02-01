import { useParams, Navigate } from 'react-router-dom';
import { ToolDetail } from '@/components/tools/ToolDetail';
import { useTool } from '@/hooks/useTools';
import { ROUTES } from '@/utils/constants';
import { Skeleton } from '@/components/ui/skeleton';

export function ToolDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: tool, isLoading, error } = useTool(id!);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-48" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (error || !tool) {
    return <Navigate to={ROUTES.TOOLS} replace />;
  }

  return <ToolDetail tool={tool} />;
}

export default ToolDetailPage;
