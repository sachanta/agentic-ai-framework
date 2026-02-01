/**
 * App card component for displaying app in grid
 */
import { Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AppStatusBadge } from './AppStatusBadge';
import { Hand, Bot, ArrowRight } from 'lucide-react';
import type { App } from '@/types/app';

interface AppCardProps {
  app: App;
}

// Map app icons to Lucide icons
const iconMap: Record<string, React.ElementType> = {
  'hand-wave': Hand,
  'bot': Bot,
};

export function AppCard({ app }: AppCardProps) {
  const IconComponent = iconMap[app.icon || ''] || Bot;

  return (
    <Card className="flex flex-col hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <IconComponent className="h-6 w-6 text-primary" />
            </div>
            <div>
              <CardTitle className="text-lg">{app.name}</CardTitle>
              <p className="text-xs text-muted-foreground">v{app.version}</p>
            </div>
          </div>
          <AppStatusBadge status={app.status} size="sm" />
        </div>
      </CardHeader>
      <CardContent className="flex-1">
        <CardDescription className="line-clamp-2">{app.description}</CardDescription>
        <div className="mt-3 flex items-center gap-2 text-sm text-muted-foreground">
          <Bot className="h-4 w-4" />
          <span>{app.agents.length} agent{app.agents.length !== 1 ? 's' : ''}</span>
        </div>
      </CardContent>
      <CardFooter>
        <Button asChild className="w-full">
          <Link to={`/apps/${app.id}`}>
            Launch
            <ArrowRight className="ml-2 h-4 w-4" />
          </Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
