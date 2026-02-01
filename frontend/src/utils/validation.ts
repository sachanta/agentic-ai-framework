import { z } from 'zod';

export const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
});

export const agentSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100, 'Name must be less than 100 characters'),
  description: z.string().max(500, 'Description must be less than 500 characters').optional(),
  config: z.object({
    model: z.string().min(1, 'Model is required'),
    temperature: z.number().min(0).max(2).optional(),
    maxTokens: z.number().min(1).max(100000).optional(),
    systemPrompt: z.string().max(10000, 'System prompt must be less than 10000 characters').optional(),
    timeout: z.number().min(1000).max(300000).optional(),
    retryAttempts: z.number().min(0).max(10).optional(),
  }),
  tools: z.array(z.string()).optional(),
});

export const toolSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100, 'Name must be less than 100 characters'),
  description: z.string().max(500, 'Description must be less than 500 characters').optional(),
  type: z.enum(['function', 'api', 'database', 'file', 'custom']),
  enabled: z.boolean().optional(),
  schema: z.object({
    name: z.string().min(1, 'Schema name is required'),
    description: z.string(),
    parameters: z.array(z.object({
      name: z.string().min(1, 'Parameter name is required'),
      type: z.string().min(1, 'Parameter type is required'),
      description: z.string(),
      required: z.boolean(),
      default: z.unknown().optional(),
      enum: z.array(z.string()).optional(),
    })),
    returns: z.object({
      type: z.string(),
      description: z.string(),
    }).optional(),
  }),
});

export const workflowSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100, 'Name must be less than 100 characters'),
  description: z.string().max(500, 'Description must be less than 500 characters').optional(),
  status: z.enum(['draft', 'active', 'inactive', 'archived']).optional(),
  variables: z.record(z.unknown()).optional(),
});

export const generalSettingsSchema = z.object({
  appName: z.string().min(1, 'App name is required'),
  logLevel: z.enum(['debug', 'info', 'warning', 'error']),
  timezone: z.string().min(1, 'Timezone is required'),
  maxConcurrentTasks: z.number().min(1).max(100),
});

export const apiSettingsSchema = z.object({
  rateLimit: z.number().min(1).max(10000),
  rateLimitWindow: z.number().min(1).max(3600),
  timeout: z.number().min(1000).max(300000),
  maxRequestSize: z.string().min(1),
});

export const llmSettingsSchema = z.object({
  defaultProvider: z.string().min(1),
  defaultModel: z.string().min(1),
  temperature: z.number().min(0).max(2),
  maxTokens: z.number().min(1).max(100000),
});

export const securitySettingsSchema = z.object({
  sessionTimeout: z.number().min(1).max(10080),
  maxLoginAttempts: z.number().min(1).max(20),
  lockoutDuration: z.number().min(1).max(1440),
  requireMFA: z.boolean(),
});

export const notificationSettingsSchema = z.object({
  emailEnabled: z.boolean(),
  slackEnabled: z.boolean(),
  webhookEnabled: z.boolean(),
});

export const settingsSchema = z.object({
  general: generalSettingsSchema,
  api: apiSettingsSchema,
  llm: llmSettingsSchema,
  security: securitySettingsSchema,
  notifications: notificationSettingsSchema,
});

export type LoginFormData = z.infer<typeof loginSchema>;
export type AgentFormData = z.infer<typeof agentSchema>;
export type ToolFormData = z.infer<typeof toolSchema>;
export type WorkflowFormData = z.infer<typeof workflowSchema>;
export type SettingsFormData = z.infer<typeof settingsSchema>;
