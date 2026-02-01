/**
 * App list component - displays grid of app cards
 */
import { AppCard } from './AppCard';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, Boxes } from 'lucide-react';
import type { App } from '@/types/app';

interface AppListProps {
  apps: App[];
  isLoading?: boolean;
  error?: Error | null;
}

export function AppList({ apps, isLoading, error }: AppListProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="space-y-3">
            <Skeleton className="h-[200px] w-full rounded-lg" />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <AlertCircle className="h-12 w-12 text-destructive mb-4" />
        <h3 className="text-lg font-semibold">Failed to load apps</h3>
        <p className="text-muted-foreground">{error.message}</p>
      </div>
    );
  }

  if (apps.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <Boxes className="h-12 w-12 text-muted-foreground mb-4" />
        <h3 className="text-lg font-semibold">No apps available</h3>
        <p className="text-muted-foreground">Apps will appear here when they are added to the system.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {apps.map((app) => (
        <AppCard key={app.id} app={app} />
      ))}
    </div>
  );
}
