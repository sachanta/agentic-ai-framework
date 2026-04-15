# Phase 8: Hello World Service Layer

## Goal
Implement the business logic layer that coordinates the Greeter Agent through an orchestrator pattern.

---

## Copilot Prompt

```
You are helping implement the service layer for the hello_world platform that coordinates agents through orchestration.

### Context
- The service layer sits between API routes and agents
- It uses orchestrators to coordinate workflow execution
- Must handle request validation, transformation, and response formatting
- Should provide graceful degradation on errors

### Files to Read First
Read these files to understand existing patterns:
- backend/app/common/base/orchestrator.py (orchestrator patterns)
- backend/app/platforms/hello_world/agents/greeter/ (Greeter Agent)
- backend/app/platforms/hello_world/ (existing platform code)

### Implementation Tasks

1. **Create `backend/app/platforms/hello_world/orchestrator/workflow.py`:**
   ```python
   from typing import Any, Dict
   from app.common.base.orchestrator import SimpleOrchestrator
   from app.common.base.workflow import WorkflowStep, StepType
   from app.platforms.hello_world.agents.greeter import GreeterAgent

   class HelloWorldOrchestrator(SimpleOrchestrator):
       """Orchestrator for the Hello World greeting workflow."""

       def __init__(self):
           agent = GreeterAgent()
           super().__init__(
               name="hello_world",
               agent=agent,
               input_mapping={
                   "name": "name",
                   "style": "style",
               },
               output_mapping={
                   "greeting": "greeting",
                   "success": "success",
                   "used_fallback": "used_fallback",
               },
               verbose=True,
           )

       async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
           """
           Execute the greeting workflow.

           Args:
               input: {
                   "name": str,
                   "style": str (optional, defaults to "friendly")
               }

           Returns:
               {
                   "success": bool,
                   "greeting": str,
                   "style": str,
                   "used_fallback": bool,
                   "metadata": {...}
               }
           """
           # Set defaults
           processed_input = {
               "name": input.get("name", "Friend"),
               "style": input.get("style", "friendly"),
           }

           # Execute via parent
           result = await super().run(processed_input)

           # Add metadata
           result["metadata"] = {
               "orchestrator": self.name,
               "agent": self.target_agent,
           }

           return result
   ```

2. **Create `backend/app/platforms/hello_world/orchestrator/__init__.py`:**
   ```python
   from .workflow import HelloWorldOrchestrator

   __all__ = ["HelloWorldOrchestrator"]
   ```

3. **Create `backend/app/platforms/hello_world/services/hello_world.py`:**
   ```python
   from typing import Any, Dict, Optional
   import logging
   from datetime import datetime, timezone

   from app.platforms.hello_world.orchestrator import HelloWorldOrchestrator

   logger = logging.getLogger(__name__)

   class HelloWorldService:
       """Service layer for Hello World platform operations."""

       def __init__(self):
           self.orchestrator = HelloWorldOrchestrator()

       async def generate_greeting(
           self,
           name: str,
           style: str = "friendly",
       ) -> Dict[str, Any]:
           """
           Generate a personalized greeting.

           Args:
               name: The name to greet
               style: Greeting style (friendly, formal, casual, enthusiastic)

           Returns:
               {
                   "success": bool,
                   "greeting": str,
                   "style": str,
                   "used_fallback": bool,
                   "timestamp": str,
               }
           """
           logger.info(f"Generating greeting for {name} with style {style}")

           try:
               result = await self.orchestrator.run({
                   "name": name,
                   "style": style,
               })

               return {
                   **result,
                   "timestamp": datetime.now(timezone.utc).isoformat(),
               }

           except Exception as e:
               logger.error(f"Greeting generation failed: {e}")
               return {
                   "success": False,
                   "greeting": f"Hello {name}!",
                   "style": style,
                   "used_fallback": True,
                   "error": str(e),
                   "timestamp": datetime.now(timezone.utc).isoformat(),
               }

       async def get_status(self) -> Dict[str, Any]:
           """Get platform status."""
           return {
               "platform": "hello_world",
               "status": "operational",
               "agents": ["greeter"],
               "timestamp": datetime.now(timezone.utc).isoformat(),
           }

       async def list_agents(self) -> list:
           """List available agents."""
           return [
               {
                   "name": "greeter",
                   "description": "Generates personalized greetings",
                   "styles": ["friendly", "formal", "casual", "enthusiastic"],
               }
           ]

   # Singleton instance
   _service: Optional[HelloWorldService] = None

   def get_hello_world_service() -> HelloWorldService:
       """Get or create the HelloWorldService singleton."""
       global _service
       if _service is None:
           _service = HelloWorldService()
       return _service
   ```

4. **Create `backend/app/platforms/hello_world/services/__init__.py`:**
   ```python
   from .hello_world import HelloWorldService, get_hello_world_service

   __all__ = ["HelloWorldService", "get_hello_world_service"]
   ```

5. **Write unit tests in `backend/app/platforms/hello_world/tests/test_hello_world_service.py`:**
   - Test HelloWorldOrchestrator with mocked GreeterAgent
   - Test HelloWorldService.generate_greeting() success path
   - Test HelloWorldService.generate_greeting() error handling
   - Test HelloWorldService.get_status()
   - Test HelloWorldService.list_agents()
   - Test singleton pattern for get_hello_world_service()
   - Mock the orchestrator/agent to return predictable outputs

### Expected Code Style
- All service methods should be async
- Use type hints throughout
- Add docstrings explaining purpose and usage
- Log important operations
- Use `datetime.now(timezone.utc)` NOT `datetime.utcnow()`
- Follow existing project conventions

### Output
After implementing, provide:
1. Summary of files changed
2. Test command: `cd backend && .venv/bin/python -m pytest app/platforms/hello_world/tests/test_hello_world_service.py -v`
3. Any design decisions made
```

