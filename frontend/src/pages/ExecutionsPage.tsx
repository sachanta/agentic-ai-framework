import { ExecutionList } from '@/components/executions/ExecutionList';

export function ExecutionsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Executions</h1>
        <p className="text-muted-foreground">Monitor workflow executions</p>
      </div>
      <ExecutionList />
    </div>
  );
}

export default ExecutionsPage;
