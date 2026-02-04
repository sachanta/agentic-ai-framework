/**
 * Article results display for Newsletter app
 */
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  FileText,
  ExternalLink,
  Clock,
  TrendingUp,
  AlertCircle,
  Newspaper,
  Sparkles,
} from 'lucide-react';
import type { Article, ResearchMetadata } from '@/types/newsletter';

interface ArticleResultsProps {
  articles: Article[] | null;
  metadata: ResearchMetadata | null;
  isLoading?: boolean;
  error?: string | null;
}

function ArticleCard({ article }: { article: Article }) {
  const scorePercent = Math.round(article.relevance_score * 100);
  const scoreColor = scorePercent >= 70 ? 'text-green-600' : scorePercent >= 50 ? 'text-yellow-600' : 'text-gray-500';

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="pt-4">
        <div className="space-y-3">
          {/* Title and Link */}
          <div className="flex items-start justify-between gap-2">
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-primary hover:underline flex items-center gap-1 flex-1"
            >
              {article.title}
              <ExternalLink className="h-3 w-3 flex-shrink-0" />
            </a>
          </div>

          {/* Source and Score */}
          <div className="flex items-center gap-3 flex-wrap">
            <Badge variant="outline" className="text-xs">
              {article.source}
            </Badge>
            <div className={`flex items-center gap-1 text-xs ${scoreColor}`}>
              <TrendingUp className="h-3 w-3" />
              <span>{scorePercent}% relevance</span>
            </div>
            {article.published_date && (
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Clock className="h-3 w-3" />
                <span>{new Date(article.published_date).toLocaleDateString()}</span>
              </div>
            )}
          </div>

          {/* Summary */}
          {article.summary && (
            <div className="space-y-1">
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Sparkles className="h-3 w-3" />
                <span>AI Summary</span>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {article.summary}
              </p>
            </div>
          )}

          {/* Key Takeaway */}
          {article.key_takeaway && (
            <div className="bg-primary/5 rounded-md p-2 text-sm">
              <span className="font-medium">Key takeaway:</span> {article.key_takeaway}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map((i) => (
        <Card key={i}>
          <CardContent className="pt-4 space-y-3">
            <Skeleton className="h-5 w-3/4" />
            <div className="flex gap-2">
              <Skeleton className="h-5 w-20" />
              <Skeleton className="h-5 w-24" />
            </div>
            <Skeleton className="h-16 w-full" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function EmptyState() {
  return (
    <Card className="border-dashed">
      <CardContent className="flex flex-col items-center justify-center py-12 text-center">
        <Newspaper className="h-12 w-12 text-muted-foreground/50 mb-4" />
        <p className="text-muted-foreground">
          Research results will appear here
        </p>
        <p className="text-sm text-muted-foreground mt-1">
          Enter topics or a custom prompt to discover content
        </p>
      </CardContent>
    </Card>
  );
}

export function ArticleResults({ articles, metadata, isLoading, error }: ArticleResultsProps) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-primary" />
          <span className="font-medium">Searching for content...</span>
        </div>
        <LoadingSkeleton />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0" />
            <div>
              <h4 className="font-medium text-destructive">Research Failed</h4>
              <p className="text-sm text-muted-foreground mt-1">{error}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!articles) {
    return <EmptyState />;
  }

  if (articles.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12 text-center">
          <FileText className="h-12 w-12 text-muted-foreground/50 mb-4" />
          <p className="text-muted-foreground">No articles found</p>
          <p className="text-sm text-muted-foreground mt-1">
            Try adjusting your topics or search criteria
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Results Header */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <FileText className="h-5 w-5 text-primary" />
            Research Results
          </CardTitle>
          <CardDescription className="flex flex-wrap items-center gap-x-4 gap-y-1">
            <span>Found {metadata?.total_found || articles.length} articles</span>
            {metadata && metadata.after_filter !== metadata.total_found && (
              <span className="text-muted-foreground">
                ({metadata.after_filter} after filtering)
              </span>
            )}
            {metadata?.cached && (
              <Badge variant="outline" className="text-xs">
                Cached
              </Badge>
            )}
            {metadata?.topics && metadata.topics.length > 0 && (
              <span className="text-muted-foreground">
                Topics: {metadata.topics.join(', ')}
              </span>
            )}
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Articles */}
      <div className="space-y-3">
        {articles.map((article, index) => (
          <ArticleCard key={`${article.url}-${index}`} article={article} />
        ))}
      </div>
    </div>
  );
}
