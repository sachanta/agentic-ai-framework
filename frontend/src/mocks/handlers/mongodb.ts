import { http, HttpResponse } from 'msw';

interface MongoDBCollection {
  name: string;
  documentCount: number;
  avgDocumentSize: number;
  indexes: Array<{ name: string; keys: Record<string, number> }>;
}

interface MongoDBDocument {
  _id: string;
  [key: string]: unknown;
}

let collections: MongoDBCollection[] = [
  {
    name: 'agents',
    documentCount: 5,
    avgDocumentSize: 1024,
    indexes: [
      { name: '_id_', keys: { _id: 1 } },
      { name: 'name_1', keys: { name: 1 } },
      { name: 'status_1', keys: { status: 1 } },
    ],
  },
  {
    name: 'executions',
    documentCount: 1250,
    avgDocumentSize: 2048,
    indexes: [
      { name: '_id_', keys: { _id: 1 } },
      { name: 'status_1', keys: { status: 1 } },
      { name: 'startedAt_-1', keys: { startedAt: -1 } },
    ],
  },
  {
    name: 'logs',
    documentCount: 50000,
    avgDocumentSize: 512,
    indexes: [
      { name: '_id_', keys: { _id: 1 } },
      { name: 'timestamp_-1', keys: { timestamp: -1 } },
      { name: 'level_1', keys: { level: 1 } },
    ],
  },
  {
    name: 'settings',
    documentCount: 1,
    avgDocumentSize: 4096,
    indexes: [{ name: '_id_', keys: { _id: 1 } }],
  },
];

const mockDocuments: Record<string, MongoDBDocument[]> = {
  agents: [
    {
      _id: 'agent-1',
      name: 'Research Assistant',
      description: 'Conducts research across multiple data sources',
      status: 'active',
      createdAt: new Date('2024-01-15T10:30:00Z'),
    },
    {
      _id: 'agent-2',
      name: 'Code Reviewer',
      description: 'Analyzes code for quality and security',
      status: 'active',
      createdAt: new Date('2024-01-10T08:00:00Z'),
    },
  ],
  executions: [
    {
      _id: 'exec-1',
      workflowId: 'workflow-1',
      status: 'completed',
      startedAt: new Date('2024-01-22T09:15:00Z'),
      completedAt: new Date('2024-01-22T09:18:30Z'),
    },
    {
      _id: 'exec-2',
      workflowId: 'workflow-2',
      status: 'running',
      startedAt: new Date('2024-01-22T10:45:00Z'),
    },
  ],
  logs: [
    {
      _id: 'log-1',
      timestamp: new Date('2024-01-22T10:00:00Z'),
      level: 'info',
      message: 'System started',
      source: 'system',
    },
    {
      _id: 'log-2',
      timestamp: new Date('2024-01-22T10:01:00Z'),
      level: 'info',
      message: 'Agent initialized',
      source: 'agent-1',
    },
  ],
  settings: [
    {
      _id: 'settings-1',
      apiUrl: 'http://localhost:8000',
      weaviateUrl: 'http://localhost:8080',
      mongodbUri: 'mongodb://localhost:27017',
      logLevel: 'info',
    },
  ],
};

