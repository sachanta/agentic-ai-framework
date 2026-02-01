import { Navigate } from 'react-router-dom';
import { usePermissions } from '@/hooks/usePermissions';
import { ROUTES } from '@/utils/constants';
import type { UserRole } from '@/types/auth';

interface RoleGuardProps {
  children: React.ReactNode;
  requiredRole: UserRole;
  fallback?: React.ReactNode;
}

export function RoleGuard({ children, requiredRole, fallback }: RoleGuardProps) {
  const { hasRole } = usePermissions();

  if (!hasRole(requiredRole)) {
    if (fallback) {
      return <>{fallback}</>;
    }
    return <Navigate to={ROUTES.DASHBOARD} replace />;
  }

  return <>{children}</>;
}

interface PermissionGuardProps {
  children: React.ReactNode;
  permission: 'read' | 'write' | 'delete' | 'admin';
  fallback?: React.ReactNode;
}

export function PermissionGuard({ children, permission, fallback }: PermissionGuardProps) {
  const { hasPermission } = usePermissions();

  if (!hasPermission(permission)) {
    if (fallback) {
      return <>{fallback}</>;
    }
    return null;
  }

  return <>{children}</>;
}
