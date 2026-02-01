import apiClient from './client';

export interface GeneralSettings {
  appName: string;
  logLevel: string;
  timezone: string;
  maxConcurrentTasks: number;
}

export interface ApiSettings {
  rateLimit: number;
  rateLimitWindow: number;
  timeout: number;
  maxRequestSize: string;
}

export interface LLMProviderSettings {
  enabled: boolean;
  models: string[];
}

export interface LLMSettings {
  defaultProvider: string;
  defaultModel: string;
  temperature: number;
  maxTokens: number;
  providers: Record<string, LLMProviderSettings>;
}

export interface SecuritySettings {
  sessionTimeout: number;
  maxLoginAttempts: number;
  lockoutDuration: number;
  requireMFA: boolean;
}

export interface NotificationSettings {
  emailEnabled: boolean;
  slackEnabled: boolean;
  webhookEnabled: boolean;
}

export interface AllSettings {
  general: GeneralSettings;
  api: ApiSettings;
  llm: LLMSettings;
  security: SecuritySettings;
  notifications: NotificationSettings;
}

export interface SettingsUpdate {
  settings: Record<string, unknown>;
}

const BASE_PATH = '/api/v1/settings';

export const settingsApi = {
  get: async (): Promise<AllSettings> => {
    const response = await apiClient.get<AllSettings>(BASE_PATH);
    return response.data;
  },

  getCategory: async (category: string): Promise<{ category: string; settings: Record<string, unknown> }> => {
    const response = await apiClient.get(`${BASE_PATH}/${category}`);
    return response.data;
  },

  update: async (data: SettingsUpdate): Promise<AllSettings> => {
    const response = await apiClient.put<AllSettings>(BASE_PATH, data);
    return response.data;
  },

  updateCategory: async (category: string, settings: Record<string, unknown>): Promise<{ category: string; settings: Record<string, unknown> }> => {
    const response = await apiClient.put(`${BASE_PATH}/${category}`, { settings });
    return response.data;
  },

  resetCategory: async (category: string): Promise<{ category: string; settings: Record<string, unknown> }> => {
    const response = await apiClient.post(`${BASE_PATH}/${category}/reset`);
    return response.data;
  },

  reset: async (): Promise<AllSettings> => {
    const response = await apiClient.post<AllSettings>(`${BASE_PATH}/reset`);
    return response.data;
  },
};
