import apiClient from './client';
import type { PaginatedResponse } from '@/types/common';

export interface MongoCollection {
  name: string;
  documentCount: number;
  avgDocumentSize: number;
  indexes: MongoIndex[];
}

export interface MongoIndex {
  name: string;
  keys: Record<string, number>;
  unique?: boolean;
  sparse?: boolean;
}

export interface MongoDocument {
  _id: string;
  [key: string]: unknown;
}

export interface MongoQuery {
  filter?: Record<string, unknown>;
  projection?: Record<string, number>;
  sort?: Record<string, number>;
  limit?: number;
  skip?: number;
}

const BASE_PATH = '/api/v1/mongodb';

export const mongodbApi = {
  listCollections: async (): Promise<MongoCollection[]> => {
    const response = await apiClient.get<MongoCollection[]>(`${BASE_PATH}/collections`);
    return response.data;
  },

  getCollection: async (collection: string): Promise<MongoCollection> => {
    const response = await apiClient.get<MongoCollection>(`${BASE_PATH}/collections/${collection}`);
    return response.data;
  },

  listDocuments: async (
    collection: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<PaginatedResponse<MongoDocument>> => {
    const response = await apiClient.get<PaginatedResponse<MongoDocument>>(
      `${BASE_PATH}/${collection}/documents`,
      { params: { page, pageSize } }
    );
    return response.data;
  },

  getDocument: async (collection: string, id: string): Promise<MongoDocument> => {
    const response = await apiClient.get<MongoDocument>(`${BASE_PATH}/${collection}/documents/${id}`);
    return response.data;
  },

  createDocument: async (
    collection: string,
    document: Record<string, unknown>
  ): Promise<MongoDocument> => {
    const response = await apiClient.post<MongoDocument>(
      `${BASE_PATH}/${collection}/documents`,
      document
    );
    return response.data;
  },

  updateDocument: async (
    collection: string,
    id: string,
    update: Record<string, unknown>
  ): Promise<MongoDocument> => {
    const response = await apiClient.patch<MongoDocument>(
      `${BASE_PATH}/${collection}/documents/${id}`,
      update
    );
    return response.data;
  },

  deleteDocument: async (collection: string, id: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/${collection}/documents/${id}`);
  },

  query: async (
    collection: string,
    query: MongoQuery
  ): Promise<{ documents: MongoDocument[]; count: number; total: number }> => {
    const response = await apiClient.post(
      `${BASE_PATH}/${collection}/query`,
      query
    );
    return response.data;
  },

  importDocuments: async (
    collection: string,
    documents: Record<string, unknown>[]
  ): Promise<{ imported: number; failed: number; total: number }> => {
    const response = await apiClient.post(`${BASE_PATH}/${collection}/import`, { documents });
    return response.data;
  },

  exportDocuments: async (collection: string, format: 'json' | 'csv' = 'json'): Promise<unknown> => {
    const response = await apiClient.get(`${BASE_PATH}/${collection}/export`, {
      params: { format },
    });
    return response.data;
  },
};
