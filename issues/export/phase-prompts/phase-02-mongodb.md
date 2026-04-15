# Phase 2: MongoDB Connection & Models

## Goal
Implement the database connection layer with async MongoDB support and base data models.

---

## Copilot Prompt

```
You are helping implement MongoDB connectivity for a FastAPI backend using the async motor driver.

### Context
- This is a multi-agent AI framework that needs persistent storage
- We use async/await throughout (motor driver, not pymongo directly)
- Connection should be pooled and reusable
- Must handle connection failures gracefully

### Files to Read First
Read these files to understand existing patterns:
- backend/app/config.py (database configuration)
- backend/app/db/ (existing database code, if any)

### Implementation Tasks

1. **Create `backend/app/db/mongodb.py`:**
   ```python
   from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
   from typing import Optional

   class MongoDB:
       client: Optional[AsyncIOMotorClient] = None
       db: Optional[AsyncIOMotorDatabase] = None

       async def connect(self, uri: str, database: str) -> None:
           """Establish connection to MongoDB."""
           # Implementation

       async def disconnect(self) -> None:
           """Close MongoDB connection."""
           # Implementation

       async def health_check(self) -> bool:
           """Check if MongoDB is accessible."""
           # Implementation

       def get_collection(self, name: str):
           """Get a collection by name."""
           # Implementation
   ```
   - Implement connection pooling (maxPoolSize, minPoolSize)
   - Add retry logic for initial connection
   - Log connection status

2. **Create `backend/app/db/base_model.py`:**
   ```python
   from pydantic import BaseModel, Field
   from datetime import datetime, timezone
   from typing import Optional
   from bson import ObjectId

   class PyObjectId(ObjectId):
       """Custom ObjectId type for Pydantic."""
       # Implementation for JSON serialization

   class BaseDocument(BaseModel):
       id: Optional[PyObjectId] = Field(default=None, alias="_id")
       created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
       updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

       model_config = {
           "populate_by_name": True,
           "arbitrary_types_allowed": True,
           "json_encoders": {
               ObjectId: str,
               datetime: lambda v: v.isoformat(),
           },
       }
   ```
   - Use `datetime.now(timezone.utc)` NOT `datetime.utcnow()`
   - Handle ObjectId serialization for JSON responses

3. **Create `backend/app/db/repository.py`:**
   ```python
   from typing import TypeVar, Generic, Optional, List

   T = TypeVar("T", bound=BaseDocument)

   class BaseRepository(Generic[T]):
       def __init__(self, collection_name: str, model_class: type[T]):
           self.collection_name = collection_name
           self.model_class = model_class

       async def create(self, document: T) -> T:
           """Insert a new document."""

       async def get_by_id(self, id: str) -> Optional[T]:
           """Retrieve document by ID."""

       async def update(self, id: str, update_data: dict) -> Optional[T]:
           """Update document by ID."""

       async def delete(self, id: str) -> bool:
           """Delete document by ID."""

       async def find(self, filter: dict, skip: int = 0, limit: int = 100) -> List[T]:
           """Find documents matching filter."""
   ```

4. **Create startup/shutdown hooks in `backend/app/main.py`:**
   ```python
   @app.on_event("startup")
   async def startup_db():
       await mongodb.connect(settings.MONGODB_URI, settings.MONGODB_DATABASE)

   @app.on_event("shutdown")
   async def shutdown_db():
       await mongodb.disconnect()
   ```

5. **Create indexes on startup:**
   - Add `create_indexes()` method to MongoDB class
   - Create indexes for common query patterns

6. **Write unit tests in `backend/app/tests/test_mongodb.py`:**
   - Mock AsyncIOMotorClient for unit tests
   - Test connection success/failure scenarios
   - Test CRUD operations on BaseRepository
   - Test health check returns correct status
   - Use `pytest-asyncio` for async tests

### Expected Code Style
- All database operations must be async
- Use type hints throughout
- Handle exceptions and log errors
- Follow Pydantic v2 patterns

### Output
After implementing, provide:
1. Summary of files changed
2. Test command: `cd backend && .venv/bin/python -m pytest app/tests/test_mongodb.py -v`
3. Any database schema decisions made
```

---

## Plan Template

Before making changes, Copilot should propose:

1. **Files to modify/create:**
   - [ ] `backend/app/db/__init__.py`
   - [ ] `backend/app/db/mongodb.py`
   - [ ] `backend/app/db/base_model.py`
   - [ ] `backend/app/db/repository.py`
   - [ ] `backend/app/tests/test_mongodb.py`
   - [ ] `backend/app/main.py` (add startup/shutdown hooks)

2. **High-level steps:**
   - Step 1: ...
   - Step 2: ...

---

## Documentation Template

After changes are complete, provide text for `docs/implementation-log.md`:

```markdown
## Phase 2: MongoDB Connection & Models

### Summary of Changes
- `backend/app/db/mongodb.py`: [description]
- `backend/app/db/base_model.py`: [description]
- `backend/app/db/repository.py`: [description]

### Tests Executed
```bash
cd backend && .venv/bin/python -m pytest app/tests/test_mongodb.py -v
```
**Results:** [PASS/FAIL with details]

### Fixes Applied
- [Any issues encountered and how they were resolved]

### Database Schema
- Collections created: [list]
- Indexes created: [list]
```

---

## Earlier Mocks to Upgrade
- None (this is Phase 2)

**Note:** MongoDB client is mocked in unit tests. In Phase 18, these mocks will be replaced with test containers for integration testing.

---

## Human Checklist
- [ ] Review Copilot's proposed plan before accepting
- [ ] Verify MongoDB is running locally for manual testing
- [ ] Run tests and confirm they pass
- [ ] Test connection error handling manually
