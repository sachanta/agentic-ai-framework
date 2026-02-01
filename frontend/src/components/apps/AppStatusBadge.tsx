/**
 * Status badge component for apps
 */
import { Badge } from '@/components/ui/badge';
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react';

interface AppStatusBadgeProps {
  status: 'active' | 'inactive' | 'error' | string;
  size?: 'sm' | 'md';
}

const statusConfig = {
  active: {
    label: 'Active',
    variant: 'default' as const,
    icon: CheckCircle,
    className: 'bg-green-500/10 text-green-500 hover:bg-green-500/20',
  },
  inactive: {
    label: 'Inactive',
    variant: 'secondary' as const,
    icon: XCircle,
    className: 'bg-gray-500/10 text-gray-500 hover:bg-gray-500/20',
  },
  error: {
    label: 'Error',
    variant: 'destructive' as const,
    icon: AlertCircle,
    className: 'bg-red-500/10 text-red-500 hover:bg-red-500/20',
  },
};

export function AppStatusBadge({ status, size = 'md' }: AppStatusBadgeProps) {
  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.inactive;
  const Icon = config.icon;

  return (
    <Badge variant={config.variant} className={`${config.className} ${size === 'sm' ? 'text-xs px-2 py-0.5' : ''}`}>
      <Icon className={`${size === 'sm' ? 'h-3 w-3' : 'h-4 w-4'} mr-1`} />
      {config.label}
    </Badge>
  );
}
