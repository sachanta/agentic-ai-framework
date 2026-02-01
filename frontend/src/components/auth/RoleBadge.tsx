import { Badge } from '@/components/ui/badge';
import type { UserRole } from '@/types/auth';

interface RoleBadgeProps {
  role: UserRole;
}

export function RoleBadge({ role }: RoleBadgeProps) {
  const variant = role === 'admin' ? 'default' : 'secondary';

  return (
    <Badge variant={variant} className="mt-1 w-fit">
      {role}
    </Badge>
  );
}