export const mongodbHandlers = [
  // List collections
  http.get('*/api/v1/mongodb/collections', () => {
    return HttpResponse.json(collections);
  }),

  // Get collection stats
  http.get('*/api/v1/mongodb/collections/:name', ({ params }) => {
    const collection = collections.find((c) => c.name === params.name);
    if (!collection) {
      return HttpResponse.json({ message: 'Collection not found' }, { status: 404 });
    }
    return HttpResponse.json(collection);
  }),

  // List documents in collection
  http.get('*/api/v1/mongodb/:collection/documents', ({ params, request }) => {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const pageSize = parseInt(url.searchParams.get('pageSize') || '20');

    const docs = mockDocuments[params.collection as string] || [];
    const total = docs.length;
    const start = (page - 1) * pageSize;
    const items = docs.slice(start, start + pageSize);

    return HttpResponse.json({
      items,
      total,
      page,
      pageSize,
      totalPages: Math.ceil(total / pageSize),
    });
  }),

  // Get single document
  http.get('*/api/v1/mongodb/:collection/documents/:id', ({ params }) => {
    const collectionName = params.collection as string;
    const docId = params.id as string;

    const docs = mockDocuments[collectionName];
    if (!docs) {
      return HttpResponse.json({ message: 'Collection not found' }, { status: 404 });
    }

    const doc = docs.find((d) => d._id === docId);
    if (!doc) {
      return HttpResponse.json({ message: 'Document not found' }, { status: 404 });
    }

    return HttpResponse.json(doc);
  }),

  // Create document
  http.post('*/api/v1/mongodb/:collection/documents', async ({ params, request }) => {
    const collectionName = params.collection as string;
    const body = await request.json() as Record<string, unknown>;

    if (!mockDocuments[collectionName]) {
      mockDocuments[collectionName] = [];
    }

    const newDoc: MongoDBDocument = {
      _id: `${collectionName.slice(0, 4)}-${Date.now()}`,
      ...body,
      createdAt: new Date(),
    };

    mockDocuments[collectionName].push(newDoc);

    const collection = collections.find((c) => c.name === collectionName);
    if (collection) {
      collection.documentCount += 1;
    }

    return HttpResponse.json(newDoc, { status: 201 });
  }),

  // Update document
  http.patch('*/api/v1/mongodb/:collection/documents/:id', async ({ params, request }) => {
    const collectionName = params.collection as string;
    const docId = params.id as string;
    const body = await request.json() as Record<string, unknown>;

    const docs = mockDocuments[collectionName];
    if (!docs) {
      return HttpResponse.json({ message: 'Collection not found' }, { status: 404 });
    }

    const index = docs.findIndex((d) => d._id === docId);
    if (index === -1) {
      return HttpResponse.json({ message: 'Document not found' }, { status: 404 });
    }

    docs[index] = { ...docs[index], ...body, updatedAt: new Date() };
    return HttpResponse.json(docs[index]);
  }),

  // Delete document
  http.delete('*/api/v1/mongodb/:collection/documents/:id', ({ params }) => {
    const collectionName = params.collection as string;
    const docId = params.id as string;

    const docs = mockDocuments[collectionName];
    if (!docs) {
      return HttpResponse.json({ message: 'Collection not found' }, { status: 404 });
    }

    const index = docs.findIndex((d) => d._id === docId);
    if (index === -1) {
      return HttpResponse.json({ message: 'Document not found' }, { status: 404 });
    }

    docs.splice(index, 1);

    const collection = collections.find((c) => c.name === collectionName);
    if (collection) {
      collection.documentCount -= 1;
    }

    return HttpResponse.json({ message: 'Document deleted' });
  }),

  // Query documents
  http.post('*/api/v1/mongodb/:collection/query', async ({ params, request }) => {
    const collectionName = params.collection as string;
    const body = await request.json() as {
      filter?: Record<string, unknown>;
      projection?: Record<string, number>;
      sort?: Record<string, number>;
      limit?: number;
      skip?: number;
    };

    const docs = mockDocuments[collectionName] || [];

    // Simple filtering simulation
    let results = [...docs];

    if (body.filter) {
      results = results.filter((doc) => {
        return Object.entries(body.filter || {}).every(([key, value]) => {
          return doc[key] === value;
        });
      });
    }

    const total = results.length;
    const skip = body.skip || 0;
    const limit = body.limit || 100;
    results = results.slice(skip, skip + limit);

    return HttpResponse.json({
      documents: results,
      count: results.length,
      total,
    });
  }),

  // Import documents
  http.post('*/api/v1/mongodb/:collection/import', async ({ params, request }) => {
    const collectionName = params.collection as string;
    const body = await request.json() as { documents: MongoDBDocument[] };

    if (!mockDocuments[collectionName]) {
      mockDocuments[collectionName] = [];
    }

    const imported = body.documents.map((doc, index) => ({
      _id: doc._id || `${collectionName.slice(0, 4)}-${Date.now()}-${index}`,
      ...doc,
    }));

    mockDocuments[collectionName].push(...imported);

    const collection = collections.find((c) => c.name === collectionName);
    if (collection) {
      collection.documentCount += imported.length;
    }

    return HttpResponse.json({
      imported: imported.length,
      failed: 0,
      total: body.documents.length,
    });
  }),

  // Export documents
  http.get('*/api/v1/mongodb/:collection/export', ({ params, request }) => {
    const collectionName = params.collection as string;
    const url = new URL(request.url);
    const format = url.searchParams.get('format') || 'json';

    const docs = mockDocuments[collectionName] || [];

    if (format === 'csv') {
      // Simple CSV conversion
      if (docs.length === 0) {
        return HttpResponse.text('');
      }
      const headers = Object.keys(docs[0]).join(',');
      const rows = docs.map((doc) =>
        Object.values(doc)
          .map((v) => (typeof v === 'object' ? JSON.stringify(v) : String(v)))
          .join(',')
      );
      return HttpResponse.text([headers, ...rows].join('\n'));
    }

    return HttpResponse.json(docs);
  }),
];
