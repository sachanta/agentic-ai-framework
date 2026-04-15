# GitHub Copilot Instructions

> **Setup:** Copy this file to `.github/copilot-instructions.md` in your repository root. Copilot will automatically read these instructions when generating code.

---

## Project Overview

This is the **Agentic AI Framework** - a full-stack application for building multi-agent AI systems.

- **Backend:** Python 3.11+ / FastAPI / async
- **Frontend:** React 18 / TypeScript / Vite / Tailwind CSS
- **Database:** MongoDB (motor async driver) + Weaviate (vector store)
- **LLM Providers:** Ollama (default), OpenAI, AWS Bedrock

Focus on the **hello_world** platform as the reference implementation.

---

## Code Style Requirements

### Python (Backend)

**Always use Pydantic v2 syntax:**
```python
# CORRECT
class MyModel(BaseModel):
    name: str
    model_config = {"populate_by_name": True}

# WRONG - deprecated
class MyModel(BaseModel):
    class Config:
        populate_by_name = True
```

**Always use timezone-aware datetime:**
```python
# CORRECT
from datetime import datetime, timezone
now = datetime.now(timezone.utc)

# WRONG - deprecated
now = datetime.utcnow()
```

**LLM Provider enum values:**
```python
# CORRECT
LLMProviderType.AWS_BEDROCK

# WRONG
LLMProviderType.BEDROCK
```

**LLM Provider parameters:**
```python
# CORRECT
get_llm_provider(provider_type=LLMProviderType.OLLAMA, default_model="llama3")

# WRONG
get_llm_provider(provider_type=LLMProviderType.OLLAMA, model="llama3")
```

**BaseAgent reserved attributes - do NOT override:**
- `self.name`
- `self.llm`
- `self.memory`

```python
# CORRECT
class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(...)
        self.cache_service = get_cache()  # Different name

# WRONG
class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(...)
        self.memory = get_cache()  # Overrides BaseAgent.memory!
```

**Async everywhere:**
- All database operations must be async
- All LLM calls must be async
- All agent methods must be async

**Type hints required:**
```python
async def generate_greeting(name: str, style: str = "friendly") -> dict[str, Any]:
    ...
```

### TypeScript (Frontend)

**Use functional components with hooks:**
```typescript
export function MyComponent({ name }: { name: string }) {
  const [value, setValue] = useState('')
  return <div>{name}: {value}</div>
}
```

**Use Zustand for state management:**
```typescript
export const useMyStore = create<MyState>()(
  persist(
    (set) => ({
      value: null,
      setValue: (v) => set({ value: v }),
    }),
    { name: 'my-storage' }
  )
)
```

**Use React Query for data fetching:**
```typescript
export function useMyData() {
  return useQuery({
    queryKey: ['my-data'],
    queryFn: api.getData,
  })
}

export function useMyMutation() {
  return useMutation({
    mutationFn: api.postData,
  })
}
```

**Use Tailwind CSS for styling** - no inline styles or CSS modules.

---

## Project Structure

### Backend
```
backend/app/
├── common/base/          # BaseAgent, BaseChain, BaseOrchestrator
├── common/providers/     # LLM providers (llm.py)
├── platforms/hello_world/
│   ├── agents/greeter/   # GreeterAgent implementation
│   ├── services/         # HelloWorldService
│   ├── orchestrator/     # HelloWorldOrchestrator
│   ├── router.py         # FastAPI routes
│   ├── schemas/          # Pydantic request/response models
│   └── config.py         # Platform-specific config
├── db/                   # MongoDB, Weaviate connections
└── config.py             # Global settings
```

### Frontend
```
frontend/src/
├── api/                  # API clients (axios + types)
├── components/           # React components
├── hooks/                # Custom hooks (React Query wrappers)
├── pages/                # Route page components
├── store/                # Zustand stores
└── types/                # TypeScript interfaces
```

---

## Testing Patterns

**Run tests from backend directory:**
```bash
cd backend
.venv/bin/python -m pytest app/platforms/hello_world/tests/ -v
```

**Use pytest.approx for float comparisons:**
```python
# CORRECT
assert score >= 0.4
assert score == pytest.approx(0.5, rel=0.1)

# WRONG - too strict
assert score == 0.5
assert score > 0.5
```

**Mock at the right level:**
```python
# Mock the provider/service, not the entire class
with patch("app.platforms.hello_world.agents.greeter.llm.get_llm_provider") as mock:
    mock.return_value.generate = AsyncMock(return_value="Hello!")
```

**Mark integration tests:**
```python
@pytest.mark.integration
async def test_with_real_llm():
    ...
```

---

## API Conventions

**FastAPI route patterns:**
```python
@router.post("/execute", response_model=GreetingResponse)
async def execute(request: GreetingRequest) -> GreetingResponse:
    service = get_hello_world_service()
    result = await service.generate_greeting(request.name, request.style)
    return GreetingResponse(**result)
```

**Pydantic schema patterns:**
```python
class GreetingRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    style: Literal["friendly", "formal", "casual", "enthusiastic"] = "friendly"

    model_config = {"json_schema_extra": {"examples": [{"name": "Alice"}]}}
```

---

## Environment Variables

Key configuration in `backend/.env`:
```
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=agentic_ai
WEAVIATE_URL=http://localhost:8080
LLM_PROVIDER=ollama
LLM_DEFAULT_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434
```

Platform-specific overrides use prefix:
```
HELLO_WORLD_LLM_PROVIDER=openai
HELLO_WORLD_LLM_MODEL=gpt-4
```

---

## Common Mistakes to Avoid

1. Using `BEDROCK` instead of `AWS_BEDROCK`
2. Using `model=` instead of `default_model=` for LLM providers
3. Using `datetime.utcnow()` instead of `datetime.now(timezone.utc)`
4. Using `class Config` instead of `model_config = {}`
5. Overriding `self.memory`, `self.llm`, or `self.name` in agents
6. Using strict equality for float assertions
7. Running pytest from wrong directory (must be in `backend/`)
8. Forgetting async/await on database and LLM operations

---

## When Generating Code

1. **Read existing files first** - follow established patterns
2. **Keep changes focused** - one feature per change
3. **Add type hints** - all function parameters and returns
4. **Write tests** - at least one test per new function
5. **Handle errors** - use try/except with meaningful messages
6. **Log important operations** - use the logging module
7. **Don't over-engineer** - simple solutions preferred
