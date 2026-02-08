/**
 * Writing Panel component for generating newsletter from selected articles
 */
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { PenLine, Loader2, FileText, X } from 'lucide-react';
import type { Article, WritingTone } from '@/types/newsletter';

interface WritingPanelProps {
  selectedArticles: Article[];
  tone: WritingTone;
  onToneChange: (tone: WritingTone) => void;
  onGenerate: () => void;
  onClearSelection: () => void;
  isGenerating: boolean;
}

const TONE_OPTIONS: { value: WritingTone; label: string; description: string }[] = [
  { value: 'professional', label: 'Professional', description: 'Formal, business-appropriate' },
  { value: 'casual', label: 'Casual', description: 'Friendly, conversational' },
  { value: 'formal', label: 'Formal', description: 'Academic, structured' },
  { value: 'enthusiastic', label: 'Enthusiastic', description: 'Energetic, engaging' },
];

export function WritingPanel({
  selectedArticles,
  tone,
  onToneChange,
  onGenerate,
  onClearSelection,
  isGenerating,
}: WritingPanelProps) {
  const articleCount = selectedArticles.length;

  if (articleCount === 0) {
    return null;
  }

  return (
    <Card className="border-primary/50 bg-primary/5">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <PenLine className="h-5 w-5 text-primary" />
            <CardTitle className="text-base">Generate Newsletter</CardTitle>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClearSelection}
            disabled={isGenerating}
          >
            <X className="h-4 w-4 mr-1" />
            Clear
          </Button>
        </div>
        <CardDescription>
          Create a newsletter from your selected articles
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Selected articles summary */}
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant="secondary" className="text-sm">
            <FileText className="h-3 w-3 mr-1" />
            {articleCount} article{articleCount !== 1 ? 's' : ''} selected
          </Badge>
          <div className="flex gap-1 flex-wrap">
            {selectedArticles.slice(0, 3).map((article, index) => (
              <Badge key={index} variant="outline" className="text-xs max-w-[150px] truncate">
                {article.title}
              </Badge>
            ))}
            {articleCount > 3 && (
              <Badge variant="outline" className="text-xs">
                +{articleCount - 3} more
              </Badge>
            )}
          </div>
        </div>

        {/* Tone selector */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Writing Tone</label>
          <Select
            value={tone}
            onValueChange={(value) => onToneChange(value as WritingTone)}
            disabled={isGenerating}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select tone" />
            </SelectTrigger>
            <SelectContent>
              {TONE_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  <div className="flex flex-col">
                    <span>{option.label}</span>
                    <span className="text-xs text-muted-foreground">{option.description}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Generate button */}
        <Button
          onClick={onGenerate}
          disabled={isGenerating || articleCount === 0}
          className="w-full"
          size="lg"
        >
          {isGenerating ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Generating Newsletter...
            </>
          ) : (
            <>
              <PenLine className="h-4 w-4 mr-2" />
              Generate Newsletter
            </>
          )}
        </Button>

        {isGenerating && (
          <p className="text-xs text-muted-foreground text-center">
            This may take a minute. The AI is crafting your newsletter...
          </p>
        )}
      </CardContent>
    </Card>
  );
}
