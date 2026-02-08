"""
Tests for Email Service.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone

from app.platforms.newsletter.services.email import (
    EmailService,
    EmailResult,
    EmailBatch,
    EmailStatus,
    EmailType,
    get_email_service,
)


class TestEmailServiceImports:
    """Tests for email service module imports."""

    def test_email_service_import(self):
        """Can import EmailService."""
        assert EmailService is not None

    def test_email_result_import(self):
        """Can import EmailResult."""
        assert EmailResult is not None

    def test_email_batch_import(self):
        """Can import EmailBatch."""
        assert EmailBatch is not None

    def test_email_status_import(self):
        """Can import EmailStatus."""
        assert EmailStatus is not None

    def test_email_type_import(self):
        """Can import EmailType."""
        assert EmailType is not None

    def test_get_email_service_import(self):
        """Can import get_email_service."""
        assert get_email_service is not None


class TestEmailStatus:
    """Tests for EmailStatus enum."""

    def test_pending_status(self):
        """EmailStatus has pending value."""
        assert EmailStatus.PENDING.value == "pending"

    def test_sent_status(self):
        """EmailStatus has sent value."""
        assert EmailStatus.SENT.value == "sent"

    def test_delivered_status(self):
        """EmailStatus has delivered value."""
        assert EmailStatus.DELIVERED.value == "delivered"

    def test_bounced_status(self):
        """EmailStatus has bounced value."""
        assert EmailStatus.BOUNCED.value == "bounced"

    def test_failed_status(self):
        """EmailStatus has failed value."""
        assert EmailStatus.FAILED.value == "failed"


class TestEmailType:
    """Tests for EmailType enum."""

    def test_newsletter_type(self):
        """EmailType has newsletter value."""
        assert EmailType.NEWSLETTER.value == "newsletter"

    def test_test_type(self):
        """EmailType has test value."""
        assert EmailType.TEST.value == "test"

    def test_welcome_type(self):
        """EmailType has welcome value."""
        assert EmailType.WELCOME.value == "welcome"

    def test_otp_type(self):
        """EmailType has otp value."""
        assert EmailType.OTP.value == "otp"


class TestEmailResult:
    """Tests for EmailResult dataclass."""

    def test_create_success_result(self):
        """Can create a successful result."""
        result = EmailResult(
            success=True,
            email_id="email-123",
            recipient="test@example.com",
            status=EmailStatus.SENT,
            sent_at=datetime.now(timezone.utc),
        )

        assert result.success is True
        assert result.email_id == "email-123"
        assert result.status == EmailStatus.SENT

    def test_create_failure_result(self):
        """Can create a failure result."""
        result = EmailResult(
            success=False,
            recipient="test@example.com",
            status=EmailStatus.FAILED,
            error="Connection timeout",
            attempts=3,
        )

        assert result.success is False
        assert result.error == "Connection timeout"
        assert result.attempts == 3

    def test_to_dict(self):
        """EmailResult can convert to dictionary."""
        result = EmailResult(
            success=True,
            email_id="email-123",
            recipient="test@example.com",
            status=EmailStatus.SENT,
        )

        data = result.to_dict()

        assert data["success"] is True
        assert data["email_id"] == "email-123"
        assert data["status"] == "sent"


class TestEmailBatch:
    """Tests for EmailBatch dataclass."""

    def test_create_batch(self):
        """Can create an email batch."""
        batch = EmailBatch(total=10, sent=8, failed=2)

        assert batch.total == 10
        assert batch.sent == 8
        assert batch.failed == 2

    def test_batch_with_results(self):
        """EmailBatch can contain results."""
        results = [
            EmailResult(success=True, recipient="a@example.com", status=EmailStatus.SENT),
            EmailResult(success=False, recipient="b@example.com", status=EmailStatus.FAILED),
        ]
        batch = EmailBatch(total=2, sent=1, failed=1, results=results)

        assert len(batch.results) == 2

    def test_to_dict(self):
        """EmailBatch can convert to dictionary."""
        batch = EmailBatch(total=10, sent=8, failed=2)
        data = batch.to_dict()

        assert data["total"] == 10
        assert data["sent"] == 8
        assert data["success_rate"] == 0.8


class TestEmailServiceInstantiation:
    """Tests for EmailService instantiation."""

    def test_instantiate_with_defaults(self):
        """Can instantiate with default config."""
        with patch("app.platforms.newsletter.services.email.config") as mock_config:
            mock_config.RESEND_API_KEY = "test-api-key"
            mock_config.FROM_EMAIL = "test@example.com"
            mock_config.FROM_NAME = "Test Newsletter"

            service = EmailService()

            assert service.api_key == "test-api-key"
            assert service.from_email == "test@example.com"

    def test_instantiate_with_custom_values(self):
        """Can instantiate with custom values."""
        service = EmailService(
            api_key="custom-key",
            from_email="custom@example.com",
            from_name="Custom Name",
            max_retries=5,
        )

        assert service.api_key == "custom-key"
        assert service.from_email == "custom@example.com"
        assert service.max_retries == 5

    def test_from_address_format(self):
        """from_address is properly formatted."""
        service = EmailService(
            api_key="key",
            from_email="test@example.com",
            from_name="Test Name",
        )

        assert service.from_address == "Test Name <test@example.com>"


class TestEmailServiceConfiguration:
    """Tests for EmailService configuration."""

    def test_ensure_configured_requires_api_key(self):
        """_ensure_configured raises error if no API key."""
        service = EmailService(api_key=None)

        with pytest.raises(ValueError, match="API key not configured"):
            service._ensure_configured()

    def test_ensure_configured_sets_api_key(self):
        """_ensure_configured sets resend.api_key."""
        with patch("app.platforms.newsletter.services.email.resend") as mock_resend:
            service = EmailService(api_key="test-key")
            service._ensure_configured()

            assert mock_resend.api_key == "test-key"


class TestEmailServiceSendEmail:
    """Tests for EmailService.send_email method."""

    @pytest.mark.asyncio
    async def test_send_email_success(self):
        """send_email returns success result."""
        mock_response = MagicMock()
        mock_response.id = "email-123"

        with patch("app.platforms.newsletter.services.email.resend") as mock_resend:
            mock_resend.Emails.send.return_value = mock_response

            service = EmailService(api_key="test-key")
            result = await service.send_email(
                to="recipient@example.com",
                subject="Test Subject",
                html_content="<p>Test content</p>",
            )

            assert result.success is True
            assert result.status == EmailStatus.SENT
            assert result.recipient == "recipient@example.com"

    @pytest.mark.asyncio
    async def test_send_email_with_plain_text(self):
        """send_email includes plain text when provided."""
        mock_response = {"id": "email-123"}

        with patch("app.platforms.newsletter.services.email.resend") as mock_resend:
            mock_resend.Emails.send.return_value = mock_response

            service = EmailService(api_key="test-key")
            await service.send_email(
                to="recipient@example.com",
                subject="Test Subject",
                html_content="<p>Test content</p>",
                plain_text="Test content",
            )

            call_args = mock_resend.Emails.send.call_args[0][0]
            assert "text" in call_args
            assert call_args["text"] == "Test content"

    @pytest.mark.asyncio
    async def test_send_email_retry_on_failure(self):
        """send_email retries on failure."""
        call_count = 0

        def mock_send(params):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary error")
            return {"id": "email-123"}

        with patch("app.platforms.newsletter.services.email.resend") as mock_resend:
            mock_resend.Emails.send.side_effect = mock_send

            service = EmailService(api_key="test-key", max_retries=3)
            result = await service.send_email(
                to="recipient@example.com",
                subject="Test",
                html_content="<p>Test</p>",
            )

            assert result.success is True
            assert result.attempts == 3

    @pytest.mark.asyncio
    async def test_send_email_fails_after_max_retries(self):
        """send_email fails after max retries exceeded."""
        with patch("app.platforms.newsletter.services.email.resend") as mock_resend:
            mock_resend.Emails.send.side_effect = Exception("Permanent error")

            service = EmailService(api_key="test-key", max_retries=2)
            result = await service.send_email(
                to="recipient@example.com",
                subject="Test",
                html_content="<p>Test</p>",
            )

            assert result.success is False
            assert result.status == EmailStatus.FAILED
            assert result.attempts == 2


class TestEmailServiceNewsletter:
    """Tests for EmailService.send_newsletter method."""

    @pytest.mark.asyncio
    async def test_send_newsletter(self):
        """send_newsletter sends with newsletter tags."""
        with patch("app.platforms.newsletter.services.email.resend") as mock_resend:
            mock_resend.Emails.send.return_value = {"id": "email-123"}

            service = EmailService(api_key="test-key")
            result = await service.send_newsletter(
                to="recipient@example.com",
                subject="Weekly Update",
                html_content="<p>Newsletter content</p>",
                plain_text="Newsletter content",
                newsletter_id="nl-123",
            )

            assert result.success is True
            call_args = mock_resend.Emails.send.call_args[0][0]
            assert "tags" in call_args


class TestEmailServiceTestEmail:
    """Tests for EmailService.send_test_email method."""

    @pytest.mark.asyncio
    async def test_send_test_email_prefixes_subject(self):
        """send_test_email prefixes subject with [TEST]."""
        with patch("app.platforms.newsletter.services.email.resend") as mock_resend:
            mock_resend.Emails.send.return_value = {"id": "email-123"}

            service = EmailService(api_key="test-key")
            await service.send_test_email(
                to="test@example.com",
                subject="Newsletter Preview",
                html_content="<p>Preview</p>",
            )

            call_args = mock_resend.Emails.send.call_args[0][0]
            assert call_args["subject"] == "[TEST] Newsletter Preview"


class TestEmailServiceWelcome:
    """Tests for EmailService.send_welcome_email method."""

    @pytest.mark.asyncio
    async def test_send_welcome_email(self):
        """send_welcome_email sends welcome message."""
        with patch("app.platforms.newsletter.services.email.resend") as mock_resend:
            mock_resend.Emails.send.return_value = {"id": "email-123"}

            service = EmailService(
                api_key="test-key",
                from_name="My Newsletter",
            )
            result = await service.send_welcome_email(
                to="new@example.com",
                subscriber_name="John",
            )

            assert result.success is True
            call_args = mock_resend.Emails.send.call_args[0][0]
            assert "Welcome" in call_args["subject"]
            assert "John" in call_args["html"]


class TestEmailServiceOTP:
    """Tests for EmailService.send_otp_email method."""

    @pytest.mark.asyncio
    async def test_send_otp_email(self):
        """send_otp_email sends OTP code."""
        with patch("app.platforms.newsletter.services.email.resend") as mock_resend:
            mock_resend.Emails.send.return_value = {"id": "email-123"}

            service = EmailService(api_key="test-key")
            result = await service.send_otp_email(
                to="user@example.com",
                otp_code="123456",
                expiry_minutes=10,
            )

            assert result.success is True
            call_args = mock_resend.Emails.send.call_args[0][0]
            assert "123456" in call_args["subject"]
            assert "123456" in call_args["html"]


class TestEmailServiceBatch:
    """Tests for EmailService.send_batch method."""

    @pytest.mark.asyncio
    async def test_send_batch_success(self):
        """send_batch sends to multiple recipients."""
        with patch("app.platforms.newsletter.services.email.resend") as mock_resend:
            mock_resend.Emails.send.return_value = {"id": "email-123"}

            service = EmailService(api_key="test-key")
            batch = await service.send_batch(
                recipients=["a@example.com", "b@example.com", "c@example.com"],
                subject="Batch Test",
                html_content="<p>Content</p>",
                batch_size=10,
            )

            assert batch.total == 3
            assert batch.sent == 3
            assert batch.failed == 0

    @pytest.mark.asyncio
    async def test_send_batch_partial_failure(self):
        """send_batch handles partial failures."""
        call_count = 0

        def mock_send(params):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("Failed for one recipient")
            return {"id": f"email-{call_count}"}

        with patch("app.platforms.newsletter.services.email.resend") as mock_resend:
            mock_resend.Emails.send.side_effect = mock_send

            service = EmailService(api_key="test-key", max_retries=1)
            batch = await service.send_batch(
                recipients=["a@example.com", "b@example.com", "c@example.com"],
                subject="Batch Test",
                html_content="<p>Content</p>",
            )

            assert batch.total == 3
            assert batch.sent == 2
            assert batch.failed == 1


class TestEmailServiceHealth:
    """Tests for EmailService.check_health method."""

    @pytest.mark.asyncio
    async def test_check_health_no_api_key(self):
        """check_health returns unhealthy if no API key."""
        service = EmailService(api_key=None)
        health = await service.check_health()

        assert health["healthy"] is False
        assert "API key not configured" in health["error"]

    @pytest.mark.asyncio
    async def test_check_health_with_api_key(self):
        """check_health returns healthy with API key."""
        with patch("app.platforms.newsletter.services.email.resend"):
            service = EmailService(
                api_key="test-key",
                from_email="test@example.com",
                from_name="Test",
            )
            health = await service.check_health()

            assert health["healthy"] is True
            assert health["from_email"] == "test@example.com"


class TestGetEmailService:
    """Tests for get_email_service singleton."""

    def test_get_email_service_returns_instance(self):
        """get_email_service returns EmailService instance."""
        # Reset singleton
        import app.platforms.newsletter.services.email as module
        module._email_service = None

        with patch("app.platforms.newsletter.services.email.config") as mock_config:
            mock_config.RESEND_API_KEY = "test-key"
            mock_config.FROM_EMAIL = "test@example.com"
            mock_config.FROM_NAME = "Test"

            service = get_email_service()
            assert isinstance(service, EmailService)

    def test_get_email_service_returns_same_instance(self):
        """get_email_service returns same instance."""
        # Reset singleton
        import app.platforms.newsletter.services.email as module
        module._email_service = None

        with patch("app.platforms.newsletter.services.email.config") as mock_config:
            mock_config.RESEND_API_KEY = "test-key"
            mock_config.FROM_EMAIL = "test@example.com"
            mock_config.FROM_NAME = "Test"

            s1 = get_email_service()
            s2 = get_email_service()
            assert s1 is s2
