/**
 * Subject line review checkpoint component
 *
 * Checkpoint 3: Select subject line for newsletter
 * Features:
 * - Radio card selection for suggested subjects
 * - Custom subject input option
 * - Style indicators (professional, casual, etc.)
 */
import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { CheckpointPanel } from './CheckpointPanel';
import { Mail, Sparkles, Pencil } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Checkpoint, CheckpointAction, SubjectLine } from '@/types/newsletter';

interface SubjectReviewProps {
  checkpoint: Checkpoint;
  subjectLines: SubjectLine[];
  onApprove: (subject: string, feedback?: string) => void;
  onReject: (feedback?: string) => void;
  isLoading?: boolean;
  loadingAction?: CheckpointAction | null;
}

export function SubjectReview({
  checkpoint,
  subjectLines,
  onApprove,
  onReject,
  isLoading = false,
  loadingAction = null,
}: SubjectReviewProps) {
  const [selectedIndex, setSelectedIndex] = useState<number>(0);
  const [customSubject, setCustomSubject] = useState('');
  const [useCustom, setUseCustom] = useState(false);

  // Get selected subject
  const getSelectedSubject = () => {
    if (useCustom) return customSubject;
    return subjectLines[selectedIndex]?.text || '';
  };

  // Handle approval
  const handleApprove = (feedback?: string) => {
    onApprove(getSelectedSubject(), feedback);
  };

  // Style badge colors
  const getStyleColor = (style: string) => {
    switch (style.toLowerCase()) {
      case 'professional':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'casual':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'formal':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
      case 'enthusiastic':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
      case 'urgent':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  return (
    <CheckpointPanel
      checkpoint={checkpoint}
      onApprove={handleApprove}
      onReject={onReject}
      isLoading={isLoading}
      loadingAction={loadingAction}
      showEdit={false}
    >
      <div className="space-y-6">
        {/* Subject line options */}
        <RadioGroup
          value={useCustom ? 'custom' : String(selectedIndex)}
          onValueChange={(value) => {
            if (value === 'custom') {
              setUseCustom(true);
            } else {
              setUseCustom(false);
              setSelectedIndex(parseInt(value));
            }
          }}
        >
          <div className="space-y-3">
            {subjectLines.map((subject, index) => (
              <Card
                key={index}
                className={cn(
                  'cursor-pointer transition-all hover:border-primary/50',
                  !useCustom && selectedIndex === index && 'border-primary bg-primary/5'
                )}
                onClick={() => {
                  setUseCustom(false);
                  setSelectedIndex(index);
                }}
              >
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <RadioGroupItem
                      value={String(index)}
                      id={`subject-${index}`}
                      className="mt-1"
                    />
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2">
                        <Mail className="h-4 w-4 text-muted-foreground" />
                        <Label
                          htmlFor={`subject-${index}`}
                          className="font-medium cursor-pointer"
                        >
                          {subject.text}
                        </Label>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge
                          variant="secondary"
                          className={cn('text-xs', getStyleColor(subject.style))}
                        >
                          <Sparkles className="h-3 w-3 mr-1" />
                          {subject.style}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {subject.text.length} characters
                        </span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}

            {/* Custom subject option */}
            <Card
              className={cn(
                'cursor-pointer transition-all hover:border-primary/50',
                useCustom && 'border-primary bg-primary/5'
              )}
              onClick={() => setUseCustom(true)}
            >
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <RadioGroupItem
                    value="custom"
                    id="subject-custom"
                    className="mt-1"
                  />
                  <div className="flex-1 space-y-3">
                    <div className="flex items-center gap-2">
                      <Pencil className="h-4 w-4 text-muted-foreground" />
                      <Label
                        htmlFor="subject-custom"
                        className="font-medium cursor-pointer"
                      >
                        Write your own subject line
                      </Label>
                    </div>
                    {useCustom && (
                      <Input
                        value={customSubject}
                        onChange={(e) => setCustomSubject(e.target.value)}
                        placeholder="Enter your custom subject line..."
                        className="mt-2"
                        autoFocus
                      />
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </RadioGroup>

        {/* Preview */}
        <div className="bg-muted rounded-lg p-4">
          <div className="text-xs text-muted-foreground mb-2">Preview</div>
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center">
              <Mail className="h-4 w-4 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-medium text-sm truncate">
                {getSelectedSubject() || 'Select a subject line...'}
              </div>
              <div className="text-xs text-muted-foreground">
                From: Your Newsletter &lt;newsletter@example.com&gt;
              </div>
            </div>
          </div>
        </div>
      </div>
    </CheckpointPanel>
  );
}

export default SubjectReview;
