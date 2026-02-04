/**
 * Research input panel for Newsletter app
 */
import { useState, KeyboardEvent } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Loader2, Search, X, ChevronDown, Settings2 } from 'lucide-react';

interface ResearchPanelProps {
  onResearch: (topics: string[], customPrompt: string | null, maxResults: number, includeSummaries: boolean) => void;
  isLoading?: boolean;
}

export function ResearchPanel({ onResearch, isLoading }: ResearchPanelProps) {
  const [topics, setTopics] = useState<string[]>([]);
  const [currentTopic, setCurrentTopic] = useState('');
  const [customPrompt, setCustomPrompt] = useState('');
  const [maxResults, setMaxResults] = useState(10);
  const [includeSummaries, setIncludeSummaries] = useState(true);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const handleAddTopic = () => {
    const trimmed = currentTopic.trim();
    if (trimmed && !topics.includes(trimmed)) {
      setTopics([...topics, trimmed]);
      setCurrentTopic('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTopic();
    }
  };

  const handleRemoveTopic = (topic: string) => {
    setTopics(topics.filter((t) => t !== topic));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Use custom prompt if provided, otherwise use topics
    const prompt = customPrompt.trim() || null;
    const topicsToUse = prompt ? [] : topics;

    if (prompt || topicsToUse.length > 0) {
      onResearch(topicsToUse, prompt, maxResults, includeSummaries);
    }
  };

  const canSubmit = customPrompt.trim().length > 0 || topics.length > 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Search className="h-5 w-5 text-primary" />
          Research Content
        </CardTitle>
        <CardDescription>
          Enter topics or a custom prompt to discover content for your newsletter
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Topics Input */}
          <div className="space-y-2">
            <Label htmlFor="topics">Topics</Label>
            <div className="flex gap-2">
              <Input
                id="topics"
                placeholder="Add a topic and press Enter..."
                value={currentTopic}
                onChange={(e) => setCurrentTopic(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isLoading}
              />
              <Button
                type="button"
                variant="outline"
                onClick={handleAddTopic}
                disabled={!currentTopic.trim() || isLoading}
              >
                Add
              </Button>
            </div>

            {/* Topic chips */}
            {topics.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {topics.map((topic) => (
                  <Badge key={topic} variant="secondary" className="px-2 py-1 text-sm">
                    {topic}
                    <button
                      type="button"
                      onClick={() => handleRemoveTopic(topic)}
                      className="ml-1.5 hover:text-destructive"
                      disabled={isLoading}
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Custom Prompt */}
          <div className="space-y-2">
            <Label htmlFor="prompt">Custom Prompt (optional)</Label>
            <Textarea
              id="prompt"
              placeholder="Or describe what content you're looking for... e.g., 'Generate content for an Observability newsletter focusing on OpenTelemetry'"
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              disabled={isLoading}
              className="min-h-[80px]"
            />
            <p className="text-xs text-muted-foreground">
              Using a custom prompt will override topics. The AI will extract relevant search terms.
            </p>
          </div>

          {/* Settings */}
          <div className="space-y-2">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="w-full justify-between"
              onClick={() => setSettingsOpen(!settingsOpen)}
            >
              <span className="flex items-center gap-2">
                <Settings2 className="h-4 w-4" />
                Settings
              </span>
              <ChevronDown className={`h-4 w-4 transition-transform ${settingsOpen ? 'rotate-180' : ''}`} />
            </Button>

            {settingsOpen && (
              <div className="space-y-4 pt-2 px-1">
                {/* Max Results */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="maxResults">Max Results</Label>
                    <span className="text-sm text-muted-foreground">{maxResults}</span>
                  </div>
                  <Input
                    id="maxResults"
                    type="range"
                    min={1}
                    max={30}
                    value={maxResults}
                    onChange={(e) => setMaxResults(Number(e.target.value))}
                    disabled={isLoading}
                    className="w-full"
                  />
                </div>

                {/* Include Summaries */}
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Include AI Summaries</Label>
                    <p className="text-xs text-muted-foreground">
                      Generate AI summaries for each article
                    </p>
                  </div>
                  <Switch
                    checked={includeSummaries}
                    onCheckedChange={setIncludeSummaries}
                    disabled={isLoading}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Submit Button */}
          <Button type="submit" className="w-full" disabled={!canSubmit || isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Researching...
              </>
            ) : (
              <>
                <Search className="mr-2 h-4 w-4" />
                Search for Content
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
