import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useToast } from '@/components/ui/use-toast';
import {
  useStudioProviders,
  useUpdateAgentConfig,
  useResetAgentConfig,
} from '@/hooks/useStudio';
import type { StudioAgentDetail } from '@/types/studio';

interface LLMConfigEditorProps {
  platformId: string;
  agentName: string;
  detail: StudioAgentDetail;
}

export function LLMConfigEditor({
  platformId,
  agentName,
  detail,
}: LLMConfigEditorProps) {
  const { toast } = useToast();
  const { data: providersData } = useStudioProviders();
  const updateConfig = useUpdateAgentConfig();
  const resetConfig = useResetAgentConfig();

  const [provider, setProvider] = useState(detail.llm_config.provider ?? '');
  const [model, setModel] = useState(detail.llm_config.model ?? '');
  const [temperature, setTemperature] = useState(detail.llm_config.temperature ?? 0.7);
  const [maxTokens, setMaxTokens] = useState(detail.llm_config.max_tokens ?? 1000);

  // Sync form when detail changes (e.g. after reset)
  useEffect(() => {
    setProvider(detail.llm_config.provider ?? '');
    setModel(detail.llm_config.model ?? '');
    setTemperature(detail.llm_config.temperature ?? 0.7);
    setMaxTokens(detail.llm_config.max_tokens ?? 1000);
  }, [detail]);

  const providers = providersData?.providers ?? [];
  const selectedProvider = providers.find((p) => p.provider_type === provider);
  const modelList = selectedProvider?.models ?? [];

  const handleSave = () => {
    updateConfig.mutate(
      {
        platformId,
        agentName,
        data: {
          provider: provider || undefined,
          model: model || undefined,
          temperature,
          max_tokens: maxTokens,
        },
      },
      {
        onSuccess: () => {
          toast({ title: 'Config updated', description: 'Session-only changes applied.' });
        },
        onError: (err) => {
          toast({ variant: 'destructive', title: 'Error', description: String(err) });
        },
      },
    );
  };

  const handleReset = () => {
    resetConfig.mutate(
      { platformId, agentName },
      {
        onSuccess: () => {
          toast({ title: 'Config reset', description: 'Reverted to agent defaults.' });
        },
        onError: (err) => {
          toast({ variant: 'destructive', title: 'Error', description: String(err) });
        },
      },
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">LLM Configuration</CardTitle>
        <p className="text-sm text-muted-foreground">
          Session-only: changes reset when the server restarts.
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Provider */}
        <div className="space-y-2">
          <Label>Provider</Label>
          <Select value={provider} onValueChange={setProvider}>
            <SelectTrigger>
              <SelectValue placeholder="Select provider" />
            </SelectTrigger>
            <SelectContent>
              {providers.map((p) => (
                <SelectItem key={p.provider_type} value={p.provider_type}>
                  {p.name} {p.available ? '' : '(unavailable)'}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Model */}
        <div className="space-y-2">
          <Label>Model</Label>
          {modelList.length > 0 ? (
            <Select value={model} onValueChange={setModel}>
              <SelectTrigger>
                <SelectValue placeholder="Select model" />
              </SelectTrigger>
              <SelectContent>
                {modelList.map((m) => (
                  <SelectItem key={m} value={m}>
                    {m}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <Input
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder="e.g. llama3, gpt-4"
            />
          )}
        </div>

        {/* Temperature */}
        <div className="space-y-2">
          <Label>Temperature: {temperature.toFixed(2)}</Label>
          <Slider
            value={[temperature]}
            onValueChange={([v]) => setTemperature(v)}
            min={0}
            max={2}
            step={0.05}
          />
        </div>

        {/* Max Tokens */}
        <div className="space-y-2">
          <Label>Max Tokens</Label>
          <Input
            type="number"
            value={maxTokens}
            onChange={(e) => setMaxTokens(Number(e.target.value))}
            min={1}
            max={128000}
          />
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <Button onClick={handleSave} disabled={updateConfig.isPending}>
            {updateConfig.isPending ? 'Saving...' : 'Save'}
          </Button>
          <Button
            variant="outline"
            onClick={handleReset}
            disabled={resetConfig.isPending}
          >
            {resetConfig.isPending ? 'Resetting...' : 'Reset to Defaults'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
