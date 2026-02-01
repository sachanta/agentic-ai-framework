/**
 * App/Platform types for the frontend
 */

export interface App {
  id: string;
  name: string;
  description: string;
  version: string;
  status: 'active' | 'inactive' | 'error';
  icon?: string;
  agents: string[];
  enabled: boolean;
  config?: Record<string, unknown>;
}

export interface AppAgent {
  id: string;
  name: string;
  description: string;
  status: string;
}

export interface AppStatus {
  platform_id: string;
  name: string;
  status: string;
  agents: string[];
  version: string;
}

export interface AppExecuteRequest {
  input: Record<string, unknown>;
}

export interface AppExecuteResponse {
  result: Record<string, unknown>;
  agent: string;
  orchestrator?: string;
  metadata?: Record<string, unknown>;
}

// Hello World specific types
export type GreetingStyle = 'friendly' | 'formal' | 'casual' | 'enthusiastic';

export interface HelloWorldRequest {
  name: string;
  style?: GreetingStyle;
}

export interface HelloWorldResponse {
  greeting: string;
  agent: string;
  metadata?: Record<string, unknown>;
}
