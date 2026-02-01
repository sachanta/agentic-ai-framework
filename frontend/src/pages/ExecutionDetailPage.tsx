import { useParams, Navigate } from 'react-router-dom';
import { ExecutionDetail } from '@/components/executions/ExecutionDetail';
import { useExecution } from '@/hooks/useExecutions';
import { ROUTES } from '@/utils/constants';
import { Skeleton } from '@/components/ui/skeleton';

export function ExecutionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: execution, isLoading, error } = useExecution(id!);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-64" />
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (error || !execution) {
    return <Navigate to={ROUTES.EXECUTIONS} replace />;
  }

  return <ExecutionDetail execution={execution} />;
}

export default ExecutionDetailPage;
