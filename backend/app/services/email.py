"""
System email service for sending transactional emails via Resend API.

This is a lightweight service for system-level emails (approval notifications,
password resets, etc.) that is independent of any platform configuration.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

import resend

from app.config import settings

logger = logging.getLogger(__name__)


class SystemEmailService:
    """
    System-level email service using Resend.

    Reads configuration from app.config.settings (no platform prefix).
    Includes retry logic with exponential backoff.
    """

    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 1.0  # seconds

    def __init__(
        self,
        api_key: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        self.api_key = api_key or settings.RESEND_API_KEY
        self.from_email = from_email or settings.SYSTEM_FROM_EMAIL
        self.from_name = from_name or settings.SYSTEM_FROM_NAME
        self.max_retries = max_retries

    def _ensure_configured(self) -> None:
        """Ensure Resend is configured with API key."""
        if not self.api_key:
            raise ValueError(
                "System email not configured: set RESEND_API_KEY in environment"
            )
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
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Send a single email with retry logic.

        Args:
            to: Recipient email address
            subject: Email subject line
            html_content: HTML content
            plain_text: Plain text fallback (optional)
            tags: Tags for categorization (optional)

        Returns:
            Dict with keys: success (bool), error (str | None)
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                params: Dict[str, Any] = {
                    "from": self.from_address,
                    "to": [to],
                    "subject": subject,
                    "html": html_content,
                }

                if plain_text:
                    params["text"] = plain_text

                if tags:
                    params["tags"] = [{"name": tag, "value": "true"} for tag in tags]

                self._ensure_configured()
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: resend.Emails.send(params),
                )

                email_id = (
                    response.get("id")
                    if isinstance(response, dict)
                    else getattr(response, "id", None)
                )
                logger.info(f"System email sent to {to}, id={email_id}")
                return {"success": True, "error": None}

            except Exception as e:
                error_msg = str(e)
                logger.warning(
                    f"System email attempt {attempt}/{self.max_retries} "
                    f"failed for {to}: {error_msg}"
                )

                if attempt < self.max_retries:
                    delay = self.DEFAULT_RETRY_DELAY * (2 ** (attempt - 1))
                    await asyncio.sleep(delay)

        logger.error(
            f"System email failed after {self.max_retries} attempts for {to}"
        )
        return {"success": False, "error": error_msg}


# Singleton
_system_email_service: Optional[SystemEmailService] = None


def get_system_email_service() -> SystemEmailService:
    """Get or create the system email service singleton."""
    global _system_email_service
    if _system_email_service is None:
        _system_email_service = SystemEmailService()
    return _system_email_service


__all__ = [
    "SystemEmailService",
    "get_system_email_service",
]
