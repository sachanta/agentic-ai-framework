/**
 * Content review checkpoint component
 *
 * Checkpoint 2: Review and edit newsletter content
 * Features:
 * - Side-by-side preview + source/edit panels
 * - Format toggle (HTML/Text/Markdown)
 * - Word count and reading time
 * - Edit mode with textarea
 */
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { CheckpointPanel } from './CheckpointPanel';
import {
  FileText,
  Eye,
  Pencil,
  RotateCcw,
  Clock,
  Hash,
} from 'lucide-react';
import type { Checkpoint, CheckpointAction, NewsletterContent, NewsletterFormats } from '@/types/newsletter';

interface ContentReviewProps {
  checkpoint: Checkpoint;
  content: NewsletterContent;
  formats?: NewsletterFormats;
  onApprove: (content: string, feedback?: string) => void;
  onEdit: (content: string, feedback?: string) => void;
  onReject: (feedback?: string) => void;
  isLoading?: boolean;
  loadingAction?: CheckpointAction | null;
}

export function ContentReview({
  checkpoint,
  content: initialContent,
  formats,
  onApprove,
  onEdit,
  onReject,
  isLoading = false,
  loadingAction = null,
}: ContentReviewProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(initialContent.content);
  const [previewFormat, setPreviewFormat] = useState<'html' | 'text' | 'markdown'>('html');

  // Calculate reading time (average 200 words per minute)
  const wordCount = editedContent.split(/\s+/).filter(Boolean).length;
  const readingTime = Math.ceil(wordCount / 200);
  const isModified = editedContent !== initialContent.content;

  // Get preview content based on format
  const getPreviewContent = () => {
    if (formats) {
      switch (previewFormat) {
        case 'html':
          return formats.html;
        case 'text':
          return formats.text;
        case 'markdown':
          return formats.markdown;
      }
    }
    return editedContent;
  };

  // Handle approval
  const handleApprove = (feedback?: string) => {
    onApprove(editedContent, feedback);
  };

  // Handle edit submission
  const handleEditSubmit = (feedback?: string) => {
    onEdit(editedContent, feedback);
    setIsEditing(false);
  };

  // Reset to original content
  const handleReset = () => {
    setEditedContent(initialContent.content);
  };

  return (
    <CheckpointPanel
      checkpoint={checkpoint}
      onApprove={handleApprove}
      onEdit={() => handleEditSubmit()}
      onReject={onReject}
      isLoading={isLoading}
      loadingAction={loadingAction}
      showEdit={true}
      className="w-full max-w-full"
    >
      <div className="w-full max-w-full space-y-4">
        {/* Toolbar */}
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <div className="flex items-center gap-1">
              <Hash className="h-4 w-4" />
              <span>{wordCount} words</span>
            </div>
            <div className="flex items-center gap-1">
              <Clock className="h-4 w-4" />
              <span>{readingTime} min read</span>
            </div>
            {isModified && (
              <Badge variant="outline" className="text-amber-600 border-amber-600">
                Modified
              </Badge>
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* Format selector */}
            {formats && (
              <Tabs value={previewFormat} onValueChange={(v) => setPreviewFormat(v as typeof previewFormat)}>
                <TabsList className="h-8">
                  <TabsTrigger value="html" className="text-xs px-2">HTML</TabsTrigger>
                  <TabsTrigger value="text" className="text-xs px-2">Text</TabsTrigger>
                  <TabsTrigger value="markdown" className="text-xs px-2">MD</TabsTrigger>
                </TabsList>
              </Tabs>
            )}

            {/* Edit toggle */}
            <Button
              variant={isEditing ? 'default' : 'outline'}
              size="sm"
              onClick={() => setIsEditing(!isEditing)}
            >
              <Pencil className="h-4 w-4 mr-1" />
              {isEditing ? 'Done Editing' : 'Edit'}
            </Button>

            {/* Reset (when modified) */}
            {isModified && (
              <Button variant="ghost" size="sm" onClick={handleReset}>
                <RotateCcw className="h-4 w-4 mr-1" />
                Reset
              </Button>
            )}
          </div>
        </div>

        {/* Two-pane side-by-side layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 w-full max-w-full">
          {/* Left pane: Preview */}
          <Card className="w-full min-w-0">
            <CardHeader className="py-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <Eye className="h-4 w-4" />
                Preview
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {previewFormat === 'html' && formats?.html ? (
                <iframe
                  srcDoc={formats.html}
                  title="Newsletter preview"
                  className="w-full h-[500px] border-0"
                  sandbox="allow-same-origin"
                />
              ) : (
                <ScrollArea className="h-[500px]">
                  <pre className="p-4 text-sm whitespace-pre-wrap break-words">
                    {getPreviewContent()}
                  </pre>
                </ScrollArea>
              )}
            </CardContent>
          </Card>

          {/* Right pane: Source or Edit */}
          <Card className="w-full min-w-0">
            <CardHeader className="py-3">
              <CardTitle className="text-sm flex items-center gap-2">
                {isEditing ? (
                  <><Pencil className="h-4 w-4" /> Edit Content</>
                ) : (
                  <><FileText className="h-4 w-4" /> Source</>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {isEditing ? (
                <Textarea
                  value={editedContent}
                  onChange={(e) => setEditedContent(e.target.value)}
                  className="min-h-[500px] rounded-t-none border-0 resize-none font-mono text-sm w-full"
                  placeholder="Newsletter content..."
                />
              ) : (
                <ScrollArea className="h-[500px]">
                  <pre className="p-4 text-sm whitespace-pre-wrap break-words font-mono">
                    {editedContent}
                  </pre>
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Edit hint */}
        {isModified && !isEditing && (
          <p className="text-xs text-muted-foreground">
            Content has been edited. Use &quot;Approve with Edits&quot; to save your changes, or click Edit to continue editing.
          </p>
        )}
      </div>
    </CheckpointPanel>
  );
}

export default ContentReview;
