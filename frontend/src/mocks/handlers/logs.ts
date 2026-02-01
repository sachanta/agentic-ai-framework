import { http, HttpResponse } from 'msw';

const mockLogs = Array.from({ length: 100 }, (_, i) => ({
  id: `log-${i}`,
  timestamp: new Date(Date.now() - i * 60000).toISOString(),
  level: ['debug', 'info', 'warn', 'error'][Math.floor(Math.random() * 4)] as 'debug' | 'info' | 'warn' | 'error',
  source: ['api', 'agent', 'workflow', 'tool'][Math.floor(Math.random() * 4)],
  message: `Log message ${i}: ${['Processing request', 'Execution complete', 'Error occurred', 'Starting workflow'][Math.floor(Math.random() * 4)]}`,
  metadata: Math.random() > 0.5 ? { requestId: `req-${i}` } : undefined,
}));

export const logsHandlers = [
  http.get('*/api/v1/logs', ({ request }) => {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const pageSize = parseInt(url.searchParams.get('pageSize') || '50');
    const level = url.searchParams.get('level');
    const source = url.searchParams.get('source');
    const search = url.searchParams.get('search')?.toLowerCase();

    let filteredLogs = mockLogs;

    if (level && level !== 'all') {
      filteredLogs = filteredLogs.filter((l) => l.level === level);
    }
    if (source && source !== 'all') {
      filteredLogs = filteredLogs.filter((l) => l.source === source);
    }
    if (search) {
      filteredLogs = filteredLogs.filter((l) =>
        l.message.toLowerCase().includes(search)
      );
    }

    const total = filteredLogs.length;
    const start = (page - 1) * pageSize;
    const items = filteredLogs.slice(start, start + pageSize);

    return HttpResponse.json({
      items,
      total,
      page,
      pageSize,
      totalPages: Math.ceil(total / pageSize),
    });
  }),

  http.get('*/api/v1/logs/:id', ({ params }) => {
    const log = mockLogs.find((l) => l.id === params.id);
    if (!log) {
      return HttpResponse.json({ message: 'Log not found' }, { status: 404 });
    }
    return HttpResponse.json(log);
  }),

  http.get('*/api/v1/logs/sources', () => {
    return HttpResponse.json(['api', 'agent', 'workflow', 'tool']);
  }),

  http.get('*/api/v1/logs/stats', () => {
    return HttpResponse.json({
      total: mockLogs.length,
      byLevel: {
        debug: mockLogs.filter((l) => l.level === 'debug').length,
        info: mockLogs.filter((l) => l.level === 'info').length,
        warn: mockLogs.filter((l) => l.level === 'warn').length,
        error: mockLogs.filter((l) => l.level === 'error').length,
      },
      bySource: {
        api: mockLogs.filter((l) => l.source === 'api').length,
        agent: mockLogs.filter((l) => l.source === 'agent').length,
        workflow: mockLogs.filter((l) => l.source === 'workflow').length,
        tool: mockLogs.filter((l) => l.source === 'tool').length,
      },
    });
  }),

  http.get('*/api/v1/logs/export', () => {
    const blob = new Blob([JSON.stringify(mockLogs, null, 2)], {
      type: 'application/json',
    });
    return new HttpResponse(blob, {
      headers: { 'Content-Type': 'application/json' },
    });
  }),

  http.delete('*/api/v1/logs', () => {
    return HttpResponse.json({ deleted: mockLogs.length });
  }),
];
