import { WorkflowList } from '@/components/workflows/WorkflowList';

export function WorkflowsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Workflows</h1>
        <p className="text-muted-foreground">Manage your automation workflows</p>
      </div>
      <WorkflowList />
    </div>
  );
}

export default WorkflowsPage;
