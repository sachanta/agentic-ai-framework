# Phase 4: RAG System with Weaviate

## Goal
Vector storage for newsletter personalization

## Status
- [x] Complete (34 unit tests passing, 2 integration tests)

## Files to Create
```
backend/app/platforms/newsletter/services/rag.py
```

## Features
- Create NewsletterRAG Weaviate collection
- Embed and store newsletters for similarity search
- User-scoped vector filtering
- Content recommendation based on history
- Preference pattern analysis
- Personalization insight generation

## Collection Schema
```python
NewsletterRAG:
  - content (TEXT)        # Newsletter content for embedding
  - user_id (TEXT)        # Owner of the newsletter
  - newsletter_id (TEXT)  # Reference to MongoDB document
  - topics (TEXT[])       # Topics covered
  - tone (TEXT)           # Writing tone used
  - engagement_score (NUMBER)  # How well it performed
  - created_at (DATE)     # When it was created
```

## How It Helps The Project

Phase 4 enables **personalization and learning** from past newsletters. Without it, every newsletter generation starts from scratch with no memory of what worked before.

### The Flow
1. User generates newsletters over time
2. RAG service stores each newsletter as vectors in Weaviate
3. When generating a new newsletter, RAG finds similar past newsletters that performed well
4. This informs the Writing Agent about:
   - What topics resonated with this user's audience
   - What tone/style got good engagement
   - What content to avoid repeating

### Key Use Cases

| Use Case | How RAG Helps |
|----------|---------------|
| "More like this" | Find newsletters similar to a high-performing one |
| Avoid repetition | Detect if new content is too similar to recent newsletters |
| Personalized recommendations | Suggest topics based on engagement patterns |
| Writing style learning | Find examples of tone/style that worked |

## Dependencies
- Weaviate client (already in pyproject.toml)
- Phase 2 models (Newsletter)

## Verification
- [x] Weaviate NewsletterRAG collection created
- [x] Can store newsletter embeddings
- [x] Can search by similarity
- [x] User-scoped filtering works
- [x] Tests passing (34 unit tests, 2 integration tests)

---

## Completion Summary

### Files Created
```
backend/app/platforms/newsletter/services/rag.py
backend/app/platforms/newsletter/tests/phase4/__init__.py
backend/app/platforms/newsletter/tests/phase4/test_rag_service.py
```

### Files Modified
```
backend/app/platforms/newsletter/services/__init__.py  # Added exports
```

### NewsletterRAGService Class

The `NewsletterRAGService` class provides vector storage for newsletter personalization:

```python
from app.platforms.newsletter.services import get_rag_service

rag = get_rag_service()

# Store a newsletter with embeddings
doc_uuid = await rag.store_newsletter(
    user_id="user123",
    newsletter_id="nl123",
    content="Newsletter content...",
    title="AI Newsletter",
    topics=["AI", "technology"],
    tone="professional",
    engagement_score=0.85,
)

# Search for similar content
results = await rag.search_similar(
    query="artificial intelligence trends",
    user_id="user123",
    limit=5,
)

# Get recommendations based on history
recommendations = await rag.get_recommendations(
    user_id="user123",
    limit=5,
)

# Analyze user patterns
patterns = await rag.get_user_patterns("user123")
```

### Weaviate Collection Schema

```python
NewsletterRAG:
  - content (TEXT)           # Newsletter content for embedding
  - user_id (TEXT)           # Owner of the newsletter
  - newsletter_id (TEXT)     # Reference to MongoDB document
  - title (TEXT)             # Newsletter title
  - topics (TEXT[])          # Topics covered
  - tone (TEXT)              # Writing tone used
  - engagement_score (NUMBER) # Performance metric (0-1)
  - metadata_json (TEXT)     # Additional metadata as JSON
  - created_at (DATE)        # When it was created
```

### Key Methods

| Method | Description |
|--------|-------------|
| `store_newsletter()` | Embed and store newsletter in Weaviate |
| `search_similar()` | Find similar content by query text |
| `get_recommendations()` | Content suggestions based on history or specific newsletter |
| `get_user_patterns()` | Analyze topic/tone preferences from history |
| `update_engagement()` | Update engagement score for a newsletter |
| `delete_newsletter()` | Remove newsletter from vector store |
| `delete_user_data()` | Remove all user's newsletters |
| `health_check()` | Service health status |

### Embeddings Integration

Uses the framework's `OllamaEmbeddings` provider (default model: `nomic-embed-text`, 768 dimensions):

```python
from app.common.providers.embeddings import get_embeddings_provider, EmbeddingsProviderType

embeddings = get_embeddings_provider(EmbeddingsProviderType.OLLAMA)
vector = await embeddings.embed_text("Newsletter content...")
```

### Test Results
- **34 unit tests** - All passing with mocked Weaviate/embeddings
- **2 integration tests** - Skipped (require running Weaviate + Ollama)
- **Total project tests at Phase 4**: 260 passing
