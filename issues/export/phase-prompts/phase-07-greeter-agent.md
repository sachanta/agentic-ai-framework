# Phase 7: Greeter Agent Implementation

## Goal
Implement the hello_world platform's primary agent that generates personalized greetings using the LLM provider.

---

## Copilot Prompt

```
You are helping implement the Greeter Agent for the hello_world platform in a multi-agent AI framework.

### Context
- The Greeter Agent takes a name and greeting style, then generates a personalized greeting
- It extends BaseAgent and uses the LLM provider abstraction
- Must support fallback greetings when LLM is unavailable
- Greeting styles: friendly, formal, casual, enthusiastic

### Files to Read First
Read these files to understand existing patterns:
- backend/app/common/base/agent.py (BaseAgent class)
- backend/app/common/providers/llm.py (LLM provider)
- backend/app/platforms/hello_world/ (existing platform code)
- backend/app/platforms/hello_world/config.py (platform config)

### Implementation Tasks

1. **Create `backend/app/platforms/hello_world/agents/greeter/prompts.py`:**
   ```python
   from app.common.base.prompt import PromptTemplate

   GREETER_SYSTEM_PROMPT = """You are a friendly greeting assistant.
   Your job is to generate personalized greetings based on the user's name and preferred style.
   Keep greetings concise (1-2 sentences) and appropriate for the requested style.
   """

   GREETING_TEMPLATES = {
       "friendly": PromptTemplate(
           template="Generate a warm and friendly greeting for {name}. "
                    "Make it welcoming and personal."
       ),
       "formal": PromptTemplate(
           template="Generate a professional and formal greeting for {name}. "
                    "Keep it respectful and businesslike."
       ),
       "casual": PromptTemplate(
           template="Generate a relaxed and casual greeting for {name}. "
                    "Make it laid-back and approachable."
       ),
       "enthusiastic": PromptTemplate(
           template="Generate an energetic and enthusiastic greeting for {name}. "
                    "Make it upbeat and exciting!"
       ),
   }

   FALLBACK_GREETINGS = {
       "friendly": "Hello {name}! It's wonderful to see you. Welcome!",
       "formal": "Good day, {name}. It is a pleasure to make your acquaintance.",
       "casual": "Hey {name}! What's up?",
       "enthusiastic": "WOW, {name}! SO GREAT to meet you! This is AMAZING!",
   }
   ```

2. **Create `backend/app/platforms/hello_world/agents/greeter/llm.py`:**
   ```python
   from app.common.providers.llm import (
       get_llm_provider,
       BaseLLMProvider,
       LLMProviderType,
       LLMConfig,
   )
   from app.platforms.hello_world.config import config

   def get_greeter_config() -> LLMConfig:
       """Get LLM configuration for the Greeter Agent."""
       return LLMConfig(
           provider=config.effective_provider,
           model=config.effective_model,
           temperature=0.7,
           max_tokens=200,
       )

   def get_greeter_llm() -> BaseLLMProvider:
       """Get the LLM provider for the Greeter Agent."""
       cfg = get_greeter_config()
       provider_type = LLMProviderType(cfg.provider)

       return get_llm_provider(
           provider_type=provider_type,
           default_model=cfg.model,  # NOT "model="
       )
   ```

3. **Create `backend/app/platforms/hello_world/agents/greeter/agent.py`:**
   ```python
   from typing import Any, Dict, Optional
   import logging

   from app.common.base.agent import BaseAgent
   from .llm import get_greeter_llm
   from .prompts import (
       GREETER_SYSTEM_PROMPT,
       GREETING_TEMPLATES,
       FALLBACK_GREETINGS,
   )

   logger = logging.getLogger(__name__)

   class GreeterAgent(BaseAgent):
       """Agent that generates personalized greetings."""

       VALID_STYLES = ["friendly", "formal", "casual", "enthusiastic"]

       def __init__(self):
           llm = get_greeter_llm()
           super().__init__(
               name="greeter",
               llm=llm,
               system_prompt=GREETER_SYSTEM_PROMPT,
           )

       async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
           """
           Generate a greeting.

           Args:
               input: {
                   "name": str - The name to greet
                   "style": str - Greeting style (friendly, formal, casual, enthusiastic)
               }

           Returns:
               {
                   "success": bool,
                   "greeting": str,
                   "style": str,
                   "used_fallback": bool,
               }
           """
           name = input.get("name", "Friend")
           style = input.get("style", "friendly")

           # Validate style
           if style not in self.VALID_STYLES:
               style = "friendly"
               logger.warning(f"Invalid style requested, defaulting to: {style}")

           try:
               greeting = await self._generate_greeting(name, style)
               used_fallback = False
           except Exception as e:
               logger.warning(f"LLM generation failed, using fallback: {e}")
               greeting = self._get_fallback_greeting(name, style)
               used_fallback = True

           return {
               "success": True,
               "greeting": greeting,
               "style": style,
               "used_fallback": used_fallback,
           }

       async def _generate_greeting(self, name: str, style: str) -> str:
           """Generate greeting using LLM."""
           template = GREETING_TEMPLATES.get(style, GREETING_TEMPLATES["friendly"])
           prompt = template.format(name=name)

           full_prompt = f"{self.system_prompt}\n\n{prompt}"

           response = await self.llm.generate(
               prompt=full_prompt,
               temperature=0.7,
               max_tokens=200,
           )

           return response.strip()

       def _get_fallback_greeting(self, name: str, style: str) -> str:
           """Get template-based fallback greeting."""
           template = FALLBACK_GREETINGS.get(style, FALLBACK_GREETINGS["friendly"])
           return template.format(name=name)
   ```

4. **Create `backend/app/platforms/hello_world/agents/greeter/__init__.py`:**
   ```python
   from .agent import GreeterAgent
   from .llm import get_greeter_llm, get_greeter_config

   __all__ = ["GreeterAgent", "get_greeter_llm", "get_greeter_config"]
   ```

5. **Write unit tests in `backend/app/platforms/hello_world/tests/test_greeter_agent.py`:**
   - Test GreeterAgent with mocked LLM provider
   - Test all four greeting styles
   - Test fallback behavior when LLM fails
   - Test invalid style defaults to friendly
   - Test get_greeter_llm() factory function
   - Test get_greeter_config() returns correct values
   - Mock the LLM provider to return predictable responses

### Expected Code Style
- All agent methods should be async
- Use type hints throughout
- Add docstrings explaining purpose and usage
- Log important operations
- Follow existing project conventions

### Important Notes
- Use `default_model` parameter (NOT `model`) when calling get_llm_provider
- Don't override `self.memory`, `self.llm`, or `self.name` after super().__init__

### Output
After implementing, provide:
1. Summary of files changed
2. Test command: `cd backend && .venv/bin/python -m pytest app/platforms/hello_world/tests/test_greeter_agent.py -v`
3. Any design decisions made
```

