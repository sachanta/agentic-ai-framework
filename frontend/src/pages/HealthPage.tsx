import { HealthDashboard } from '@/components/health/HealthDashboard';

export function HealthPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">System Health</h1>
        <p className="text-muted-foreground">Monitor system status and performance</p>
      </div>
      <HealthDashboard />
    </div>
  );
}

export default HealthPage;
