import apiClient from './client';
import type { User } from '@/types/auth';

export const adminApi = {
  listPendingUsers: async (): Promise<User[]> => {
    const response = await apiClient.get<User[]>('/api/v1/auth/admin/users/pending');
    return response.data;
  },

  approveUser: async (userId: string): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>(
      `/api/v1/auth/admin/users/${userId}/approve`
    );
    return response.data;
  },

  rejectUser: async (userId: string): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>(
      `/api/v1/auth/admin/users/${userId}/reject`
    );
    return response.data;
  },
};
