export const APP_NAME = import.meta.env.VITE_APP_NAME || 'Agentic AI Framework';
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
export const AUTH_ENABLED = import.meta.env.VITE_AUTH_ENABLED !== 'false';
export const ENABLE_MOCKS = import.meta.env.VITE_ENABLE_MOCKS === 'true';

export const TOKEN_KEY = 'auth_token';
export const USER_KEY = 'auth_user';

export const ROUTES = {
  LOGIN: '/login',
  DASHBOARD: '/',
  APPS: '/apps',
  APP_DETAIL: '/apps/:appId',
  HELLO_WORLD_APP: '/apps/hello-world',
  NEWSLETTER_APP: '/apps/newsletter',
  NEWSLETTER_CAMPAIGNS: '/apps/newsletter/campaigns',
  NEWSLETTER_CAMPAIGN_DETAIL: '/apps/newsletter/campaigns/:id',
  NEWSLETTER_SUBSCRIBERS: '/apps/newsletter/subscribers',
  NEWSLETTER_TEMPLATES: '/apps/newsletter/templates',
  NEWSLETTER_ANALYTICS: '/apps/newsletter/analytics',
  NEWSLETTER_WORKFLOW: '/apps/newsletter/workflow/:id',
  AGENTS: '/agents',
  STUDIO: '/studio',
  STUDIO_INSPECTOR: '/studio/:platformId/:agentName',
  AGENT_DETAIL: '/agents/:id',
  TOOLS: '/tools',
  TOOLS_INSPECTOR: '/tools/:toolId',
  TOOL_DETAIL: '/tools/:id',
  WORKFLOWS: '/workflows',
  WORKFLOW_BUILDER: '/workflows/:id',
  EXECUTIONS: '/executions',
  EXECUTION_DETAIL: '/executions/:id',
  DATA: '/data',
  WEAVIATE: '/data/weaviate',
  MONGODB: '/data/mongodb',
  LOGS: '/logs',
  HEALTH: '/health',
  SETTINGS: '/settings',
  API_EXPLORER: '/api-explorer',
} as const;

export const ROLE_PERMISSIONS = {
  admin: ['read', 'write', 'delete', 'admin'],
  user: ['read'],
} as const;

export const PUBLIC_ROUTES = [ROUTES.LOGIN];

export const ADMIN_ROUTES = [
  ROUTES.DATA,
  ROUTES.WEAVIATE,
  ROUTES.MONGODB,
  ROUTES.SETTINGS,
  ROUTES.API_EXPLORER,
];

export const HEALTH_REFRESH_INTERVAL = 30000; // 30 seconds
export const LOG_STREAM_RECONNECT_INTERVAL = 5000; // 5 seconds

export const DEFAULT_PAGE_SIZE = 20;
export const MAX_PAGE_SIZE = 100;
