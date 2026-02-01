import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, Save, RotateCcw } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { settingsSchema, type SettingsFormData } from '@/utils/validation';
import { settingsApi, type AllSettings } from '@/api/settings';
import { notify } from '@/store/notificationStore';

export function SettingsForm() {
  const queryClient = useQueryClient();

  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: () => settingsApi.get(),
  });

  const updateMutation = useMutation({
    mutationFn: (data: AllSettings) => settingsApi.update({ settings: data as unknown as Record<string, unknown> }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      notify.success('Settings saved successfully');
    },
    onError: (error: Error) => {
      notify.error('Failed to save settings', error.message);
    },
  });

  const resetMutation = useMutation({
    mutationFn: settingsApi.reset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      notify.success('Settings reset to defaults');
    },
    onError: (error: Error) => {
      notify.error('Failed to reset settings', error.message);
    },
  });

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<SettingsFormData>({
    resolver: zodResolver(settingsSchema),
    values: settings as SettingsFormData | undefined,
  });

  const onSubmit = (data: SettingsFormData) => {
    updateMutation.mutate(data as AllSettings);
  };

  const handleReset = () => {
    if (confirm('Are you sure you want to reset all settings to defaults?')) {
      resetMutation.mutate();
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>General Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="general.appName">Application Name</Label>
              <Input id="general.appName" {...register('general.appName')} />
              {errors.general?.appName && (
                <p className="text-sm text-destructive">{errors.general.appName.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="general.logLevel">Log Level</Label>
              <Select
                value={watch('general.logLevel')}
                onValueChange={(value) => setValue('general.logLevel', value as 'debug' | 'info' | 'warning' | 'error')}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="debug">Debug</SelectItem>
                  <SelectItem value="info">Info</SelectItem>
                  <SelectItem value="warning">Warning</SelectItem>
                  <SelectItem value="error">Error</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="general.timezone">Timezone</Label>
              <Input id="general.timezone" {...register('general.timezone')} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="general.maxConcurrentTasks">Max Concurrent Tasks</Label>
              <Input
                id="general.maxConcurrentTasks"
                type="number"
                {...register('general.maxConcurrentTasks', { valueAsNumber: true })}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>API Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="api.rateLimit">Rate Limit (requests)</Label>
              <Input
                id="api.rateLimit"
                type="number"
                {...register('api.rateLimit', { valueAsNumber: true })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="api.rateLimitWindow">Rate Limit Window (seconds)</Label>
              <Input
                id="api.rateLimitWindow"
                type="number"
                {...register('api.rateLimitWindow', { valueAsNumber: true })}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="api.timeout">Timeout (ms)</Label>
              <Input
                id="api.timeout"
                type="number"
                {...register('api.timeout', { valueAsNumber: true })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="api.maxRequestSize">Max Request Size</Label>
              <Input id="api.maxRequestSize" {...register('api.maxRequestSize')} />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>LLM Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="llm.defaultProvider">Default Provider</Label>
              <Input id="llm.defaultProvider" {...register('llm.defaultProvider')} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="llm.defaultModel">Default Model</Label>
              <Input id="llm.defaultModel" {...register('llm.defaultModel')} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="llm.temperature">Temperature</Label>
              <Input
                id="llm.temperature"
                type="number"
                step="0.1"
                {...register('llm.temperature', { valueAsNumber: true })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="llm.maxTokens">Max Tokens</Label>
              <Input
                id="llm.maxTokens"
                type="number"
                {...register('llm.maxTokens', { valueAsNumber: true })}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Security Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="security.sessionTimeout">Session Timeout (minutes)</Label>
              <Input
                id="security.sessionTimeout"
                type="number"
                {...register('security.sessionTimeout', { valueAsNumber: true })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="security.maxLoginAttempts">Max Login Attempts</Label>
              <Input
                id="security.maxLoginAttempts"
                type="number"
                {...register('security.maxLoginAttempts', { valueAsNumber: true })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="security.lockoutDuration">Lockout Duration (minutes)</Label>
              <Input
                id="security.lockoutDuration"
                type="number"
                {...register('security.lockoutDuration', { valueAsNumber: true })}
              />
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Switch
              id="security.requireMFA"
              checked={watch('security.requireMFA')}
              onCheckedChange={(checked) => setValue('security.requireMFA', checked)}
            />
            <Label htmlFor="security.requireMFA">Require MFA</Label>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Notification Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center space-x-2">
            <Switch
              id="notifications.emailEnabled"
              checked={watch('notifications.emailEnabled')}
              onCheckedChange={(checked) => setValue('notifications.emailEnabled', checked)}
            />
            <Label htmlFor="notifications.emailEnabled">Email Notifications</Label>
          </div>
          <div className="flex items-center space-x-2">
            <Switch
              id="notifications.slackEnabled"
              checked={watch('notifications.slackEnabled')}
              onCheckedChange={(checked) => setValue('notifications.slackEnabled', checked)}
            />
            <Label htmlFor="notifications.slackEnabled">Slack Notifications</Label>
          </div>
          <div className="flex items-center space-x-2">
            <Switch
              id="notifications.webhookEnabled"
              checked={watch('notifications.webhookEnabled')}
              onCheckedChange={(checked) => setValue('notifications.webhookEnabled', checked)}
            />
            <Label htmlFor="notifications.webhookEnabled">Webhook Notifications</Label>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-between">
        <Button
          type="button"
          variant="outline"
          onClick={handleReset}
          disabled={resetMutation.isPending}
        >
          <RotateCcw className="mr-2 h-4 w-4" />
          Reset to Defaults
        </Button>
        <Button type="submit" disabled={updateMutation.isPending}>
          {updateMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          <Save className="mr-2 h-4 w-4" />
          Save Settings
        </Button>
      </div>
    </form>
  );
}
