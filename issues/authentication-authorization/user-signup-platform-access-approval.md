# User Signup with Platform Access & Admin Approval

## Summary

Extend the authentication system to allow new users to sign up from the UI. At signup, users provide their email (used as username), password, and select which platform(s) they want access to (e.g. "newsletter"). The account is created in a **pending** state. An approval email is sent to `achantas@gmail.com`. The admin approves or rejects the user via a link in the email or from an admin panel. Only approved users can log in.

---

## Current State

### What exists today

| Layer | Component | Status |
|-------|-----------|--------|
| Backend | `POST /api/v1/auth/register` endpoint | Exists but creates active users immediately with no platform scoping |
| Backend | `User` model (`app/models/user.py`) | Has `username`, `email`, `role`, `is_active` — no `status` or `platforms` fields |
| Backend | `UserRepository` (`app/db/repositories/user.py`) | Full CRUD, `set_active()`, `change_role()` — no approval or platform methods |
| Backend | `AuthService` (`app/services/auth.py`) | `create_user()`, `activate_user()`, `deactivate_user()` — no approval workflow |
| Backend | Email service (`app/platforms/newsletter/services/email.py`) | Resend-based email sending — can be reused for approval emails |
| Frontend | `LoginPage` + `LoginForm` | Login only — no signup link, no registration form |
| Frontend | `authStore` (Zustand) | Manages `user`, `token`, `isAuthenticated` — no signup method |
| Frontend | `auth.ts` API client | `login`, `logout`, `getCurrentUser`, `refreshToken` — no `register` |
| Frontend | User types (`types/auth.ts`) | `User` has `role`, `is_active` — no `status` or `platforms` fields |

### What needs to change

1. **User model** — add `status` (pending/approved/rejected) and `platforms` (list of platform IDs)
2. **Registration endpoint** — accept platform selection, create user as pending, send approval email
3. **Approval endpoint** — admin approves/rejects via signed token link or admin panel
4. **Login flow** — block pending/rejected users with clear error messages
5. **Frontend** — signup page with form, platform selector, success/pending state
6. **Admin panel** — list pending users, approve/reject actions

---

## Architecture

```
                         ┌──────────────────────────┐
                         │   Frontend (React)        │
                         │                           │
                         │   LoginPage               │
                         │     └─ "Create account"   │
                         │          ↓                 │
                         │   SignupPage               │
                         │     └─ email, password,    │
                         │        platform select     │
                         │          ↓                 │
                         │   PendingApprovalPage      │
                         └───────────┬───────────────┘
                                     │ POST /auth/register
                                     ▼
┌────────────────────────────────────────────────────────────────┐
│  Backend                                                       │
│                                                                │
│  POST /auth/register                                           │
│    1. Validate email, password, platforms                      │
│    2. Create user (status=pending, is_active=false)            │
│    3. Send approval email to achantas@gmail.com                │
│    4. Return {message: "Awaiting approval"}                    │
│                                                                │
│  POST /auth/login                                              │
│    - If status=pending → 403 "Account pending approval"        │
│    - If status=rejected → 403 "Account request was rejected"   │
│    - If status=approved + is_active → issue token              │
│                                                                │
│  GET /admin/users/pending (admin only)                         │
│    - List users with status=pending                            │
│                                                                │
│  POST /admin/users/{id}/approve (admin only)                   │
│    - Set status=approved, is_active=true                       │
│                                                                │
│  POST /admin/users/{id}/reject (admin only)                    │
│    - Set status=rejected                                       │
│                                                                │
│  GET /auth/approve?token=xxx (public, signed token)            │
│    - One-click approval from email link                        │
│                                                                │
│  GET /auth/reject?token=xxx (public, signed token)             │
│    - One-click rejection from email link                       │
└────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼ (on registration)
                         ┌──────────────────────────┐
                         │  Email (Resend)           │
                         │  To: achantas@gmail.com   │
                         │                           │
                         │  "New signup request"     │
                         │  User: john@example.com   │
                         │  Platform: newsletter     │
                         │                           │
                         │  [Approve] [Reject]       │
                         │  (signed URL links)       │
                         └──────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Backend — Model & Schema Changes (4 files)

#### 1.1 Update User Model

**File:** `backend/app/models/user.py`

Add two fields to the `User` model:

```python
class User(BaseModel):
    # ... existing fields ...
    status: str = "approved"        # "pending", "approved", "rejected"
    platforms: List[str] = []       # ["newsletter", "hello_world"] — empty = all access
