import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Boxes,
  Bot,
  Wrench,
  GitBranch,
  Play,
  FileText,
  Activity,
  Settings,
  Database,
  Code,
  ChevronLeft,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { useUIStore } from '@/store/uiStore';
import { usePermissions } from '@/hooks/usePermissions';
import { ROUTES } from '@/utils/constants';

interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  adminOnly?: boolean;
}

const mainNavItems: NavItem[] = [
  { title: 'Dashboard', href: ROUTES.DASHBOARD, icon: LayoutDashboard },
  { title: 'Apps', href: ROUTES.APPS, icon: Boxes },
  { title: 'Agents', href: ROUTES.AGENTS, icon: Bot },
  { title: 'Tools', href: ROUTES.TOOLS, icon: Wrench },
  { title: 'Workflows', href: ROUTES.WORKFLOWS, icon: GitBranch },
  { title: 'Executions', href: ROUTES.EXECUTIONS, icon: Play },
  { title: 'Logs', href: ROUTES.LOGS, icon: FileText },
  { title: 'Health', href: ROUTES.HEALTH, icon: Activity },
];

const adminNavItems: NavItem[] = [
  { title: 'Data', href: ROUTES.DATA, icon: Database, adminOnly: true },
  { title: 'Settings', href: ROUTES.SETTINGS, icon: Settings, adminOnly: true },
  { title: 'API Explorer', href: ROUTES.API_EXPLORER, icon: Code, adminOnly: true },
];

export function Sidebar() {
  const location = useLocation();
  const { sidebarCollapsed, toggleSidebarCollapsed } = useUIStore();
  const { isAdmin } = usePermissions();

  const isActive = (href: string) => {
    if (href === '/') return location.pathname === '/';
    return location.pathname.startsWith(href);
  };

  return (
    <aside
      className={cn(
        'relative flex flex-col border-r bg-background transition-all duration-300',
        sidebarCollapsed ? 'w-16' : 'w-64'
      )}
    >
      <div className="flex h-16 items-center justify-between px-4">
        {!sidebarCollapsed && (
          <Link to="/" className="flex items-center space-x-2">
            <Bot className="h-6 w-6" />
            <span className="font-bold">AI Framework</span>
          </Link>
        )}
        <Button
          variant="ghost"
          size="icon"
          className={cn('h-8 w-8', sidebarCollapsed && 'mx-auto')}
          onClick={toggleSidebarCollapsed}
        >
          <ChevronLeft
            className={cn('h-4 w-4 transition-transform', sidebarCollapsed && 'rotate-180')}
          />
        </Button>
      </div>

      <Separator />

      <ScrollArea className="flex-1 px-2 py-4">
        <nav className="space-y-1">
          {mainNavItems.map((item) => (
            <Link
              key={item.href}
              to={item.href}
              className={cn(
                'flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive(item.href)
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-muted',
                sidebarCollapsed && 'justify-center px-2'
              )}
            >
              <item.icon className={cn('h-5 w-5', !sidebarCollapsed && 'mr-3')} />
              {!sidebarCollapsed && item.title}
            </Link>
          ))}
        </nav>

        {isAdmin() && (
          <>
            <Separator className="my-4" />
            <nav className="space-y-1">
              {adminNavItems.map((item) => (
                <Link
                  key={item.href}
                  to={item.href}
                  className={cn(
                    'flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors',
                    isActive(item.href)
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted',
                    sidebarCollapsed && 'justify-center px-2'
                  )}
                >
                  <item.icon className={cn('h-5 w-5', !sidebarCollapsed && 'mr-3')} />
                  {!sidebarCollapsed && item.title}
                </Link>
              ))}
            </nav>
          </>
        )}
      </ScrollArea>
    </aside>
  );
}
