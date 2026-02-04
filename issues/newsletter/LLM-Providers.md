# LLM Provider Configuration Update

**Date:** 2026-02-02
**Status:** Completed

## Overview

Added multi-provider LLM support with Perplexity Sonar as the new default provider, while maintaining full compatibility with Gemini and other existing providers.

## Supported Providers

| Provider | Type | Models | Features |
|----------|------|--------|----------|
| **Perplexity** | `perplexity` | sonar, sonar-pro, sonar-reasoning, sonar-deep-research | Built-in web search, citations |
| **Gemini** | `gemini` | gemini-2.5-flash, gemini-2.0-flash, gemma-3-4b-it | Google AI, fast inference |
| **OpenAI** | `openai` | gpt-4, gpt-4-turbo, gpt-3.5-turbo | Industry standard |
| **Ollama** | `ollama` | llama3, mistral, codellama, etc. | Local deployment |
| **AWS Bedrock** | `aws_bedrock` | claude-3, titan | Enterprise, AWS integration |

## Changes Made

### 1. Core LLM Provider (`backend/app/common/providers/llm.py`)

**Added `PerplexityProvider` class:**
- OpenAI-compatible API integration
- Support for all Sonar models
- Citation extraction from responses
- Streaming support
- Health check endpoint

**Updated `LLMProviderType` enum:**
```python
class LLMProviderType(str, Enum):
    GEMINI = "gemini"
    PERPLEXITY = "perplexity"  # NEW
    OPENAI = "openai"
    OLLAMA = "ollama"
    AWS_BEDROCK = "aws_bedrock"
```

**Updated provider registry:**
```python
provider_classes = {
    "gemini": GeminiProvider,
    "perplexity": PerplexityProvider,  # NEW
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,
    "aws_bedrock": AWSBedrockProvider,
}
```

### 2. Configuration (`backend/app/config.py`)

**Added Perplexity settings:**
```python
# Perplexity Configuration (Sonar models with search)
PERPLEXITY_API_KEY: str | None = None
PERPLEXITY_BASE_URL: str = "https://api.perplexity.ai"
```

**Updated LLM_PROVIDER comment:**
```python
LLM_PROVIDER: str = "gemini"  # gemini | perplexity | ollama | openai | aws_bedrock
```

### 3. Environment Variables (`backend/.env`)

```bash
# LLM Configuration
LLM_PROVIDER=perplexity
LLM_DEFAULT_MODEL=sonar

# LLM Providers
PERPLEXITY_API_KEY=pplx-xxx...
GEMINI_API_KEY=AIza...
```

### 4. Newsletter Research Agent (`backend/app/platforms/newsletter/agents/research/llm.py`)

**Added Perplexity to provider mapping:**
```python
provider_type = {
    "gemini": LLMProviderType.GEMINI,
    "perplexity": LLMProviderType.PERPLEXITY,  # NEW
    "ollama": LLMProviderType.OLLAMA,
    "openai": LLMProviderType.OPENAI,
    "aws_bedrock": LLMProviderType.AWS_BEDROCK,
}.get(provider_name, LLMProviderType.GEMINI)
```

### 5. Research Agent Improvements (`backend/app/platforms/newsletter/agents/research/agent.py`)

**Added JSON repair for batch summarization:**
- `_repair_json()` method to fix common LLM JSON output issues
- Fallback to individual LLM summarization instead of text extraction

## Perplexity Sonar Models

| Model | Use Case | Features |
|-------|----------|----------|
| `sonar` | General queries | Fast, search-augmented |
| `sonar-pro` | Complex queries | Deeper search, more sources |
| `sonar-reasoning` | Analysis tasks | Extended chain-of-thought |
| `sonar-deep-research` | Research tasks | Comprehensive investigation |

## Usage Examples

### Switch Provider via Environment
```bash
# Use Perplexity (current default)
LLM_PROVIDER=perplexity
LLM_DEFAULT_MODEL=sonar

# Use Gemini
LLM_PROVIDER=gemini
LLM_DEFAULT_MODEL=gemini-2.5-flash
```

### Programmatic Provider Selection
```python
from app.common.providers.llm import get_llm_provider, LLMProviderType

# Use default (Perplexity)
llm = get_llm_provider()

# Explicitly use Perplexity
llm = get_llm_provider(provider_type=LLMProviderType.PERPLEXITY)

# Explicitly use Gemini
llm = get_llm_provider(provider_type=LLMProviderType.GEMINI)

# With custom model
llm = get_llm_provider(
    provider_type=LLMProviderType.PERPLEXITY,
    default_model="sonar-pro"
)
```

### Perplexity with Citations
```python
response = await llm.chat(
    messages=[{"role": "user", "content": "What is Kubernetes?"}],
    return_citations=True
)
print(response.content)
print(response.raw_response.get("citations", []))
```

## Testing

All providers tested successfully:

```
=== Perplexity Sonar ===
Health Check: PASS
Simple Generation: PASS
Chat with System Prompt: PASS
Search-Augmented Response: PASS (with citations)

=== Gemini ===
Health Check: PASS
Simple Generation: PASS
Chat: PASS

=== Research Agent Integration ===
Tavily Search: PASS
LLM Summarization: PASS
Full Pipeline: PASS
```

## API Keys Required

| Provider | Environment Variable | Required |
|----------|---------------------|----------|
| Perplexity | `PERPLEXITY_API_KEY` | Yes (if using) |
| Gemini | `GEMINI_API_KEY` | Yes (if using) |
| OpenAI | `OPENAI_API_KEY` | Yes (if using) |
| Ollama | N/A (local) | No |
| AWS Bedrock | AWS credentials | Yes (if using) |

## Notes

1. **Rate Limits:** Perplexity subscription eliminates rate limit concerns
2. **Gemini Free Tier:** Has quota limits (5 req/min), consider paid tier for production
3. **Provider Caching:** Providers are cached as singletons; use `clear_provider_cache()` to reset
4. **Fallback:** If batch summarization fails, system falls back to individual LLM calls, then text extraction
