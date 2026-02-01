import { Navigate } from 'react-router-dom';
import { Bot } from 'lucide-react';
import { LoginForm } from '@/components/auth/LoginForm';
import { useAuthStore } from '@/store/authStore';
import { ROUTES } from '@/utils/constants';

export function LoginPage() {
  const { isAuthenticated } = useAuthStore();

  if (isAuthenticated) {
    return <Navigate to={ROUTES.DASHBOARD} replace />;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30">
      <div className="w-full max-w-md space-y-8 px-4">
        <div className="text-center">
          <Bot className="mx-auto h-12 w-12" />
          <h1 className="mt-4 text-3xl font-bold">Agentic AI Framework</h1>
          <p className="mt-2 text-muted-foreground">Sign in to your account</p>
        </div>
        <LoginForm />
      </div>
    </div>
  );
}

export default LoginPage;
