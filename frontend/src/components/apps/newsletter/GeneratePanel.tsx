/**
 * Newsletter generation panel
 *
 * Form for initiating a new newsletter generation workflow
 * Collects topics, tone, and other preferences
 */
import { useState } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import {
  Sparkles,
  X,
  Plus,
  Loader2,
  Wand2,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useFormDraft } from '@/store/newsletterStore';
import type { WritingTone } from '@/types/newsletter';

const TONE_OPTIONS: { value: WritingTone; label: string; description: string }[] = [
  { value: 'professional', label: 'Professional', description: 'Formal and business-appropriate' },
  { value: 'casual', label: 'Casual', description: 'Friendly and conversational' },
  { value: 'formal', label: 'Formal', description: 'Traditional and structured' },
  { value: 'enthusiastic', label: 'Enthusiastic', description: 'Energetic and engaging' },
];

interface GeneratePanelProps {
  onGenerate: (options: {
    topics: string[];
    tone: string;
    maxArticles: number;
    customPrompt?: string;
    includeRag: boolean;
  }) => void;
  isLoading?: boolean;
  className?: string;
}

export function GeneratePanel({
  onGenerate,
  isLoading = false,
  className,
}: GeneratePanelProps) {
  // Use store for persistent state
  const {
    topics,
    tone,
    customPrompt,
    maxArticles,
    addResearchTopic,
    removeResearchTopic,
    setSelectedTone,
    setCustomPrompt,
    setMaxArticles,
  } = useFormDraft();

  const [topicInput, setTopicInput] = useState('');
  const [useCustomPrompt, setUseCustomPrompt] = useState(false);
  const [includeRag, setIncludeRag] = useState(true);

  // Add topic handler
  const handleAddTopic = () => {
    if (topicInput.trim()) {
      addResearchTopic(topicInput.trim());
      setTopicInput('');
    }
  };

  // Handle enter key
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTopic();
    }
  };

  // Handle generate
  const handleGenerate = () => {
    onGenerate({
      topics,
      tone,
      maxArticles,
      customPrompt: useCustomPrompt ? customPrompt : undefined,
      includeRag,
    });
  };

  const canGenerate = topics.length > 0 || (useCustomPrompt && customPrompt.trim());

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          Generate Newsletter
        </CardTitle>
        <CardDescription>
          Configure your newsletter preferences and start the AI-powered generation
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Topics */}
        <div className="space-y-3">
          <Label>Topics</Label>
          <div className="flex gap-2">
            <Input
              value={topicInput}
              onChange={(e) => setTopicInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter a topic (e.g., AI, Technology)"
              disabled={useCustomPrompt}
            />
            <Button
              type="button"
              variant="outline"
              onClick={handleAddTopic}
              disabled={!topicInput.trim() || useCustomPrompt}
            >
              <Plus className="h-4 w-4" />
            </Button>
          </div>
          {topics.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {topics.map((topic) => (
                <Badge
                  key={topic}
                  variant="secondary"
                  className="flex items-center gap-1"
                >
                  {topic}
                  <button
                    onClick={() => removeResearchTopic(topic)}
                    className="ml-1 hover:text-destructive"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
          )}
        </div>

        {/* Custom prompt toggle */}
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label>Use custom prompt</Label>
            <p className="text-xs text-muted-foreground">
              Write your own research instructions
            </p>
          </div>
          <Switch
            checked={useCustomPrompt}
            onCheckedChange={setUseCustomPrompt}
          />
        </div>

        {useCustomPrompt && (
          <Textarea
            value={customPrompt}
            onChange={(e) => setCustomPrompt(e.target.value)}
            placeholder="Find articles about emerging AI trends in healthcare, focusing on recent breakthroughs..."
            rows={3}
          />
        )}

        {/* Tone selection */}
        <div className="space-y-3">
          <Label>Writing Tone</Label>
          <RadioGroup
            value={tone}
            onValueChange={setSelectedTone}
            className="grid grid-cols-2 gap-2"
          >
            {TONE_OPTIONS.map((option) => (
              <div key={option.value}>
                <RadioGroupItem
                  value={option.value}
                  id={`tone-${option.value}`}
                  className="peer sr-only"
                />
                <Label
                  htmlFor={`tone-${option.value}`}
                  className={cn(
                    'flex flex-col items-center justify-center rounded-md border-2 border-muted bg-popover p-3 hover:bg-accent hover:text-accent-foreground cursor-pointer',
                    'peer-data-[state=checked]:border-primary [&:has([data-state=checked])]:border-primary'
                  )}
                >
                  <span className="font-medium text-sm">{option.label}</span>
                  <span className="text-xs text-muted-foreground text-center">
                    {option.description}
                  </span>
                </Label>
              </div>
            ))}
          </RadioGroup>
        </div>

        {/* Max articles */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label>Max Articles</Label>
            <span className="text-sm text-muted-foreground">{maxArticles}</span>
          </div>
          <Slider
            value={[maxArticles]}
            onValueChange={(values: number[]) => setMaxArticles(values[0])}
            min={3}
            max={20}
            step={1}
          />
          <p className="text-xs text-muted-foreground">
            Maximum number of articles to include in the newsletter
          </p>
        </div>

        {/* RAG toggle */}
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label>Use RAG examples</Label>
            <p className="text-xs text-muted-foreground">
              Learn from previous successful newsletters
            </p>
          </div>
          <Switch
            checked={includeRag}
            onCheckedChange={setIncludeRag}
          />
        </div>
      </CardContent>

      <CardFooter>
        <Button
          onClick={handleGenerate}
          disabled={!canGenerate || isLoading}
          className="w-full"
        >
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Wand2 className="h-4 w-4 mr-2" />
              Start Generation
            </>
          )}
        </Button>
      </CardFooter>
    </Card>
  );
}

export default GeneratePanel;
