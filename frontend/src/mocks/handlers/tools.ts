import { http, HttpResponse } from 'msw';
import { mockTools } from '../data/tools';

let tools = [...mockTools];

export const toolsHandlers = [
  http.get('*/api/v1/tools', ({ request }) => {
    const url = new URL(request.url);
    const search = url.searchParams.get('search')?.toLowerCase();
    const page = parseInt(url.searchParams.get('page') || '1');
    const pageSize = parseInt(url.searchParams.get('pageSize') || '20');

    let filteredTools = tools;
    if (search) {
      filteredTools = tools.filter(
        (t) =>
          t.name.toLowerCase().includes(search) ||
          t.description.toLowerCase().includes(search)
      );
    }

    const total = filteredTools.length;
    const start = (page - 1) * pageSize;
    const items = filteredTools.slice(start, start + pageSize);

    return HttpResponse.json({
      items,
      total,
      page,
      pageSize,
      totalPages: Math.ceil(total / pageSize),
    });
  }),

  http.get('*/api/v1/tools/:id', ({ params }) => {
    const tool = tools.find((t) => t.id === params.id);
    if (!tool) {
      return HttpResponse.json({ message: 'Tool not found' }, { status: 404 });
    }
    return HttpResponse.json(tool);
  }),

  http.post('*/api/v1/tools', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    const newTool = {
      id: `tool-${Date.now()}`,
      ...body,
      enabled: body.enabled ?? true,
      version: '1.0.0',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      usageCount: 0,
    };
    tools.push(newTool as typeof mockTools[0]);
    return HttpResponse.json(newTool, { status: 201 });
  }),

  http.patch('*/api/v1/tools/:id', async ({ params, request }) => {
    const index = tools.findIndex((t) => t.id === params.id);
    if (index === -1) {
      return HttpResponse.json({ message: 'Tool not found' }, { status: 404 });
    }
    const body = await request.json() as Record<string, unknown>;
    tools[index] = { ...tools[index], ...body, updatedAt: new Date().toISOString() };
    return HttpResponse.json(tools[index]);
  }),

  http.delete('*/api/v1/tools/:id', ({ params }) => {
    const index = tools.findIndex((t) => t.id === params.id);
    if (index === -1) {
      return HttpResponse.json({ message: 'Tool not found' }, { status: 404 });
    }
    tools.splice(index, 1);
    return HttpResponse.json({ message: 'Tool deleted' });
  }),

  http.post('*/api/v1/tools/:id/enable', ({ params }) => {
    const tool = tools.find((t) => t.id === params.id);
    if (!tool) {
      return HttpResponse.json({ message: 'Tool not found' }, { status: 404 });
    }
    tool.enabled = true;
    return HttpResponse.json(tool);
  }),

  http.post('*/api/v1/tools/:id/disable', ({ params }) => {
    const tool = tools.find((t) => t.id === params.id);
    if (!tool) {
      return HttpResponse.json({ message: 'Tool not found' }, { status: 404 });
    }
    tool.enabled = false;
    return HttpResponse.json(tool);
  }),

  http.post('*/api/v1/tools/:id/test', () => {
    return HttpResponse.json({
      success: true,
      result: { message: 'Tool executed successfully' },
      executionTime: Math.floor(Math.random() * 1000) + 100,
    });
  }),

  http.get('*/api/v1/tools/:id/schema', ({ params }) => {
    const tool = tools.find((t) => t.id === params.id);
    if (!tool) {
      return HttpResponse.json({ message: 'Tool not found' }, { status: 404 });
    }
    return HttpResponse.json(tool.schema);
  }),
];
