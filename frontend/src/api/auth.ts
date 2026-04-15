import apiClient from './client';
import type { User, LoginCredentials, LoginResponse, RegisterRequest, RegisterResponse } from '@/types/auth';

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<LoginResponse> => {
    // Use /login/json endpoint which accepts JSON body
    const response = await apiClient.post<LoginResponse>('/api/v1/auth/login/json', credentials);
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<RegisterResponse> => {
    const response = await apiClient.post<RegisterResponse>('/api/v1/auth/register', data);
    return response.data;
  },

  logout: async (): Promise<void> => {
    await apiClient.post('/api/v1/auth/logout');
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/api/v1/auth/me');
    return response.data;
  },

  refreshToken: async (): Promise<{ token: string; expiresAt: string }> => {
    const response = await apiClient.post('/api/v1/auth/refresh');
    return response.data;
  },
};
