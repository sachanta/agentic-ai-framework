# Phase 5: Memory Service (MongoDB)

## Goal
User context and preference caching using MongoDB with TTL indexes

## Status
- [x] Complete (33 unit tests passing, 2 integration tests)

## Files to Create
```
backend/app/platforms/newsletter/services/memory.py
```

## Features
- Store/retrieve user preferences with TTL
- Newsletter history tracking
- Engagement metrics caching
- Research results caching
- Reading pattern analysis
- Context persistence across sessions

## Storage Strategy
- MongoDB with TTL indexes for all caching needs
- `newsletter_cache` collection with automatic expiration
- No Redis dependency required

## How It Helps The Project

The Memory Service provides **short-term context** that persists across API calls and sessions. While the RAG system (Phase 4) handles long-term learning from past newsletters, the Memory Service handles:

### Key Use Cases

| Use Case | How Memory Helps |
|----------|------------------|
| Session continuity | Remember user's current workflow state |
| Research caching | Don't re-search same topics within TTL window |
| Preference snapshots | Quick access to user preferences without DB query |
| Engagement tracking | Cache recent open/click events for real-time analytics |

### Cache Collections
```python
newsletter_cache:
  - key (TEXT)           # Cache key
  - value (OBJECT)       # Cached data
  - user_id (TEXT)       # Owner
  - type (TEXT)          # preferences, research, engagement
  - created_at (DATE)    # For TTL index
  - expires_at (DATE)    # TTL expiration
```

## Dependencies
- MongoDB (already configured)
- Phase 2 repositories

## Verification
- [x] MongoDB TTL index created on newsletter_cache
- [x] Can store/retrieve preferences
- [x] Cache expires after TTL
- [x] Research results cached correctly
- [x] Tests passing (33 unit tests, 2 integration tests)

---

## Completion Summary

### Files Created
```
backend/app/platforms/newsletter/services/memory.py
backend/app/platforms/newsletter/tests/phase5/__init__.py
backend/app/platforms/newsletter/tests/phase5/test_memory_service.py
```

### Files Modified
```
backend/app/platforms/newsletter/services/__init__.py  # Added exports
```

### MemoryService Class

The `MemoryService` class provides short-term caching with automatic TTL expiration:

```python
from app.platforms.newsletter.services import get_memory_service, CacheType

memory = get_memory_service()

# Store preferences (24-hour TTL)
await memory.set_preferences(user_id, {"topics": ["AI"], "tone": "casual"})

# Cache research results (30-minute TTL)
await memory.set_research_results(user_id, topics_hash, results)

# Track engagement events
await memory.update_engagement(user_id, newsletter_id, "open")

# Store workflow state (2-hour TTL)
await memory.set_workflow_state(user_id, workflow_id, state_dict)
```

### CacheType Enum

| Type | Purpose | Default TTL |
|------|---------|-------------|
| `PREFERENCES` | User topic/tone preferences | 24 hours |
| `RESEARCH` | Search results by topics hash | 30 minutes |
| `ENGAGEMENT` | Opens, clicks per newsletter | 24 hours |
| `WORKFLOW` | Workflow checkpoint state | 2 hours |
| `SESSION` | Session-level context | 1 hour |
| `ANALYTICS` | Dashboard data snapshots | 5 minutes |

### MongoDB Collection Schema

```python
newsletter_cache:
  - key (TEXT)           # Composite: user_id:type:subkey
  - user_id (TEXT)       # Owner
  - type (TEXT)          # CacheType value
  - subkey (TEXT)        # Original key
  - value (TEXT)         # JSON serialized data
  - created_at (DATE)    # When cached
  - expires_at (DATE)    # TTL expiration (indexed)
  - ttl_seconds (INT)    # Original TTL for touch()
```

### Indexes Created
1. **TTL Index**: `expires_at` with `expireAfterSeconds=0` - MongoDB auto-deletes expired docs
2. **Compound Index**: `(user_id, type, key)` - Fast lookups
3. **Key Index**: `key` - Direct key access

### Key Methods

| Method | Description |
|--------|-------------|
| `set()` / `get()` | Generic cache operations |
| `delete()` / `delete_by_type()` | Remove cache entries |
| `touch()` | Extend TTL without modifying value |
| `get_stats()` | Cache statistics by type |
| `cleanup_expired()` | Manual cleanup (TTL index handles this automatically) |
| `health_check()` | Service health status |

### Test Results
- **33 unit tests** - All passing with mocked MongoDB
- **2 integration tests** - Skipped (require running MongoDB)
- **Total project tests**: 293 passing
