# Phase 10: Email Service Integration

## Status: Completed

## Overview

Phase 10 implements newsletter delivery via the Resend API. The EmailService provides reliable email sending with retry logic, batch support, and multiple email types (newsletter, test, welcome, OTP).

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EMAIL SERVICE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         EmailService                                  │   │
│  │                                                                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │ send_email  │  │ send_batch  │  │ send_test   │  │ send_welcome│  │   │
│  │  │             │  │             │  │             │  │             │  │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │   │
│  │         │                │                │                │         │   │
│  │         └────────────────┴────────────────┴────────────────┘         │   │
│  │                                   │                                   │   │
│  │                                   ▼                                   │   │
│  │                    ┌──────────────────────────┐                      │   │
│  │                    │     Retry Logic          │                      │   │
│  │                    │  (3 retries, exp backoff)│                      │   │
│  │                    └──────────────┬───────────┘                      │   │
│  │                                   │                                   │   │
│  └───────────────────────────────────┼───────────────────────────────────┘   │
│                                      │                                       │
│                                      ▼                                       │
│                       ┌──────────────────────────┐                          │
│                       │      Resend API          │                          │
│                       │   resend.Emails.send()   │                          │
│                       └──────────────────────────┘                          │
│                                      │                                       │
│                                      ▼                                       │
│                       ┌──────────────────────────┐                          │
│                       │      EmailResult         │                          │
│                       │  - success: bool         │                          │
│                       │  - email_id: str         │                          │
│                       │  - status: EmailStatus   │                          │
│                       │  - attempts: int         │                          │
│                       └──────────────────────────┘                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Files Created

```
backend/app/platforms/newsletter/services/
└── email.py              # EmailService, EmailResult, EmailBatch

backend/app/platforms/newsletter/tests/phase10/
├── __init__.py
└── test_email_service.py # 40 tests
```

---

## Key Components

### 1. EmailStatus Enum

```python
class EmailStatus(str, Enum):
    """Email delivery status."""
    PENDING = "pending"      # Not yet sent
    SENT = "sent"            # Successfully sent to Resend
    DELIVERED = "delivered"  # Confirmed delivered
    BOUNCED = "bounced"      # Delivery bounced
    FAILED = "failed"        # Failed after retries
```

### 2. EmailType Enum

```python
class EmailType(str, Enum):
    """Types of emails that can be sent."""
    NEWSLETTER = "newsletter"    # Regular newsletter
    TEST = "test"                # Test/preview email
    WELCOME = "welcome"          # New subscriber welcome
    OTP = "otp"                  # Verification code
    CONFIRMATION = "confirmation" # Action confirmation
```

### 3. EmailResult Dataclass

```python
@dataclass
class EmailResult:
    """Result of an email send operation."""
    success: bool                          # Whether send succeeded
    email_id: Optional[str] = None         # Resend email ID
    recipient: str = ""                    # Recipient address
    status: EmailStatus = EmailStatus.PENDING
    error: Optional[str] = None            # Error message if failed
    attempts: int = 0                      # Number of attempts made
    sent_at: Optional[datetime] = None     # Timestamp when sent

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "email_id": self.email_id,
            "recipient": self.recipient,
            "status": self.status.value,
            "error": self.error,
            "attempts": self.attempts,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }
```

### 4. EmailBatch Dataclass

```python
@dataclass
class EmailBatch:
    """Batch of email results."""
    total: int = 0                              # Total recipients
    sent: int = 0                               # Successfully sent
    failed: int = 0                             # Failed to send
    results: List[EmailResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "sent": self.sent,
            "failed": self.failed,
            "success_rate": self.sent / self.total if self.total > 0 else 0,
            "results": [r.to_dict() for r in self.results],
        }
```

### 5. EmailService Class

```python
class EmailService:
    """
    Service for sending emails via Resend API.

    Features:
    - Send newsletter emails with HTML and plain text
    - Retry mechanism with exponential backoff
    - Delivery tracking
    - Test email support
    - Batch sending for campaigns
    """

    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 1.0  # seconds
    DEFAULT_BATCH_SIZE = 50

    def __init__(
        self,
        api_key: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        self.api_key = api_key or config.RESEND_API_KEY
        self.from_email = from_email or config.FROM_EMAIL
        self.from_name = from_name or config.FROM_NAME
        self.max_retries = max_retries
```