```

- `status` defaults to `"approved"` for backward compatibility (existing users keep working)
- `platforms` defaults to `[]` (empty list means unrestricted access, preserving current behavior for existing admin/user accounts)

#### 1.2 Update Auth Schemas

**File:** `backend/app/schemas/auth.py`

Add/update schemas:

```python
class RegisterRequest(BaseModel):
    """Public signup request."""
    email: EmailStr
    password: str
    platforms: List[str] = []       # e.g. ["newsletter"]

class UserResponse(BaseModel):
    """User response (excludes password)."""
    id: str
    username: str
    email: str
    role: str
    is_active: bool
    status: str                     # NEW
    platforms: List[str]            # NEW
    created_at: str
```

#### 1.3 Update Frontend Auth Types

**File:** `frontend/src/types/auth.ts`

```typescript
export type UserStatus = 'pending' | 'approved' | 'rejected';

export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  status: UserStatus;           // NEW
  platforms: string[];           // NEW
  createdAt?: string;
  lastLogin?: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  platforms: string[];
}

export interface RegisterResponse {
  message: string;
  status: UserStatus;
}
```

#### 1.4 Database Migration for Existing Users

**File:** `backend/app/db/mongodb.py` (update `init_default_data`)

Add migration logic that runs on startup:

```python
# Backfill existing users with new fields
await users.update_many(
    {"status": {"$exists": False}},
    {"$set": {"status": "approved", "platforms": []}}
)
```

This ensures the default admin/user accounts and any previously created users get `status: "approved"` and `platforms: []` (unrestricted).

---

### Phase 2: Backend — Registration & Approval Endpoints (3 files)

#### 2.1 Update Registration Endpoint

**File:** `backend/app/api/v1/endpoints/auth.py`

Modify the existing `POST /register` endpoint:

```python
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    platforms: list[str] = []

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, auth_service=Depends(get_auth_service)):
    """
    Register a new user account.

    Creates the account in pending status. An approval email
    is sent to the admin. The user cannot log in until approved.
    """
    # Validate platform IDs
    valid_platforms = ["newsletter", "hello_world"]
    for p in request.platforms:
        if p not in valid_platforms:
            raise HTTPException(400, f"Invalid platform: {p}")

    # Create user with pending status
    user = await auth_service.create_user(
        username=request.email,    # email IS the username
        email=request.email,
        password=request.password,
        role="user",
        status="pending",
        is_active=False,
        platforms=request.platforms,
    )

    # Send approval email to admin
    await auth_service.send_approval_email(user)

    return {"message": "Account created. Awaiting admin approval.", "status": "pending"}
```

#### 2.2 Update Login to Check Status

**File:** `backend/app/api/v1/endpoints/auth.py`

Update the `authenticate` method in `UserRepository` (or add status check in the endpoint):

```python
@router.post("/login/json", response_model=TokenResponse)
async def login_json(request: LoginRequest, auth_service=Depends(get_auth_service)):
    user = await auth_service.authenticate_user(request.username, request.password)

    if not user:
        # Check if user exists but is pending
        existing = await auth_service.get_user_by_username(request.username)
        if existing and existing.get("status") == "pending":
            raise HTTPException(403, "Your account is pending admin approval.")
        if existing and existing.get("status") == "rejected":
            raise HTTPException(403, "Your account request was not approved.")
        raise HTTPException(401, "Invalid username or password")

    tokens = auth_service.create_tokens(user)
    return TokenResponse(...)
```

#### 2.3 Add Admin Approval Endpoints

**File:** `backend/app/api/v1/endpoints/auth.py` (or new file `backend/app/api/v1/endpoints/admin.py`)

```python
# --- Admin endpoints (require admin role) ---

@router.get("/admin/users/pending", dependencies=[Depends(require_admin)])
async def list_pending_users(auth_service=Depends(get_auth_service)):
    """List all users awaiting approval."""
    return await auth_service.list_users_by_status("pending")

