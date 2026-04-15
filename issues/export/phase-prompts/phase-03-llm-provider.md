# Phase 3: LLM Provider Abstraction

## Goal
Create a unified interface for multiple LLM backends (Ollama, OpenAI, AWS Bedrock) with provider factory pattern.

---

## Copilot Prompt

```
You are helping implement a multi-provider LLM abstraction layer for a FastAPI backend.

### Context
- This framework supports multiple LLM providers: Ollama (default), OpenAI, AWS Bedrock
- Each provider has different APIs but should present a unified interface
- Provider selection is via configuration
- IMPORTANT: Use `AWS_BEDROCK` (not `BEDROCK`) for the Bedrock provider enum value
- IMPORTANT: Use `default_model` parameter (not `model`) when passing to provider constructors

### Files to Read First
Read these files to understand existing patterns:
- backend/app/config.py (LLM configuration)
- backend/app/common/providers/ (existing provider code, if any)

### Implementation Tasks

1. **Create `backend/app/common/providers/llm.py`:**

   a) Define the provider enum:
   ```python
   from enum import Enum

   class LLMProviderType(str, Enum):
       OPENAI = "openai"
       OLLAMA = "ollama"
       AWS_BEDROCK = "aws_bedrock"  # NOT "BEDROCK"
   ```

   b) Define configuration model:
   ```python
   from pydantic import BaseModel

   class LLMConfig(BaseModel):
       provider: str = "ollama"
       model: str = "llama3"
       temperature: float = 0.7
       max_tokens: int = 1000
       timeout: int = 30
   ```

   c) Define abstract base provider:
   ```python
   from abc import ABC, abstractmethod
   from typing import AsyncGenerator, Optional, List, Dict, Any

   class BaseLLMProvider(ABC):
       def __init__(self, default_model: str, timeout: int = 30):
           self.default_model = default_model
           self.timeout = timeout

       @abstractmethod
       async def generate(
           self,
           prompt: str,
           model: Optional[str] = None,
           temperature: float = 0.7,
           max_tokens: int = 1000,
           **kwargs
       ) -> str:
           """Generate a response from the LLM."""
           pass

       @abstractmethod
       async def generate_stream(
           self,
           prompt: str,
           model: Optional[str] = None,
           **kwargs
       ) -> AsyncGenerator[str, None]:
           """Stream response tokens from the LLM."""
           pass

       @abstractmethod
       async def health_check(self) -> bool:
           """Check if the LLM provider is accessible."""
           pass
   ```

   d) Implement OllamaProvider:
   ```python
   import httpx

   class OllamaProvider(BaseLLMProvider):
       def __init__(self, base_url: str, default_model: str, timeout: int = 30):
           super().__init__(default_model, timeout)
           self.base_url = base_url.rstrip("/")
           self.client = httpx.AsyncClient(timeout=timeout)

       async def generate(self, prompt: str, model: Optional[str] = None, **kwargs) -> str:
           # POST to /api/generate
           # Handle response
           pass

       async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
           # POST to /api/generate with stream=True
           pass

       async def health_check(self) -> bool:
           # GET /api/tags to verify Ollama is running
           pass
   ```

   e) Implement OpenAIProvider:
   ```python
   class OpenAIProvider(BaseLLMProvider):
       def __init__(self, api_key: str, default_model: str, timeout: int = 30):
           super().__init__(default_model, timeout)
           self.api_key = api_key
           # Use openai library or httpx

       async def generate(self, prompt: str, **kwargs) -> str:
           # Call OpenAI chat completions API
           pass
   ```

   f) Implement AWSBedrockProvider:
   ```python
   class AWSBedrockProvider(BaseLLMProvider):
       def __init__(self, region: str, default_model: str, timeout: int = 30):
           super().__init__(default_model, timeout)
           self.region = region
           # Use boto3 bedrock-runtime client

       async def generate(self, prompt: str, **kwargs) -> str:
           # Call Bedrock invoke_model API
           pass
   ```

   g) Create factory function with caching:
   ```python
   from functools import lru_cache

   _providers: Dict[LLMProviderType, BaseLLMProvider] = {}

   def get_llm_provider(
       provider_type: LLMProviderType = LLMProviderType.OLLAMA,
       config: Optional[LLMConfig] = None,
       **kwargs
   ) -> BaseLLMProvider:
       """Get or create an LLM provider instance."""
       # Check cache first
       # Create and cache if not exists
       # Return provider
       pass
   ```

2. **Write unit tests in `backend/app/tests/test_llm_provider.py`:**
   - Mock httpx.AsyncClient for Ollama tests
   - Mock OpenAI client for OpenAI tests
   - Mock boto3 for Bedrock tests
   - Test generate() returns expected response
   - Test generate_stream() yields tokens
   - Test health_check() returns True/False appropriately
   - Test factory function caching behavior
   - Test error handling (timeout, connection error, invalid response)

### Expected Code Style
- All LLM calls must be async
- Use type hints throughout
- Handle exceptions gracefully with meaningful error messages
- Log LLM calls for debugging (sanitize any sensitive data)
- Follow existing project conventions

### Important Notes
- The enum value is `AWS_BEDROCK`, NOT `BEDROCK`
- Pass `default_model` to constructors, NOT `model`
- Providers should be cached/reused (singleton per type)

### Output
After implementing, provide:
1. Summary of files changed
2. Test command: `cd backend && .venv/bin/python -m pytest app/tests/test_llm_provider.py -v`
3. Any provider-specific decisions made
```

---

## Plan Template

Before making changes, Copilot should propose:

1. **Files to modify/create:**
   - [ ] `backend/app/common/providers/__init__.py`
   - [ ] `backend/app/common/providers/llm.py`
   - [ ] `backend/app/tests/test_llm_provider.py`

2. **High-level steps:**
   - Step 1: ...
   - Step 2: ...

---

## Documentation Template

After changes are complete, provide text for `docs/implementation-log.md`:

```markdown
## Phase 3: LLM Provider Abstraction

### Summary of Changes
- `backend/app/common/providers/llm.py`: [description]

### Tests Executed
```bash
cd backend && .venv/bin/python -m pytest app/tests/test_llm_provider.py -v
```
**Results:** [PASS/FAIL with details]

### Fixes Applied
- [Any issues encountered and how they were resolved]

### Provider Details
| Provider | Model Format | Health Check Endpoint |
|----------|--------------|----------------------|
| Ollama | llama3, mistral | /api/tags |
| OpenAI | gpt-4, gpt-3.5-turbo | N/A (API call) |
| AWS Bedrock | anthropic.claude-v2 | N/A (API call) |
```

---

## Earlier Mocks to Upgrade
- None (this is Phase 3)

**Note:** HTTP clients are mocked in unit tests. In Phase 18, integration tests will call real Ollama (marked with `@pytest.mark.integration`).

---

## Human Checklist
- [ ] Review Copilot's proposed plan before accepting
- [ ] Verify Ollama is running locally: `curl http://localhost:11434/api/tags`
- [ ] Run tests and confirm they pass
- [ ] Manually test with real Ollama:
  ```python
  provider = get_llm_provider(LLMProviderType.OLLAMA)
  result = await provider.generate("Hello!")
  print(result)
  ```
