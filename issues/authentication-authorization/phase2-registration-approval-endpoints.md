# Phase 2: Registration & Approval Endpoints — Implementation Summary

## Overview

Updated the auth endpoints to implement the full registration-with-approval flow: signup creates a pending user, login checks status, and admin can approve/reject via API or one-click email links.

---

## Changes

### File: `backend/app/api/v1/endpoints/auth.py`

#### Schema Updates

**`UserResponse`** — added `status` and `platforms` fields:
```python
status: str = "approved"
platforms: List[str] = []
```

**`RegisterRequest`** — changed to accept email + password + platforms (email IS the username):
```python
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    platforms: List[str] = []
```

**`RegisterResponse`** — new schema for registration response:
```python
class RegisterResponse(BaseModel):
    message: str
    status: str
```

**`_user_to_response()`** — updated to include `status` and `platforms` in the response.

#### New Imports

- `settings` from `app.config` — for `SIGNUP_AVAILABLE_PLATFORMS` validation
- `require_admin` from `app.core.security` — for admin-only endpoints
- `List` from `typing` — for response models

#### Login Status Check

**`_check_user_status_on_login_failure()`** — new helper function:
- Called when `authenticate_user()` returns `None`
- Looks up the user by username to check their status
- If status is `pending` → raises HTTP 403 with "Your account is pending admin approval."
- If status is `rejected` → raises HTTP 403 with "Your account request was not approved."
- If user doesn't exist or is approved → falls through to the normal 401 error

Applied to both `POST /login` (OAuth2 form) and `POST /login/json` (JSON body).

#### Updated Registration Endpoint

**`POST /register`** — complete rewrite:
1. Validates platform IDs against `SIGNUP_AVAILABLE_PLATFORMS` config
2. Creates user with `status="pending"`, `is_active=False`, `username=email`
3. Sends approval email to admin (non-blocking — registration succeeds even if email fails)
4. Returns `RegisterResponse` with message and status

Response model changed from `UserResponse` to `RegisterResponse` since pending users don't need full user details exposed.

#### New Public Endpoints (signed token)

**`GET /auth/approve?token=xxx`**:
- Decodes the signed JWT approval token
- Calls `approve_user_by_token()` → sets status=approved, is_active=true
- Returns success message with user's email
- Returns 400 for invalid/expired tokens

**`GET /auth/reject?token=xxx`**:
- Same as above but for rejection
- Calls `reject_user_by_token()` → sets status=rejected

#### New Admin Endpoints

**`GET /auth/admin/users/pending`** (admin only):
- Lists all users with `status=pending`
- Returns `List[UserResponse]`
- Protected by `require_admin` dependency

**`POST /auth/admin/users/{user_id}/approve`** (admin only):
- Approves a pending user by ID
- Sets status=approved, is_active=true
- Returns 404 if user not found

**`POST /auth/admin/users/{user_id}/reject`** (admin only):
- Rejects a pending user by ID
- Sets status=rejected
- Returns 404 if user not found

---

## Endpoint Summary

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/login` | None | Login (OAuth2 form) — now checks pending/rejected status |
| POST | `/auth/login/json` | None | Login (JSON) — now checks pending/rejected status |
| POST | `/auth/register` | None | Register — creates pending user, sends approval email |
| GET | `/auth/approve?token=` | None (signed token) | One-click approval from email |
| GET | `/auth/reject?token=` | None (signed token) | One-click rejection from email |
| GET | `/auth/admin/users/pending` | Admin | List pending users |
| POST | `/auth/admin/users/{id}/approve` | Admin | Approve user |
| POST | `/auth/admin/users/{id}/reject` | Admin | Reject user |
| POST | `/auth/logout` | User | Logout (unchanged) |
| GET | `/auth/me` | User | Get current user (now includes status/platforms) |
| POST | `/auth/refresh` | User | Refresh token (now includes status/platforms) |
| POST | `/auth/change-password` | User | Change password (unchanged) |

---

## Design Decisions

1. **Email as username**: The `register` endpoint sets `username=email`. The plan specifies that users sign up with their email as the username.

2. **Non-blocking email**: If `send_approval_email()` fails, registration still succeeds. The admin can still approve via the admin panel.

3. **Platform validation from config**: Valid platforms come from `SIGNUP_AVAILABLE_PLATFORMS` setting (comma-separated), making it easy to add new platforms without code changes.

4. **Status check on login failure**: Instead of modifying `authenticate()` (which would break the separation of concerns), we check status as a secondary step only when authentication fails. This preserves backward compatibility.

5. **Admin endpoints under auth router**: The admin user management endpoints are mounted at `/auth/admin/users/...` rather than creating a separate router, keeping all user/auth operations in one place.