@router.post("/admin/users/{user_id}/approve", dependencies=[Depends(require_admin)])
async def approve_user(user_id: str, auth_service=Depends(get_auth_service)):
    """Approve a pending user account."""
    user = await auth_service.approve_user(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    # Optionally send welcome email to user
    return {"message": f"User {user['email']} approved", "user": _user_to_response(user)}

@router.post("/admin/users/{user_id}/reject", dependencies=[Depends(require_admin)])
async def reject_user(user_id: str, auth_service=Depends(get_auth_service)):
    """Reject a pending user account."""
    user = await auth_service.reject_user(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return {"message": f"User {user['email']} rejected"}

# --- Email-based one-click approval (public, signed token) ---

@router.get("/approve")
async def approve_via_email(token: str, auth_service=Depends(get_auth_service)):
    """One-click approval from email link. Token is a signed JWT with user_id."""
    user = await auth_service.approve_user_by_token(token)
    if not user:
        raise HTTPException(400, "Invalid or expired approval link")
    return {"message": f"User {user['email']} has been approved."}

@router.get("/reject")
async def reject_via_email(token: str, auth_service=Depends(get_auth_service)):
    """One-click rejection from email link. Token is a signed JWT with user_id."""
    user = await auth_service.reject_user_by_token(token)
    if not user:
        raise HTTPException(400, "Invalid or expired rejection link")
    return {"message": f"User {user['email']} has been rejected."}
```

---

### Phase 3: Backend — Service & Repository Updates (3 files)

#### 3.1 Update UserRepository

**File:** `backend/app/db/repositories/user.py`

Add methods:

```python
async def create(self, ..., status="approved", platforms=None):
    """Create user with status and platforms fields."""
    user_doc = {
        # ... existing fields ...
        "status": status,
        "platforms": platforms or [],
    }

async def find_by_status(self, status: str) -> List[dict]:
    """Find all users with a given status."""

async def set_status(self, user_id: str, status: str) -> Optional[dict]:
    """Update user status (pending/approved/rejected)."""
```

#### 3.2 Update AuthService

**File:** `backend/app/services/auth.py`

Add methods:

```python
async def create_user(self, ..., status="approved", is_active=True, platforms=None):
    """Create user — pass through status and platforms."""

async def approve_user(self, user_id: str) -> Optional[dict]:
    """Set user status to approved and is_active to True."""

async def reject_user(self, user_id: str) -> Optional[dict]:
    """Set user status to rejected."""

async def list_users_by_status(self, status: str) -> List[dict]:
    """List users filtered by status."""

async def send_approval_email(self, user: dict) -> None:
    """Send approval request email to admin with approve/reject links."""

async def approve_user_by_token(self, token: str) -> Optional[dict]:
    """Decode signed approval token and approve the user."""

async def reject_user_by_token(self, token: str) -> Optional[dict]:
    """Decode signed rejection token and reject the user."""

def _create_approval_token(self, user_id: str, action: str) -> str:
    """Create a signed JWT for email-based approve/reject links.
    Payload: {sub: user_id, action: 'approve'|'reject', exp: 7 days}"""
```

#### 3.3 Approval Email Template

The email sent to `achantas@gmail.com` will contain:

```
Subject: New signup request — {email}

Body:
A new user has requested access to the Agentic AI Framework.

    Email:     {email}
    Platform:  {platforms joined by ", "}
    Requested: {timestamp}

    [Approve]  →  {base_url}/api/v1/auth/approve?token={approve_token}
    [Reject]   →  {base_url}/api/v1/auth/reject?token={reject_token}

You can also manage pending users from the admin panel:
    {base_url}/settings (→ Users tab)
```

The approve/reject tokens are JWTs signed with the app's `SECRET_KEY`, valid for 7 days, containing `{sub: user_id, action: "approve"|"reject", type: "approval"}`.

---

### Phase 4: Frontend — Signup Page & Flow (6 files)

#### 4.1 Add Signup API

**File:** `frontend/src/api/auth.ts`

```typescript
register: async (data: RegisterRequest): Promise<RegisterResponse> => {
    const response = await apiClient.post<RegisterResponse>('/api/v1/auth/register', data);
    return response.data;
},
```

#### 4.2 Add Signup Store Method

**File:** `frontend/src/store/authStore.ts`

```typescript
register: async (data: RegisterRequest) => {
    set({ isLoading: true, error: null });
    try {
        const response = await authApi.register(data);
        set({ isLoading: false });
        return response;
    } catch (error) {
        set({ error: message, isLoading: false });
        throw error;
    }
},
```

#### 4.3 Create Signup Form Component

**File:** `frontend/src/components/auth/SignupForm.tsx` (NEW)

Form fields:
- **Email** — text input with email validation (this IS the username)
- **Password** — password input with min 8 chars, strength indicator
- **Confirm Password** — must match
- **Platform Access** — checkbox group:
  - Newsletter (`newsletter`)
  - Hello World (`hello_world`)
  - (Future platforms auto-populate from `/api/v1/platforms`)

Validation (Zod schema in `validation.ts`):
```typescript
const signupSchema = z.object({
    email: z.string().email("Valid email required"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirmPassword: z.string(),
    platforms: z.array(z.string()).min(1, "Select at least one platform"),
}).refine(data => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
});
```

#### 4.4 Create Signup Page

**File:** `frontend/src/pages/SignupPage.tsx` (NEW)

Layout mirrors `LoginPage`:
- App logo + title
- "Create your account" heading
- `<SignupForm />`
- "Already have an account? Sign in" link → `/login`

On successful registration, navigate to a pending confirmation view:
- "Account created! Awaiting admin approval."
- "You'll receive an email once your account is approved."
- "Back to sign in" link

#### 4.5 Update Login Page

**File:** `frontend/src/pages/LoginPage.tsx`

Add a "Create account" link below the login form:

```tsx
<p className="text-center text-sm text-muted-foreground">
  Don't have an account?{' '}
  <Link to={ROUTES.SIGNUP} className="text-primary hover:underline">
    Create one
  </Link>
</p>
```

Update error handling to show specific messages for pending/rejected accounts (HTTP 403).

#### 4.6 Update Routes

**File:** `frontend/src/utils/constants.ts`

```typescript
SIGNUP: '/signup',
```

**File:** `frontend/src/App.tsx`

```tsx
import SignupPage from '@/pages/SignupPage';

// In Routes:
<Route path={ROUTES.SIGNUP} element={<SignupPage />} />
```

---

### Phase 5: Frontend — Admin User Management (3 files)

#### 5.1 Admin Users API

**File:** `frontend/src/api/admin.ts` (NEW)

```typescript
export const adminApi = {
    listPendingUsers: async (): Promise<User[]> => { ... },
    approveUser: async (userId: string): Promise<void> => { ... },
    rejectUser: async (userId: string): Promise<void> => { ... },
};
```

#### 5.2 Pending Users Panel

**File:** `frontend/src/components/admin/PendingUsersPanel.tsx` (NEW)

A panel/card shown on the Settings page (admin only) or as a notification badge:
- Table of pending users: email, requested platforms, signup date
- **Approve** button (green) — calls `POST /admin/users/{id}/approve`
- **Reject** button (red) — calls `POST /admin/users/{id}/reject`
- Toast notification on success

#### 5.3 Mount in Settings or Dashboard

**File:** `frontend/src/pages/SettingsPage.tsx` (or `DashboardPage.tsx`)

Add a "Pending Users" section visible to admin users only:

```tsx
{isAdmin && <PendingUsersPanel />}
```

Optionally, show a badge count on the sidebar "Settings" link when there are pending users.

---

### Phase 6: Platform Access Enforcement (2 files)

#### 6.1 Backend Platform Guard

**File:** `backend/app/core/security.py`

Add a new dependency:

```python
def require_platform(platform_id: str):
    """Dependency that checks if the current user has access to a platform."""
    async def _guard(current_user: dict = Depends(get_current_user)):
        user_platforms = current_user.get("platforms", [])
        # Empty list = unrestricted (backward compat for admin/existing users)
        if user_platforms and platform_id not in user_platforms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You don't have access to the {platform_id} platform",
            )
        # Admin always has access
        if current_user.get("role") == "admin":
            return current_user
        return current_user
    return _guard
```

#### 6.2 Apply to Platform Routes

**File:** `backend/app/platforms/newsletter/router.py` (and other platform routers)

```python
from app.core.security import require_platform

# Add to newsletter routes that need platform scoping:
@router.post("/execute", dependencies=[Depends(require_platform("newsletter"))])
async def execute_newsletter(...):
    ...
```

> **Note:** The `require_platform` guard is additive. Admin users always pass. Existing users with `platforms: []` (empty) also pass (unrestricted). Only new users with specific platform lists are restricted.

---

## Files Summary

| # | File | Action | Phase |
|---|------|--------|-------|
| 1 | `backend/app/models/user.py` | Modify — add `status`, `platforms` fields | 1 |
| 2 | `backend/app/schemas/auth.py` | Modify — add `RegisterRequest`, update `UserResponse` | 1 |
| 3 | `frontend/src/types/auth.ts` | Modify — add `UserStatus`, `platforms`, `RegisterRequest` | 1 |
| 4 | `backend/app/db/mongodb.py` | Modify — backfill migration in `init_default_data` | 1 |
| 5 | `backend/app/api/v1/endpoints/auth.py` | Modify — update register, login; add approve/reject endpoints | 2 |
| 6 | `backend/app/api/v1/router.py` | Modify — mount admin endpoints if separated | 2 |
| 7 | `backend/app/db/repositories/user.py` | Modify — add `find_by_status`, `set_status`, update `create` | 3 |
| 8 | `backend/app/services/auth.py` | Modify — add approval methods, email sending, token generation | 3 |
| 9 | `frontend/src/api/auth.ts` | Modify — add `register` method | 4 |
| 10 | `frontend/src/store/authStore.ts` | Modify — add `register` action | 4 |
| 11 | `frontend/src/utils/validation.ts` | Modify — add `signupSchema` | 4 |
| 12 | `frontend/src/components/auth/SignupForm.tsx` | Create — signup form with email, password, platform selector | 4 |
| 13 | `frontend/src/pages/SignupPage.tsx` | Create — signup page layout | 4 |
| 14 | `frontend/src/pages/LoginPage.tsx` | Modify — add "Create account" link, handle 403 errors | 4 |
| 15 | `frontend/src/utils/constants.ts` | Modify — add `SIGNUP` route | 4 |
| 16 | `frontend/src/App.tsx` | Modify — add SignupPage route | 4 |
| 17 | `frontend/src/api/admin.ts` | Create — admin user management API | 5 |
| 18 | `frontend/src/components/admin/PendingUsersPanel.tsx` | Create — pending users table with approve/reject | 5 |
| 19 | `frontend/src/pages/SettingsPage.tsx` | Modify — add PendingUsersPanel for admins | 5 |
| 20 | `backend/app/core/security.py` | Modify — add `require_platform` dependency | 6 |
| 21 | `backend/app/platforms/newsletter/router.py` | Modify — apply platform guard to routes | 6 |

**Total: 21 files (4 new, 17 modified) across 6 phases**

---

## User Flow Diagrams

### Signup Flow

```
User visits /login
    │
    ├── Clicks "Create account"
    │       ↓
    │   /signup page
    │       ↓
    │   Fills: email, password, confirm password
    │   Selects: platform(s) [checkbox: Newsletter, Hello World]
    │       ↓
    │   POST /api/v1/auth/register
    │       ↓
    │   Backend creates user (status=pending, is_active=false)
    │   Backend sends email to achantas@gmail.com
    │       ↓
    │   UI shows: "Account created! Awaiting admin approval."
    │   User sees: "You'll get an email once approved."
    │
    └── Tries to login while pending
            ↓
        403: "Your account is pending admin approval."
```

### Admin Approval Flow (Email)

```
Admin receives email at achantas@gmail.com
    │
    ├── Clicks [Approve]
    │       ↓
    │   GET /api/v1/auth/approve?token=xxx
    │       ↓
    │   Backend decodes JWT, sets status=approved, is_active=true
    │       ↓
    │   Shows: "User john@example.com has been approved."
    │   User can now log in.
    │
    └── Clicks [Reject]
            ↓
        GET /api/v1/auth/reject?token=xxx
            ↓
        Backend decodes JWT, sets status=rejected
            ↓
        Shows: "User john@example.com has been rejected."
```

### Admin Approval Flow (Panel)

```
Admin logs in → navigates to /settings
    │
    └── Sees "Pending Users (3)" section
            ↓
        Table: email | platforms | signup date | [Approve] [Reject]
            ↓
        Clicks Approve on john@example.com
            ↓
        POST /api/v1/admin/users/{id}/approve
            ↓
        Toast: "john@example.com approved"
        Row removed from pending list
```

---

## Approval Token Design

The email links use signed JWTs (not random UUIDs) so they don't require database storage:

```python
# Token payload
{
    "sub": "user_id_here",          # the user being approved/rejected
    "action": "approve",             # or "reject"
    "type": "approval",              # distinguishes from access tokens
    "exp": now + 7 days,             # expires in 7 days
    "iat": now,
}
```

- Signed with the same `SECRET_KEY` used for access tokens
- 7-day expiration (configurable)
- `type: "approval"` prevents reuse as an access token
- One-time semantics: once status is changed, clicking the link again is a no-op (user already approved/rejected)

---

## Configuration

**New settings** (in `backend/app/config.py` or `.env`):

```bash
# Admin email for signup approval notifications
SIGNUP_APPROVAL_EMAIL=achantas@gmail.com

# Base URL for approval links in emails (auto-detected in production)
APP_BASE_URL=http://localhost:8000

# Approval token expiry (days)
SIGNUP_APPROVAL_TOKEN_EXPIRY_DAYS=7

# Available platforms for signup selection
SIGNUP_AVAILABLE_PLATFORMS=newsletter,hello_world
```

---

## Backward Compatibility

| Concern | Solution |
|---------|----------|
| Existing users have no `status` field | Migration sets `status: "approved"` on startup |
| Existing users have no `platforms` field | Migration sets `platforms: []` (empty = unrestricted) |
| Admin/user default accounts | Already approved, unrestricted access |
| Existing login flow | Unchanged — approved users with `is_active=true` work exactly as before |
| `require_platform` guard | `platforms: []` passes through (unrestricted) |
| Frontend `User` type | New fields are additive, no breaking changes |

---

## Testing Checklist

### Backend

- [ ] `POST /register` with valid email, password, platforms → 201, status=pending
- [ ] `POST /register` with duplicate email → 400
- [ ] `POST /register` with invalid platform → 400
- [ ] `POST /login/json` with pending user → 403 "pending approval"
- [ ] `POST /login/json` with rejected user → 403 "not approved"
- [ ] `POST /login/json` with approved user → 200, token returned
- [ ] `GET /approve?token=valid` → user status changes to approved
- [ ] `GET /reject?token=valid` → user status changes to rejected
- [ ] `GET /approve?token=expired` → 400 "expired"
- [ ] `GET /approve?token=invalid` → 400 "invalid"
- [ ] `GET /admin/users/pending` as admin → list of pending users
- [ ] `GET /admin/users/pending` as non-admin → 403
- [ ] `POST /admin/users/{id}/approve` → user approved
- [ ] `POST /admin/users/{id}/reject` → user rejected
- [ ] Approval email received at achantas@gmail.com with correct links
- [ ] Existing admin/user accounts unaffected after migration
- [ ] Platform guard blocks user without access to newsletter routes
- [ ] Platform guard allows user with newsletter access
- [ ] Platform guard allows admin regardless of platforms list

### Frontend

- [ ] Login page shows "Create account" link
- [ ] Signup page renders with email, password, confirm password, platform checkboxes
- [ ] Form validates: required email, min 8 char password, passwords match, min 1 platform
- [ ] Successful signup shows pending approval message
- [ ] Login attempt with pending account shows clear "pending approval" error
- [ ] Login attempt with rejected account shows "not approved" error
- [ ] Admin sees pending users panel on settings page
- [ ] Approve button works and removes user from pending list
- [ ] Reject button works and removes user from pending list
- [ ] Non-admin does not see pending users panel
