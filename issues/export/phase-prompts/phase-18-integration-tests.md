# Phase 18: Integration Testing

## Goal
Add integration tests that verify the full stack works together.

---

## Copilot Prompt

```
You are helping add integration tests for a full-stack application.

### Context
- Backend integration tests use real MongoDB (or test containers)
- API integration tests call real endpoints
- Tests are marked with @pytest.mark.integration so they can be skipped in CI
- Frontend E2E tests can use Playwright or be done manually

### Files to Read First
- backend/app/tests/ (existing test patterns)
- backend/app/platforms/hello_world/tests/ (platform tests)

### Implementation Tasks

1. **Create backend integration test in `backend/app/tests/integration/test_hello_world_integration.py`:**
   ```python
   import pytest
   from fastapi.testclient import TestClient
   from app.main import app

   @pytest.mark.integration
   class TestHelloWorldIntegration:
       """Integration tests that call real services."""

       @pytest.fixture
       def client(self):
           return TestClient(app)

       def test_full_greeting_flow(self, client):
           """Test the complete greeting generation flow."""
           # This test calls real LLM if available
           response = client.post(
               "/api/v1/platforms/hello-world/execute",
               json={"name": "Integration Test", "style": "friendly"}
           )

           assert response.status_code == 200
           data = response.json()
           assert data["success"] is True
           assert "greeting" in data
           assert len(data["greeting"]) > 0

       def test_health_check_integration(self, client):
           """Test health endpoint returns correct status."""
           response = client.get("/api/v1/platforms/hello-world/health")

           assert response.status_code == 200
           data = response.json()
           assert "llm_available" in data

       def test_fallback_works(self, client):
           """Test that fallback greetings work when LLM unavailable."""
           # Even if LLM is down, should get a fallback greeting
           response = client.post(
               "/api/v1/platforms/hello-world/execute",
               json={"name": "Fallback Test", "style": "formal"}
           )

           assert response.status_code == 200
           data = response.json()
           # Should succeed even if using fallback
           assert data["success"] is True
   ```

2. **Create pytest configuration in `backend/pytest.ini`:**
   ```ini
   [pytest]
   markers =
       integration: marks tests as integration tests (may require external services)
   asyncio_mode = auto
   ```

3. **Update test commands in documentation:**
   ```bash
   # Run unit tests only (fast, no external deps)
   cd backend && .venv/bin/python -m pytest -m "not integration" -v

   # Run integration tests (requires MongoDB, Ollama)
   cd backend && .venv/bin/python -m pytest -m "integration" -v

   # Run all tests
   cd backend && .venv/bin/python -m pytest -v
   ```

4. **Create manual E2E test checklist:**
   ```markdown
   ## Manual E2E Test Checklist

   ### Prerequisites
   - Backend running: `cd backend && uvicorn app.main:app --reload`
   - Frontend running: `cd frontend && npm run dev`
   - Ollama running: `ollama serve`

   ### Test Cases
   1. [ ] Login with valid credentials -> redirects to home
   2. [ ] Navigate to /hello-world
   3. [ ] Enter name "Alice" with style "friendly" -> get greeting
   4. [ ] Change style to "formal" -> get different greeting
   5. [ ] Stop Ollama -> should see "LLM unavailable" warning
   6. [ ] Generate greeting -> should get fallback greeting
   7. [ ] Logout -> redirects to login
   8. [ ] Try to access /hello-world -> redirects to login
   ```

### Earlier Mocks to Replace
- Phase 2: MongoDB mocks -> real MongoDB (if available)
- Phase 3: LLM mocks -> real Ollama (marked as integration test)
- Phase 9: Service mocks -> real service (in integration tests)

### Output
After implementing, provide:
1. Files created
2. Commands to run tests
3. Test coverage summary
```

---

## Human Checklist
- [ ] Run unit tests pass without external services
- [ ] Run integration tests with services running
- [ ] Complete manual E2E checklist
- [ ] Document any flaky tests
