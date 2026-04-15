# Phase 19: Observability & Metrics

## Goal
Add basic monitoring, health checks, and request tracing.

---

## Copilot Prompt

```
You are helping add observability features to a FastAPI application.

### Context
- Health check endpoints for liveness/readiness probes
- Request timing and basic metrics
- Correlation IDs for request tracing
- Keep it simple - no external monitoring services required

### Files to Read First
- backend/app/main.py (app setup)
- backend/app/common/middleware.py (existing middleware)
- backend/app/common/logging.py (logging setup)

### Implementation Tasks

1. **Create health endpoints in `backend/app/api/v1/health.py`:**
   ```python
   from fastapi import APIRouter
   from datetime import datetime, timezone

   router = APIRouter(tags=["Health"])

   @router.get("/health/live")
   async def liveness():
       """Liveness probe - is the app running?"""
       return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}

   @router.get("/health/ready")
   async def readiness():
       """Readiness probe - is the app ready to serve traffic?"""
       # Could check database, LLM availability, etc.
       return {"status": "ready", "timestamp": datetime.now(timezone.utc).isoformat()}
   ```

2. **Add request timing to middleware in `backend/app/common/middleware.py`:**
   ```python
   import time

   class TimingMiddleware(BaseHTTPMiddleware):
       """Add request timing to response headers."""

       async def dispatch(self, request: Request, call_next):
           start = time.time()
           response = await call_next(request)
           duration = time.time() - start

           response.headers["X-Response-Time"] = f"{duration:.3f}s"
           return response
   ```

3. **Create simple metrics endpoint in `backend/app/api/v1/metrics.py`:**
   ```python
   from fastapi import APIRouter
   from datetime import datetime, timezone

   router = APIRouter(tags=["Metrics"])

   # Simple in-memory counters (use Redis/Prometheus in production)
   _metrics = {
       "requests_total": 0,
       "errors_total": 0,
       "start_time": datetime.now(timezone.utc).isoformat(),
   }

   def increment_request():
       _metrics["requests_total"] += 1

   def increment_error():
       _metrics["errors_total"] += 1

   @router.get("/metrics")
   async def get_metrics():
       """Get basic application metrics."""
       return {
           **_metrics,
           "uptime_seconds": (datetime.now(timezone.utc) - datetime.fromisoformat(_metrics["start_time"].replace('Z', '+00:00'))).total_seconds(),
       }
   ```

4. **Update middleware to track metrics:**
   ```python
   from app.api.v1.metrics import increment_request, increment_error

   # In RequestLoggingMiddleware.dispatch:
   increment_request()
   if response.status_code >= 400:
       increment_error()
   ```

5. **Add correlation ID helper:**
   ```python
   # Already in logging.py, ensure it's used consistently:
   # - Set on request entry
   # - Include in all log messages
   # - Return in X-Correlation-ID header
   ```

### Output
After implementing, provide:
1. Files created/updated
2. Endpoints added
3. How to test observability features
```

---

## Human Checklist
- [ ] Test /health/live returns 200
- [ ] Test /health/ready returns 200
- [ ] Verify X-Response-Time header in responses
- [ ] Verify X-Correlation-ID header in responses
- [ ] Test /metrics returns counters
