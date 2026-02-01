import type { User } from '@/types/auth';

export const mockUsers: Array<User & { password: string }> = [
  {
    id: 'user-1',
    username: 'admin',
    email: 'admin@example.com',
    role: 'admin',
    password: 'admin123',
    createdAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 'user-2',
    username: 'user',
    email: 'user@example.com',
    role: 'user',
    password: 'user123',
    createdAt: '2024-01-05T10:00:00Z',
  },
];

export function validateCredentials(username: string, password: string): User | null {
  const user = mockUsers.find(
    (u) => u.username === username && u.password === password
  );
  if (!user) return null;

  const { password: _, ...userWithoutPassword } = user;
  return userWithoutPassword;
}

export function generateToken(user: User): string {
  return btoa(JSON.stringify({ userId: user.id, role: user.role, exp: Date.now() + 86400000 }));
}
