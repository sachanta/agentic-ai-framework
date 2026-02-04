/**
 * Newsletter Platform types
 */

// Research request/response types
export interface ResearchRequest {
  topics: string[];
  max_results?: number;
  include_summaries?: boolean;
  days_back?: number;
}

export interface CustomResearchRequest {
  prompt: string;
  max_results?: number;
  include_summaries?: boolean;
}

export interface Article {
  title: string;
  url: string;
  source: string;
  content?: string;
  summary?: string;
  key_takeaway?: string;
  published_date?: string;
  score: number;
  relevance_score: number;
  quality_score: number;
  recency_boost: number;
}

export interface ResearchMetadata {
  topics: string[];
  total_found: number;
  after_filter: number;
  source: string;
  cached: boolean;
  message?: string;
}

export interface ResearchResponse {
  success: boolean;
  articles: Article[];
  metadata: ResearchMetadata;
  error?: string;
}

// Platform status types
export interface NewsletterStatus {
  platform_id: string;
  name: string;
  status: string;
  agents: string[];
  version: string;
  llm_provider: string;
  llm_model: string;
}

export interface NewsletterAgent {
  id: string;
  name: string;
  description: string;
  status: string;
}
