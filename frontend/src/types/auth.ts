export type UserRole = 'admin' | 'user';
export type UserStatus = 'pending' | 'approved' | 'rejected';

export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  status: UserStatus;
  platforms: string[];
  createdAt?: string;
  lastLogin?: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RegisterRequest {
  email: string;
  password: string;
  platforms: string[];
}

export interface RegisterResponse {
  message: string;
  status: UserStatus;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
