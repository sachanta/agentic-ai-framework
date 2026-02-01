import { http, HttpResponse } from 'msw';

interface WeaviateCollection {
  name: string;
  vectorizer: string;
  properties: Array<{ name: string; dataType: string[] }>;
  objectCount: number;
}

interface WeaviateDocument {
  id: string;
  class: string;
  properties: Record<string, unknown>;
  vector?: number[];
  createdAt: string;
}

let collections: WeaviateCollection[] = [
  {
    name: 'Documents',
    vectorizer: 'text2vec-openai',
    properties: [
      { name: 'title', dataType: ['text'] },
      { name: 'content', dataType: ['text'] },
      { name: 'source', dataType: ['text'] },
      { name: 'createdAt', dataType: ['date'] },
    ],
    objectCount: 1523,
  },
  {
    name: 'KnowledgeBase',
    vectorizer: 'text2vec-openai',
    properties: [
      { name: 'question', dataType: ['text'] },
      { name: 'answer', dataType: ['text'] },
      { name: 'category', dataType: ['text'] },
    ],
    objectCount: 456,
  },
  {
    name: 'Embeddings',
    vectorizer: 'text2vec-transformers',
    properties: [
      { name: 'text', dataType: ['text'] },
      { name: 'metadata', dataType: ['object'] },
    ],
    objectCount: 8921,
  },
];

const mockDocuments: Record<string, WeaviateDocument[]> = {
  Documents: [
    {
      id: 'doc-1',
      class: 'Documents',
      properties: {
        title: 'Introduction to AI Agents',
        content: 'AI agents are autonomous systems that can perceive their environment...',
        source: 'internal-wiki',
        createdAt: '2024-01-15T10:30:00Z',
      },
      createdAt: '2024-01-15T10:30:00Z',
    },
    {
      id: 'doc-2',
      class: 'Documents',
      properties: {
        title: 'Building Scalable Workflows',
        content: 'Workflow orchestration is essential for managing complex AI pipelines...',
        source: 'documentation',
        createdAt: '2024-01-16T14:20:00Z',
      },
      createdAt: '2024-01-16T14:20:00Z',
    },
    {
      id: 'doc-3',
      class: 'Documents',
      properties: {
        title: 'Vector Database Best Practices',
        content: 'When working with vector databases, consider the following best practices...',
        source: 'blog',
        createdAt: '2024-01-18T09:00:00Z',
      },
      createdAt: '2024-01-18T09:00:00Z',
    },
  ],
  KnowledgeBase: [
    {
      id: 'kb-1',
      class: 'KnowledgeBase',
      properties: {
        question: 'What is an AI agent?',
        answer: 'An AI agent is an autonomous system capable of perceiving and acting on its environment.',
        category: 'concepts',
      },
      createdAt: '2024-01-10T08:00:00Z',
    },
    {
      id: 'kb-2',
      class: 'KnowledgeBase',
      properties: {
        question: 'How do workflows work?',
        answer: 'Workflows orchestrate multiple steps and agents to accomplish complex tasks.',
        category: 'workflows',
      },
      createdAt: '2024-01-12T11:30:00Z',
    },
  ],
};

