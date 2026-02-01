import { http, HttpResponse } from 'msw';
import { mockWorkflows } from '../data/workflows';

let workflows = [...mockWorkflows];

export const workflowsHandlers = [
  http.get('*/api/v1/workflows', ({ request }) => {
    const url = new URL(request.url);
    const search = url.searchParams.get('search')?.toLowerCase();
    const page = parseInt(url.searchParams.get('page') || '1');
    const pageSize = parseInt(url.searchParams.get('pageSize') || '20');

    let filteredWorkflows = workflows;
    if (search) {
      filteredWorkflows = workflows.filter(
        (w) =>
          w.name.toLowerCase().includes(search) ||
          w.description.toLowerCase().includes(search)
      );
    }

    const total = filteredWorkflows.length;
    const start = (page - 1) * pageSize;
    const items = filteredWorkflows.slice(start, start + pageSize);

    return HttpResponse.json({
      items,
      total,
      page,
      pageSize,
      totalPages: Math.ceil(total / pageSize),
    });
  }),

  http.get('*/api/v1/workflows/:id', ({ params }) => {
    const workflow = workflows.find((w) => w.id === params.id);
    if (!workflow) {
      return HttpResponse.json({ message: 'Workflow not found' }, { status: 404 });
    }
    return HttpResponse.json(workflow);
  }),

  http.post('*/api/v1/workflows', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    const newWorkflow = {
      id: `workflow-${Date.now()}`,
      ...body,
      status: 'draft',
      steps: body.steps || [],
      variables: body.variables || {},
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      executionCount: 0,
    };
    workflows.push(newWorkflow as typeof mockWorkflows[0]);
    return HttpResponse.json(newWorkflow, { status: 201 });
  }),

  http.patch('*/api/v1/workflows/:id', async ({ params, request }) => {
    const index = workflows.findIndex((w) => w.id === params.id);
    if (index === -1) {
      return HttpResponse.json({ message: 'Workflow not found' }, { status: 404 });
    }
    const body = await request.json() as Record<string, unknown>;
    workflows[index] = { ...workflows[index], ...body, updatedAt: new Date().toISOString() };
    return HttpResponse.json(workflows[index]);
  }),

  http.delete('*/api/v1/workflows/:id', ({ params }) => {
    const index = workflows.findIndex((w) => w.id === params.id);
    if (index === -1) {
      return HttpResponse.json({ message: 'Workflow not found' }, { status: 404 });
    }
    workflows.splice(index, 1);
    return HttpResponse.json({ message: 'Workflow deleted' });
  }),

  http.post('*/api/v1/workflows/:id/activate', ({ params }) => {
    const workflow = workflows.find((w) => w.id === params.id);
    if (!workflow) {
      return HttpResponse.json({ message: 'Workflow not found' }, { status: 404 });
    }
    workflow.status = 'active';
    return HttpResponse.json(workflow);
  }),

  http.post('*/api/v1/workflows/:id/deactivate', ({ params }) => {
    const workflow = workflows.find((w) => w.id === params.id);
    if (!workflow) {
      return HttpResponse.json({ message: 'Workflow not found' }, { status: 404 });
    }
    workflow.status = 'inactive';
    return HttpResponse.json(workflow);
  }),

  http.post('*/api/v1/workflows/:id/duplicate', ({ params }) => {
    const workflow = workflows.find((w) => w.id === params.id);
    if (!workflow) {
      return HttpResponse.json({ message: 'Workflow not found' }, { status: 404 });
    }
    const duplicate = {
      ...workflow,
      id: `workflow-${Date.now()}`,
      name: `${workflow.name} (Copy)`,
      status: 'draft' as const,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      executionCount: 0,
    };
    workflows.push(duplicate);
    return HttpResponse.json(duplicate);
  }),

  http.post('*/api/v1/workflows/:id/execute', ({ params }) => {
    const workflow = workflows.find((w) => w.id === params.id);
    if (!workflow) {
      return HttpResponse.json({ message: 'Workflow not found' }, { status: 404 });
    }
    return HttpResponse.json({
      id: `exec-${Date.now()}`,
      workflowId: params.id,
      workflowName: workflow.name,
      status: 'running',
      input: {},
      steps: [],
      startedAt: new Date().toISOString(),
      triggeredBy: 'manual',
    });
  }),

  http.get('*/api/v1/workflows/:id/executions', () => {
    return HttpResponse.json({
      items: [],
      total: 0,
      page: 1,
      pageSize: 20,
      totalPages: 0,
    });
  }),

  http.post('*/api/v1/workflows/:id/validate', () => {
    return HttpResponse.json({ valid: true, errors: [] });
  }),
];
