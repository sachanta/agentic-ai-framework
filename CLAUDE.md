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
6. **LLM Provider kwargs** → Check provider `__init__` signature before passing args
7. **BaseAgent reserved attributes** → Don't overwrite `self.memory`, `self.llm`, `self.name`

### BaseAgent Reserved Attributes

When extending `BaseAgent`, these attributes are used internally and should NOT be overwritten:

```python
class BaseAgent:
    self.name        # Agent name
    self.llm         # LLM provider instance
    self.memory      # AgentMemory for conversation history (NOT for caching!)
    self.system_prompt
    self.tools
```

**Common mistake:** Using `self.memory` for a caching service:

```python
# WRONG - overwrites BaseAgent's conversation memory
class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(...)
        self.memory = get_cache_service()  # Breaks BaseAgent!

# CORRECT - use a different attribute name
class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(...)
        self.cache_service = get_cache_service()  # Safe
```

### LLM Provider Initialization

Each provider has different `__init__` parameters:

```python
# OllamaProvider accepts:
OllamaProvider(base_url=..., default_model=..., timeout=...)

# OpenAIProvider accepts:
OpenAIProvider(api_key=..., default_model=..., timeout=...)

# AWSBedrockProvider accepts:
AWSBedrockProvider(region=..., default_model=..., timeout=...)
```

**IMPORTANT:** Use `default_model`, NOT `model`:

```python
# Correct
get_llm_provider(provider_type=LLMProviderType.OLLAMA, default_model="llama3")

# Wrong - causes "unexpected keyword argument 'model'"
get_llm_provider(provider_type=LLMProviderType.OLLAMA, model="llama3")
```

## Test Coverage Guidelines

### Mock at the Right Level

When testing API endpoints that use agents, consider what level to mock:

1. **Mocking the entire agent class** (fast, but misses initialization bugs):
   ```python
   # This skips agent.__init__(), so LLM init bugs won't be caught
   with patch("...routers.research.ResearchAgent") as MockAgent:
       mock_agent = MagicMock()
       mock_agent.run = AsyncMock(return_value=result)
       MockAgent.return_value = mock_agent
   ```

2. **Mocking agent dependencies** (slower, but catches init bugs):
   ```python
   # This runs agent.__init__(), catching LLM/service init issues
   with patch("...agents.research.agent.get_tavily_service") as mock_tavily, \
        patch("...agents.research.agent.get_memory_service") as mock_memory, \
        patch("...agents.research.llm.get_llm_provider") as mock_llm:
       # Agent init runs, dependencies are mocked
   ```

### Test Initialization Separately

Always add unit tests for factory functions like `get_*_llm()`:

```python
def test_get_research_llm_initializes():
    """Ensure LLM provider can be initialized without errors."""
    with patch("...get_llm_provider") as mock_provider:
        mock_provider.return_value = MagicMock()
        llm = get_research_llm()
        # Verify correct kwargs were passed
        mock_provider.assert_called_once()
        call_kwargs = mock_provider.call_args.kwargs
        assert "default_model" in call_kwargs or "provider_type" in call_kwargs
```

### Integration Test Checklist

Before marking a phase complete, ensure:
- [ ] Unit tests pass with mocked dependencies
- [ ] Factory functions (`get_*_llm`, `get_*_service`) are tested
- [ ] At least one integration test exists (can be skipped if requires external API)
- [ ] Manual smoke test with real services works
