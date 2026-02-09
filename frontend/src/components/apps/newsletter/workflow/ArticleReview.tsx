/**
 * Article review checkpoint component
 *
 * Checkpoint 1: Review and reorder selected articles
 * Features:
 * - Drag-to-reorder articles
 * - Remove articles
 * - View article details
 * - Score indicators
 */
import { useState, useCallback } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { ScrollArea } from '@/components/ui/scroll-area';
import { CheckpointPanel } from './CheckpointPanel';
import {
  GripVertical,
  ExternalLink,
  Trash2,
  ChevronDown,
  ChevronUp,
  Star,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Article, Checkpoint, CheckpointAction } from '@/types/newsletter';

interface ArticleReviewProps {
  checkpoint: Checkpoint;
  articles: Article[];
  onApprove: (selectedArticles: Article[], feedback?: string) => void;
  onReject: (feedback?: string) => void;
  isLoading?: boolean;
  loadingAction?: CheckpointAction | null;
}

export function ArticleReview({
  checkpoint,
  articles: initialArticles,
  onApprove,
  onReject,
  isLoading = false,
  loadingAction = null,
}: ArticleReviewProps) {
  const [articles, setArticles] = useState<Article[]>(initialArticles);
  const [selectedUrls, setSelectedUrls] = useState<Set<string>>(
    new Set(initialArticles.map((a) => a.url))
  );
  const [expandedUrl, setExpandedUrl] = useState<string | null>(null);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);

  // Toggle article selection
  const toggleArticle = useCallback((url: string) => {
    setSelectedUrls((prev) => {
      const next = new Set(prev);
      if (next.has(url)) {
        next.delete(url);
      } else {
        next.add(url);
      }
      return next;
    });
  }, []);

  // Remove article from list
  const removeArticle = useCallback((url: string) => {
    setArticles((prev) => prev.filter((a) => a.url !== url));
    setSelectedUrls((prev) => {
      const next = new Set(prev);
      next.delete(url);
      return next;
    });
  }, []);

  // Drag and drop handlers
  const handleDragStart = (index: number) => {
    setDraggedIndex(index);
  };

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault();
    if (draggedIndex === null || draggedIndex === index) return;

    const newArticles = [...articles];
    const [dragged] = newArticles.splice(draggedIndex, 1);
    newArticles.splice(index, 0, dragged);
    setArticles(newArticles);
    setDraggedIndex(index);
  };

  const handleDragEnd = () => {
    setDraggedIndex(null);
  };

  // Move article up/down
  const moveArticle = (index: number, direction: 'up' | 'down') => {
    const newIndex = direction === 'up' ? index - 1 : index + 1;
    if (newIndex < 0 || newIndex >= articles.length) return;

    const newArticles = [...articles];
    [newArticles[index], newArticles[newIndex]] = [newArticles[newIndex], newArticles[index]];
    setArticles(newArticles);
  };

  // Handle approval
  const handleApprove = (feedback?: string) => {
    const selectedArticles = articles.filter((a) => selectedUrls.has(a.url));
    onApprove(selectedArticles, feedback);
  };

  // Get score color
  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 dark:text-green-400';
    if (score >= 0.6) return 'text-amber-600 dark:text-amber-400';
    return 'text-red-600 dark:text-red-400';
  };

  const selectedCount = selectedUrls.size;

  return (
    <CheckpointPanel
      checkpoint={checkpoint}
      onApprove={handleApprove}
      onReject={onReject}
      isLoading={isLoading}
      loadingAction={loadingAction}
      showEdit={false}
    >
      <div className="space-y-4">
        {/* Summary */}
        <div className="flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            {selectedCount} of {articles.length} articles selected
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSelectedUrls(new Set(articles.map((a) => a.url)))}
            >
              Select All
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSelectedUrls(new Set())}
            >
              Clear
            </Button>
          </div>
        </div>

        {/* Article list */}
        <ScrollArea className="h-[400px] pr-4">
          <div className="space-y-2">
            {articles.map((article, index) => {
              const isSelected = selectedUrls.has(article.url);
              const isExpanded = expandedUrl === article.url;

              return (
                <Card
                  key={article.url}
                  draggable
                  onDragStart={() => handleDragStart(index)}
                  onDragOver={(e) => handleDragOver(e, index)}
                  onDragEnd={handleDragEnd}
                  className={cn(
                    'transition-all cursor-move',
                    isSelected ? 'border-primary/50 bg-primary/5' : 'opacity-60',
                    draggedIndex === index && 'opacity-50 scale-[0.98]'
                  )}
                >
                  <CardContent className="p-3">
                    <div className="flex items-start gap-3">
                      {/* Drag handle */}
                      <div className="flex flex-col items-center gap-1 text-muted-foreground">
                        <GripVertical className="h-4 w-4" />
                        <span className="text-xs font-medium">{index + 1}</span>
                      </div>

                      {/* Checkbox */}
                      <Checkbox
                        checked={isSelected}
                        onCheckedChange={() => toggleArticle(article.url)}
                        className="mt-1"
                      />

                      {/* Article content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <h4 className="font-medium text-sm line-clamp-1">
                              {article.title}
                            </h4>
                            <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                              <span>{article.source}</span>
                              {article.published_date && (
                                <>
                                  <span>•</span>
                                  <span>{article.published_date}</span>
                                </>
                              )}
                            </div>
                          </div>

                          {/* Score */}
                          <div className="flex items-center gap-1">
                            <Star className={cn('h-3 w-3', getScoreColor(article.score))} />
                            <span className={cn('text-xs font-medium', getScoreColor(article.score))}>
                              {(article.score * 100).toFixed(0)}
                            </span>
                          </div>
                        </div>

                        {/* Expanded content */}
                        {isExpanded && (
                          <div className="mt-3 space-y-2">
                            {article.summary && (
                              <p className="text-sm text-muted-foreground">
                                {article.summary}
                              </p>
                            )}
                            {article.key_takeaway && (
                              <div className="text-sm">
                                <span className="font-medium">Key takeaway: </span>
                                {article.key_takeaway}
                              </div>
                            )}
                            <div className="flex flex-wrap gap-1">
                              <Badge variant="secondary" className="text-xs">
                                Relevance: {(article.relevance_score * 100).toFixed(0)}%
                              </Badge>
                              <Badge variant="secondary" className="text-xs">
                                Quality: {(article.quality_score * 100).toFixed(0)}%
                              </Badge>
                            </div>
                          </div>
                        )}

                        {/* Actions */}
                        <div className="flex items-center gap-2 mt-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 px-2 text-xs"
                            onClick={() => setExpandedUrl(isExpanded ? null : article.url)}
                          >
                            {isExpanded ? (
                              <>
                                <ChevronUp className="h-3 w-3 mr-1" />
                                Less
                              </>
                            ) : (
                              <>
                                <ChevronDown className="h-3 w-3 mr-1" />
                                More
                              </>
                            )}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 px-2 text-xs"
                            asChild
                          >
                            <a href={article.url} target="_blank" rel="noopener noreferrer">
                              <ExternalLink className="h-3 w-3 mr-1" />
                              View
                            </a>
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 px-2 text-xs text-destructive hover:text-destructive"
                            onClick={() => removeArticle(article.url)}
                          >
                            <Trash2 className="h-3 w-3 mr-1" />
                            Remove
                          </Button>
                        </div>
                      </div>

                      {/* Reorder buttons */}
                      <div className="flex flex-col gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6"
                          onClick={() => moveArticle(index, 'up')}
                          disabled={index === 0}
                        >
                          <ChevronUp className="h-3 w-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6"
                          onClick={() => moveArticle(index, 'down')}
                          disabled={index === articles.length - 1}
                        >
                          <ChevronDown className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </ScrollArea>

        {articles.length === 0 && (
          <div className="text-center py-8 text-muted-foreground">
            No articles to review
          </div>
        )}
      </div>
    </CheckpointPanel>
  );
}

export default ArticleReview;
