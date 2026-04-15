# Phase 3: Service & Repository Updates — Implementation Summary

## Overview

Updated the `UserRepository` and `AuthService` layers to support the full approval workflow: status-based queries, approve/reject operations, signed approval tokens, and email notification to the admin.

---

## Changes

### 1. UserRepository (`backend/app/db/repositories/user.py`)

**Updated `create()` method** (done in Phase 1):
- Added `status: str = "approved"` parameter
- Added `platforms: Optional[List[str]] = None` parameter
- Both fields are persisted in the user document

**Added `find_by_status()`**:
```python
async def find_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[dict]
```
- Queries MongoDB for all users matching a given status (`pending`, `approved`, `rejected`)
- Supports pagination via `skip`/`limit`
- Used by the admin panel to list pending users

**Added `set_status()`**:
```python
async def set_status(self, user_id: str, status: str) -> Optional[dict]
```
- Validates status is one of `pending`, `approved`, `rejected`
- Delegates to `update()` which handles `updated_at` timestamp
- Raises `ValueError` for invalid status values

### 2. AuthService (`backend/app/services/auth.py`)

**Updated `create_user()`**:
- Added parameters: `status`, `is_active`, `platforms`
- Passes through to repository's `create()` method
- Backward compatible — defaults remain `status="approved"`, `is_active=True`, `platforms=None`

**Added `approve_user(user_id)`**:
- Sets status to `approved` and `is_active` to `True`
- Two-step operation: `set_status()` then `set_active()`
- Logs the approval with user email

**Added `reject_user(user_id)`**:
- Sets status to `rejected`
- Does not change `is_active` (already `False` for pending users)

**Added `list_users_by_status(status)`**:
- Delegates to `find_by_status()` on the repository

**Added `_create_approval_token(user_id, action)`**:
- Creates a signed JWT with payload: `{sub, action, type: "approval", exp, iat}`
- Token expiration: configurable via `SIGNUP_APPROVAL_TOKEN_EXPIRY_DAYS` (default 7 days)
- `type: "approval"` prevents reuse as an access token

**Added `approve_user_by_token(token)`**:
- Decodes JWT, validates `type == "approval"` and `action == "approve"`
- Calls `approve_user()` with the user ID from the token
- Returns `None` for invalid/expired tokens

**Added `reject_user_by_token(token)`**:
- Same as above but validates `action == "reject"` and calls `reject_user()`

**Added `send_approval_email(user)`**:
- Generates approve/reject tokens via `_create_approval_token()`
- Builds approval URL: `{APP_BASE_URL}/api/v1/auth/approve?token=...`
- Builds rejection URL: `{APP_BASE_URL}/api/v1/auth/reject?token=...`
- Sends HTML email to `SIGNUP_APPROVAL_EMAIL` with:
  - User email, requested platforms, timestamp
  - Green "Approve" button and red "Reject" button
  - Link to admin panel for manual management
  - Token expiry notice
- Uses the existing Resend-based `EmailService` via lazy import
- Graceful degradation: if email service unavailable, logs a warning

### 3. New imports in `auth.py`

- `datetime, timezone` — for token timestamps
- `jose.JWTError, jose.jwt` — for approval token encode/decode
- `List` from typing — for `list_users_by_status` return type

---

## Files Modified

| File | Changes |
|------|---------|
| `backend/app/db/repositories/user.py` | Added `find_by_status()`, `set_status()` |
| `backend/app/services/auth.py` | Updated `create_user()`, added 7 new methods for approval workflow |

---

## Design Decisions

1. **Lazy email import**: `send_approval_email()` imports `get_email_service` inside the method to avoid circular imports and allow the auth service to work even when the newsletter platform's email service is not configured.

2. **Two-step approve**: `approve_user()` calls `set_status()` then `set_active()` as separate operations. This ensures the status is updated even if the active flag update fails.

3. **Token validation**: Both `approve_user_by_token()` and `reject_user_by_token()` check `type == "approval"` to prevent access tokens from being used as approval tokens, and `action` to prevent an approve token from being used for rejection (and vice versa).

4. **Idempotent approve/reject**: Clicking the email link twice is safe — the second call just updates the status to the same value.
