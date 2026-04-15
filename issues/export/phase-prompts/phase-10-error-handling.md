# Phase 10: Backend Error Handling & Logging

## Goal
Implement structured logging and comprehensive error handling middleware for the backend.

---

## Copilot Prompt

```
You are helping implement error handling and logging for a FastAPI backend in a multi-agent AI framework.

### Context
- Need structured JSON logging for production observability
- Custom exception classes for different error types
- Global exception handler middleware
- Request/response logging with correlation IDs
- Sensitive data must be sanitized from logs

### Files to Read First
Read these files to understand existing patterns:
- backend/app/main.py (FastAPI app setup)
- backend/app/config.py (logging configuration)
- backend/app/common/ (existing common code)

### Implementation Tasks

1. **Create `backend/app/common/exceptions.py`:**
   ```python
   from typing import Any, Dict, Optional

   class BaseAppException(Exception):
       """Base exception for all application errors."""

       def __init__(
           self,
           message: str,
           error_code: str = "INTERNAL_ERROR",
           details: Optional[Dict[str, Any]] = None,
           status_code: int = 500,
       ):
           self.message = message
           self.error_code = error_code
           self.details = details or {}
           self.status_code = status_code
           super().__init__(message)

       def to_dict(self) -> Dict[str, Any]:
           return {
               "error": self.error_code,
               "message": self.message,
               "details": self.details,
           }

   class ValidationError(BaseAppException):
       """Raised when input validation fails."""
       def __init__(self, message: str, details: Optional[Dict] = None):
           super().__init__(
               message=message,
               error_code="VALIDATION_ERROR",
               details=details,
               status_code=400,
           )

   class NotFoundError(BaseAppException):
       """Raised when a resource is not found."""
       def __init__(self, resource: str, identifier: str):
           super().__init__(
               message=f"{resource} not found: {identifier}",
               error_code="NOT_FOUND",
               details={"resource": resource, "identifier": identifier},
               status_code=404,
           )

   class LLMError(BaseAppException):
       """Raised when LLM operations fail."""
       def __init__(self, message: str, provider: str, details: Optional[Dict] = None):
           super().__init__(
               message=message,
               error_code="LLM_ERROR",
               details={"provider": provider, **(details or {})},
               status_code=503,
           )

   class AgentError(BaseAppException):
       """Raised when agent execution fails."""
       def __init__(self, agent_name: str, message: str, details: Optional[Dict] = None):
           super().__init__(
               message=message,
               error_code="AGENT_ERROR",
               details={"agent": agent_name, **(details or {})},
               status_code=500,
           )

   class ConfigurationError(BaseAppException):
       """Raised when configuration is invalid."""
       def __init__(self, message: str, config_key: Optional[str] = None):
           super().__init__(
               message=message,
               error_code="CONFIGURATION_ERROR",
               details={"config_key": config_key} if config_key else {},
               status_code=500,
           )
   ```

2. **Create `backend/app/common/logging.py`:**
   ```python
   import logging
   import json
   import sys
   from typing import Any, Dict
   from datetime import datetime, timezone
   import uuid
   from contextvars import ContextVar

   # Context variable for request correlation
   correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")

   def get_correlation_id() -> str:
       return correlation_id_var.get() or str(uuid.uuid4())

   def set_correlation_id(correlation_id: str) -> None:
       correlation_id_var.set(correlation_id)

   class JSONFormatter(logging.Formatter):
       """JSON log formatter for structured logging."""

       SENSITIVE_KEYS = {"password", "token", "api_key", "secret", "authorization"}

       def format(self, record: logging.LogRecord) -> str:
           log_data = {
               "timestamp": datetime.now(timezone.utc).isoformat(),
               "level": record.levelname,
               "logger": record.name,
               "message": record.getMessage(),
               "correlation_id": get_correlation_id(),
           }

           # Add exception info if present
           if record.exc_info:
               log_data["exception"] = self.formatException(record.exc_info)

           # Add extra fields
           if hasattr(record, "extra_data"):
               log_data["data"] = self._sanitize(record.extra_data)

           return json.dumps(log_data)

       def _sanitize(self, data: Any) -> Any:
           """Remove sensitive information from log data."""
           if isinstance(data, dict):
               return {
                   k: "***REDACTED***" if k.lower() in self.SENSITIVE_KEYS else self._sanitize(v)
                   for k, v in data.items()
               }
           elif isinstance(data, list):
               return [self._sanitize(item) for item in data]
           return data

   def setup_logging(level: str = "INFO", json_format: bool = True) -> None:
       """Configure application logging."""
       root_logger = logging.getLogger()
       root_logger.setLevel(getattr(logging, level.upper()))

       # Remove existing handlers
       for handler in root_logger.handlers[:]:
           root_logger.removeHandler(handler)

       # Add console handler
       console_handler = logging.StreamHandler(sys.stdout)
       if json_format:
           console_handler.setFormatter(JSONFormatter())
       else:
           console_handler.setFormatter(
               logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
           )
       root_logger.addHandler(console_handler)

   class LoggerAdapter(logging.LoggerAdapter):
       """Logger adapter that includes correlation ID and extra data."""

       def process(self, msg, kwargs):
           extra = kwargs.get("extra", {})
           extra["correlation_id"] = get_correlation_id()
           kwargs["extra"] = extra
           return msg, kwargs
   ```

3. **Create `backend/app/common/middleware.py`:**
   ```python
   import time
   import uuid
   import logging
   from typing import Callable
   from fastapi import Request, Response
   from fastapi.responses import JSONResponse
   from starlette.middleware.base import BaseHTTPMiddleware

   from .logging import set_correlation_id, get_correlation_id
   from .exceptions import BaseAppException

   logger = logging.getLogger(__name__)

   class RequestLoggingMiddleware(BaseHTTPMiddleware):
       """Middleware for request/response logging."""

       async def dispatch(self, request: Request, call_next: Callable) -> Response:
           # Set correlation ID
           correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
           set_correlation_id(correlation_id)

           # Log request
           start_time = time.time()
           logger.info(
               f"Request started: {request.method} {request.url.path}",
               extra={"extra_data": {
                   "method": request.method,
                   "path": request.url.path,
                   "query": str(request.query_params),
               }},
           )

           try:
               response = await call_next(request)

               # Log response
               duration = time.time() - start_time
               logger.info(
                   f"Request completed: {response.status_code}",
                   extra={"extra_data": {
                       "status_code": response.status_code,
                       "duration_ms": round(duration * 1000, 2),
                   }},
               )

               # Add correlation ID to response
               response.headers["X-Correlation-ID"] = correlation_id
               return response

           except Exception as e:
               duration = time.time() - start_time
               logger.error(
                   f"Request failed: {str(e)}",
                   exc_info=True,
                   extra={"extra_data": {"duration_ms": round(duration * 1000, 2)}},
               )
               raise

   async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
       """Global exception handler for unhandled exceptions."""
       correlation_id = get_correlation_id()

       if isinstance(exc, BaseAppException):
           logger.warning(
               f"Application error: {exc.error_code}",
               extra={"extra_data": exc.to_dict()},
           )
           return JSONResponse(
               status_code=exc.status_code,
               content={
                   **exc.to_dict(),
                   "correlation_id": correlation_id,
               },
           )

       # Unhandled exception
       logger.error(
           f"Unhandled exception: {str(exc)}",
           exc_info=True,
       )
       return JSONResponse(
           status_code=500,
           content={
               "error": "INTERNAL_ERROR",
               "message": "An unexpected error occurred",
               "correlation_id": correlation_id,
           },
       )
   ```

4. **Update `backend/app/main.py`:**
   ```python
   from app.common.logging import setup_logging
   from app.common.middleware import RequestLoggingMiddleware, exception_handler
   from app.common.exceptions import BaseAppException

   # Setup logging early
   setup_logging(level=settings.LOG_LEVEL, json_format=not settings.DEBUG)

   # Add middleware
   app.add_middleware(RequestLoggingMiddleware)

   # Add exception handlers
   app.add_exception_handler(BaseAppException, exception_handler)
   app.add_exception_handler(Exception, exception_handler)
   ```

5. **Write unit tests in `backend/app/tests/test_error_handling.py`:**
   - Test custom exception classes
   - Test exception_handler returns correct responses
   - Test logging middleware adds correlation IDs
   - Test sensitive data is sanitized from logs
   - Test JSON formatter output

### Expected Code Style
- Use `datetime.now(timezone.utc)` NOT `datetime.utcnow()`
- Add type hints throughout
- Document all exception classes
- Follow existing project conventions

### Output
After implementing, provide:
1. Summary of files changed
2. Test command: `cd backend && .venv/bin/python -m pytest app/tests/test_error_handling.py -v`
3. Any design decisions made
```

