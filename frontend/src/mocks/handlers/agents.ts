import { http, HttpResponse } from 'msw';
import { mockAgents } from '../data/agents';

let agents = [...mockAgents];

export const agentsHandlers = [
  http.get('*/api/v1/agents', ({ request }) => {
    const url = new URL(request.url);
    const search = url.searchParams.get('search')?.toLowerCase();
    const page = parseInt(url.searchParams.get('page') || '1');
    const pageSize = parseInt(url.searchParams.get('pageSize') || '20');

    let filteredAgents = agents;
    if (search) {
      filteredAgents = agents.filter(
        (a) =>
          a.name.toLowerCase().includes(search) ||
          a.description.toLowerCase().includes(search)
      );
    }

    const total = filteredAgents.length;
    const start = (page - 1) * pageSize;
    const items = filteredAgents.slice(start, start + pageSize);

    return HttpResponse.json({
      items,
      total,
      page,
      pageSize,
      totalPages: Math.ceil(total / pageSize),
    });
  }),

  http.get('*/api/v1/agents/:id', ({ params }) => {
    const agent = agents.find((a) => a.id === params.id);
    if (!agent) {
      return HttpResponse.json({ message: 'Agent not found' }, { status: 404 });
    }
    return HttpResponse.json(agent);
  }),

  http.post('*/api/v1/agents', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    const newAgent = {
      id: `agent-${Date.now()}`,
      ...body,
      status: 'inactive',
      tools: body.tools || [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      executionCount: 0,
      successRate: 0,
    };
    agents.push(newAgent as typeof mockAgents[0]);
    return HttpResponse.json(newAgent, { status: 201 });
  }),

  http.patch('*/api/v1/agents/:id', async ({ params, request }) => {
    const index = agents.findIndex((a) => a.id === params.id);
    if (index === -1) {
      return HttpResponse.json({ message: 'Agent not found' }, { status: 404 });
    }
    const body = await request.json() as Record<string, unknown>;
    agents[index] = { ...agents[index], ...body, updatedAt: new Date().toISOString() };
    return HttpResponse.json(agents[index]);
  }),

  http.delete('*/api/v1/agents/:id', ({ params }) => {
    const index = agents.findIndex((a) => a.id === params.id);
    if (index === -1) {
      return HttpResponse.json({ message: 'Agent not found' }, { status: 404 });
    }
    agents.splice(index, 1);
    return HttpResponse.json({ message: 'Agent deleted' });
  }),

  http.post('*/api/v1/agents/:id/activate', ({ params }) => {
    const agent = agents.find((a) => a.id === params.id);
    if (!agent) {
      return HttpResponse.json({ message: 'Agent not found' }, { status: 404 });
    }
    agent.status = 'active';
    return HttpResponse.json(agent);
  }),

  http.post('*/api/v1/agents/:id/deactivate', ({ params }) => {
    const agent = agents.find((a) => a.id === params.id);
    if (!agent) {
      return HttpResponse.json({ message: 'Agent not found' }, { status: 404 });
    }
    agent.status = 'inactive';
    return HttpResponse.json(agent);
  }),

  http.post('*/api/v1/agents/:id/execute', ({ params }) => {
    const agent = agents.find((a) => a.id === params.id);
    if (!agent) {
      return HttpResponse.json({ message: 'Agent not found' }, { status: 404 });
    }
    return HttpResponse.json({
      id: `exec-${Date.now()}`,
      agentId: params.id,
      status: 'running',
      input: {},
      startedAt: new Date().toISOString(),
    });
  }),

  http.get('*/api/v1/agents/:id/executions', () => {
    return HttpResponse.json({
      items: [],
      total: 0,
      page: 1,
      pageSize: 20,
      totalPages: 0,
    });
  }),

  http.post('*/api/v1/agents/:id/tools', async ({ params, request }) => {
    const agent = agents.find((a) => a.id === params.id);
    if (!agent) {
      return HttpResponse.json({ message: 'Agent not found' }, { status: 404 });
    }
    const body = await request.json() as { toolIds: string[] };
    agent.tools = body.toolIds;
    return HttpResponse.json(agent);
  }),
];
