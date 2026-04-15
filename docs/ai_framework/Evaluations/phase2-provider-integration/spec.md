# Phase 2 — Provider Integration

**Goal:** make both eval tools call models through the project's existing LLM abstraction (`app.common.providers.llm`), so eval results reflect the same models, configs, and credentials production uses.

**Estimated effort:** 4–6 hours.

## Learning objectives

1. Why is "evaluating the same model that runs in prod" a non-negotiable design property?
2. How does promptfoo's custom Python provider interface work? (`call_api(prompt, options, context) -> {output, tokenUsage, ...}`)
3. How do Moonshot connectors work, and where do they live in the `moonshot-data` directory tree?
4. What's the right boundary between "eval-tool-specific glue" and "framework code"?

## Design principle

> Both tools call our `LLMProviderType` enum. Neither tool re-implements provider auth, retries, or model selection. If we change `NEWSLETTER_LLM_MODEL` in env, both eval tools follow.

This means we write **one shared shim** and bind both tools to it.

## Architecture

```
┌──────────────┐   call_api()    ┌──────────────────────────┐
│  promptfoo   ├────────────────►│                          │
└──────────────┘                 │  evals/shared/           │
                                 │  framework_invoke.py     │     ┌─────────────────────────┐
┌──────────────┐  predict()      │  - reads env             ├────►│ app.common.providers.llm │
│  Moonshot    ├────────────────►│  - returns model output  │     │ (Bedrock / Ollama / ...) │
│  connector   │                 │  - normalizes errors     │     └─────────────────────────┘
└──────────────┘                 └──────────────────────────┘
```

A **single Python module** does the actual model call. Each tool gets a thin adapter that satisfies its interface contract.

## Deliverables

### 2.1 — Shared invoker

**File:** `evals/shared/framework_invoke.py` — *I'll implement this.*

```python
# claude-implements
"""Single entry point both eval tools call into."""
from app.common.providers.llm import LLMProviderType, get_llm_provider

def invoke(prompt: str, *, provider: str, model: str, **kwargs) -> dict:
    """
    Returns: {"text": str, "usage": {"input": int, "output": int}, "raw": Any}
    Raises:  InvokeError on transport / auth / rate-limit failures.
    """
    ...
```

Why a wrapper instead of importing `get_llm_provider` directly into each adapter?
- Stable signature for tools to bind to.
- One place to add eval-specific concerns (timeouts, redaction, cost capture).
- Easier to mock for unit-testing the adapters themselves.

### 2.2 — promptfoo custom provider

**File:** `evals/promptfoo/providers/framework_provider.py` — *I'll implement this.*

```python
# claude-implements
from evals.shared.framework_invoke import invoke

def call_api(prompt, options, context):
    cfg = options.get("config", {})
    result = invoke(prompt, provider=cfg["provider"], model=cfg["model"])
    return {
        "output": result["text"],
        "tokenUsage": {
            "prompt": result["usage"]["input"],
            "completion": result["usage"]["output"],
            "total": sum(result["usage"].values()),
        },
    }
```

**Reference in `promptfooconfig.yaml`:**

```yaml
providers:
  - id: 'file://evals/promptfoo/providers/framework_provider.py'
    label: 'bedrock-claude-haiku'
    config:
      provider: AWS_BEDROCK
      model: anthropic.claude-haiku-4-5-20251001-v1:0
  - id: 'file://evals/promptfoo/providers/framework_provider.py'
    label: 'ollama-llama3'
    config:
      provider: OLLAMA
      model: llama3
```

### 2.3 — Moonshot connector

**File:** `evals/moonshot/connectors/framework_connector.py` — *I'll implement this.*

Moonshot's connector base class lives in `moonshot.src.connectors.connector`. The contract is roughly:

```python
# claude-implements (sketch — exact API depends on installed Moonshot version)
from moonshot.src.connectors.connector import Connector, perform_retry

class FrameworkConnector(Connector):
    async def get_response(self, prompt: str) -> str:
        result = invoke(
            prompt,
            provider=self.endpoint.params["provider"],
            model=self.endpoint.params["model"],
        )
        return result["text"]
```

**Endpoint JSON** (registered with `python -m moonshot -i ...` or via UI):

```json
{
  "name": "framework-bedrock-haiku",
  "connector_type": "framework_connector",
  "uri": "internal",
  "token": "n/a",
  "max_calls_per_second": 5,
  "max_concurrency": 1,
  "params": {
    "provider": "AWS_BEDROCK",
    "model": "anthropic.claude-haiku-4-5-20251001-v1:0"
  }
}
```

The connector file is dropped into `~/.moonshot/connectors-endpoints/` (or wherever `moonshot-data` is configured) and discovered by name.

### 2.4 — Sanity tests for the shim

**File:** `evals/shared/tests/test_framework_invoke.py` — *I'll implement this.*

- Mocks `get_llm_provider` and asserts the wrapper passes through correctly.
- One live test (skipped by default, run with `-m live`) that hits Ollama if available.

### 2.5 — One-shot smoke run for each tool

A tiny config file in each tool that asks both providers a fixed question and prints the result. This is your "the wiring works" proof.

```bash
# you-run (after I've created the configs)
promptfoo eval -c evals/promptfoo/smoke.yaml
python -m moonshot cli run-recipe smoke-recipe framework-bedrock-haiku
```

## Acceptance criteria

- [ ] `framework_invoke.py` exists, has tests, and tests pass.
- [ ] promptfoo smoke config returns real model output for both Bedrock and Ollama labels.
- [ ] Moonshot CLI lists `framework-bedrock-haiku` under `list endpoints`.
- [ ] Switching `NEWSLETTER_LLM_MODEL` env var changes the model both tools use, with no code edits.

## Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| promptfoo provider returns `undefined` output | Returned `text` instead of `output` key | Match contract exactly: key is `"output"` |
| Moonshot connector not discovered | File in wrong dir or wrong base class import path | Run `python -m moonshot cli list connectors`; check `~/.moonshot/connectors/` |
| `ImportError: app.common.providers.llm` from Moonshot venv | Moonshot venv (3.11) doesn't have project on PYTHONPATH | Add a `.pth` file or `pip install -e backend/` into the moonshot venv |
| Different Python versions cause subtle behavior diffs | Bedrock client behavior on Py 3.11 vs 3.12 | Standardize on 3.11 for both venvs if possible |
| Eval calls hammer prod rate limits | No throttling in shim | Add `max_calls_per_second` in endpoint JSON; consider a `RATE_LIMIT_EVAL=1` flag |

## Design decisions to make explicit

Before implementing, decide and document in `notes.md`:

1. **Where do eval credentials come from?** Same `.env` as backend, or a separate `.env.evals`?
2. **Do evals count against prod budget?** If yes, tag spend (`x-cost-tag: evals`). If no, use a separate AWS account / Ollama only.
3. **Is the eval invoker async?** promptfoo can drive sync; Moonshot is async-native. The shim should expose both `invoke` and `ainvoke`.

## Reading list

- promptfoo: [Custom Python provider full reference](https://www.promptfoo.dev/docs/providers/python/)
- Moonshot: read `moonshot/src/connectors/connectors/openai_connector.py` from the installed package — this is the canonical example connector, copy its shape.
- LangChain Bedrock client source — useful background on what `get_llm_provider` is wrapping.

## Exit criteria → next phase

Both tools can call your models with one shared shim. Now we use them — Phase 3 builds the per-agent eval suites in promptfoo.
