import { http, HttpResponse } from 'msw';

interface Settings {
  apiUrl: string;
  weaviateUrl: string;
  mongodbUri: string;
  maxConcurrentExecutions: number;
  executionTimeout: number;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
  enableMetrics: boolean;
  metricsRetentionDays: number;
}

let settings: Settings = {
  apiUrl: 'http://localhost:8000',
  weaviateUrl: 'http://localhost:8080',
  mongodbUri: 'mongodb://localhost:27017/agentic-ai',
  maxConcurrentExecutions: 10,
  executionTimeout: 300000,
  logLevel: 'info',
  enableMetrics: true,
  metricsRetentionDays: 30,
};

const defaultSettings: Settings = { ...settings };

export const settingsHandlers = [
  http.get('*/api/v1/settings', () => {
    return HttpResponse.json(settings);
  }),

  http.patch('*/api/v1/settings', async ({ request }) => {
    const updates = await request.json() as Partial<Settings>;
    settings = { ...settings, ...updates };
    return HttpResponse.json(settings);
  }),

  http.post('*/api/v1/settings/reset', () => {
    settings = { ...defaultSettings };
    return HttpResponse.json(settings);
  }),
];
