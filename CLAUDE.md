# Claude Code Project Instructions

Project-specific patterns, conventions, and gotchas for the agentic-ai-framework.

## Project Structure

```
backend/
├── app/
│   ├── common/          # Shared framework code (BaseAgent, providers)
│   ├── platforms/       # Platform implementations (newsletter, hello_world)
│   └── db/              # Database connections (MongoDB, Weaviate)
frontend/
├── src/
│   ├── components/      # React components
│   ├── pages/           # Route pages
│   ├── hooks/           # React Query & custom hooks
│   ├── store/           # Zustand state
│   ├── api/             # API clients
│   └── types/           # TypeScript types
docs/                    # Detailed phase documentation
```

## Newsletter Platform Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1-5 | Backend infrastructure | ✅ |
| 6-10 | Agents & orchestrator | ✅ |
| 11 | API endpoints | ✅ |
| 12 | Frontend infrastructure | ✅ |
| 13 | Frontend components | ✅ |
| 14 | Integration testing | Next |

See `docs/phase*.md` for detailed documentation per phase.

## Backend Patterns

### LLM Providers

```python
from app.common.providers.llm import LLMProviderType

# Use AWS_BEDROCK, not BEDROCK
LLMProviderType.AWS_BEDROCK

# Use default_model, not model
get_llm_provider(provider_type=..., default_model="llama3")
```

### Pydantic Models

```python
# Pydantic v2 - use model_config dict
class MyModel(BaseModel):
    model_config = {"populate_by_name": True}
```

### DateTime

```python
# Use timezone-aware
from datetime import datetime, timezone
now = datetime.now(timezone.utc)
```

### Agent Structure

```
agents/{name}/
├── agent.py         # Agent class
├── llm.py           # get_{name}_llm()
├── prompts.py       # Templates
└── tools.py         # Optional
```

### BaseAgent Reserved Attributes

Don't overwrite: `self.name`, `self.llm`, `self.memory`, `self.system_prompt`, `self.tools`

## Frontend Patterns

### React Query Hooks

```tsx
// Queries
const { data, isLoading } = useWorkflow(id);

// Mutations with cache invalidation
const mutation = useApproveCheckpoint();
mutation.mutate({ workflowId, request });
```

### Zustand Store

```tsx
const { activeWorkflowId, setActiveWorkflow } = useWorkflowState();
const { selectedArticles, toggleArticle } = useArticleSelection();
```

### SSE Integration

```tsx
useWorkflowSSE(workflowId ?? null, {
  onStatus: (e) => setStatus(e.status),
  onCheckpoint: (e) => toast({ title: e.title }),
  onError: (e) => toast({ variant: 'destructive', ... }),
});
```

### Toast Notifications

```tsx
import { useToast } from '@/components/ui/use-toast';
const { toast } = useToast();
toast({ title: 'Success', description: '...' });
```

## Common Gotchas

### Backend

| Issue | Solution |
|-------|----------|
| `LLMProviderType.BEDROCK` | Use `AWS_BEDROCK` |
| `datetime.utcnow()` | Use `datetime.now(timezone.utc)` |
| `class Config` in Pydantic | Use `model_config = {...}` |
| Float assertions `> 0.5` | Use `>= 0.5` or `pytest.approx()` |
| Missing `default_model` | Check provider `__init__` signature |

### Frontend

| Issue | Solution |
|-------|----------|
| Toast import | Use `@/components/ui/use-toast` |
| SSE id type | `useWorkflowSSE(id ?? null, ...)` |
| Unknown in JSX | Extract to variable, then `String(val)` |
| Unused imports | Remove or prefix with `_` |

### TypeScript

```tsx
// useParams returns undefined, SSE expects null
const { id } = useParams<{ id: string }>();
useWorkflowSSE(id ?? null, callbacks);

// Handle Record<string, unknown> in JSX
const msg = item.data.message;
{msg != null && <p>{String(msg)}</p>}
```

## Testing

### Backend

```bash
cd backend
.venv/bin/python -m pytest app/platforms/newsletter/tests/ -v
```

### Frontend

```bash
cd frontend
npx tsc --noEmit  # Type check
npm run dev       # Dev server
```

## Environment Variables

```bash
# Required
NEWSLETTER_TAVILY_API_KEY=xxx
NEWSLETTER_RESEND_API_KEY=xxx

# Optional overrides
NEWSLETTER_LLM_PROVIDER=ollama
NEWSLETTER_LLM_MODEL=llama3
```

## Documentation

Detailed documentation in `docs/`:
- `phase7-writing-agent.md`
- `phase8-preference-custom-prompt-agents.md`
- `phase9-langgraph-orchestrator.md`
- `phase10-email-service.md`
- `phase11-api-endpoints.md`
- `phase12-frontend-infrastructure.md`
- `phase13-frontend-components.md`
- `e2e-testing-plan.md`
