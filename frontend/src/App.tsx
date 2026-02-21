import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppLayout } from '@/components/layout/AppLayout';
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';
import { RoleGuard } from '@/components/layout/RoleGuard';
import { TooltipProvider } from '@/components/ui/tooltip';
import { Toaster } from '@/components/ui/toaster';
import { ROUTES } from '@/utils/constants';

// Pages
import LoginPage from '@/pages/LoginPage';
import DashboardPage from '@/pages/DashboardPage';
import AppsPage from '@/pages/AppsPage';
import AppDetailPage from '@/pages/AppDetailPage';
import HelloWorldPage from '@/pages/apps/HelloWorldPage';
import NewsletterPage from '@/pages/apps/NewsletterPage';
import {
  CampaignsPage,
  CampaignDetailPage,
  SubscribersPage,
  TemplatesPage,
  AnalyticsPage,
  WorkflowPage,
} from '@/pages/newsletter';
import AgentsPage from '@/pages/AgentsPage';
import StudioPage from '@/pages/StudioPage';
import AgentInspectorPage from '@/pages/AgentInspectorPage';
import AgentDetailPage from '@/pages/AgentDetailPage';
import ToolsPage from '@/pages/ToolsPage';
import ToolInspectorPage from '@/pages/ToolInspectorPage';
import ToolDetailPage from '@/pages/ToolDetailPage';
import WorkflowsPage from '@/pages/WorkflowsPage';
import WorkflowBuilderPage from '@/pages/WorkflowBuilderPage';
import ExecutionsPage from '@/pages/ExecutionsPage';
import ExecutionDetailPage from '@/pages/ExecutionDetailPage';
import DataPage from '@/pages/DataPage';
import WeaviatePage from '@/pages/WeaviatePage';
import MongoDBPage from '@/pages/MongoDBPage';
import LogsPage from '@/pages/LogsPage';
import HealthPage from '@/pages/HealthPage';
import SettingsPage from '@/pages/SettingsPage';
import ApiExplorerPage from '@/pages/ApiExplorerPage';
import NotFoundPage from '@/pages/NotFoundPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60, // 1 minute
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <BrowserRouter>
          <Routes>
            {/* Public routes */}
            <Route path={ROUTES.LOGIN} element={<LoginPage />} />

            {/* Protected routes */}
            <Route
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route path={ROUTES.DASHBOARD} element={<DashboardPage />} />
              <Route path={ROUTES.APPS} element={<AppsPage />} />
              <Route path={ROUTES.HELLO_WORLD_APP} element={<HelloWorldPage />} />
              <Route path={ROUTES.NEWSLETTER_APP} element={<NewsletterPage />} />
              <Route path={ROUTES.NEWSLETTER_CAMPAIGNS} element={<CampaignsPage />} />
              <Route path={ROUTES.NEWSLETTER_CAMPAIGN_DETAIL} element={<CampaignDetailPage />} />
              <Route path={ROUTES.NEWSLETTER_SUBSCRIBERS} element={<SubscribersPage />} />
              <Route path={ROUTES.NEWSLETTER_TEMPLATES} element={<TemplatesPage />} />
              <Route path={ROUTES.NEWSLETTER_ANALYTICS} element={<AnalyticsPage />} />
              <Route path={ROUTES.NEWSLETTER_WORKFLOW} element={<WorkflowPage />} />
              <Route path={ROUTES.APP_DETAIL} element={<AppDetailPage />} />
              <Route path={ROUTES.AGENTS} element={<AgentsPage />} />
              <Route path={ROUTES.STUDIO} element={<StudioPage />} />
              <Route path={ROUTES.STUDIO_INSPECTOR} element={<AgentInspectorPage />} />
              <Route path="/agents/:id" element={<AgentDetailPage />} />
              <Route path={ROUTES.TOOLS} element={<ToolsPage />} />
              <Route path={ROUTES.TOOLS_INSPECTOR} element={<ToolInspectorPage />} />
              <Route path="/tools/:id" element={<ToolDetailPage />} />
              <Route path={ROUTES.WORKFLOWS} element={<WorkflowsPage />} />
              <Route path="/workflows/:id" element={<WorkflowBuilderPage />} />
              <Route path={ROUTES.EXECUTIONS} element={<ExecutionsPage />} />
              <Route path="/executions/:id" element={<ExecutionDetailPage />} />
              <Route path={ROUTES.LOGS} element={<LogsPage />} />
              <Route path={ROUTES.HEALTH} element={<HealthPage />} />

              {/* Admin only routes */}
              <Route
                path={ROUTES.DATA}
                element={
                  <RoleGuard requiredRole="admin">
                    <DataPage />
                  </RoleGuard>
                }
              />
              <Route
                path={ROUTES.WEAVIATE}
                element={
                  <RoleGuard requiredRole="admin">
                    <WeaviatePage />
                  </RoleGuard>
                }
              />
              <Route
                path={ROUTES.MONGODB}
                element={
                  <RoleGuard requiredRole="admin">
                    <MongoDBPage />
                  </RoleGuard>
                }
              />
              <Route
                path={ROUTES.SETTINGS}
                element={
                  <RoleGuard requiredRole="admin">
                    <SettingsPage />
                  </RoleGuard>
                }
              />
              <Route
                path={ROUTES.API_EXPLORER}
                element={
                  <RoleGuard requiredRole="admin">
                    <ApiExplorerPage />
                  </RoleGuard>
                }
              />

              {/* Fallback */}
              <Route path="*" element={<NotFoundPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
