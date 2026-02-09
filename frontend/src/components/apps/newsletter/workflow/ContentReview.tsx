/**
 * Content review checkpoint component
 *
 * Checkpoint 2: Review and edit newsletter content
 * Features:
 * - Side-by-side editor and preview
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
    >
      <div className="space-y-4">
        {/* Stats bar */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <div className="flex items-center gap-1">
              <Hash className="h-4 w-4" />
              <span>{wordCount} words</span>
            </div>
            <div className="flex items-center gap-1">
              <Clock className="h-4 w-4" />
              <span>{readingTime} min read</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant={isEditing ? 'default' : 'outline'}
              size="sm"
              onClick={() => setIsEditing(!isEditing)}
            >
              {isEditing ? (
                <>
                  <Eye className="h-4 w-4 mr-1" />
                  Preview
                </>
              ) : (
                <>
                  <Pencil className="h-4 w-4 mr-1" />
                  Edit
                </>
              )}
            </Button>
            {isEditing && editedContent !== initialContent.content && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleReset}
              >
                <RotateCcw className="h-4 w-4 mr-1" />
                Reset
              </Button>
            )}
          </div>
        </div>

        {/* Content area */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Editor / Source */}
          <Card>
            <CardHeader className="py-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <FileText className="h-4 w-4" />
                {isEditing ? 'Edit Content' : 'Source'}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {isEditing ? (
                <Textarea
                  value={editedContent}
                  onChange={(e) => setEditedContent(e.target.value)}
                  className="min-h-[400px] rounded-t-none border-0 resize-none font-mono text-sm"
                  placeholder="Newsletter content..."
                />
              ) : (
                <ScrollArea className="h-[400px]">
                  <pre className="p-4 text-sm whitespace-pre-wrap font-mono">
                    {editedContent}
                  </pre>
                </ScrollArea>
              )}
            </CardContent>
          </Card>

          {/* Preview */}
          <Card>
            <CardHeader className="py-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Eye className="h-4 w-4" />
                  Preview
                </CardTitle>
                {formats && (
                  <Tabs value={previewFormat} onValueChange={(v) => setPreviewFormat(v as typeof previewFormat)}>
                    <TabsList className="h-7">
                      <TabsTrigger value="html" className="text-xs h-6 px-2">
                        HTML
                      </TabsTrigger>
                      <TabsTrigger value="text" className="text-xs h-6 px-2">
                        Text
                      </TabsTrigger>
                      <TabsTrigger value="markdown" className="text-xs h-6 px-2">
                        MD
                      </TabsTrigger>
                    </TabsList>
                  </Tabs>
                )}
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[400px]">
                {previewFormat === 'html' && formats?.html ? (
                  <div
                    className="p-4 prose prose-sm dark:prose-invert max-w-none"
                    dangerouslySetInnerHTML={{ __html: formats.html }}
                  />
                ) : (
                  <pre className="p-4 text-sm whitespace-pre-wrap">
                    {getPreviewContent()}
                  </pre>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* Edit indicator */}
        {editedContent !== initialContent.content && (
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-amber-600 border-amber-600">
              Modified
            </Badge>
            <span className="text-xs text-muted-foreground">
              Content has been edited. Click "Edit" to save changes or "Reset" to revert.
            </span>
          </div>
        )}
      </div>
    </CheckpointPanel>
  );
}

export default ContentReview;
