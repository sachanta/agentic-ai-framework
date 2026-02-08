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
import { WritingPanel } from './WritingPanel';
import { NewsletterPreview } from './NewsletterPreview';
import {
  useNewsletterStatus,
  useNewsletterAgents,
  useResearch,
  useResearchCustom,
  useGenerateNewsletter,
} from '@/hooks/useNewsletter';
import { ArrowLeft, Newspaper, Bot, Info } from 'lucide-react';
import type { Article, ResearchResponse, GenerateResponse, WritingTone } from '@/types/newsletter';

type AppPhase = 'research' | 'writing' | 'preview';

export function NewsletterApp() {
  // Phase management
  const [phase, setPhase] = useState<AppPhase>('research');

  // Research state
  const [researchResult, setResearchResult] = useState<ResearchResponse | null>(null);
  const [selectedArticles, setSelectedArticles] = useState<Article[]>([]);

  // Writing state
  const [tone, setTone] = useState<WritingTone>('professional');
  const [generatedNewsletter, setGeneratedNewsletter] = useState<GenerateResponse | null>(null);

  // Queries and mutations
  const { data: status } = useNewsletterStatus();
  const { data: agents } = useNewsletterAgents();
  const researchMutation = useResearch();
  const researchCustomMutation = useResearchCustom();
  const generateMutation = useGenerateNewsletter();

  const isResearching = researchMutation.isPending || researchCustomMutation.isPending;
  const isGenerating = generateMutation.isPending;
  const researchError = researchMutation.error?.message || researchCustomMutation.error?.message || researchResult?.error;

  // Research handlers
  const handleResearch = (
    topics: string[],
    customPrompt: string | null,
    maxResults: number,
    includeSummaries: boolean
  ) => {
    // Reset state for new research
    setResearchResult(null);
    setSelectedArticles([]);
    setGeneratedNewsletter(null);
    setPhase('research');

    if (customPrompt) {
      researchCustomMutation.mutate(
        {
          prompt: customPrompt,
          max_results: maxResults,
          include_summaries: includeSummaries,
        },
        {
          onSuccess: (data) => {
            setResearchResult(data);
          },
        }
      );
    } else {
      researchMutation.mutate(
        {
          topics,
          max_results: maxResults,
          include_summaries: includeSummaries,
        },
        {
          onSuccess: (data) => {
            setResearchResult(data);
          },
        }
      );
    }
  };

  // Article selection handlers
  const handleArticleSelect = (article: Article, selected: boolean) => {
    if (selected) {
      setSelectedArticles([...selectedArticles, article]);
    } else {
      setSelectedArticles(selectedArticles.filter((a) => a.url !== article.url));
    }
  };

  const handleSelectAll = () => {
    if (researchResult?.articles) {
      setSelectedArticles([...researchResult.articles]);
    }
  };

  const handleClearSelection = () => {
    setSelectedArticles([]);
  };

  // Generate handlers
  const handleGenerate = () => {
    generateMutation.mutate(
      {
        articles: selectedArticles,
        tone,
        include_rag: true,
      },
      {
        onSuccess: (data) => {
          setGeneratedNewsletter(data);
          if (data.success) {
            setPhase('preview');
          }
        },
      }
    );
  };

  const handleRegenerate = () => {
    handleGenerate();
  };

  // Reset to research phase
  const handleBackToResearch = () => {
    setPhase('research');
    setGeneratedNewsletter(null);
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
              <h1 className="text-2xl font-bold">
                {phase === 'preview' ? 'Newsletter Preview' : 'Newsletter Research'}
              </h1>
              {status && <AppStatusBadge status={status.status} />}
            </div>
            <p className="text-muted-foreground">
              {phase === 'preview'
                ? 'Review and customize your generated newsletter'
                : 'Discover content for your newsletter using AI-powered research'}
            </p>
          </div>
          {phase === 'preview' && (
            <Button variant="outline" onClick={handleBackToResearch}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Research
            </Button>
          )}
        </div>
      </div>

      {/* Preview Phase */}
      {phase === 'preview' && generatedNewsletter && (
        <NewsletterPreview
          result={generatedNewsletter}
          onRegenerate={handleRegenerate}
          isRegenerating={isGenerating}
        />
      )}

      {/* Research/Writing Phase */}
      {phase !== 'preview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main content - Panel and Results */}
          <div className="lg:col-span-2 space-y-6">
            <ResearchPanel onResearch={handleResearch} isLoading={isResearching} />

            {/* Writing Panel - shows when articles are selected */}
            <WritingPanel
              selectedArticles={selectedArticles}
              tone={tone}
              onToneChange={setTone}
              onGenerate={handleGenerate}
              onClearSelection={handleClearSelection}
              isGenerating={isGenerating}
            />

            {/* Generation error */}
            {generateMutation.error && (
              <Card className="border-destructive">
                <CardContent className="pt-6">
                  <p className="text-destructive text-sm">
                    Failed to generate newsletter: {generateMutation.error.message}
                  </p>
                </CardContent>
              </Card>
            )}

            <ArticleResults
              articles={researchResult?.articles || null}
              metadata={researchResult?.metadata || null}
              isLoading={isResearching}
              error={!isResearching ? researchError : null}
              selectedArticles={selectedArticles}
              onArticleSelect={handleArticleSelect}
              onSelectAll={handleSelectAll}
              onClearSelection={handleClearSelection}
            />
          </div>

          {/* Sidebar - Info */}
          <div className="space-y-6">
            {/* About */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Info className="h-4 w-4" />
                  How It Works
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground space-y-3">
                <div className="space-y-2">
                  <p className="font-medium text-foreground">1. Research</p>
                  <p>Enter topics or a custom prompt to discover relevant articles.</p>
                </div>
                <div className="space-y-2">
                  <p className="font-medium text-foreground">2. Select</p>
                  <p>Choose the articles you want to include in your newsletter.</p>
                </div>
                <div className="space-y-2">
                  <p className="font-medium text-foreground">3. Generate</p>
                  <p>Pick a tone and generate your AI-powered newsletter.</p>
                </div>
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
      )}
    </div>
  );
}
