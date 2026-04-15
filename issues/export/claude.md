# Claude Code Project Guidance

This file provides guidance for using Claude Code to maintain and extend the Agentic AI Framework.

## Project Overview

The **Agentic AI Framework** is a full-stack application for building multi-agent AI systems:

- **Backend**: Python/FastAPI with async support, multi-LLM provider abstraction
- **Frontend**: React/TypeScript with Vite, Tailwind CSS, Zustand state management
- **Database**: MongoDB for persistence, Weaviate for vector storage (optional)
- **LLM Support**: Ollama (default), OpenAI, AWS Bedrock

The **hello_world** platform is the reference implementation demonstrating all patterns.

---

## Workflow

### Claude Code's Role
- Analyze the repository structure and code patterns
- Propose and refine implementation plans
- Generate GitHub Copilot prompts for each phase
- Review code and suggest improvements
- Help debug issues

### Human Developer's Role
- Use Claude's prompts with GitHub Copilot
- Review and edit generated code
- Run tests and commands
- Make final decisions on implementation
- Commit and deploy changes

---

## Coding Conventions

### Python (Backend)

**Framework**: FastAPI with async/await

```python
# Correct: Pydantic v2 style
class MyModel(BaseModel):
    name: str
    model_config = {"populate_by_name": True}

# Wrong: Deprecated Pydantic v1 style
class MyModel(BaseModel):
    class Config:
        populate_by_name = True
```

**DateTime**: Use timezone-aware
```python
# Correct
from datetime import datetime, timezone
now = datetime.now(timezone.utc)

# Wrong
now = datetime.utcnow()  # Deprecated
```

**LLM Providers**: Use correct enum and parameter names
```python
# Correct
from app.common.providers.llm import LLMProviderType
get_llm_provider(provider_type=LLMProviderType.AWS_BEDROCK, default_model="claude-v2")

# Wrong
get_llm_provider(provider_type=LLMProviderType.BEDROCK, model="claude-v2")
```

**BaseAgent**: Don't override reserved attributes
```python
# Reserved: self.name, self.llm, self.memory
class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(...)
        self.cache_service = get_cache()  # OK - different name
        # self.memory = get_cache()  # WRONG - overrides BaseAgent.memory
```

### TypeScript (Frontend)

**State Management**: Zustand with persist
```typescript
export const useMyStore = create<MyState>()(
  persist(
    (set) => ({ /* state and actions */ }),
    { name: 'my-storage' }
  )
)
```

**API Calls**: React Query hooks
```typescript
export function useMyData() {
  return useQuery({
    queryKey: ['my-data'],
    queryFn: myApi.getData,
  })
}
```

---

## Project Structure

```
agentic-ai-framework/
├── backend/
│   ├── app/
│   │   ├── common/              # Shared framework code
│   │   │   ├── base/            # BaseAgent, BaseChain, BaseOrchestrator
│   │   │   └── providers/       # LLM, embeddings providers
│   │   ├── platforms/
│   │   │   └── hello_world/     # Reference implementation
│   │   │       ├── agents/
│   │   │       ├── services/
│   │   │       ├── router.py
│   │   │       └── config.py
│   │   ├── db/                  # Database connections
│   │   └── config.py            # Global settings
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── api/                 # API clients
│   │   ├── components/          # React components
│   │   ├── hooks/               # Custom hooks
│   │   ├── pages/               # Route pages
│   │   ├── store/               # Zustand stores
│   │   └── types/               # TypeScript types
│   └── package.json
├── docs/
│   └── implementation-log.md    # Phase progress log
└── CLAUDE.md                    # Project instructions
```

---

## Phase Progress Tracking

Track implementation progress in `docs/implementation-log.md`:

```markdown
## Phase X: [Title]
- **Status**: Pending | In Progress | Complete
- **Files Changed**: [list]
- **Tests**: [pass/fail]
- **Notes**: [any issues or decisions]
```

---

## Git Conventions

### Branches
- `main` - Production-ready code
- `feature/phase-XX-description` - Phase implementation branches

### Commits
```
feat(hello-world): implement greeter agent

- Add GreeterAgent class with LLM integration
- Add prompt templates for greeting styles
- Add fallback greeting generation
```

---

## Safety Guidelines

### Do
- Run tests before committing
- Review generated code carefully
- Keep changes focused and incremental
- Document decisions in implementation log

### Don't
- Commit secrets or API keys
- Make large destructive changes without review
- Skip error handling
- Ignore test failures

---

## Common Commands

### Backend
```bash
cd backend

# Setup
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run
uvicorn app.main:app --reload

# Test
.venv/bin/python -m pytest -v
.venv/bin/python -m pytest -m "not integration" -v  # Skip integration tests
```

### Frontend
```bash
cd frontend

# Setup
npm install

# Run
npm run dev

# Build
npm run build
```

### Docker
```bash
# Build and run all services
docker-compose up --build

# Just backend
docker-compose up backend mongo
```

---

## Troubleshooting

### LLM Connection Issues
1. Check Ollama is running: `curl http://localhost:11434/api/tags`
2. Verify environment variables in `.env`
3. Check health endpoint: `curl http://localhost:8000/api/v1/platforms/hello-world/health`

### MongoDB Connection Issues
1. Check MongoDB is running: `mongosh --eval "db.stats()"`
2. Verify MONGODB_URI in environment
3. Check backend logs for connection errors

### Test Failures
1. Run with verbose output: `pytest -v --tb=long`
2. Check if integration tests need external services
3. Verify mocks match current interfaces
