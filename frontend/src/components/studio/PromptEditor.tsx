import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/components/ui/use-toast';
import { useUpdateAgentPrompt } from '@/hooks/useStudio';
import type { StudioAgentDetail } from '@/types/studio';

interface PromptEditorProps {
  platformId: string;
  agentName: string;
  detail: StudioAgentDetail;
}

export function PromptEditor({
  platformId,
  agentName,
  detail,
}: PromptEditorProps) {
  const { toast } = useToast();
  const updatePrompt = useUpdateAgentPrompt();
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(detail.system_prompt ?? '');

  const handleEdit = () => {
    setDraft(detail.system_prompt ?? '');
    setEditing(true);
  };

  const handleCancel = () => {
    setEditing(false);
    setDraft(detail.system_prompt ?? '');
  };

  const handleSave = () => {
    updatePrompt.mutate(
      {
        platformId,
        agentName,
        data: { system_prompt: draft },
      },
      {
        onSuccess: () => {
          setEditing(false);
          toast({ title: 'Prompt updated', description: 'Session-only change applied.' });
        },
        onError: (err) => {
          toast({ variant: 'destructive', title: 'Error', description: String(err) });
        },
      },
    );
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="text-lg">System Prompt</CardTitle>
          <p className="text-sm text-muted-foreground">
            Session-only: changes reset when the server restarts.
          </p>
        </div>
        {!editing && (
          <Button variant="outline" size="sm" onClick={handleEdit}>
            Edit
          </Button>
        )}
      </CardHeader>
      <CardContent>
        {editing ? (
          <div className="space-y-4">
            <Textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              rows={12}
              className="font-mono text-sm"
              placeholder="Enter system prompt..."
            />
            <div className="flex gap-3">
              <Button onClick={handleSave} disabled={updatePrompt.isPending}>
                {updatePrompt.isPending ? 'Saving...' : 'Save'}
              </Button>
              <Button variant="outline" onClick={handleCancel}>
                Cancel
              </Button>
            </div>
          </div>
        ) : detail.system_prompt ? (
          <pre className="whitespace-pre-wrap text-sm font-mono bg-muted p-4 rounded-md">
            {detail.system_prompt}
          </pre>
        ) : (
          <p className="text-muted-foreground py-4">
            No system prompt configured. Click Edit to add one.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
