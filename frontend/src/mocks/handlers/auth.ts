import { http, HttpResponse } from 'msw';
import { mockUsers } from '../data/users';

const loginHandler = async ({ request }: { request: Request }) => {
  const body = await request.json() as { username: string; password: string };
  const user = mockUsers.find(
    (u) => u.username === body.username && u.password === body.password
  );

  if (!user) {
    return HttpResponse.json(
      { message: 'Invalid username or password' },
      { status: 401 }
    );
  }

  const { password: _, ...userWithoutPassword } = user;
  return HttpResponse.json({
    user: userWithoutPassword,
    token: `mock-token-${user.id}`,
    expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
  });
};

export const authHandlers = [
  http.post('*/api/v1/auth/login', loginHandler),
  http.post('*/api/v1/auth/login/json', loginHandler),

  http.post('*/api/v1/auth/logout', () => {
    return HttpResponse.json({ message: 'Logged out' });
  }),

  http.get('*/api/v1/auth/me', ({ request }) => {
    const authHeader = request.headers.get('Authorization');
    if (!authHeader?.startsWith('Bearer ')) {
      return HttpResponse.json({ message: 'Unauthorized' }, { status: 401 });
    }

    const token = authHeader.slice(7);
    const userId = token.replace('mock-token-', '');
    const user = mockUsers.find((u) => u.id === userId);

    if (!user) {
      return HttpResponse.json({ message: 'Unauthorized' }, { status: 401 });
    }

    const { password: _, ...userWithoutPassword } = user;
    return HttpResponse.json(userWithoutPassword);
  }),

  http.post('*/api/v1/auth/refresh', ({ request }) => {
    const authHeader = request.headers.get('Authorization');
    if (!authHeader?.startsWith('Bearer ')) {
      return HttpResponse.json({ message: 'Unauthorized' }, { status: 401 });
    }

    return HttpResponse.json({
      token: authHeader.slice(7),
      expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
    });
  }),
];
