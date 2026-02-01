import { useCallback } from 'react';
import { useAuthStore } from '@/store/authStore';
import { ADMIN_ROUTES } from '@/utils/constants';
import type { UserRole } from '@/types/auth';

type Permission = 'read' | 'write' | 'delete' | 'admin';

const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  admin: ['read', 'write', 'delete', 'admin'],
  user: ['read'],
};

export function usePermissions() {
  const { user, isAuthenticated } = useAuthStore();

  const hasPermission = useCallback(
    (permission: Permission): boolean => {
      if (!isAuthenticated || !user) return false;
      return ROLE_PERMISSIONS[user.role]?.includes(permission) ?? false;
    },
    [isAuthenticated, user]
  );

  const hasRole = useCallback(
    (role: UserRole): boolean => {
      if (!isAuthenticated || !user) return false;
      if (user.role === 'admin') return true;
      return user.role === role;
    },
    [isAuthenticated, user]
  );

  const canAccessRoute = useCallback(
    (path: string): boolean => {
      if (!isAuthenticated) return false;
      if (!user) return false;

      // Check if it's an admin-only route
      const isAdminRoute = ADMIN_ROUTES.some(
        (route) => path === route || path.startsWith(route + '/')
      );

      if (isAdminRoute) {
        return user.role === 'admin';
      }

      return true;
    },
    [isAuthenticated, user]
  );

  const canRead = useCallback(() => hasPermission('read'), [hasPermission]);
  const canWrite = useCallback(() => hasPermission('write'), [hasPermission]);
  const canDelete = useCallback(() => hasPermission('delete'), [hasPermission]);
  const isAdmin = useCallback(() => hasPermission('admin'), [hasPermission]);

  return {
    hasPermission,
    hasRole,
    canAccessRoute,
    canRead,
    canWrite,
    canDelete,
    isAdmin,
    role: user?.role ?? null,
  };
}