---

## API Methods

### send_email

Core method for sending a single email with retry logic.

```python
async def send_email(
    self,
    to: str,
    subject: str,
    html_content: str,
    plain_text: Optional[str] = None,
    email_type: EmailType = EmailType.NEWSLETTER,
    reply_to: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> EmailResult:
    """
    Send a single email with retry logic.

    Retries up to max_retries times with exponential backoff:
    - Attempt 1: immediate
    - Attempt 2: 1 second delay
    - Attempt 3: 2 seconds delay
    """
```

### send_newsletter

Specialized method for newsletter delivery.

```python
async def send_newsletter(
    self,
    to: str,
    subject: str,
    html_content: str,
    plain_text: str,
    newsletter_id: Optional[str] = None,
) -> EmailResult:
    """
    Send a newsletter email.

    Automatically adds "newsletter" tag and newsletter ID for tracking.
    """
```

### send_test_email

Send a test/preview email.

```python
async def send_test_email(
    self,
    to: str,
    subject: str,
    html_content: str,
    plain_text: Optional[str] = None,
) -> EmailResult:
    """
    Send a test email.

    Prefixes subject with [TEST] and adds "test" tag.
    """
```

### send_welcome_email

Send welcome email to new subscribers.

```python
async def send_welcome_email(
    self,
    to: str,
    subscriber_name: Optional[str] = None,
) -> EmailResult:
    """
    Send a welcome email to new subscriber.

    Uses a built-in HTML template with personalization.
    """
```

### send_otp_email

Send OTP verification email.

```python
async def send_otp_email(
    self,
    to: str,
    otp_code: str,
    expiry_minutes: int = 10,
) -> EmailResult:
    """
    Send an OTP verification email.

    Displays code prominently with expiry notice.
    """
```

### send_batch

Send to multiple recipients with batching.

```python
async def send_batch(
    self,
    recipients: List[str],
    subject: str,
    html_content: str,
    plain_text: Optional[str] = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    delay_between_batches: float = 1.0,
) -> EmailBatch:
    """
    Send emails to multiple recipients in batches.

    Features:
    - Concurrent sending within each batch
    - Delay between batches to avoid rate limiting
    - Aggregate success/failure tracking
    """
```

### check_health

Check email service health.

```python
async def check_health(self) -> Dict[str, Any]:
    """
    Check email service health.

    Returns:
        {
            "healthy": True/False,
            "from_email": "...",
            "from_name": "...",
            "error": "..." (if unhealthy)
        }
    """
```

---

## Configuration

### Environment Variables

```bash
# Required
NEWSLETTER_RESEND_API_KEY=re_xxxxxxxxxxxxx

# Optional (have defaults)
NEWSLETTER_FROM_EMAIL=newsletter@yourdomain.com
NEWSLETTER_FROM_NAME="Your Newsletter"
```

### In config.py

```python
class NewsletterConfig(BaseSettings):
    # External service API keys
    RESEND_API_KEY: Optional[str] = None

    # Email settings
    FROM_EMAIL: str = "newsletter@example.com"
    FROM_NAME: str = "AI Newsletter"
```

---

## Usage Examples

### Basic Newsletter Send

```python
from app.platforms.newsletter.services import get_email_service

service = get_email_service()

result = await service.send_newsletter(
    to="subscriber@example.com",
    subject="Weekly AI Digest - January 2024",
    html_content="""
    <html>
        <body>
            <h1>This Week in AI</h1>
            <p>Top stories from the AI world...</p>
        </body>
    </html>
    """,
    plain_text="This Week in AI\n\nTop stories from the AI world...",
    newsletter_id="nl-2024-01-15",
)

if result.success:
    print(f"Email sent! ID: {result.email_id}")
else:
    print(f"Failed after {result.attempts} attempts: {result.error}")
```

### Batch Send to Subscribers

