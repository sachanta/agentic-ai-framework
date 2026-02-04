/**
 * Main Newsletter app component
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { AppStatusBadge } from '../AppStatusBadge';
import { ResearchPanel } from './ResearchPanel';
import { ArticleResults } from './ArticleResults';
import { useNewsletterStatus, useNewsletterAgents, useResearch, useResearchCustom } from '@/hooks/useNewsletter';
import { ArrowLeft, Newspaper, Bot, Info } from 'lucide-react';
import type { ResearchResponse } from '@/types/newsletter';

export function NewsletterApp() {
  const [result, setResult] = useState<ResearchResponse | null>(null);

  const { data: status } = useNewsletterStatus();
  const { data: agents } = useNewsletterAgents();
  const researchMutation = useResearch();
  const researchCustomMutation = useResearchCustom();

  const isLoading = researchMutation.isPending || researchCustomMutation.isPending;
  const error = researchMutation.error?.message || researchCustomMutation.error?.message || result?.error;

  const handleResearch = (
    topics: string[],
    customPrompt: string | null,
    maxResults: number,
    includeSummaries: boolean
  ) => {
    // Reset previous results
    setResult(null);

    if (customPrompt) {
      // Use custom prompt endpoint
      researchCustomMutation.mutate(
        {
          prompt: customPrompt,
          max_results: maxResults,
          include_summaries: includeSummaries,
        },
        {
          onSuccess: (data) => {
            setResult(data);
          },
        }
      );
    } else {
      // Use topics endpoint
      researchMutation.mutate(
        {
          topics,
          max_results: maxResults,
          include_summaries: includeSummaries,
        },
        {
          onSuccess: (data) => {
            setResult(data);
          },
        }
      );
    }
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
            <Newspaper className="h-8 w-8 text-primary" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">Newsletter Research</h1>
              {status && <AppStatusBadge status={status.status} />}
            </div>
            <p className="text-muted-foreground">
              Discover content for your newsletter using AI-powered research
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content - Panel and Results */}
        <div className="lg:col-span-2 space-y-6">
          <ResearchPanel onResearch={handleResearch} isLoading={isLoading} />

          <ArticleResults
            articles={result?.articles || null}
            metadata={result?.metadata || null}
            isLoading={isLoading}
            error={!isLoading ? error : null}
          />
        </div>

        {/* Sidebar - Info */}
        <div className="space-y-6">
          {/* About */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Info className="h-4 w-4" />
                About Research
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground space-y-3">
              <p>
                The Research Agent searches for articles using Tavily AI search,
                filters them by quality and relevance, and generates AI summaries.
              </p>
              <p>
                <strong>Topics:</strong> Enter specific keywords like "AI", "observability", "DevOps"
              </p>
              <p>
                <strong>Custom Prompt:</strong> Describe what you're looking for in natural language,
                e.g., "Latest developments in quantum computing for healthcare"
              </p>
            </CardContent>
          </Card>

          {/* LLM Info */}
          {status && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Bot className="h-4 w-4" />
                  LLM Configuration
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Provider</span>
                    <span className="font-medium">{status.llm_provider}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Model</span>
                    <span className="font-medium">{status.llm_model}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Agents */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Bot className="h-4 w-4" />
                Agents
              </CardTitle>
              <CardDescription>Agents powering this platform</CardDescription>
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
