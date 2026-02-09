/**
 * Final approval checkpoint component
 *
 * Checkpoint 4: Final review before sending
 * Features:
 * - Full newsletter preview
 * - Summary of selected options
 * - Recipient count
 * - Send now or schedule option
 */
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import {
  Mail,
  Users,
  Calendar,
  Clock,
  FileText,
  Send,
  AlertCircle,
  CheckCircle,
} from 'lucide-react';
import type { Checkpoint, CheckpointAction, NewsletterFormats } from '@/types/newsletter';

interface FinalApprovalProps {
  checkpoint: Checkpoint;
  subject: string;
  content: string;
  formats?: NewsletterFormats;
  articleCount: number;
  recipientCount?: number;
  onApprove: (scheduleAt?: string, feedback?: string) => void;
  onReject: (feedback?: string) => void;
  isLoading?: boolean;
  loadingAction?: CheckpointAction | null;
}

export function FinalApproval({
  checkpoint,
  subject,
  content,
  formats,
  articleCount,
  recipientCount = 0,
  onApprove,
  onReject,
  isLoading = false,
  loadingAction = null,
}: FinalApprovalProps) {
  const [scheduleEnabled, setScheduleEnabled] = useState(false);
  const [scheduleDate, setScheduleDate] = useState('');
  const [scheduleTime, setScheduleTime] = useState('09:00');

  // Calculate stats
  const wordCount = content.split(/\s+/).filter(Boolean).length;
  const readingTime = Math.ceil(wordCount / 200);

  // Handle approval
  const handleApprove = () => {
    let scheduleAt: string | undefined;
    if (scheduleEnabled && scheduleDate) {
      scheduleAt = `${scheduleDate}T${scheduleTime}:00`;
    }
    onApprove(scheduleAt);
  };

  // Get minimum date (today)
  const today = new Date().toISOString().split('T')[0];

  return (
    <Card className="border-primary/20">
      <CardHeader className="bg-primary/5 border-b">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              {checkpoint.title}
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              {checkpoint.description}
            </p>
          </div>
          <Badge variant="outline" className="text-green-600 border-green-600">
            Ready to Send
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="p-6 space-y-6">
        {/* Summary cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4 text-center">
              <Mail className="h-5 w-5 mx-auto text-muted-foreground mb-2" />
              <div className="text-2xl font-bold">{subject.length}</div>
              <div className="text-xs text-muted-foreground">Subject chars</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <FileText className="h-5 w-5 mx-auto text-muted-foreground mb-2" />
              <div className="text-2xl font-bold">{articleCount}</div>
              <div className="text-xs text-muted-foreground">Articles</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <Clock className="h-5 w-5 mx-auto text-muted-foreground mb-2" />
              <div className="text-2xl font-bold">{readingTime}</div>
              <div className="text-xs text-muted-foreground">Min read</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <Users className="h-5 w-5 mx-auto text-muted-foreground mb-2" />
              <div className="text-2xl font-bold">{recipientCount}</div>
              <div className="text-xs text-muted-foreground">Recipients</div>
            </CardContent>
          </Card>
        </div>

        {/* Subject preview */}
        <div className="space-y-2">
          <Label className="text-sm font-medium">Subject Line</Label>
          <div className="bg-muted rounded-lg p-3">
            <div className="flex items-center gap-2">
              <Mail className="h-4 w-4 text-muted-foreground" />
              <span className="font-medium">{subject}</span>
            </div>
          </div>
        </div>

        <Separator />

        {/* Content preview */}
        <div className="space-y-2">
          <Label className="text-sm font-medium">Content Preview</Label>
          <Card>
            <ScrollArea className="h-[300px]">
              {formats?.html ? (
                <div
                  className="p-4 prose prose-sm dark:prose-invert max-w-none"
                  dangerouslySetInnerHTML={{ __html: formats.html }}
                />
              ) : (
                <pre className="p-4 text-sm whitespace-pre-wrap">{content}</pre>
              )}
            </ScrollArea>
          </Card>
        </div>

        <Separator />

        {/* Schedule option */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-sm font-medium">Schedule for later</Label>
              <p className="text-xs text-muted-foreground">
                Schedule the newsletter to be sent at a specific time
              </p>
            </div>
            <Switch
              checked={scheduleEnabled}
              onCheckedChange={setScheduleEnabled}
            />
          </div>

          {scheduleEnabled && (
            <div className="grid grid-cols-2 gap-4 p-4 bg-muted rounded-lg">
              <div className="space-y-2">
                <Label htmlFor="schedule-date" className="text-xs">Date</Label>
                <Input
                  id="schedule-date"
                  type="date"
                  value={scheduleDate}
                  onChange={(e) => setScheduleDate(e.target.value)}
                  min={today}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="schedule-time" className="text-xs">Time</Label>
                <Input
                  id="schedule-time"
                  type="time"
                  value={scheduleTime}
                  onChange={(e) => setScheduleTime(e.target.value)}
                />
              </div>
            </div>
          )}
        </div>

        {/* Warning if no recipients */}
        {recipientCount === 0 && (
          <div className="flex items-center gap-2 p-3 bg-amber-50 dark:bg-amber-950 rounded-lg text-amber-600 dark:text-amber-400">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            <span className="text-sm">
              No recipients configured. Add subscribers before sending.
            </span>
          </div>
        )}

        <Separator />

        {/* Actions */}
        <div className="flex items-center justify-center gap-3">
          <Button
            onClick={handleApprove}
            disabled={isLoading || (scheduleEnabled && !scheduleDate)}
            className="min-w-[150px]"
          >
            {isLoading && loadingAction === 'approve' ? (
              <span className="animate-spin">...</span>
            ) : scheduleEnabled ? (
              <>
                <Calendar className="h-4 w-4 mr-2" />
                Schedule
              </>
            ) : (
              <>
                <Send className="h-4 w-4 mr-2" />
                Send Now
              </>
            )}
          </Button>
          <Button
            variant="outline"
            onClick={() => onReject()}
            disabled={isLoading}
            className="min-w-[150px]"
          >
            Go Back
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default FinalApproval;
