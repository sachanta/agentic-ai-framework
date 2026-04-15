# Phase 11: Backend Unit Tests

## Goal
Add comprehensive unit test coverage for all backend components with consistent mocking patterns.

---

## Copilot Prompt

```
You are helping add unit tests for a FastAPI backend. Focus on high-value tests with simple mocking.

### Context
- Tests use pytest and pytest-asyncio
- Run tests from backend directory: `cd backend && .venv/bin/python -m pytest`
- Mock external dependencies (LLM, database) for fast, deterministic tests
- Use `>=` for score comparisons, `pytest.approx()` for floats

### Files to Read First
- backend/app/platforms/hello_world/ (code to test)
- backend/app/tests/ (existing test patterns)

### Implementation Tasks

1. **Create test fixtures in `backend/app/tests/conftest.py`:**
   ```python
   import pytest
   from unittest.mock import AsyncMock, MagicMock

   @pytest.fixture
   def mock_llm_provider():
       """Mock LLM provider that returns predictable responses."""
       mock = MagicMock()
       mock.generate = AsyncMock(return_value="Hello, Test User! Welcome!")
       mock.health_check = AsyncMock(return_value=True)
       return mock

   @pytest.fixture
   def mock_mongodb():
       """Mock MongoDB client."""
       mock = MagicMock()
       mock.health_check = AsyncMock(return_value=True)
       return mock
   ```

2. **Test the Greeter Agent in `backend/app/platforms/hello_world/tests/test_greeter.py`:**
   ```python
   import pytest
   from unittest.mock import patch, AsyncMock

   @pytest.mark.asyncio
   async def test_greeter_generates_greeting():
       """Test that greeter agent generates a greeting."""
       with patch("app.platforms.hello_world.agents.greeter.llm.get_llm_provider") as mock:
           mock.return_value.generate = AsyncMock(return_value="Hello Alice!")

           from app.platforms.hello_world.agents.greeter import GreeterAgent
           agent = GreeterAgent()
           result = await agent.run({"name": "Alice", "style": "friendly"})

           assert result["success"] is True
           assert "greeting" in result

   @pytest.mark.asyncio
   async def test_greeter_fallback_on_error():
       """Test fallback when LLM fails."""
       # Test implementation
   ```

3. **Test the API routes in `backend/app/platforms/hello_world/tests/test_api.py`:**
   ```python
   import pytest
   from fastapi.testclient import TestClient
   from unittest.mock import patch, AsyncMock

   def test_execute_endpoint_returns_greeting():
       """Test POST /execute returns a greeting."""
       with patch("app.platforms.hello_world.router.get_hello_world_service") as mock:
           mock.return_value.generate_greeting = AsyncMock(return_value={
               "success": True,
               "greeting": "Hello!",
               "style": "friendly",
               "used_fallback": False,
               "timestamp": "2024-01-01T00:00:00Z",
           })

           from app.main import app
           client = TestClient(app)
           response = client.post(
               "/api/v1/platforms/hello-world/execute",
               json={"name": "Alice", "style": "friendly"}
           )

           assert response.status_code == 200
           assert response.json()["success"] is True

   def test_health_endpoint():
       """Test GET /health returns status."""
       # Test implementation
   ```

4. **Run all tests:**
   ```bash
   cd backend && .venv/bin/python -m pytest app/platforms/hello_world/tests/ -v
   ```

### Tips for Copilot
- Keep tests simple and focused on one behavior
- Use descriptive test names that explain what is being tested
- Mock at the boundary (service or provider level)
- Don't test framework code (FastAPI, Pydantic)

### Output
After implementing, provide:
1. List of test files created/updated
2. Test command to run
3. Expected coverage areas
```

---

## Human Checklist
- [ ] Review test coverage for critical paths
- [ ] Run tests and verify all pass
- [ ] Check that mocks are at appropriate level
