/**
 * Apps listing page
 */
import { useState } from 'react';
import { AppList } from '@/components/apps/AppList';
import { useApps } from '@/hooks/useApps';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Boxes } from 'lucide-react';

type StatusFilter = 'all' | 'active' | 'inactive';

export default function AppsPage() {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const { data: apps = [], isLoading, error } = useApps();

  const filteredApps = apps.filter((app) => {
    if (statusFilter === 'all') return true;
    return app.status === statusFilter;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Boxes className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-2xl font-bold">Apps</h1>
            <p className="text-muted-foreground">
              Browse and launch available multi-agent applications
            </p>
          </div>
        </div>

        <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value as StatusFilter)}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Apps</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* App Grid */}
      <AppList apps={filteredApps} isLoading={isLoading} error={error} />
    </div>
  );
}
