/**
 * Main Hello World app component
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { AppStatusBadge } from '../AppStatusBadge';
import { GreetingForm } from './GreetingForm';
import { GreetingResult } from './GreetingResult';
import { useHelloWorldStatus, useHelloWorldAgents, useExecuteHelloWorld } from '@/hooks/useHelloWorld';
import { ArrowLeft, Hand, Bot, Info } from 'lucide-react';
import type { GreetingStyle, HelloWorldResponse } from '@/types/app';

export function HelloWorldApp() {
  const [result, setResult] = useState<HelloWorldResponse | null>(null);

  const { data: status } = useHelloWorldStatus();
  const { data: agents } = useHelloWorldAgents();
  const executeMutation = useExecuteHelloWorld();

  const handleGenerateGreeting = (name: string, style: GreetingStyle) => {
    executeMutation.mutate(
      { name, style },
      {
        onSuccess: (data) => {
          setResult(data);
        },
      }
    );
  };

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
            <Hand className="h-8 w-8 text-primary" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">Hello World</h1>
              {status && <AppStatusBadge status={status.status} />}
            </div>
            <p className="text-muted-foreground">A sample multi-agent platform for demonstration</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content - Form and Result */}
        <div className="lg:col-span-2 space-y-6">
          <GreetingForm
            onSubmit={handleGenerateGreeting}
            isLoading={executeMutation.isPending}
          />

          <GreetingResult result={result} />

          {executeMutation.isError && (
            <Card className="border-destructive">
              <CardContent className="pt-6">
                <p className="text-destructive">
                  Error: {executeMutation.error?.message || 'Failed to generate greeting'}
                </p>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar - Info */}
        <div className="space-y-6">
          {/* About */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Info className="h-4 w-4" />
                About this App
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              <p>
                The Hello World app demonstrates the multi-agent platform architecture.
                It uses a simple greeter agent to generate personalized greetings based on
                the name and style you provide.
              </p>
            </CardContent>
          </Card>

          {/* Agents */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Bot className="h-4 w-4" />
                Agents
              </CardTitle>
              <CardDescription>
                Agents powering this app
              </CardDescription>
            </CardHeader>
            <CardContent>
              {agents && agents.length > 0 ? (
                <div className="space-y-3">
                  {agents.map((agent, index) => (
                    <div key={agent.id}>
                      {index > 0 && <Separator className="my-3" />}
                      <div>
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-sm">{agent.name}</span>
                          <AppStatusBadge status={agent.status} size="sm" />
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                          {agent.description}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground text-center py-2">
                  Loading agents...
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
