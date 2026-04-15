# Phase 5: Base Chain Implementation

## Goal
Implement chain patterns for composing LLM operations including prompt templates, sequential chains, and conditional branching.

---

## Copilot Prompt

```
You are helping implement chain abstractions for composing LLM operations in a multi-agent AI framework.

### Context
- Chains represent composable sequences of LLM operations
- Each chain takes input, processes it, and produces output
- Chains can be composed: sequential, parallel, conditional
- Prompt templates use `{variable_name}` syntax for variable substitution

### Files to Read First
Read these files to understand existing patterns:
- backend/app/common/providers/llm.py (LLM provider interface)
- backend/app/common/base/agent.py (agent patterns)
- backend/app/common/base/ (existing chain code, if any)

### Implementation Tasks

1. **Create `backend/app/common/base/prompt.py`:**
   ```python
   from typing import Dict, List, Any, Optional
   import re

   class PromptTemplate:
       """Template for generating prompts with variable substitution."""

       def __init__(self, template: str, input_variables: Optional[List[str]] = None):
           self.template = template
           self.input_variables = input_variables or self._extract_variables()

       def _extract_variables(self) -> List[str]:
           """Extract variable names from template using {var} syntax."""
           return re.findall(r'\{(\w+)\}', self.template)

       def format(self, **kwargs) -> str:
           """Format template with provided variables."""
           # Validate all required variables are provided
           # Substitute variables
           # Return formatted string
           pass

       def partial(self, **kwargs) -> 'PromptTemplate':
           """Create a new template with some variables pre-filled."""
           pass

   class ChatPromptTemplate:
       """Template for chat-style prompts with system/user/assistant roles."""

       def __init__(self, messages: List[Dict[str, str]]):
           """
           messages: [{"role": "system", "content": "..."}, {"role": "user", "content": "{input}"}]
           """
           self.messages = messages

       def format_messages(self, **kwargs) -> List[Dict[str, str]]:
           """Format all message templates with provided variables."""
           pass
   ```

2. **Create `backend/app/common/base/chain.py`:**
   ```python
   from abc import ABC, abstractmethod
   from typing import Any, Dict, List, Optional, Callable

   class BaseChain(ABC):
       """Base class for all chains."""

       def __init__(self, name: str, verbose: bool = False):
           self.name = name
           self.verbose = verbose

       @abstractmethod
       async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
           """Execute the chain."""
           pass

       @property
       @abstractmethod
       def input_keys(self) -> List[str]:
           """Keys expected in input dict."""
           pass

       @property
       @abstractmethod
       def output_keys(self) -> List[str]:
           """Keys produced in output dict."""
           pass

   class LLMChain(BaseChain):
       """Chain that formats a prompt and calls an LLM."""

       def __init__(
           self,
           name: str,
           llm: BaseLLMProvider,
           prompt: PromptTemplate,
           output_key: str = "output",
           verbose: bool = False,
       ):
           super().__init__(name, verbose)
           self.llm = llm
           self.prompt = prompt
           self.output_key = output_key

       async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
           # 1. Format prompt with input
           # 2. Call LLM
           # 3. Return {output_key: response}
           pass

       @property
       def input_keys(self) -> List[str]:
           return self.prompt.input_variables

       @property
       def output_keys(self) -> List[str]:
           return [self.output_key]

   class SequentialChain(BaseChain):
       """Chain that runs multiple chains in sequence, passing outputs to inputs."""

       def __init__(
           self,
           name: str,
           chains: List[BaseChain],
           input_keys: List[str],
           output_keys: List[str],
           verbose: bool = False,
       ):
           super().__init__(name, verbose)
           self.chains = chains
           self._input_keys = input_keys
           self._output_keys = output_keys

       async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
           # Run chains in order, merging outputs into state
           pass

   class ConditionalChain(BaseChain):
       """Chain that branches based on a condition."""

       def __init__(
           self,
           name: str,
           condition: Callable[[Dict[str, Any]], str],
           branches: Dict[str, BaseChain],
           default_branch: Optional[str] = None,
           verbose: bool = False,
       ):
           super().__init__(name, verbose)
           self.condition = condition
           self.branches = branches
           self.default_branch = default_branch

       async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
           # Evaluate condition to get branch name
           # Run selected branch
           pass

   class TransformChain(BaseChain):
       """Chain for non-LLM data transformations."""

       def __init__(
           self,
           name: str,
           transform_func: Callable[[Dict[str, Any]], Dict[str, Any]],
           input_keys: List[str],
           output_keys: List[str],
           verbose: bool = False,
       ):
           super().__init__(name, verbose)
           self.transform_func = transform_func
           self._input_keys = input_keys
           self._output_keys = output_keys

       async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
           # Apply transform function (handle both sync and async)
           pass
   ```

3. **Write unit tests in `backend/app/tests/test_base_chain.py`:**
   - Test PromptTemplate variable extraction and formatting
   - Test LLMChain with mocked LLM provider
   - Test SequentialChain passes outputs correctly
   - Test ConditionalChain selects correct branch
   - Test TransformChain applies transformation
   - Test error handling (missing variables, chain failures)
   - Use pytest-asyncio for async tests

### Expected Code Style
- All chain methods should be async
- Use type hints throughout
- Add docstrings explaining purpose and usage
- Log chain execution when verbose=True
- Follow existing project conventions

### Output
After implementing, provide:
1. Summary of files changed
2. Test command: `cd backend && .venv/bin/python -m pytest app/tests/test_base_chain.py -v`
3. Any design decisions made
```

---

## Plan Template

Before making changes, Copilot should propose:

1. **Files to modify/create:**
   - [ ] `backend/app/common/base/prompt.py`
   - [ ] `backend/app/common/base/chain.py`
   - [ ] `backend/app/common/base/__init__.py` (update exports)
   - [ ] `backend/app/tests/test_base_chain.py`

2. **High-level steps:**
   - Step 1: ...
   - Step 2: ...

---

## Documentation Template

After changes are complete, provide text for `docs/implementation-log.md`:

```markdown
## Phase 5: Base Chain Implementation

### Summary of Changes
- `backend/app/common/base/prompt.py`: [description]
- `backend/app/common/base/chain.py`: [description]

### Tests Executed
```bash
cd backend && .venv/bin/python -m pytest app/tests/test_base_chain.py -v
```
**Results:** [PASS/FAIL with details]

### Fixes Applied
- [Any issues encountered and how they were resolved]

### Chain Types
| Type | Purpose | Example Use |
|------|---------|-------------|
| LLMChain | Single LLM call | Generate greeting |
| SequentialChain | Multi-step pipeline | Translate then summarize |
| ConditionalChain | Branching logic | Route by intent |
| TransformChain | Data transformation | Parse JSON response |
```

---

## Earlier Mocks to Upgrade
- Uses LLM provider mocks from Phase 3

**Note:** LLM provider is mocked in unit tests. Real LLM integration tested in Phase 18.

---

## Human Checklist
- [ ] Review Copilot's proposed plan before accepting
- [ ] Verify prompt template syntax matches existing patterns
- [ ] Run tests and confirm they pass
- [ ] Test with a simple LLMChain manually
