import apiClient from './client';
import { API_URL } from '@/utils/constants';
import type { PaginatedResponse, QueryParams } from '@/types/common';

export interface WeaviateCollection {
  name: string;
  description?: string;
  vectorizer: string;
  properties: WeaviateProperty[];
  object_count: number;
}

export interface WeaviateProperty {
  name: string;
  dataType: string[];
  description?: string;
  indexInverted?: boolean;
  tokenization?: string;
}

export interface WeaviateDocument {
  id: string;
  class: string;
  properties: Record<string, unknown>;
  vector?: number[];
  createdAt: string;
  updatedAt: string;
}

export interface VectorSearchRequest {
  collection: string;
  query: string;
  limit?: number;
  certainty?: number;
  properties?: string[];
}

export interface VectorSearchResult {
  id: string;
  properties: Record<string, unknown>;
  certainty: number;
  distance?: number;
}

export interface PDFUploadProgress {
  upload_id: string;
  stage: 'validating' | 'extracting' | 'chunking' | 'embedding' | 'storing' | 'completed' | 'failed' | 'heartbeat';
  progress: number;
  message: string;
  current_chunk?: number;
  total_chunks?: number;
  chunks_stored?: number;
  error?: string;
  timestamp?: string;
}

export interface PDFUploadResponse {
  upload_id: string;
  filename: string;
  title: string;
  status: string;
  message: string;
}

export interface PDFUploadResult {
  upload_id: string;
  success: boolean;
  filename: string;
  title: string;
  chunks_created: number;
  chunks_stored: number;
  chunks_failed: number;
  total_pages: number;
  processing_time_seconds: number;
  error?: string;
  chunk_ids: string[];
}

const BASE_PATH = '/api/v1/weaviate';

export const weaviateApi = {
  listCollections: async (): Promise<WeaviateCollection[]> => {
    const response = await apiClient.get<WeaviateCollection[]>(`${BASE_PATH}/collections`);
    return response.data;
  },

  getCollection: async (name: string): Promise<WeaviateCollection> => {
    const response = await apiClient.get<WeaviateCollection>(`${BASE_PATH}/collections/${name}`);
    return response.data;
  },

  createCollection: async (data: {
    name: string;
    description?: string;
    vectorizer?: string;
    properties: WeaviateProperty[];
  }): Promise<WeaviateCollection> => {
    const response = await apiClient.post<WeaviateCollection>(`${BASE_PATH}/collections`, data);
    return response.data;
  },

  deleteCollection: async (name: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/collections/${name}`);
  },

  listDocuments: async (collection: string, page: number = 1, pageSize: number = 20): Promise<PaginatedResponse<WeaviateDocument>> => {
    const response = await apiClient.get<PaginatedResponse<WeaviateDocument>>(
      `${BASE_PATH}/collections/${collection}/documents`,
      { params: { page, pageSize } }
    );
    return response.data;
  },

  getDocument: async (collection: string, id: string): Promise<WeaviateDocument> => {
    const response = await apiClient.get<WeaviateDocument>(
      `${BASE_PATH}/collections/${collection}/documents/${id}`
    );
    return response.data;
  },

  addDocument: async (collection: string, properties: Record<string, unknown>): Promise<WeaviateDocument> => {
    const response = await apiClient.post<WeaviateDocument>(
      `${BASE_PATH}/collections/${collection}/documents`,
      { properties }
    );
    return response.data;
  },

  updateDocument: async (collection: string, id: string, data: {
    properties: Record<string, unknown>;
  }): Promise<WeaviateDocument> => {
    const response = await apiClient.patch<WeaviateDocument>(
      `${BASE_PATH}/collections/${collection}/documents/${id}`,
      data
    );
    return response.data;
  },

  deleteDocument: async (collection: string, id: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/collections/${collection}/documents/${id}`);
  },

  search: async (request: VectorSearchRequest): Promise<VectorSearchResult[]> => {
    const response = await apiClient.post<VectorSearchResult[]>(`${BASE_PATH}/search`, request);
    return response.data;
  },

  bulkImport: async (collection: string, documents: Array<{
    properties: Record<string, unknown>;
    vector?: number[];
  }>): Promise<{ imported: number; failed: number; total: number }> => {
    const response = await apiClient.post(`${BASE_PATH}/collections/${collection}/import`, { documents });
    return response.data;
  },

  uploadPDF: async (file: File, options?: {
    title?: string;
    source?: string;
    chunkSize?: number;
    chunkOverlap?: number;
    metadata?: Record<string, unknown>;
  }): Promise<PDFUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    if (options?.title) formData.append('title', options.title);
    if (options?.source) formData.append('source', options.source);
    if (options?.chunkSize) formData.append('chunk_size', options.chunkSize.toString());
    if (options?.chunkOverlap) formData.append('chunk_overlap', options.chunkOverlap.toString());
    if (options?.metadata) formData.append('metadata', JSON.stringify(options.metadata));

    const response = await apiClient.post<PDFUploadResponse>(
      `${BASE_PATH}/rag/upload-pdf`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return response.data;
  },

  getPDFUploadStatus: async (uploadId: string): Promise<{
    upload_id: string;
    filename: string;
    state: string;
    started_at?: string;
    completed_at?: string;
    result?: PDFUploadResult;
  }> => {
    const response = await apiClient.get(`${BASE_PATH}/rag/upload-pdf/${uploadId}/status`);
    return response.data;
  },

  cancelPDFUpload: async (uploadId: string): Promise<{ cancelled: boolean; message: string }> => {
    const response = await apiClient.delete(`${BASE_PATH}/rag/upload-pdf/${uploadId}`);
    return response.data;
  },

  createPDFProgressEventSource: (uploadId: string): EventSource => {
    return new EventSource(`${API_URL}${BASE_PATH}/rag/upload-pdf/${uploadId}/progress`);
  },
};
