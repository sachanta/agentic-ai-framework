import { http, HttpResponse } from 'msw';
import { mockExecutions } from '../data/executions';

let executions = [...mockExecutions];

export const executionsHandlers = [
  http.get('*/api/v1/executions', ({ request }) => {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const pageSize = parseInt(url.searchParams.get('pageSize') || '20');

    const total = executions.length;
    const start = (page - 1) * pageSize;
    const items = executions.slice(start, start + pageSize);

    return HttpResponse.json({
      items,
      total,
      page,
      pageSize,
      totalPages: Math.ceil(total / pageSize),
    });
  }),

  http.get('*/api/v1/executions/:id', ({ params }) => {
    const execution = executions.find((e) => e.id === params.id);
    if (!execution) {
      return HttpResponse.json({ message: 'Execution not found' }, { status: 404 });
    }
    return HttpResponse.json(execution);
  }),

  http.post('*/api/v1/executions', async ({ request }) => {
    const body = await request.json() as { workflowId: string; input?: Record<string, unknown> };
    const newExecution = {
      id: `exec-${Date.now()}`,
      workflowId: body.workflowId,
      workflowName: 'Unknown Workflow',
      status: 'pending' as const,
      input: body.input || {},
      steps: [],
      startedAt: new Date().toISOString(),
      triggeredBy: 'manual',
    };
    executions.unshift(newExecution);
    return HttpResponse.json(newExecution, { status: 201 });
  }),

  http.post('*/api/v1/executions/:id/cancel', ({ params }) => {
    const execution = executions.find((e) => e.id === params.id);
    if (!execution) {
      return HttpResponse.json({ message: 'Execution not found' }, { status: 404 });
    }
    execution.status = 'cancelled';
    execution.completedAt = new Date().toISOString();
    return HttpResponse.json(execution);
  }),

  http.post('*/api/v1/executions/:id/pause', ({ params }) => {
    const execution = executions.find((e) => e.id === params.id);
    if (!execution) {
      return HttpResponse.json({ message: 'Execution not found' }, { status: 404 });
    }
    execution.status = 'paused';
    return HttpResponse.json(execution);
  }),

  http.post('*/api/v1/executions/:id/resume', ({ params }) => {
    const execution = executions.find((e) => e.id === params.id);
    if (!execution) {
      return HttpResponse.json({ message: 'Execution not found' }, { status: 404 });
    }
    execution.status = 'running';
    return HttpResponse.json(execution);
  }),

  http.post('*/api/v1/executions/:id/retry', ({ params }) => {
    const execution = executions.find((e) => e.id === params.id);
    if (!execution) {
      return HttpResponse.json({ message: 'Execution not found' }, { status: 404 });
    }
    const newExecution = {
      ...execution,
      id: `exec-${Date.now()}`,
      status: 'pending' as const,
      startedAt: new Date().toISOString(),
      completedAt: undefined,
      error: undefined,
    };
    executions.unshift(newExecution);
    return HttpResponse.json(newExecution);
  }),

  http.get('*/api/v1/executions/:id/logs', () => {
    return HttpResponse.json({
      items: [
        {
          id: 'log-1',
          executionId: 'exec-1',
          level: 'info',
          message: 'Execution started',
          timestamp: new Date().toISOString(),
        },
        {
          id: 'log-2',
          executionId: 'exec-1',
          level: 'info',
          message: 'Processing step 1',
          timestamp: new Date().toISOString(),
        },
      ],
      total: 2,
      page: 1,
      pageSize: 20,
      totalPages: 1,
    });
  }),

  http.get('*/api/v1/executions/stats', () => {
    return HttpResponse.json({
      total: executions.length,
      completed: executions.filter((e) => e.status === 'completed').length,
      failed: executions.filter((e) => e.status === 'failed').length,
      running: executions.filter((e) => e.status === 'running').length,
      pending: executions.filter((e) => e.status === 'pending').length,
      avgDuration: 5000,
      successRate: 0.85,
    });
  }),

  http.delete('*/api/v1/executions/:id', ({ params }) => {
    const index = executions.findIndex((e) => e.id === params.id);
    if (index === -1) {
      return HttpResponse.json({ message: 'Execution not found' }, { status: 404 });
    }
    executions.splice(index, 1);
    return HttpResponse.json({ message: 'Execution deleted' });
  }),
];
