/**
 * App detail page - shows app info and redirects to app-specific page
 */
import { useParams, useNavigate } from 'react-router-dom';
import { AppDetail } from '@/components/apps/AppDetail';
import { useApp, useAppAgents } from '@/hooks/useApps';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';

export default function AppDetailPage() {
  const { appId } = useParams<{ appId: string }>();
  const navigate = useNavigate();

  const { data: app, isLoading: appLoading, error: appError } = useApp(appId || '');
  const { data: agents = [] } = useAppAgents(appId || '');

  const handleLaunch = () => {
    // Navigate to app-specific page
    navigate(`/apps/${appId}`);
  };

  if (appLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-60 w-full" />
      </div>
    );
  }

  if (appError || !app) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <AlertCircle className="h-12 w-12 text-destructive mb-4" />
        <h3 className="text-lg font-semibold">App not found</h3>
        <p className="text-muted-foreground mb-4">
          The app you're looking for doesn't exist or couldn't be loaded.
        </p>
        <Button asChild>
          <Link to="/apps">Back to Apps</Link>
        </Button>
      </div>
    );
  }

  return <AppDetail app={app} agents={agents} onLaunch={handleLaunch} />;
}
