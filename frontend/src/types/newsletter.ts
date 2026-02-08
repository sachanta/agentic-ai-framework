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

// Writing request/response types (Phase 7)
export interface GenerateRequest {
  articles: Article[];
  tone: string;
  user_id?: string;
  include_rag?: boolean;
}

export interface SubjectLine {
  text: string;
  style: string;
}

export interface NewsletterContent {
  content: string;
  word_count: number;
}

export interface NewsletterFormats {
  html: string;
  text: string;
  markdown: string;
}

export interface NewsletterSummary {
  bullets: string[];
  raw?: string;
}

export interface GenerateMetadata {
  article_count: number;
  topics: string[];
  tone: string;
  generated_at: string;
  rag_examples_used?: number;
}

export interface GenerateResponse {
  success: boolean;
  newsletter?: NewsletterContent;
  subject_lines: SubjectLine[];
  summary?: NewsletterSummary;
  formats?: NewsletterFormats;
  metadata?: GenerateMetadata;
  error?: string;
}

export type WritingTone = 'professional' | 'casual' | 'formal' | 'enthusiastic';