---

## Plan Template

Before making changes, Copilot should propose:

1. **Files to modify/create:**
   - [ ] `backend/app/platforms/hello_world/orchestrator/__init__.py`
   - [ ] `backend/app/platforms/hello_world/orchestrator/workflow.py`
   - [ ] `backend/app/platforms/hello_world/services/__init__.py`
   - [ ] `backend/app/platforms/hello_world/services/hello_world.py`
   - [ ] `backend/app/platforms/hello_world/tests/test_hello_world_service.py`

2. **High-level steps:**
   - Step 1: ...
   - Step 2: ...

---

## Documentation Template

After changes are complete, provide text for `docs/implementation-log.md`:

```markdown
## Phase 8: Hello World Service Layer

### Summary of Changes
- `backend/app/platforms/hello_world/orchestrator/workflow.py`: HelloWorldOrchestrator
- `backend/app/platforms/hello_world/services/hello_world.py`: HelloWorldService

### Tests Executed
```bash
cd backend && .venv/bin/python -m pytest app/platforms/hello_world/tests/test_hello_world_service.py -v
```
**Results:** [PASS/FAIL with details]

### Fixes Applied
- [Any issues encountered and how they were resolved]

### Service Methods
| Method | Input | Output |
|--------|-------|--------|
| generate_greeting | name, style | greeting result |
| get_status | - | platform status |
| list_agents | - | agent list |
```

---

## Earlier Mocks to Upgrade
- Uses GreeterAgent from Phase 7 (mocked in unit tests)
- Uses orchestrator patterns from Phase 6

**Note:** In Phase 18, integration tests will use real agents.

---

## Human Checklist
- [ ] Review Copilot's proposed plan before accepting
- [ ] Verify error handling returns safe fallback
- [ ] Run tests and confirm they pass
- [ ] Test service manually:
  ```python
  service = get_hello_world_service()
  result = await service.generate_greeting("Alice", "enthusiastic")
  print(result)
  ```
