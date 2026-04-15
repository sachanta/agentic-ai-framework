# Phase 6: Base Orchestrator Implementation

## Goal
Implement workflow coordination patterns for orchestrating multiple agents with state management, routing, and parallel execution.

---

## Copilot Prompt

```
You are helping implement orchestrator patterns for coordinating multiple agents in a multi-agent AI framework.

### Context
- Orchestrators coordinate workflows involving multiple agents
- They manage shared state across workflow steps
- Steps can be: agent execution, function calls, or conditions
- Orchestrators can run steps sequentially or in parallel

### Files to Read First
Read these files to understand existing patterns:
- backend/app/common/base/agent.py (agent interface)
- backend/app/common/base/chain.py (chain patterns)
- backend/app/common/base/ (existing orchestrator code, if any)

### Implementation Tasks

1. **Create `backend/app/common/base/workflow.py`:**
   ```python
   from typing import Any, Dict, List, Optional, Callable, Union
   from enum import Enum
   from pydantic import BaseModel

   class StepType(str, Enum):
       AGENT = "agent"
       FUNCTION = "function"
       CONDITION = "condition"
       PARALLEL = "parallel"

   class WorkflowStep(BaseModel):
       """Definition of a single workflow step."""
       name: str
       step_type: StepType
       # For AGENT steps
       agent_name: Optional[str] = None
       # For FUNCTION steps
       function: Optional[Callable] = None
       # For CONDITION steps
       condition: Optional[Callable[[Dict[str, Any]], str]] = None
       branches: Optional[Dict[str, List['WorkflowStep']]] = None
       # For PARALLEL steps
       parallel_steps: Optional[List['WorkflowStep']] = None
       # Input/output mapping
       input_mapping: Optional[Dict[str, str]] = None  # {step_input: state_key}
       output_mapping: Optional[Dict[str, str]] = None  # {step_output: state_key}

       model_config = {"arbitrary_types_allowed": True}

   class WorkflowState(BaseModel):
       """Manages state throughout workflow execution."""
       data: Dict[str, Any] = {}
       history: List[Dict[str, Any]] = []
       current_step: Optional[str] = None
       status: str = "pending"  # pending, running, completed, failed
       error: Optional[str] = None

       def get(self, key: str, default: Any = None) -> Any:
           return self.data.get(key, default)

       def set(self, key: str, value: Any) -> None:
           self.data[key] = value

       def update(self, updates: Dict[str, Any]) -> None:
           self.data.update(updates)

       def add_history(self, step_name: str, input: Dict, output: Dict) -> None:
           self.history.append({
               "step": step_name,
               "input": input,
               "output": output,
           })
   ```

2. **Create `backend/app/common/base/orchestrator.py`:**
   ```python
   from abc import ABC, abstractmethod
   from typing import Any, Dict, List, Optional
   import asyncio
   import logging

   class BaseOrchestrator(ABC):
       """Base class for all orchestrators."""

       def __init__(self, name: str, verbose: bool = False):
           self.name = name
           self.verbose = verbose
           self.agents: Dict[str, BaseAgent] = {}
           self.logger = logging.getLogger(f"orchestrator.{name}")

       def register_agent(self, agent: BaseAgent) -> None:
           """Register an agent with the orchestrator."""
           self.agents[agent.name] = agent

       def get_agent(self, name: str) -> Optional[BaseAgent]:
           """Get a registered agent by name."""
           return self.agents.get(name)

       @abstractmethod
       async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
           """Execute the orchestration workflow."""
           pass

       async def _execute_step(
           self,
           step: WorkflowStep,
           state: WorkflowState
       ) -> Dict[str, Any]:
           """Execute a single workflow step."""
           # Map inputs from state
           # Execute based on step_type
           # Map outputs to state
           pass

   class SimpleOrchestrator(BaseOrchestrator):
       """Orchestrator that routes to a single agent."""

       def __init__(
           self,
           name: str,
           agent: BaseAgent,
           input_mapping: Optional[Dict[str, str]] = None,
           output_mapping: Optional[Dict[str, str]] = None,
           verbose: bool = False,
       ):
           super().__init__(name, verbose)
           self.register_agent(agent)
           self.target_agent = agent.name
           self.input_mapping = input_mapping or {}
           self.output_mapping = output_mapping or {}

       async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
           # Map input, call agent, map output
           pass

   class SequentialOrchestrator(BaseOrchestrator):
       """Orchestrator that runs steps in sequence."""

       def __init__(
           self,
           name: str,
           steps: List[WorkflowStep],
           verbose: bool = False,
       ):
           super().__init__(name, verbose)
           self.steps = steps

       async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
           state = WorkflowState(data=input.copy())
           state.status = "running"

           for step in self.steps:
               state.current_step = step.name
               try:
                   output = await self._execute_step(step, state)
                   state.add_history(step.name, state.data.copy(), output)
                   # Apply output_mapping
                   if step.output_mapping:
                       for out_key, state_key in step.output_mapping.items():
                           if out_key in output:
                               state.set(state_key, output[out_key])
                   else:
                       state.update(output)
               except Exception as e:
                   state.status = "failed"
                   state.error = str(e)
                   raise

           state.status = "completed"
           return state.data

   class ParallelOrchestrator(BaseOrchestrator):
       """Orchestrator that runs steps in parallel."""

       def __init__(
           self,
           name: str,
           steps: List[WorkflowStep],
           verbose: bool = False,
       ):
           super().__init__(name, verbose)
           self.steps = steps

       async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
           state = WorkflowState(data=input.copy())
           state.status = "running"

           # Run all steps concurrently
           tasks = [self._execute_step(step, state) for step in self.steps]
           results = await asyncio.gather(*tasks, return_exceptions=True)

           # Process results
           for step, result in zip(self.steps, results):
               if isinstance(result, Exception):
                   state.status = "failed"
                   state.error = str(result)
                   raise result
               # Merge results into state
               state.update(result)

           state.status = "completed"
           return state.data
   ```

3. **Write unit tests in `backend/app/tests/test_base_orchestrator.py`:**
   - Test SimpleOrchestrator routes to agent correctly
   - Test SequentialOrchestrator runs steps in order
   - Test ParallelOrchestrator runs steps concurrently
   - Test state management (get, set, update)
   - Test input/output mapping
   - Test error handling and state.status updates
   - Test workflow history recording
   - Use mock agents that return predictable outputs
   - Use pytest-asyncio for async tests

### Expected Code Style
- All orchestrator methods should be async
- Use type hints throughout
- Add docstrings explaining purpose and usage
- Log step execution when verbose=True
- Follow existing project conventions

### Output
After implementing, provide:
1. Summary of files changed
2. Test command: `cd backend && .venv/bin/python -m pytest app/tests/test_base_orchestrator.py -v`
3. Any design decisions made
```

