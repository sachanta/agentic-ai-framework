/**
 * Greeting result display for Hello World app
 */
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MessageSquare, Bot, Clock } from 'lucide-react';
import type { HelloWorldResponse } from '@/types/app';

interface GreetingResultProps {
  result: HelloWorldResponse | null;
}

export function GreetingResult({ result }: GreetingResultProps) {
  if (!result) {
    return (
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center justify-center py-12 text-center">
          <MessageSquare className="h-12 w-12 text-muted-foreground/50 mb-4" />
          <p className="text-muted-foreground">
            Your generated greeting will appear here
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-primary/20 bg-primary/5">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5 text-primary" />
          Result
        </CardTitle>
        <CardDescription>Generated greeting from the AI agent</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Greeting */}
        <div className="p-4 rounded-lg bg-background border">
          <p className="text-lg font-medium">{result.greeting}</p>
        </div>

        {/* Metadata */}
        <div className="flex flex-wrap gap-3 text-sm">
          <div className="flex items-center gap-1.5">
            <Bot className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">Agent:</span>
            <Badge variant="secondary">{result.agent}</Badge>
          </div>

          {result.metadata?.style && (
            <div className="flex items-center gap-1.5">
              <span className="text-muted-foreground">Style:</span>
              <Badge variant="outline">{result.metadata.style as string}</Badge>
            </div>
          )}

          {result.metadata?.timestamp && (
            <div className="flex items-center gap-1.5">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">
                {new Date(result.metadata.timestamp as string).toLocaleTimeString()}
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
