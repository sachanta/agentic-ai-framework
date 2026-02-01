/**
 * Mock data for apps/platforms
 */
import type { App, AppAgent, AppStatus } from '@/types/app';

export const mockApps: App[] = [
  {
    id: 'hello-world',
    name: 'Hello World',
    description: 'A sample multi-agent platform for demonstration. Generates personalized greetings using AI agents.',
    version: '1.0.0',
    status: 'active',
    icon: 'hand-wave',
    agents: ['greeter'],
  },
];

export const mockAppAgents: Record<string, AppAgent[]> = {
  'hello-world': [
    {
      id: 'greeter',
      name: 'Greeter Agent',
      description: 'Generates personalized greetings based on name and style',
      status: 'active',
    },
  ],
};

export const mockAppStatus: Record<string, AppStatus> = {
  'hello-world': {
    platform_id: 'hello-world',
    name: 'Hello World',
    status: 'active',
    agents: ['greeter'],
    version: '1.0.0',
  },
};

// Greeting responses based on style
export const greetingsByStyle: Record<string, (name: string) => string> = {
  friendly: (name) => `Hello there, ${name}! Hope you're having a wonderful day!`,
  formal: (name) => `Good day, ${name}. It is a pleasure to make your acquaintance.`,
  casual: (name) => `Hey ${name}! What's up?`,
  enthusiastic: (name) => `WOW! ${name}! SO GREAT to meet you! This is AMAZING!`,
};
