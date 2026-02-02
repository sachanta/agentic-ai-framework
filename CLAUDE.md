# Claude Code Project Instructions

This file contains project-specific patterns, conventions, and gotchas for the agentic-ai-framework.

## Project Structure

```
backend/
├── app/
│   ├── common/          # Shared framework code
│   │   ├── base/        # BaseAgent, BaseChain, BaseOrchestrator
│   │   └── providers/   # LLM, embeddings, vectorstore providers
│   ├── platforms/       # Platform implementations (newsletter, hello_world)
│   └── db/              # Database connections (MongoDB, Weaviate)
└── tests/
```

## Common Patterns

### LLM Provider Types

**Location:** `app/common/providers/llm.py`

```python
class LLMProviderType(str, Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"
    AWS_BEDROCK = "aws_bedrock"  # NOT "BEDROCK"
```

**IMPORTANT:** The Bedrock provider is `AWS_BEDROCK`, not `BEDROCK`. Always check the actual enum values before using.

### Pydantic Models

Use `model_config` dict (Pydantic v2), not deprecated `class Config`:

```python
# Correct (Pydantic v2)
class MyModel(BaseModel):
    name: str

    model_config = {
        "populate_by_name": True,
        "json_encoders": {datetime: lambda v: v.isoformat()},
    }

# Wrong (deprecated)
class MyModel(BaseModel):
    name: str

    class Config:
        populate_by_name = True
```

### DateTime Handling

Use timezone-aware datetimes:

```python
# Correct
from datetime import datetime, timezone
now = datetime.now(timezone.utc)

# Wrong (deprecated)
now = datetime.utcnow()
```

### Agent Implementation Pattern

Follow the hello_world greeter agent structure:

```
agents/{agent_name}/
├── __init__.py      # Exports
├── agent.py         # Agent class extending BaseAgent
├── llm.py           # get_{agent}_llm(), get_{agent}_config()
├── prompts.py       # Prompt templates
└── tools.py         # Optional tool definitions
```

### Test Patterns

1. **Floating point comparisons** - Use `>=` or `pytest.approx()`:
   ```python
   # Good
   assert score >= 0.4
   assert score == pytest.approx(0.5, rel=0.1)

   # Bad - too strict
   assert score > 0.5
   ```

2. **Run tests from backend directory:**
   ```bash
   cd backend
   .venv/bin/python -m pytest app/platforms/newsletter/tests/ -v
   ```

3. **Mark integration tests:**
   ```python
   @pytest.mark.integration
   class TestIntegration:
       ...
   ```

## Newsletter Platform

### Phase Status
- Phase 1: Platform Scaffolding ✅
- Phase 2: MongoDB Models & Repositories ✅
- Phase 3: Tavily Search Service ✅
- Phase 4: RAG System (Weaviate) ✅
- Phase 5: Memory Service (MongoDB TTL) ✅
- Phase 6: Research Agent ✅
- Phase 7-15: Pending

### Key Services

| Service | Location | Purpose |
|---------|----------|---------|
| TavilySearchService | `services/tavily.py` | Web search via Tavily API |
| NewsletterRAGService | `services/rag.py` | Vector storage in Weaviate |
| MemoryService | `services/memory.py` | MongoDB cache with TTL |
| ResearchAgent | `agents/research/` | Content discovery pipeline |

### Config Pattern

Newsletter config uses prefix `NEWSLETTER_` with fallback to global settings:

```python
from app.platforms.newsletter.config import config

# These fall back to global if not set
config.effective_provider  # NEWSLETTER_LLM_PROVIDER or LLM_PROVIDER
config.effective_model     # NEWSLETTER_LLM_MODEL or LLM_DEFAULT_MODEL
```

## Environment Variables

### Required for Newsletter
```bash
NEWSLETTER_TAVILY_API_KEY=xxx     # Tavily search API
NEWSLETTER_RESEND_API_KEY=xxx     # Email sending (Phase 11)
```

### Optional Overrides
```bash
NEWSLETTER_LLM_PROVIDER=ollama    # Override global LLM provider
NEWSLETTER_LLM_MODEL=llama3       # Override global model
```

## Common Gotchas

1. **LLMProviderType.BEDROCK** → Use `AWS_BEDROCK` instead
2. **datetime.utcnow()** → Use `datetime.now(timezone.utc)`
3. **class Config** in Pydantic → Use `model_config = {...}`
4. **Strict float assertions** → Use `>=` or `pytest.approx()`
5. **Python command** → Use `.venv/bin/python` from backend directory
