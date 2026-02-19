/** LLM configuration extracted from an agent. */
export interface StudioLLMConfig {
  provider: string | null;
  model: string | null;
  temperature: number | null;
  max_tokens: number | null;
}

/** Tool metadata for display. */
export interface StudioToolInfo {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
}

/** Lightweight agent summary for catalog grid. */
export interface StudioAgentSummary {
  agent_id: string;
  name: string;
  display_name: string;
  platform_id: string;
  platform_name: string;
  description: string;
  llm_config: StudioLLMConfig;
  tool_count: number;
  has_system_prompt: boolean;
  agent_class: string;
  status: string;
}

/** Full agent detail including prompt and tools. */
export interface StudioAgentDetail extends StudioAgentSummary {
  system_prompt: string | null;
  tools: StudioToolInfo[];
  parameters: Record<string, unknown>;
}

/** Platform summary with agent counts. */
export interface StudioPlatformSummary {
  id: string;
  name: string;
  description: string;
  version: string;
  agent_count: number;
  agents: string[];
  enabled: boolean;
}

/** Response for GET /studio/agents. */
export interface StudioAgentsListResponse {
  agents: StudioAgentSummary[];
  total: number;
  platforms: StudioPlatformSummary[];
}

/** Response for GET /studio/platforms. */
export interface StudioPlatformsListResponse {
  platforms: StudioPlatformSummary[];
  total: number;
}
