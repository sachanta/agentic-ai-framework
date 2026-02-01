import { http, HttpResponse } from 'msw';
import { mockHealth } from '../data/health';

export const healthHandlers = [
  http.get('*/api/v1/health', () => {
    return HttpResponse.json(mockHealth);
  }),

  http.get('*/api/v1/health/weaviate', () => {
    return HttpResponse.json(mockHealth.databases.weaviate);
  }),

  http.get('*/api/v1/health/mongodb', () => {
    return HttpResponse.json(mockHealth.databases.mongodb);
  }),

  http.get('*/api/v1/health/memory', () => {
    return HttpResponse.json(mockHealth.memory);
  }),

  http.get('*/api/v1/health/queue', () => {
    return HttpResponse.json(mockHealth.queue);
  }),

  http.get('*/api/v1/health/history', () => {
    const history = [];
    const now = Date.now();
    for (let i = 0; i < 24; i++) {
      history.push({
        timestamp: new Date(now - i * 3600000).toISOString(),
        memory: 60 + Math.random() * 20,
        queueDepth: Math.floor(Math.random() * 20),
        activeAgents: Math.floor(Math.random() * 5),
        runningWorkflows: Math.floor(Math.random() * 3),
      });
    }
    return HttpResponse.json(history);
  }),

  http.get('*/api/v1/health/ping', () => {
    return HttpResponse.json({ status: 'ok' });
  }),
];
