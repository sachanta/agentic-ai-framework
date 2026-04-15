import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuthStore } from '@/store/authStore';
import { signupSchema, type SignupFormData } from '@/utils/validation';

const AVAILABLE_PLATFORMS = [
  { id: 'newsletter', label: 'Newsletter' },
  { id: 'hello_world', label: 'Hello World' },
];

export function SignupForm() {
  const { register: registerUser, isLoading, error, clearError } = useAuthStore();
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      platforms: [],
    },
  });

  const selectedPlatforms = watch('platforms');

  const togglePlatform = (platformId: string) => {
    const current = selectedPlatforms || [];
    const updated = current.includes(platformId)
      ? current.filter((p) => p !== platformId)
      : [...current, platformId];
    setValue('platforms', updated, { shouldValidate: true });
  };

  const onSubmit = async (data: SignupFormData) => {
    clearError();
    try {
      await registerUser({
        email: data.email,
        password: data.password,
        platforms: data.platforms,
      });
      setSuccess(true);
    } catch {
      // Error is handled by the store
    }
  };

  if (success) {
    return (
      <Card className="w-full max-w-md">
        <CardContent className="pt-6">
          <div className="text-center space-y-4">
            <CheckCircle className="mx-auto h-12 w-12 text-green-500" />
            <h3 className="text-lg font-semibold">Account Created!</h3>
            <p className="text-muted-foreground">
              Your account is awaiting admin approval. You'll be able to sign in
              once your account has been approved.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl font-bold">Create an account</CardTitle>
        <CardDescription>Enter your details to get started</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {error && (
            <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="you@example.com"
              {...register('email')}
              disabled={isLoading}
            />
            {errors.email && (
              <p className="text-sm text-destructive">{errors.email.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="At least 8 characters"
              {...register('password')}
              disabled={isLoading}
            />
            {errors.password && (
              <p className="text-sm text-destructive">{errors.password.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirm Password</Label>
            <Input
              id="confirmPassword"
              type="password"
              placeholder="Confirm your password"
              {...register('confirmPassword')}
              disabled={isLoading}
            />
            {errors.confirmPassword && (
              <p className="text-sm text-destructive">{errors.confirmPassword.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label>Platform Access</Label>
            <p className="text-sm text-muted-foreground">
              Select which platform(s) you need access to
            </p>
            <div className="space-y-2 pt-1">
              {AVAILABLE_PLATFORMS.map((platform) => (
                <label
                  key={platform.id}
                  className="flex items-center gap-3 rounded-md border p-3 cursor-pointer hover:bg-muted/50 transition-colors"
                >
                  <input
                    type="checkbox"
                    checked={selectedPlatforms?.includes(platform.id) ?? false}
                    onChange={() => togglePlatform(platform.id)}
                    disabled={isLoading}
                    className="h-4 w-4 rounded border-gray-300"
                  />
                  <span className="text-sm font-medium">{platform.label}</span>
                </label>
              ))}
            </div>
            {errors.platforms && (
              <p className="text-sm text-destructive">{errors.platforms.message}</p>
            )}
          </div>

          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Create account
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