---

## Plan Template

Before making changes, Copilot should propose:

1. **Files to modify/create:**
   - [ ] `backend/app/common/exceptions.py`
   - [ ] `backend/app/common/logging.py`
   - [ ] `backend/app/common/middleware.py`
   - [ ] `backend/app/main.py` (add middleware and handlers)
   - [ ] `backend/app/config.py` (add LOG_LEVEL setting)
   - [ ] `backend/app/tests/test_error_handling.py`

2. **High-level steps:**
   - Step 1: ...
   - Step 2: ...

---

## Documentation Template

After changes are complete, provide text for `docs/implementation-log.md`:

```markdown
## Phase 10: Backend Error Handling & Logging

### Summary of Changes
- `backend/app/common/exceptions.py`: Custom exception classes
- `backend/app/common/logging.py`: Structured JSON logging
- `backend/app/common/middleware.py`: Request logging middleware

### Exception Types
| Exception | Code | HTTP Status |
|-----------|------|-------------|
| ValidationError | VALIDATION_ERROR | 400 |
| NotFoundError | NOT_FOUND | 404 |
| LLMError | LLM_ERROR | 503 |
| AgentError | AGENT_ERROR | 500 |

### Tests Executed
```bash
cd backend && .venv/bin/python -m pytest app/tests/test_error_handling.py -v
```
**Results:** [PASS/FAIL with details]

### Fixes Applied
- [Any issues encountered and how they were resolved]
```

---

## Earlier Mocks to Upgrade
- Update Phase 9 API tests to verify error responses use new exception format

**Note:** Verify existing tests still pass after adding middleware.

---

## Human Checklist
- [ ] Review Copilot's proposed plan before accepting
- [ ] Verify sensitive data is properly sanitized
- [ ] Run tests and confirm they pass
- [ ] Test correlation ID propagation manually
