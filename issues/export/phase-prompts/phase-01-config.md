# Phase 1: Project Setup & Configuration

## Goal
Establish the backend project structure with proper configuration management using Pydantic v2 Settings.

---

## Copilot Prompt

```
You are helping implement configuration management for a FastAPI backend. The goal is to create a robust settings system using Pydantic v2.

### Context
- This is a multi-agent AI framework
- Configuration should load from environment variables with sensible defaults
- Platform-specific configs should be able to override global settings
- We're using Pydantic v2 (use `model_config = {}` dict, NOT `class Config`)

### Files to Read First
Read these files to understand existing patterns:
- backend/app/config.py (if exists, modify; otherwise create)
- backend/app/platforms/hello_world/config.py (platform config example)

### Implementation Tasks

1. **Create/Update `backend/app/config.py`:**
   - Create a `Settings` class extending `pydantic_settings.BaseSettings`
   - Add these configuration groups:
     ```python
     # Application
     APP_NAME: str = "Agentic AI Framework"
     DEBUG: bool = False

     # LLM Configuration
     LLM_PROVIDER: str = "ollama"  # ollama | openai | aws_bedrock
     LLM_DEFAULT_MODEL: str = "llama3"
     LLM_TEMPERATURE: float = 0.7
     LLM_MAX_TOKENS: int = 1000

     # Ollama
     OLLAMA_BASE_URL: str = "http://localhost:11434"

     # OpenAI (optional)
     OPENAI_API_KEY: str | None = None

     # AWS Bedrock (optional)
     AWS_REGION: str = "us-east-1"

     # MongoDB
     MONGODB_URI: str = "mongodb://localhost:27017"
     MONGODB_DATABASE: str = "agentic_ai"

     # CORS
     CORS_ORIGINS_STR: str = "http://localhost:5173,http://localhost:3000"

     # Auth
     SECRET_KEY: str = "change-me-in-production"
     ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
     ```
   - Add computed properties:
     - `cors_origins` - split CORS_ORIGINS_STR into list
   - Add validators:
     - Validate LLM_PROVIDER is one of: ollama, openai, aws_bedrock
     - Validate LLM_TEMPERATURE is between 0 and 2
   - Use `model_config` for settings:
     ```python
     model_config = {
         "env_file": ".env",
         "env_file_encoding": "utf-8",
         "extra": "ignore",
     }
     ```

2. **Create singleton pattern:**
   ```python
   from functools import lru_cache

   @lru_cache
   def get_settings() -> Settings:
       return Settings()
   ```

3. **Create `backend/app/platforms/hello_world/config.py`:**
   - Create `HelloWorldConfig` class for platform-specific overrides
   - Support these environment variables:
     - HELLO_WORLD_LLM_PROVIDER (overrides LLM_PROVIDER)
     - HELLO_WORLD_LLM_MODEL (overrides LLM_DEFAULT_MODEL)
   - Add computed properties:
     - `effective_provider` - platform override or global
     - `effective_model` - platform override or global

4. **Write unit tests in `backend/app/tests/test_config.py`:**
   - Test default values load correctly
   - Test environment variable override works
   - Test validation errors for invalid LLM_PROVIDER
   - Test CORS origins parsing
   - Test platform config fallback behavior
   - Use `monkeypatch` to set test environment variables

### Expected Code Style
- Type hints on all parameters and return values
- Docstrings for classes and complex methods
- Follow existing project conventions

### Output
After implementing, provide:
1. Summary of files changed
2. Test command: `cd backend && .venv/bin/python -m pytest app/tests/test_config.py -v`
3. Any configuration decisions made
```

---

## Plan Template

Before making changes, Copilot should propose:

1. **Files to modify/create:**
   - [ ] `backend/app/config.py`
   - [ ] `backend/app/platforms/hello_world/config.py`
   - [ ] `backend/app/tests/test_config.py`

2. **High-level steps:**
   - Step 1: ...
   - Step 2: ...

---

## Documentation Template

After changes are complete, provide text for `docs/implementation-log.md`:

```markdown
## Phase 1: Project Setup & Configuration

### Summary of Changes
- `backend/app/config.py`: [description]
- `backend/app/platforms/hello_world/config.py`: [description]
- `backend/app/tests/test_config.py`: [description]

### Tests Executed
```bash
cd backend && .venv/bin/python -m pytest app/tests/test_config.py -v
```
**Results:** [PASS/FAIL with details]

### Fixes Applied
- [Any issues encountered and how they were resolved]

### Configuration Decisions
- [Any design decisions made]
```

---

## Earlier Mocks to Upgrade
- None (this is Phase 1)

---

## Human Checklist
- [ ] Review Copilot's proposed plan before accepting
- [ ] Verify environment variable names are appropriate
- [ ] Run tests and confirm they pass
- [ ] Update `.env.example` if one exists
