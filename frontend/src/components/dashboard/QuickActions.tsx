import { Link } from 'react-router-dom';
import { Plus, Play, RefreshCw, FileText } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ROUTES } from '@/utils/constants';

export function QuickActions() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-2">
        <Button variant="outline" className="h-auto py-4 flex-col" asChild>
          <Link to={ROUTES.AGENTS}>
            <Plus className="h-5 w-5 mb-1" />
            <span className="text-xs">New Agent</span>
          </Link>
        </Button>

        <Button variant="outline" className="h-auto py-4 flex-col" asChild>
          <Link to={ROUTES.WORKFLOWS}>
            <Plus className="h-5 w-5 mb-1" />
            <span className="text-xs">New Workflow</span>
          </Link>
        </Button>

        <Button variant="outline" className="h-auto py-4 flex-col" asChild>
          <Link to={ROUTES.EXECUTIONS}>
            <Play className="h-5 w-5 mb-1" />
            <span className="text-xs">Executions</span>
          </Link>
        </Button>

        <Button variant="outline" className="h-auto py-4 flex-col" asChild>
          <Link to={ROUTES.LOGS}>
            <FileText className="h-5 w-5 mb-1" />
            <span className="text-xs">View Logs</span>
          </Link>
        </Button>
      </CardContent>
    </Card>
  );
}
