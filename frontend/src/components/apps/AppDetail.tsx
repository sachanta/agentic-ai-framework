/**
 * App detail component - displays full app information
 */
import { Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { AppStatusBadge } from './AppStatusBadge';
import { ArrowLeft, Bot, Play, Hand } from 'lucide-react';
import type { App, AppAgent } from '@/types/app';

interface AppDetailProps {
  app: App;
  agents?: AppAgent[];
  onLaunch?: () => void;
}

// Map app icons to Lucide icons
const iconMap: Record<string, React.ElementType> = {
  'hand-wave': Hand,
  'bot': Bot,
};

export function AppDetail({ app, agents = [], onLaunch }: AppDetailProps) {
  const IconComponent = iconMap[app.icon || ''] || Bot;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link to="/apps">
            <ArrowLeft className="h-5 w-5" />
          </Link>
        </Button>
        <div className="flex items-center gap-4 flex-1">
          <div className="p-3 rounded-lg bg-primary/10">
            <IconComponent className="h-8 w-8 text-primary" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">{app.name}</h1>
              <AppStatusBadge status={app.status} />
            </div>
            <p className="text-muted-foreground">Version {app.version}</p>
          </div>
          {onLaunch && app.status === 'active' && (
            <Button onClick={onLaunch} size="lg">
              <Play className="mr-2 h-5 w-5" />
              Launch App
            </Button>
          )}
        </div>
      </div>

      {/* Description */}
      <Card>
        <CardHeader>
          <CardTitle>About</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">{app.description}</p>
        </CardContent>
      </Card>

      {/* Agents */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            Agents
          </CardTitle>
          <CardDescription>
            This app uses {agents.length} agent{agents.length !== 1 ? 's' : ''} to process requests
          </CardDescription>
        </CardHeader>
        <CardContent>
          {agents.length === 0 ? (
            <p className="text-muted-foreground text-center py-4">No agents available</p>
          ) : (
            <div className="space-y-3">
              {agents.map((agent, index) => (
                <div key={agent.id}>
                  {index > 0 && <Separator className="my-3" />}
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-medium">{agent.name}</h4>
                      <p className="text-sm text-muted-foreground">{agent.description}</p>
                    </div>
                    <AppStatusBadge status={agent.status} size="sm" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
