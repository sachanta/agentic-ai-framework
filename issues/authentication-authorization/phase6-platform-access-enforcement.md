# Phase 6: Platform Access Enforcement — Implementation Summary

## Overview

Added a `require_platform` dependency guard to the security module and applied it to platform-specific routes that require authentication. This enforces that users can only access platforms they were granted access to during signup.

---

## Changes

### 1. Security Module (`backend/app/core/security.py`)

Added `require_platform(platform_id)` factory function:

```python
def require_platform(platform_id: str):
    async def check_platform(current_user: dict = Depends(get_current_user)) -> dict:
        # Admin always has access
        if current_user.get("role") == "admin":
            return current_user
        # Empty list = unrestricted (backward compat)
        user_platforms = current_user.get("platforms", [])
        if not user_platforms:
            return current_user
        if platform_id not in user_platforms:
            raise HTTPException(403, f"You don't have access to the {platform_id} platform")
        return current_user
    return check_platform
```

**Access logic:**
| User type | `platforms` value | Result |
|-----------|------------------|--------|
| Admin | any | Always passes |
| Existing user | `[]` (empty) | Passes (unrestricted, backward compat) |
| New user | `["newsletter"]` | Passes for newsletter, blocked for hello_world |
| New user | `["newsletter", "hello_world"]` | Passes for both |

### 2. Newsletter Router (`backend/app/platforms/newsletter/router.py`)

Applied `require_platform("newsletter")` to:
- `POST /generate` — newsletter generation endpoint

Added `require_platform` to imports from `app.core.security`.

### 3. Hello World Router (`backend/app/platforms/hello_world/router.py`)

Applied `require_platform("hello_world")` to:
- `POST /execute` — greeting execution endpoint
- `POST /agents/greeter/run` — direct agent run endpoint

Added `require_platform` to imports from `app.core.security`.

---

## Files Modified

| File | Changes |
|------|---------|
| `backend/app/core/security.py` | Added `require_platform()` dependency factory |
| `backend/app/platforms/newsletter/router.py` | Applied platform guard to `/generate` |
| `backend/app/platforms/hello_world/router.py` | Applied platform guard to `/execute` and `/agents/greeter/run` |

---

## Design Decisions

1. **Read-only endpoints unguarded**: Status, config, health, and agent listing endpoints are not guarded by `require_platform`. Only mutation/execution endpoints require platform access. This allows the UI to show platform information even if the user doesn't have access.

2. **Additive guard**: `require_platform` is used as a `dependencies=[...]` parameter alongside the existing `get_current_user` dependency, so authentication is still checked first.

3. **Backward compatibility**: Users with `platforms: []` (empty list) have unrestricted access. This preserves behavior for admin accounts and any users created before the platform access feature.
