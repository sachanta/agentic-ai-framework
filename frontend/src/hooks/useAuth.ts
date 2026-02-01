import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { ROUTES } from '@/utils/constants';
import type { LoginCredentials, UserRole } from '@/types/auth';

export function useAuth() {
  const navigate = useNavigate();
  const {
    user,
    token,
    isAuthenticated,
    isLoading,
    error,
    login: storeLogin,
    logout: storeLogout,
    checkAuth,
    clearError,
    hasRole,
    hasPermission,
  } = useAuthStore();

  const login = useCallback(
    async (credentials: LoginCredentials) => {
      await storeLogin(credentials);
      navigate(ROUTES.DASHBOARD);
    },
    [storeLogin, navigate]
  );

  const logout = useCallback(() => {
    storeLogout();
    navigate(ROUTES.LOGIN);
  }, [storeLogout, navigate]);

  const isAdmin = useCallback(() => hasRole('admin'), [hasRole]);
  const isUser = useCallback(() => hasRole('user'), [hasRole]);

  const canAccess = useCallback(
    (requiredRole?: UserRole) => {
      if (!isAuthenticated) return false;
      if (!requiredRole) return true;
      return hasRole(requiredRole);
    },
    [isAuthenticated, hasRole]
  );

  return {
    user,
    token,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    checkAuth,
    clearError,
    hasRole,
    hasPermission,
    isAdmin,
    isUser,
    canAccess,
  };
}
