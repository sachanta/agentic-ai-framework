"""
Email Service for newsletter delivery via Resend API.

Provides email sending capabilities with retry logic and delivery tracking.
"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import resend

from app.platforms.newsletter.config import config

logger = logging.getLogger(__name__)


class EmailStatus(str, Enum):
    """Email delivery status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    BOUNCED = "bounced"
    FAILED = "failed"


class EmailType(str, Enum):
    """Types of emails that can be sent."""
    NEWSLETTER = "newsletter"
    TEST = "test"
    WELCOME = "welcome"
    OTP = "otp"
    CONFIRMATION = "confirmation"


@dataclass
class EmailResult:
    """Result of an email send operation."""
    success: bool
    email_id: Optional[str] = None
    recipient: str = ""
    status: EmailStatus = EmailStatus.PENDING
    error: Optional[str] = None
    attempts: int = 0
    sent_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "email_id": self.email_id,
            "recipient": self.recipient,
            "status": self.status.value,
            "error": self.error,
            "attempts": self.attempts,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }


@dataclass
class EmailBatch:
    """Batch of email results."""
    total: int = 0
    sent: int = 0
    failed: int = 0
    results: List[EmailResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total": self.total,
            "sent": self.sent,
            "failed": self.failed,
            "success_rate": self.sent / self.total if self.total > 0 else 0,
            "results": [r.to_dict() for r in self.results],
        }


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
        """
        Initialize email service.

        Args:
            api_key: Resend API key (defaults to config)
            from_email: Sender email (defaults to config)
            from_name: Sender name (defaults to config)
            max_retries: Maximum retry attempts
        """
        self.api_key = api_key or config.RESEND_API_KEY
        self.from_email = from_email or config.FROM_EMAIL
        self.from_name = from_name or config.FROM_NAME
        self.max_retries = max_retries
        self._client: Optional[resend.Resend] = None

    def _ensure_configured(self) -> None:
        """Ensure Resend is configured with API key."""
        if not self.api_key:
            raise ValueError("Resend API key not configured")
        resend.api_key = self.api_key

    @property
    def from_address(self) -> str:
        """Get formatted from address."""
        return f"{self.from_name} <{self.from_email}>"

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

        Args:
            to: Recipient email address
            subject: Email subject line
            html_content: HTML content
            plain_text: Plain text content (optional)
            email_type: Type of email being sent
            reply_to: Reply-to address (optional)
            tags: Tags for categorization (optional)

        Returns:
            EmailResult with send status
        """
        result = EmailResult(
            success=False,
            recipient=to,
            status=EmailStatus.PENDING,
        )

        for attempt in range(1, self.max_retries + 1):
            result.attempts = attempt
            try:
                params: Dict[str, Any] = {
                    "from": self.from_address,
                    "to": [to],
                    "subject": subject,
                    "html": html_content,
                }

                if plain_text:
                    params["text"] = plain_text

                if reply_to:
                    params["reply_to"] = reply_to

                if tags:
                    params["tags"] = [{"name": tag, "value": "true"} for tag in tags]

                # Configure and send email (Resend SDK is sync, run in executor)
                self._ensure_configured()
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: resend.Emails.send(params)
                )

                result.success = True
                result.email_id = response.get("id") if isinstance(response, dict) else getattr(response, "id", None)
                result.status = EmailStatus.SENT
                result.sent_at = datetime.now(timezone.utc)

                logger.info(f"Email sent successfully to {to}, id={result.email_id}")
                return result

            except Exception as e:
                error_msg = str(e)
                logger.warning(
                    f"Email send attempt {attempt}/{self.max_retries} failed for {to}: {error_msg}"
                )
                result.error = error_msg

                if attempt < self.max_retries:
                    delay = self.DEFAULT_RETRY_DELAY * (2 ** (attempt - 1))
                    await asyncio.sleep(delay)

        result.status = EmailStatus.FAILED
        logger.error(f"Email send failed after {self.max_retries} attempts for {to}")
        return result

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

        Args:
            to: Recipient email
            subject: Newsletter subject
            html_content: HTML newsletter content
            plain_text: Plain text version
            newsletter_id: Newsletter ID for tracking

        Returns:
            EmailResult with send status
        """
        tags = ["newsletter"]
        if newsletter_id:
            tags.append(f"newsletter:{newsletter_id}")

        return await self.send_email(
            to=to,
            subject=subject,
            html_content=html_content,
            plain_text=plain_text,
            email_type=EmailType.NEWSLETTER,
            tags=tags,
        )

    async def send_test_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        plain_text: Optional[str] = None,
    ) -> EmailResult:
        """
        Send a test email (single recipient, no tracking).

        Args:
            to: Test recipient email
            subject: Email subject (will be prefixed with [TEST])
            html_content: HTML content
            plain_text: Plain text content

        Returns:
            EmailResult with send status
        """
        return await self.send_email(
            to=to,
            subject=f"[TEST] {subject}",
            html_content=html_content,
            plain_text=plain_text,
            email_type=EmailType.TEST,
            tags=["test"],
        )

    async def send_welcome_email(
        self,
        to: str,
        subscriber_name: Optional[str] = None,
    ) -> EmailResult:
        """
        Send a welcome email to new subscriber.

        Args:
            to: New subscriber email
            subscriber_name: Subscriber name for personalization

        Returns:
            EmailResult with send status
        """
        name = subscriber_name or "there"
        html_content = f"""
        <html>
        <body>
            <h1>Welcome to {self.from_name}!</h1>
            <p>Hi {name},</p>
            <p>Thank you for subscribing to our newsletter. You'll receive
            curated content directly in your inbox.</p>
            <p>Stay tuned for great content!</p>
            <p>Best regards,<br>The {self.from_name} Team</p>
        </body>
        </html>
        """
        plain_text = f"""
Welcome to {self.from_name}!

Hi {name},

Thank you for subscribing to our newsletter. You'll receive
curated content directly in your inbox.

Stay tuned for great content!

Best regards,
The {self.from_name} Team
        """

        return await self.send_email(
            to=to,
            subject=f"Welcome to {self.from_name}!",
            html_content=html_content,
            plain_text=plain_text,
            email_type=EmailType.WELCOME,
            tags=["welcome"],
        )

    async def send_otp_email(
        self,
        to: str,
        otp_code: str,
        expiry_minutes: int = 10,
    ) -> EmailResult:
        """
        Send an OTP verification email.

        Args:
            to: Recipient email
            otp_code: The OTP code
            expiry_minutes: Minutes until OTP expires

        Returns:
            EmailResult with send status
        """
        html_content = f"""
        <html>
        <body>
            <h1>Your Verification Code</h1>
            <p>Your verification code is:</p>
            <h2 style="font-size: 32px; letter-spacing: 8px; font-family: monospace;">
                {otp_code}
            </h2>
            <p>This code will expire in {expiry_minutes} minutes.</p>
            <p>If you didn't request this code, please ignore this email.</p>
        </body>
        </html>
        """
        plain_text = f"""
Your Verification Code

Your verification code is: {otp_code}

This code will expire in {expiry_minutes} minutes.

If you didn't request this code, please ignore this email.
        """

        return await self.send_email(
            to=to,
            subject=f"Your verification code: {otp_code}",
            html_content=html_content,
            plain_text=plain_text,
            email_type=EmailType.OTP,
            tags=["otp", "verification"],
        )

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

        Args:
            recipients: List of recipient emails
            subject: Email subject
            html_content: HTML content
            plain_text: Plain text content
            batch_size: Number of emails per batch
            delay_between_batches: Delay between batches in seconds

        Returns:
            EmailBatch with aggregate results
        """
        batch_result = EmailBatch(total=len(recipients))

        for i in range(0, len(recipients), batch_size):
            batch = recipients[i:i + batch_size]

            # Send batch concurrently
            tasks = [
                self.send_email(
                    to=recipient,
                    subject=subject,
                    html_content=html_content,
                    plain_text=plain_text,
                )
                for recipient in batch
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    batch_result.failed += 1
                    batch_result.results.append(
                        EmailResult(
                            success=False,
                            status=EmailStatus.FAILED,
                            error=str(result),
                        )
                    )
                elif isinstance(result, EmailResult):
                    batch_result.results.append(result)
                    if result.success:
                        batch_result.sent += 1
                    else:
                        batch_result.failed += 1

            # Delay between batches to avoid rate limiting
            if i + batch_size < len(recipients):
                await asyncio.sleep(delay_between_batches)

        return batch_result

    async def check_health(self) -> Dict[str, Any]:
        """
        Check email service health.

        Returns:
            Health status dictionary
        """
        try:
            # Verify API key is configured
            if not self.api_key:
                return {
                    "healthy": False,
                    "error": "API key not configured",
                }

            # Verify we can configure resend
            self._ensure_configured()

            return {
                "healthy": True,
                "from_email": self.from_email,
                "from_name": self.from_name,
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
            }


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create the email service singleton."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


__all__ = [
    "EmailService",
    "EmailResult",
    "EmailBatch",
    "EmailStatus",
    "EmailType",
    "get_email_service",
]