---

## Plan Template

Before making changes, Copilot should propose:

1. **Files to modify/create:**
   - [ ] `backend/app/common/base/workflow.py`
   - [ ] `backend/app/common/base/orchestrator.py`
   - [ ] `backend/app/common/base/__init__.py` (update exports)
   - [ ] `backend/app/tests/test_base_orchestrator.py`

2. **High-level steps:**
   - Step 1: ...
   - Step 2: ...

---

## Documentation Template

After changes are complete, provide text for `docs/implementation-log.md`:

```markdown
## Phase 6: Base Orchestrator Implementation

### Summary of Changes
- `backend/app/common/base/workflow.py`: [description]
- `backend/app/common/base/orchestrator.py`: [description]

### Tests Executed
```bash
cd backend && .venv/bin/python -m pytest app/tests/test_base_orchestrator.py -v
```
**Results:** [PASS/FAIL with details]

### Fixes Applied
- [Any issues encountered and how they were resolved]

### Orchestrator Types
| Type | Execution | Use Case |
|------|-----------|----------|
| SimpleOrchestrator | Single agent | Direct routing |
| SequentialOrchestrator | In order | Multi-step pipeline |
| ParallelOrchestrator | Concurrent | Fan-out operations |
```

---

## Earlier Mocks to Upgrade
- Uses agent mocks based on BaseAgent from Phase 4

**Note:** Agents are mocked in unit tests. Real agent integration tested in Phase 11 and 18.

---

## Human Checklist
- [ ] Review Copilot's proposed plan before accepting
- [ ] Verify workflow state management handles edge cases
- [ ] Run tests and confirm they pass
- [ ] Test parallel orchestrator with timing assertions
