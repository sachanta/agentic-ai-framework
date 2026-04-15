# Project Overview

## Summary

The **Agentic AI Framework** is a full-stack application designed for building, orchestrating, and deploying multi-agent AI systems. The architecture follows a clean separation between a Python/FastAPI backend and a React/TypeScript frontend. The backend provides a flexible abstraction layer for LLM providers (Ollama, OpenAI, AWS Bedrock), agent orchestration patterns (sequential, parallel, conditional), and data persistence (MongoDB + Weaviate vector store). The frontend offers a modern SPA with role-based authentication, state management via Zustand, and data fetching via TanStack Query.

The **hello_world** platform serves as the reference implementation, demonstrating the complete pattern: a `GreeterAgent` that generates personalized greetings using configurable LLM backends, coordinated by an orchestrator, exposed via REST API, and consumed by React components.

---

## Technology Stack

### Backend
| Category | Technology |
|----------|------------|
| Framework | FastAPI 0.109+ |
| Runtime | Python 3.11+, Uvicorn (ASGI) |
| Database | MongoDB (motor async driver) |
| Vector Store | Weaviate |
| LLM Providers | Ollama (default), OpenAI, AWS Bedrock |
| Configuration | Pydantic v2 Settings |
| Testing | pytest, pytest-asyncio, pytest-cov |
| Linting/Format | ruff, black |

### Frontend
| Category | Technology |
|----------|------------|
| Framework | React 18.2 + TypeScript 5.3 |
| Build Tool | Vite 5.1.0 |
| Router | React Router v6.22 |
| State Management | Zustand 4.5.0 (with persist) |
| Data Fetching | TanStack React Query 5.17 |
| UI Components | Radix UI (headless) |
| Styling | Tailwind CSS 3.4.1 |
| Forms | React Hook Form 7.50 + Zod 3.22 |
| Testing/Mocks | MSW (Mock Service Worker) |

---

## Known Constraints

1. **Monorepo Layout**: Backend and frontend are in separate top-level directories (`backend/`, `frontend/`). Each has its own dependency management (pip/npm).

2. **LLM Provider Dependency**: The system gracefully degrades if Ollama is unavailable (falls back to template greetings), but full functionality requires a running LLM service.

3. **External Services**: MongoDB is required for persistence. Weaviate is optional but needed for RAG features.

4. **Test Isolation**: Backend tests should be run from the `backend/` directory using `.venv/bin/python -m pytest`.

5. **Environment Configuration**: Platform-specific settings override global settings (e.g., `HELLO_WORLD_LLM_PROVIDER` overrides `LLM_PROVIDER`).

6. **Reserved Attributes**: When extending `BaseAgent`, do not override `self.memory`, `self.llm`, or `self.name`.

7. **Provider Parameter**: Use `default_model` (not `model`) when initializing LLM providers.

8. **Pydantic v2**: Use `model_config = {}` dict, not deprecated `class Config`.

9. **DateTime Handling**: Use `datetime.now(timezone.utc)`, not deprecated `datetime.utcnow()`.

---

## Directory Structure

```
agentic-ai-framework/
├── backend/
│   ├── app/
│   │   ├── common/              # Shared framework code
│   │   │   ├── base/            # BaseAgent, BaseChain, BaseOrchestrator
│   │   │   └── providers/       # LLM, embeddings, vectorstore providers
│   │   ├── platforms/           # Platform implementations
│   │   │   └── hello_world/     # Reference implementation
│   │   │       ├── agents/greeter/
│   │   │       ├── orchestrator/
│   │   │       ├── services/
│   │   │       ├── router.py
│   │   │       └── config.py
│   │   ├── db/                  # MongoDB, Weaviate connections
│   │   ├── api/v1/              # REST API routes
│   │   └── config.py            # Global settings
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── api/                 # API clients
│   │   ├── components/          # React components
│   │   │   ├── ui/              # Radix UI wrappers
│   │   │   └── apps/hello-world/
│   │   ├── hooks/               # Custom hooks
│   │   ├── pages/               # Route handlers
│   │   ├── store/               # Zustand stores
│   │   ├── types/               # TypeScript interfaces
│   │   └── mocks/               # MSW mock handlers
│   └── package.json
└── CLAUDE.md                    # Project instructions
```

---

## Build & Run Commands

### Backend
```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Tests
.venv/bin/python -m pytest app/platforms/hello_world/tests/ -v
```

### Frontend
```bash
cd frontend
npm install
npm run dev:mock    # With MSW mocks
npm run dev:real    # Against real API
npm run build       # Production build
```

---

## API Endpoints (Hello World Platform)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/platforms/hello-world/status` | Platform status |
| GET | `/api/v1/platforms/hello-world/config` | LLM configuration |
| GET | `/api/v1/platforms/hello-world/health` | Platform + LLM health |
| GET | `/api/v1/platforms/hello-world/agents` | List available agents |
| POST | `/api/v1/platforms/hello-world/execute` | Generate greeting |
