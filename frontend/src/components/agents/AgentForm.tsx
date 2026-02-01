import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { agentSchema, type AgentFormData } from '@/utils/validation';
import { useCreateAgent, useUpdateAgent } from '@/hooks/useAgents';
import type { Agent } from '@/types/agent';

interface AgentFormProps {
  agent?: Agent;
  onSuccess?: () => void;
}

const AVAILABLE_MODELS = [
  'gpt-4-turbo',
  'gpt-4',
  'gpt-3.5-turbo',
  'claude-3-opus',
  'claude-3-sonnet',
  'claude-3-haiku',
];

export function AgentForm({ agent, onSuccess }: AgentFormProps) {
  const createMutation = useCreateAgent();
  const updateMutation = useUpdateAgent();
  const isEditing = !!agent;

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<AgentFormData>({
    resolver: zodResolver(agentSchema),
    defaultValues: agent
      ? {
          name: agent.name,
          description: agent.description,
          config: agent.config,
          tools: agent.tools,
        }
      : {
          config: {
            model: 'gpt-4-turbo',
            temperature: 0.7,
            maxTokens: 4096,
          },
        },
  });

  const onSubmit = async (data: AgentFormData) => {
    try {
      if (isEditing) {
        await updateMutation.mutateAsync({ id: agent.id, data });
      } else {
        await createMutation.mutateAsync(data);
      }
      onSuccess?.();
    } catch {
      // Error handled by mutation
    }
  };

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="name">Name</Label>
        <Input
          id="name"
          placeholder="My Agent"
          {...register('name')}
          disabled={isPending}
        />
        {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          placeholder="Describe what this agent does..."
          {...register('description')}
          disabled={isPending}
        />
        {errors.description && (
          <p className="text-sm text-destructive">{errors.description.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="model">Model</Label>
        <Select
          value={watch('config.model')}
          onValueChange={(value) => setValue('config.model', value)}
          disabled={isPending}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select a model" />
          </SelectTrigger>
          <SelectContent>
            {AVAILABLE_MODELS.map((model) => (
              <SelectItem key={model} value={model}>
                {model}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {errors.config?.model && (
          <p className="text-sm text-destructive">{errors.config.model.message}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="temperature">Temperature</Label>
          <Input
            id="temperature"
            type="number"
            step="0.1"
            min="0"
            max="2"
            {...register('config.temperature', { valueAsNumber: true })}
            disabled={isPending}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="maxTokens">Max Tokens</Label>
          <Input
            id="maxTokens"
            type="number"
            min="1"
            max="100000"
            {...register('config.maxTokens', { valueAsNumber: true })}
            disabled={isPending}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="systemPrompt">System Prompt</Label>
        <Textarea
          id="systemPrompt"
          placeholder="Enter system prompt..."
          rows={4}
          {...register('config.systemPrompt')}
          disabled={isPending}
        />
      </div>

      <div className="flex justify-end gap-2">
        <Button type="submit" disabled={isPending}>
          {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {isEditing ? 'Update Agent' : 'Create Agent'}
        </Button>
      </div>
    </form>
  );
}
