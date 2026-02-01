/**
 * MSW handlers for apps/platforms endpoints
 */
import { http, HttpResponse } from 'msw';
import { mockApps, mockAppAgents, mockAppStatus, greetingsByStyle } from '../data/apps';
import type { HelloWorldRequest } from '@/types/app';

export const appsHandlers = [
  // List all apps/platforms
  http.get('*/api/v1/platforms', () => {
    return HttpResponse.json(mockApps);
  }),

  // Get app by ID
  http.get('*/api/v1/platforms/:appId', ({ params }) => {
    const app = mockApps.find((a) => a.id === params.appId);
    if (!app) {
      return HttpResponse.json({ message: 'App not found' }, { status: 404 });
    }
    return HttpResponse.json(app);
  }),

  // Get app status
  http.get('*/api/v1/platforms/:appId/status', ({ params }) => {
    const status = mockAppStatus[params.appId as string];
    if (!status) {
      return HttpResponse.json({ message: 'App not found' }, { status: 404 });
    }
    return HttpResponse.json(status);
  }),

  // Get app agents
  http.get('*/api/v1/platforms/:appId/agents', ({ params }) => {
    const agents = mockAppAgents[params.appId as string];
    if (!agents) {
      return HttpResponse.json({ message: 'App not found' }, { status: 404 });
    }
    return HttpResponse.json(agents);
  }),

  // Execute app
  http.post('*/api/v1/platforms/:appId/execute', async ({ params, request }) => {
    const appId = params.appId as string;
    const app = mockApps.find((a) => a.id === appId);

    if (!app) {
      return HttpResponse.json({ message: 'App not found' }, { status: 404 });
    }

    const body = await request.json() as Record<string, unknown>;

    // Generic execute response
    return HttpResponse.json({
      result: { executed: true, input: body },
      agent: app.agents[0] || 'unknown',
      orchestrator: `${app.name} Orchestrator`,
      metadata: {
        app_id: appId,
        timestamp: new Date().toISOString(),
      },
    });
  }),

  // Hello World specific: execute greeting
  http.post('*/api/v1/platforms/hello-world/execute', async ({ request }) => {
    const body = await request.json() as HelloWorldRequest;
    const name = body.name || 'World';
    const style = body.style || 'friendly';

    const greetingFn = greetingsByStyle[style] || greetingsByStyle.friendly;
    const greeting = greetingFn(name);

    // Simulate some processing delay
    await new Promise((resolve) => setTimeout(resolve, 500));

    return HttpResponse.json({
      greeting,
      agent: 'greeter',
      metadata: {
        name,
        style,
        timestamp: new Date().toISOString(),
      },
    });
  }),
];
