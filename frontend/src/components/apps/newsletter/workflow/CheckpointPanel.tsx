/**
 * Generic checkpoint panel container
 *
 * Provides the common layout for checkpoint review screens:
 * - Header with title and description
 * - Content area for checkpoint-specific UI
 * - Footer with approval actions
 */
import { ReactNode, useState } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { ApprovalActions } from './ApprovalActions';
import { AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Checkpoint, CheckpointAction } from '@/types/newsletter';

interface CheckpointPanelProps {
  checkpoint: Checkpoint;
  children: ReactNode;
  onApprove: (feedback?: string) => void;
  onEdit?: (modifications: Record<string, unknown>, feedback?: string) => void;
  onReject: (feedback?: string) => void;
  isLoading?: boolean;
  loadingAction?: CheckpointAction | null;
  showFeedback?: boolean;
  showEdit?: boolean;
  className?: string;
}

export function CheckpointPanel({
  checkpoint,
  children,
  onApprove,
  onEdit,
  onReject,
  isLoading = false,
  loadingAction = null,
  showFeedback = true,
  showEdit = true,
  className,
}: CheckpointPanelProps) {
  const [feedback, setFeedback] = useState('');
  const [showFeedbackInput, setShowFeedbackInput] = useState(false);

  const handleApprove = () => {
    onApprove(feedback || undefined);
  };

  const handleReject = () => {
    onReject(feedback || undefined);
  };

  return (
    <Card className={cn('border-primary/20', className)}>
      <CardHeader className="bg-primary/5 border-b">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-amber-500" />
              {checkpoint.title}
            </CardTitle>
            <CardDescription className="mt-1">
              {checkpoint.description}
            </CardDescription>
          </div>
          <div className="text-xs text-muted-foreground bg-background px-2 py-1 rounded">
            Checkpoint: {checkpoint.checkpoint_type.replace('_', ' ')}
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-6">
        {children}
      </CardContent>

      <CardFooter className="flex flex-col gap-4 border-t bg-muted/30 pt-6">
        {/* Feedback input (collapsible) */}
        {showFeedback && (
          <div className="w-full">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowFeedbackInput(!showFeedbackInput)}
              className="text-muted-foreground mb-2"
            >
              {showFeedbackInput ? (
                <ChevronUp className="h-4 w-4 mr-1" />
              ) : (
                <ChevronDown className="h-4 w-4 mr-1" />
              )}
              Add feedback (optional)
            </Button>

            {showFeedbackInput && (
              <div className="space-y-2">
                <Label htmlFor="feedback" className="text-sm text-muted-foreground">
                  Feedback for the AI (will be used to improve future results)
                </Label>
                <Textarea
                  id="feedback"
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                  placeholder="e.g., Focus more on technical details, use a more casual tone..."
                  rows={2}
                />
              </div>
            )}
          </div>
        )}

        {/* Approval actions */}
        <ApprovalActions
          onApprove={handleApprove}
          onEdit={onEdit ? () => onEdit({}, feedback) : undefined}
          onReject={handleReject}
          isLoading={isLoading}
          loadingAction={loadingAction}
          showEdit={showEdit}
          className="w-full"
        />
      </CardFooter>
    </Card>
  );
}

/**
 * Simple checkpoint container without actions (for display only)
 */
interface CheckpointDisplayProps {
  title: string;
  description?: string;
  children: ReactNode;
  className?: string;
}

export function CheckpointDisplay({
  title,
  description,
  children,
  className,
}: CheckpointDisplayProps) {
  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

export default CheckpointPanel;
