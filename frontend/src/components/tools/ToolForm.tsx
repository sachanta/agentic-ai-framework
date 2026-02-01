import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, Plus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toolSchema, type ToolFormData } from '@/utils/validation';
import { useCreateTool, useUpdateTool } from '@/hooks/useTools';
import type { Tool } from '@/types/tool';

interface ToolFormProps {
  tool?: Tool;
  onSuccess?: () => void;
}

const TOOL_TYPES = ['function', 'api', 'database', 'file', 'custom'] as const;
const PARAM_TYPES = ['string', 'number', 'boolean', 'array', 'object'];

export function ToolForm({ tool, onSuccess }: ToolFormProps) {
  const createMutation = useCreateTool();
  const updateMutation = useUpdateTool();
  const isEditing = !!tool;

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<ToolFormData>({
    resolver: zodResolver(toolSchema),
    defaultValues: tool
      ? {
          name: tool.name,
          description: tool.description,
          type: tool.type,
          enabled: tool.enabled,
          schema: tool.schema,
        }
      : {
          type: 'function',
          enabled: true,
          schema: {
            name: '',
            description: '',
            parameters: [],
          },
        },
  });

  const parameters = watch('schema.parameters') || [];

  const addParameter = () => {
    setValue('schema.parameters', [
      ...parameters,
      { name: '', type: 'string', description: '', required: false },
    ]);
  };

  const removeParameter = (index: number) => {
    setValue(
      'schema.parameters',
      parameters.filter((_, i) => i !== index)
    );
  };

  const onSubmit = async (data: ToolFormData) => {
    try {
      if (isEditing) {
        await updateMutation.mutateAsync({ id: tool.id, data });
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
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 max-h-[70vh] overflow-y-auto pr-2">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="name">Name</Label>
          <Input id="name" placeholder="my_tool" {...register('name')} disabled={isPending} />
          {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
        </div>

        <div className="space-y-2">
          <Label htmlFor="type">Type</Label>
          <Select
            value={watch('type')}
            onValueChange={(value) => setValue('type', value as typeof TOOL_TYPES[number])}
            disabled={isPending}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select type" />
            </SelectTrigger>
            <SelectContent>
              {TOOL_TYPES.map((type) => (
                <SelectItem key={type} value={type}>
                  {type}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          placeholder="Describe what this tool does..."
          {...register('description')}
          disabled={isPending}
        />
      </div>

      <div className="flex items-center space-x-2">
        <Switch
          id="enabled"
          checked={watch('enabled')}
          onCheckedChange={(checked) => setValue('enabled', checked)}
          disabled={isPending}
        />
        <Label htmlFor="enabled">Enabled</Label>
      </div>

      <div className="space-y-4 border-t pt-4">
        <div className="flex items-center justify-between">
          <Label>Parameters</Label>
          <Button type="button" variant="outline" size="sm" onClick={addParameter}>
            <Plus className="mr-2 h-4 w-4" />
            Add Parameter
          </Button>
        </div>

        {parameters.map((_, index) => (
          <div key={index} className="grid grid-cols-12 gap-2 items-start border p-3 rounded-md">
            <div className="col-span-3">
              <Input
                placeholder="Name"
                {...register(`schema.parameters.${index}.name`)}
                disabled={isPending}
              />
            </div>
            <div className="col-span-2">
              <Select
                value={watch(`schema.parameters.${index}.type`)}
                onValueChange={(value) => setValue(`schema.parameters.${index}.type`, value)}
                disabled={isPending}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PARAM_TYPES.map((type) => (
                    <SelectItem key={type} value={type}>
                      {type}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="col-span-4">
              <Input
                placeholder="Description"
                {...register(`schema.parameters.${index}.description`)}
                disabled={isPending}
              />
            </div>
            <div className="col-span-2 flex items-center space-x-2">
              <Switch
                checked={watch(`schema.parameters.${index}.required`)}
                onCheckedChange={(checked) =>
                  setValue(`schema.parameters.${index}.required`, checked)
                }
                disabled={isPending}
              />
              <Label className="text-xs">Required</Label>
            </div>
            <div className="col-span-1">
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() => removeParameter(index)}
                disabled={isPending}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        ))}
      </div>

      <div className="flex justify-end gap-2 pt-4 border-t">
        <Button type="submit" disabled={isPending}>
          {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {isEditing ? 'Update Tool' : 'Create Tool'}
        </Button>
      </div>
    </form>
  );
}