---

## Plan Template

Before making changes, Copilot should propose:

1. **Files to modify/create:**
   - [ ] `backend/app/platforms/hello_world/agents/__init__.py`
   - [ ] `backend/app/platforms/hello_world/agents/greeter/__init__.py`
   - [ ] `backend/app/platforms/hello_world/agents/greeter/prompts.py`
   - [ ] `backend/app/platforms/hello_world/agents/greeter/llm.py`
   - [ ] `backend/app/platforms/hello_world/agents/greeter/agent.py`
   - [ ] `backend/app/platforms/hello_world/tests/test_greeter_agent.py`

2. **High-level steps:**
   - Step 1: ...
   - Step 2: ...

---

## Documentation Template

After changes are complete, provide text for `docs/implementation-log.md`:

```markdown
## Phase 7: Greeter Agent Implementation

### Summary of Changes
- `backend/app/platforms/hello_world/agents/greeter/`: Complete agent implementation
- Greeting styles: friendly, formal, casual, enthusiastic
- Fallback mechanism when LLM unavailable

### Tests Executed
```bash
cd backend && .venv/bin/python -m pytest app/platforms/hello_world/tests/test_greeter_agent.py -v
```
**Results:** [PASS/FAIL with details]

### Fixes Applied
- [Any issues encountered and how they were resolved]

### Greeting Styles
| Style | Tone | Example Output |
|-------|------|----------------|
| friendly | Warm, welcoming | "Hello Alice! Great to see you!" |
| formal | Professional | "Good day, Alice. A pleasure." |
| casual | Relaxed | "Hey Alice! What's up?" |
| enthusiastic | Energetic | "WOW Alice! AMAZING to meet you!" |
```

---

## Earlier Mocks to Upgrade
- Uses LLM provider from Phase 3 (mocked in unit tests)

**Note:** In Phase 18, integration tests will call real Ollama for greeting generation.

---

## Human Checklist
- [ ] Review Copilot's proposed plan before accepting
- [ ] Verify greeting templates are appropriate
- [ ] Run tests and confirm they pass
- [ ] Manually test with real Ollama:
  ```python
  agent = GreeterAgent()
  result = await agent.run({"name": "Alice", "style": "friendly"})
  print(result["greeting"])
  ```
