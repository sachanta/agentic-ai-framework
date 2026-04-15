# Phase 1: Backend Model & Schema Changes + Migration

## Summary

Added `status` and `platforms` fields to the user model across backend and frontend, plus a startup migration to backfill existing users. Added signup/approval configuration settings.

## Changes

### 1. `backend/app/models/user.py` (Modified)

Added two fields to the `User` model:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `status` | `str` | `"approved"` | User approval status: `"pending"`, `"approved"`, or `"rejected"` |
| `platforms` | `List[str]` | `[]` | Platform IDs the user has access to. Empty list = unrestricted access |

Default of `"approved"` ensures existing code creating users continues to work without changes.

### 2. `backend/app/schemas/auth.py` (Modified)

- **`UserCreate`**: Added `platforms: List[str] = []` field
- **`UserResponse`**: Added `status: str = "approved"` and `platforms: List[str] = []` fields

### 3. `frontend/src/types/auth.ts` (Modified)

- Added `UserStatus` type: `'pending' | 'approved' | 'rejected'`
- Added `status: UserStatus` and `platforms: string[]` to `User` interface
- Added `RegisterRequest` interface: `{email, password, platforms}`
- Added `RegisterResponse` interface: `{message, status}`

### 4. `backend/app/config.py` (Modified)

Added new settings:

| Setting | Default | Description |
|---------|---------|-------------|
| `SIGNUP_APPROVAL_EMAIL` | `achantas@gmail.com` | Admin email for signup notifications |
| `APP_BASE_URL` | `http://localhost:8000` | Base URL for approval links in emails |
| `SIGNUP_APPROVAL_TOKEN_EXPIRY_DAYS` | `7` | How long approval links stay valid |
| `SIGNUP_AVAILABLE_PLATFORMS` | `newsletter,hello_world` | Platforms available for signup selection |

### 5. `backend/app/db/mongodb.py` (Modified)

- Default admin and user accounts now include `status: "approved"` and `platforms: []`
- Added backfill migration at end of `init_default_data()`:
  ```python
  await users.update_many(
      {"status": {"$exists": False}},
      {"$set": {"status": "approved", "platforms": []}},
  )
  ```
  This runs on every startup and is idempotent — it only modifies users that don't yet have a `status` field.

## Backward Compatibility

- Existing users get `status: "approved"` and `platforms: []` via migration (unrestricted access)
- All existing login/auth flows work unchanged (approved + is_active users behave identically)
- Frontend `User` type changes are additive (new optional-like fields with defaults)
