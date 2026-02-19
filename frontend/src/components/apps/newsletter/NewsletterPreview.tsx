/**
 * Newsletter Preview component with subject lines, format tabs, and summary
 */
import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import {
  Newspaper,
  RefreshCw,
  Copy,
  Download,
  Check,
  Mail,
  FileText,
  Code,
  Sparkles,
  Hash,
} from 'lucide-react';
import type { GenerateResponse, SubjectLine } from '@/types/newsletter';

interface NewsletterPreviewProps {
  result: GenerateResponse;
  onRegenerate: () => void;
  isRegenerating: boolean;
}

// Style icons for subject lines
const styleIcons: Record<string, string> = {
  curiosity: '🎯',
  benefit: '💡',
  urgency: '🚀',
  question: '❓',
  trend: '📈',
  informative: '📰',
};

function SubjectLinePicker({
  subjectLines,
  selectedIndex,
  onSelect,
}: {
  subjectLines: SubjectLine[];
  selectedIndex: number;
  onSelect: (index: number) => void;
}) {
  if (subjectLines.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Mail className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm font-medium">Choose Subject Line</span>
      </div>
      <RadioGroup
        value={String(selectedIndex)}
        onValueChange={(value: string) => onSelect(Number(value))}
        className="space-y-2"
      >
        {subjectLines.map((line, index) => (
          <div
            key={index}
            className={`flex items-center space-x-3 rounded-md border p-3 cursor-pointer transition-colors ${
              selectedIndex === index ? 'border-primary bg-primary/5' : 'hover:bg-muted/50'
            }`}
            onClick={() => onSelect(index)}
          >
            <RadioGroupItem value={String(index)} id={`subject-${index}`} />
            <Label
              htmlFor={`subject-${index}`}
              className="flex-1 cursor-pointer flex items-center gap-2"
            >
              <span>{styleIcons[line.style] || '📧'}</span>
              <span className="flex-1">{line.text}</span>
              <Badge variant="outline" className="text-xs capitalize">
                {line.style}
              </Badge>
            </Label>
          </div>
        ))}
      </RadioGroup>
    </div>
  );
}

function FormatTabs({ formats }: { formats: { html: string; text: string; markdown: string } }) {
  const [copied, setCopied] = useState<string | null>(null);

  const handleCopy = async (content: string, format: string) => {
    await navigator.clipboard.writeText(content);
    setCopied(format);
    setTimeout(() => setCopied(null), 2000);
  };

  const handleDownload = (content: string, format: string) => {
    const extension = format === 'html' ? 'html' : format === 'markdown' ? 'md' : 'txt';
    const mimeType = format === 'html' ? 'text/html' : 'text/plain';
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `newsletter.${extension}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Tabs defaultValue="html" className="w-full">
      <div className="flex items-center justify-between mb-2">
        <TabsList>
          <TabsTrigger value="html" className="flex items-center gap-1">
            <Code className="h-3 w-3" />
            HTML
          </TabsTrigger>
          <TabsTrigger value="text" className="flex items-center gap-1">
            <FileText className="h-3 w-3" />
            Text
          </TabsTrigger>
          <TabsTrigger value="markdown" className="flex items-center gap-1">
            <Hash className="h-3 w-3" />
            Markdown
          </TabsTrigger>
        </TabsList>
      </div>

      <TabsContent value="html" className="mt-0">
        <div className="relative">
          <div className="absolute top-2 right-2 flex gap-1">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleCopy(formats.html, 'html')}
            >
              {copied === 'html' ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleDownload(formats.html, 'html')}
            >
              <Download className="h-3 w-3" />
            </Button>
          </div>
          <div className="border rounded-md bg-white min-h-[300px] max-h-[500px] overflow-auto">
            <iframe
              srcDoc={formats.html}
              title="Newsletter HTML preview"
              className="w-full h-[500px] border-0"
              sandbox="allow-same-origin"
            />
          </div>
        </div>
      </TabsContent>

      <TabsContent value="text" className="mt-0">
        <div className="relative">
          <div className="absolute top-2 right-2 flex gap-1">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleCopy(formats.text, 'text')}
            >
              {copied === 'text' ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleDownload(formats.text, 'text')}
            >
              <Download className="h-3 w-3" />
            </Button>
          </div>
          <pre className="border rounded-md p-4 bg-muted/50 min-h-[300px] max-h-[500px] overflow-auto text-sm whitespace-pre-wrap font-mono">
            {formats.text}
          </pre>
        </div>
      </TabsContent>

      <TabsContent value="markdown" className="mt-0">
        <div className="relative">
          <div className="absolute top-2 right-2 flex gap-1">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleCopy(formats.markdown, 'markdown')}
            >
              {copied === 'markdown' ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleDownload(formats.markdown, 'markdown')}
            >
              <Download className="h-3 w-3" />
            </Button>
          </div>
          <pre className="border rounded-md p-4 bg-muted/50 min-h-[300px] max-h-[500px] overflow-auto text-sm whitespace-pre-wrap font-mono">
            {formats.markdown}
          </pre>
        </div>
      </TabsContent>
    </Tabs>
  );
}

function SummaryBullets({ bullets }: { bullets: string[] }) {
  if (bullets.length === 0) return null;

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm font-medium">Key Points</span>
      </div>
      <ul className="space-y-1.5 text-sm text-muted-foreground">
        {bullets.map((bullet, index) => (
          <li key={index} className="flex items-start gap-2">
            <span className="text-primary">•</span>
            <span>{bullet}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function NewsletterPreview({
  result,
  onRegenerate,
  isRegenerating,
}: NewsletterPreviewProps) {
  const [selectedSubjectIndex, setSelectedSubjectIndex] = useState(0);

  const { newsletter, subject_lines, summary, formats, metadata } = result;

  if (!newsletter || !formats) {
    return (
      <Card className="border-destructive">
        <CardContent className="pt-6">
          <p className="text-destructive">Failed to generate newsletter. Please try again.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Newspaper className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">Newsletter Generated</CardTitle>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={onRegenerate}
            disabled={isRegenerating}
          >
            <RefreshCw className={`h-4 w-4 mr-1 ${isRegenerating ? 'animate-spin' : ''}`} />
            Regenerate
          </Button>
        </div>
        <CardDescription className="flex flex-wrap items-center gap-3">
          {metadata && (
            <>
              <span className="flex items-center gap-1">
                <FileText className="h-3 w-3" />
                {metadata.article_count} articles
              </span>
              <span className="flex items-center gap-1">
                <Hash className="h-3 w-3" />
                {newsletter.word_count} words
              </span>
              <Badge variant="outline" className="capitalize">
                {metadata.tone}
              </Badge>
              {metadata.rag_examples_used && metadata.rag_examples_used > 0 && (
                <Badge variant="secondary">
                  RAG enhanced
                </Badge>
              )}
            </>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Subject Lines */}
        <SubjectLinePicker
          subjectLines={subject_lines}
          selectedIndex={selectedSubjectIndex}
          onSelect={setSelectedSubjectIndex}
        />

        <Separator />

        {/* Format Tabs */}
        <FormatTabs formats={formats} />

        <Separator />

        {/* Summary */}
        {summary && summary.bullets && summary.bullets.length > 0 && (
          <SummaryBullets bullets={summary.bullets} />
        )}
      </CardContent>
    </Card>
  );
}