export const weaviateHandlers = [
  // List collections
  http.get('*/api/v1/weaviate/collections', () => {
    return HttpResponse.json(collections);
  }),

  // Get collection details
  http.get('*/api/v1/weaviate/collections/:name', ({ params }) => {
    const collection = collections.find((c) => c.name === params.name);
    if (!collection) {
      return HttpResponse.json({ message: 'Collection not found' }, { status: 404 });
    }
    return HttpResponse.json(collection);
  }),

  // Create collection
  http.post('*/api/v1/weaviate/collections', async ({ request }) => {
    const body = await request.json() as { name: string; vectorizer: string; properties: Array<{ name: string; dataType: string[] }> };
    const newCollection: WeaviateCollection = {
      name: body.name,
      vectorizer: body.vectorizer || 'text2vec-openai',
      properties: body.properties || [],
      objectCount: 0,
    };
    collections.push(newCollection);
    mockDocuments[body.name] = [];
    return HttpResponse.json(newCollection, { status: 201 });
  }),

  // Delete collection
  http.delete('*/api/v1/weaviate/collections/:name', ({ params }) => {
    const index = collections.findIndex((c) => c.name === params.name);
    if (index === -1) {
      return HttpResponse.json({ message: 'Collection not found' }, { status: 404 });
    }
    collections.splice(index, 1);
    delete mockDocuments[params.name as string];
    return HttpResponse.json({ message: 'Collection deleted' });
  }),

  // List documents in collection
  http.get('*/api/v1/weaviate/collections/:name/documents', ({ params, request }) => {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const pageSize = parseInt(url.searchParams.get('pageSize') || '20');

    const docs = mockDocuments[params.name as string] || [];
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

  // Add document to collection
  http.post('*/api/v1/weaviate/collections/:name/documents', async ({ params, request }) => {
    const body = await request.json() as { properties: Record<string, unknown> };
    const collectionName = params.name as string;

    if (!mockDocuments[collectionName]) {
      return HttpResponse.json({ message: 'Collection not found' }, { status: 404 });
    }

    const newDoc: WeaviateDocument = {
      id: `doc-${Date.now()}`,
      class: collectionName,
      properties: body.properties,
      createdAt: new Date().toISOString(),
    };

    mockDocuments[collectionName].push(newDoc);

    const collection = collections.find((c) => c.name === collectionName);
    if (collection) {
      collection.objectCount += 1;
    }

    return HttpResponse.json(newDoc, { status: 201 });
  }),

  // Delete document
  http.delete('*/api/v1/weaviate/collections/:name/documents/:id', ({ params }) => {
    const collectionName = params.name as string;
    const docId = params.id as string;

    const docs = mockDocuments[collectionName];
    if (!docs) {
      return HttpResponse.json({ message: 'Collection not found' }, { status: 404 });
    }

    const index = docs.findIndex((d) => d.id === docId);
    if (index === -1) {
      return HttpResponse.json({ message: 'Document not found' }, { status: 404 });
    }

    docs.splice(index, 1);

    const collection = collections.find((c) => c.name === collectionName);
    if (collection) {
      collection.objectCount -= 1;
    }

    return HttpResponse.json({ message: 'Document deleted' });
  }),

  // Vector search
  http.post('*/api/v1/weaviate/search', async ({ request }) => {
    const body = await request.json() as { query: string; collection: string; limit?: number };
    const docs = mockDocuments[body.collection] || [];
    const limit = body.limit || 10;

    // Simulate search by returning random documents with mock scores
    const results = docs.slice(0, limit).map((doc, index) => ({
      ...doc,
      score: 0.95 - index * 0.05,
      distance: 0.05 + index * 0.05,
    }));

    return HttpResponse.json({
      results,
      query: body.query,
      collection: body.collection,
    });
  }),

  // Bulk import
  http.post('*/api/v1/weaviate/collections/:name/import', async ({ params, request }) => {
    const collectionName = params.name as string;
    const body = await request.json() as { documents: Array<{ properties: Record<string, unknown> }> };

    if (!mockDocuments[collectionName]) {
      mockDocuments[collectionName] = [];
    }

    const imported = body.documents.map((doc, index) => ({
      id: `doc-${Date.now()}-${index}`,
      class: collectionName,
      properties: doc.properties,
      createdAt: new Date().toISOString(),
    }));

    mockDocuments[collectionName].push(...imported);

    const collection = collections.find((c) => c.name === collectionName);
    if (collection) {
      collection.objectCount += imported.length;
    }

    return HttpResponse.json({
      imported: imported.length,
      failed: 0,
      total: body.documents.length,
    });
  }),
];
