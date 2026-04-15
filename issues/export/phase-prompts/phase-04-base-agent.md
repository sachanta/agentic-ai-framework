# Phase 4: Base Agent Implementation

## Goal
Implement the foundational agent class with memory, tools interface, and execution patterns that all agents will extend.

---

## Copilot Prompt

```
You are helping implement the base agent abstraction for a multi-agent AI framework.

### Context
- Agents are the core building blocks that interact with LLMs
- Each agent has a name, LLM provider, system prompt, and optional tools
- Agents can be stateless (SimpleAgent) or conversational (with memory)
- IMPORTANT: `self.memory`, `self.llm`, and `self.name` are reserved attributes in BaseAgent - do not override these in subclasses

### Files to Read First
Read these files to understand existing patterns:
- backend/app/common/providers/llm.py (LLM provider interface)
- backend/app/common/base/ (existing base classes, if any)

### Implementation Tasks

1. **Create `backend/app/common/base/memory.py`:**
   ```python
   from typing import List, Dict, Any, Optional
   from pydantic import BaseModel

   class Message(BaseModel):
       role: str  # "user", "assistant", "system"
       content: str
       metadata: Optional[Dict[str, Any]] = None

   class AgentMemory:
       """Manages conversation history for an agent."""

       def __init__(self, max_messages: int = 100):
           self.max_messages = max_messages
           self._messages: List[Message] = []

       def add_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> None:
           """Add a message to memory."""
           # Implement with size limit enforcement
           pass

       def get_messages(self, limit: Optional[int] = None) -> List[Message]:
           """Get recent messages."""
           pass

       def get_context_string(self) -> str:
           """Format messages as a string for LLM context."""
           pass

       def clear(self) -> None:
           """Clear all messages."""
           pass

       def to_dict(self) -> List[Dict[str, Any]]:
           """Export messages as dictionaries."""
           pass
   ```

2. **Create `backend/app/common/base/tool.py`:**
   ```python
   from abc import ABC, abstractmethod
   from typing import Any, Dict, Optional, Callable
   from pydantic import BaseModel

   class ToolParameter(BaseModel):
       name: str
       type: str
       description: str
       required: bool = True

   class ToolDefinition(BaseModel):
       name: str
       description: str
       parameters: List[ToolParameter] = []

   class BaseTool(ABC):
       """Base class for agent tools."""

       def __init__(self, name: str, description: str):
           self.name = name
           self.description = description

       @abstractmethod
       async def execute(self, **kwargs) -> Any:
           """Execute the tool with given parameters."""
           pass

       def get_definition(self) -> ToolDefinition:
           """Get tool definition for LLM."""
           pass

   class FunctionTool(BaseTool):
       """Tool wrapper for simple functions."""

       def __init__(self, name: str, description: str, func: Callable):
           super().__init__(name, description)
           self.func = func

       async def execute(self, **kwargs) -> Any:
           # Handle both sync and async functions
           pass
   ```

3. **Create `backend/app/common/base/agent.py`:**
   ```python
   from abc import ABC, abstractmethod
   from typing import Any, Dict, List, Optional
   import logging

   class BaseAgent(ABC):
       """
       Base class for all agents.

       IMPORTANT: Do not override these attributes in subclasses:
       - self.name
       - self.llm
       - self.memory
       """

       def __init__(
           self,
           name: str,
           llm: BaseLLMProvider,
           system_prompt: str = "",
           tools: Optional[List[BaseTool]] = None,
           memory: Optional[AgentMemory] = None,
       ):
           self.name = name
           self.llm = llm
           self.system_prompt = system_prompt
           self.tools = tools or []
           self.memory = memory
           self.logger = logging.getLogger(f"agent.{name}")

       @abstractmethod
       async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
           """
           Execute the agent's main logic.

           Args:
               input: Dictionary containing input parameters

           Returns:
               Dictionary containing output results
           """
           pass

       async def _build_prompt(self, user_input: str) -> str:
           """Build the full prompt including system prompt and memory."""
           pass

       async def _call_llm(self, prompt: str, **kwargs) -> str:
           """Call the LLM with the given prompt."""
           pass

       def _get_tool(self, name: str) -> Optional[BaseTool]:
           """Get a tool by name."""
           pass

       async def _execute_tool(self, name: str, **kwargs) -> Any:
           """Execute a tool by name."""
           pass

   class SimpleAgent(BaseAgent):
       """Agent for stateless, single-turn operations."""

       async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
           # Implementation for simple prompt -> response
           pass

   class ConversationalAgent(BaseAgent):
       """Agent with conversation memory for multi-turn interactions."""

       def __init__(self, *args, **kwargs):
           super().__init__(*args, **kwargs)
           if self.memory is None:
               self.memory = AgentMemory()

       async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
           # Implementation with memory management
           pass

       async def reset_conversation(self) -> None:
           """Clear conversation history."""
           pass
   ```

4. **Write unit tests in `backend/app/tests/test_base_agent.py`:**
   - Test AgentMemory message management
   - Test SimpleAgent execution with mocked LLM
   - Test ConversationalAgent memory persistence
   - Test tool registration and execution
   - Test error handling (LLM failure, tool failure)
   - Use pytest-asyncio for async tests
   - Mock LLM provider responses

### Expected Code Style
- All agent methods should be async
- Use type hints throughout
- Add docstrings explaining the purpose and usage
- Log important operations (prompt building, LLM calls, tool execution)
- Follow existing project conventions

### Important Notes
- `self.memory` is for conversation history, NOT for caching services
- When creating custom agents, use different attribute names for custom services (e.g., `self.cache_service`)
- The `run()` method must be implemented by all subclasses

### Output
After implementing, provide:
1. Summary of files changed
2. Test command: `cd backend && .venv/bin/python -m pytest app/tests/test_base_agent.py -v`
3. Any design decisions made
```

---

## Plan Template

Before making changes, Copilot should propose:

1. **Files to modify/create:**
   - [ ] `backend/app/common/base/__init__.py`
   - [ ] `backend/app/common/base/memory.py`
   - [ ] `backend/app/common/base/tool.py`
   - [ ] `backend/app/common/base/agent.py`
   - [ ] `backend/app/tests/test_base_agent.py`

2. **High-level steps:**
   - Step 1: ...
   - Step 2: ...

---

## Documentation Template

After changes are complete, provide text for `docs/implementation-log.md`:

```markdown
## Phase 4: Base Agent Implementation

### Summary of Changes
- `backend/app/common/base/memory.py`: [description]
- `backend/app/common/base/tool.py`: [description]
- `backend/app/common/base/agent.py`: [description]

### Tests Executed
```bash
cd backend && .venv/bin/python -m pytest app/tests/test_base_agent.py -v
```
**Results:** [PASS/FAIL with details]

### Fixes Applied
- [Any issues encountered and how they were resolved]

### Agent Types
| Type | Memory | Use Case |
|------|--------|----------|
| SimpleAgent | No | Single-turn operations |
| ConversationalAgent | Yes | Multi-turn chat |
```

---

## Earlier Mocks to Upgrade
- None directly, but uses LLM provider from Phase 3

**Note:** LLM provider is mocked in unit tests. Real LLM integration tested in Phase 18.

---

## Human Checklist
- [ ] Review Copilot's proposed plan before accepting
- [ ] Verify base class doesn't have conflicting attribute names
- [ ] Run tests and confirm they pass
- [ ] Document reserved attribute names for future developers
