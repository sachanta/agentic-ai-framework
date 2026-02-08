# Phase 11: Email Service Integration

## Goal
Newsletter delivery via Resend API

## Status
- [ ] Not Started

## Files to Create
```
backend/app/platforms/newsletter/services/email.py
```

## Features
- Send newsletter emails with Resend
- HTML and plain text versions
- Retry mechanism (3 retries)
- Delivery tracking
- Test email support
- OTP/Welcome emails

## Configuration
```python
NEWSLETTER_RESEND_API_KEY=xxx
NEWSLETTER_FROM_EMAIL=newsletter@yourdomain.com
NEWSLETTER_FROM_NAME="Your Newsletter"
```

## How It Helps The Project

The Email Service is the **final delivery mechanism** for newsletters:

### The Flow
1. Newsletter approved at Checkpoint 4
2. Email Service formats content for delivery
3. Sends to all campaign recipients
4. Tracks delivery status and updates analytics

### Key Capabilities

| Capability | Description |
|------------|-------------|
| Multi-format | Sends both HTML and plain text versions |
| Retry logic | Retries failed sends up to 3 times |
| Tracking | Records delivered/bounced/opened status |
| Test mode | Send test email before full campaign |

### Resend Integration
```python
from resend import Resend

client = Resend(api_key=config.RESEND_API_KEY)

response = client.emails.send({
    "from": f"{config.FROM_NAME} <{config.FROM_EMAIL}>",
    "to": subscriber.email,
    "subject": newsletter.subject_line,
    "html": newsletter.html_content,
    "text": newsletter.plain_text,
})
```

## Dependencies
- Phase 2 (Subscriber repository)
- Phase 7 (Newsletter content)
- Phase 9 (Mindmap SVG)
- Resend API (add to pyproject.toml)

## Verification
- [ ] Can send test emails
- [ ] HTML and plain text both work
- [ ] SVG embedding works
- [ ] Retry mechanism works
- [ ] Delivery tracking updates campaign analytics
- [ ] Tests passing
