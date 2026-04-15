# Phase 7: Decouple Approval Emails from Newsletter Platform

## Problem

`AuthService.send_approval_email()` imported `get_email_service()` from
`app.platforms.newsletter.services.email`, which reads its config from
newsletter-prefixed env vars (`NEWSLETTER_RESEND_API_KEY`, etc.). This meant
approval emails only worked when the newsletter platform was fully configured —
a tight coupling that shouldn't exist for a system-level feature.

## Solution

Created a standalone **system email service** at `app.services.email` that reads
from top-level settings (`RESEND_API_KEY`, `SYSTEM_FROM_EMAIL`, `SYSTEM_FROM_NAME`).

## Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/config.py` | Modified | Added `RESEND_API_KEY`, `SYSTEM_FROM_EMAIL`, `SYSTEM_FROM_NAME` settings |
| `backend/app/services/email.py` | Created | `SystemEmailService` with retry logic and exponential backoff |
| `backend/app/services/auth.py` | Modified | Import from `app.services.email` instead of newsletter service |
| `backend/app/services/__init__.py` | Modified | Export `SystemEmailService`, `get_system_email_service` |

## Configuration

```bash
# .env — system email (for approval emails, password resets, etc.)
RESEND_API_KEY=re_xxxxxxxxxxxxx
SYSTEM_FROM_EMAIL=noreply@yourdomain.com
SYSTEM_FROM_NAME=Agentic AI Framework
```

The newsletter platform can independently use its own `NEWSLETTER_RESEND_API_KEY`
for newsletter-specific sending.

## Key Design Decisions

- **Simpler than newsletter EmailService**: No batch sending, no EmailType enum,
  no EmailResult dataclass. Returns a plain `{"success": bool, "error": str | None}` dict.
- **Same retry pattern**: Exponential backoff with 3 retries (1s, 2s, 4s).
- **Removed ImportError catch** in `send_approval_email`: The system email module
  is always available (it's part of core services, not a platform). General
  `Exception` catch remains for runtime errors (missing API key, network issues).

## Verification

1. Set `RESEND_API_KEY` and `SYSTEM_FROM_EMAIL` in `.env`
2. Register a new user via `POST /api/v1/auth/register`
3. Confirm approval email arrives at the configured `SIGNUP_APPROVAL_EMAIL`
4. Confirm approve/reject links in the email work
5. Confirm newsletter email sending still works independently