```python
subscribers = ["alice@example.com", "bob@example.com", "charlie@example.com"]

batch = await service.send_batch(
    recipients=subscribers,
    subject="Newsletter Update",
    html_content=html_newsletter,
    plain_text=text_newsletter,
    batch_size=50,
    delay_between_batches=1.0,
)

print(f"Sent: {batch.sent}/{batch.total}")
print(f"Success rate: {batch.to_dict()['success_rate']:.1%}")

# Check individual results
for result in batch.results:
    if not result.success:
        print(f"Failed: {result.recipient} - {result.error}")
```

### Test Email Before Campaign

```python
# Send test to yourself first
test_result = await service.send_test_email(
    to="admin@example.com",
    subject="Weekly Newsletter",
    html_content=newsletter_html,
)

if test_result.success:
    print("Test email sent! Subject will show as [TEST] Weekly Newsletter")
    # Review the test email, then send to all subscribers
```

### Welcome New Subscriber

```python
result = await service.send_welcome_email(
    to="newuser@example.com",
    subscriber_name="Alice",
)
# Sends personalized welcome with "Hi Alice, ..."
```

### OTP Verification

```python
import secrets

otp = secrets.token_hex(3).upper()  # e.g., "A1B2C3"

result = await service.send_otp_email(
    to="user@example.com",
    otp_code=otp,
    expiry_minutes=10,
)
# Subject: "Your verification code: A1B2C3"
```

---

## Retry Logic

The service implements exponential backoff for reliability:

```python
for attempt in range(1, max_retries + 1):
    try:
        response = await send_to_resend(params)
        return EmailResult(success=True, ...)
    except Exception as e:
        if attempt < max_retries:
            delay = 1.0 * (2 ** (attempt - 1))  # 1s, 2s, 4s...
            await asyncio.sleep(delay)
        else:
            return EmailResult(success=False, error=str(e), ...)
```

| Attempt | Delay Before Retry |
|---------|-------------------|
| 1 | Immediate |
| 2 | 1 second |
| 3 | 2 seconds |
| (fail) | Return failure |

---

## Integration with Orchestrator

The EmailService is called from the `send_email_node` in the LangGraph workflow:

```python
# In orchestrator/nodes.py
async def send_email_node(state: NewsletterState) -> dict[str, Any]:
    """Send newsletter via email service."""
    from app.platforms.newsletter.services import get_email_service

    service = get_email_service()

    # Get subscribers for this newsletter
    subscribers = await get_campaign_subscribers(state["newsletter_id"])

    # Send batch
    batch = await service.send_batch(
        recipients=subscribers,
        subject=state["selected_subject"],
        html_content=state["newsletter_html"],
        plain_text=state["newsletter_plain"],
    )

    return {
        "email_sent": batch.sent > 0,
        "recipient_count": batch.total,
        "status": "completed",
    }
```

---

## Tests

```
tests/phase10/test_email_service.py

TestEmailServiceImports          # 6 tests
TestEmailStatus                  # 5 tests
TestEmailType                    # 4 tests
TestEmailResult                  # 3 tests
TestEmailBatch                   # 3 tests
TestEmailServiceInstantiation    # 3 tests
TestEmailServiceConfiguration    # 2 tests
TestEmailServiceSendEmail        # 4 tests
TestEmailServiceNewsletter       # 1 test
TestEmailServiceTestEmail        # 1 test
TestEmailServiceWelcome          # 1 test
TestEmailServiceOTP              # 1 test
TestEmailServiceBatch            # 2 tests
TestEmailServiceHealth           # 2 tests
TestGetEmailService              # 2 tests

Total: 40 tests
```

---

## Dependencies

- `resend>=2.0.0` (added to pyproject.toml)
- Phase 2: Subscriber model for recipient lists
- Phase 7: Newsletter content (HTML/plain text)
- Phase 9: Orchestrator integration via `send_email_node`

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| No API key | `ValueError("Resend API key not configured")` |
| Network error | Retry up to 3 times with backoff |
| Invalid recipient | Returns `EmailResult(success=False)` |
| Rate limited | Batch delay helps avoid, retries help recover |
| Partial batch failure | `EmailBatch` tracks individual results |
