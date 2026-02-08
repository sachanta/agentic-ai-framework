"""
Tests for Phase 11 API Endpoints.

Tests the complete REST API for the newsletter platform.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone
from fastapi.testclient import TestClient


# Mock user for authenticated endpoints
MOCK_USER = {"id": "test-user-123", "email": "test@example.com"}


class TestRouterImports:
    """Test that all routers can be imported."""

    def test_import_newsletters_router(self):
        """Can import newsletters router."""
        from app.platforms.newsletter.routers.newsletters import router
        assert router is not None

    def test_import_workflows_router(self):
        """Can import workflows router."""
        from app.platforms.newsletter.routers.workflows import router
        assert router is not None

    def test_import_campaigns_router(self):
        """Can import campaigns router."""
        from app.platforms.newsletter.routers.campaigns import router
        assert router is not None

    def test_import_subscribers_router(self):
        """Can import subscribers router."""
        from app.platforms.newsletter.routers.subscribers import router
        assert router is not None

    def test_import_templates_router(self):
        """Can import templates router."""
        from app.platforms.newsletter.routers.templates import router
        assert router is not None

    def test_import_analytics_router(self):
        """Can import analytics router."""
        from app.platforms.newsletter.routers.analytics import router
        assert router is not None


class TestNewslettersSchemas:
    """Test newsletter endpoint schemas."""

    def test_newsletter_list_item(self):
        """NewsletterListItem schema works."""
        from app.platforms.newsletter.routers.newsletters import NewsletterListItem

        item = NewsletterListItem(
            id="nl-123",
            title="Test Newsletter",
            status="draft",
            created_at=datetime.now(timezone.utc),
        )
        assert item.id == "nl-123"
        assert item.status == "draft"

    def test_newsletter_detail(self):
        """NewsletterDetail schema works."""
        from app.platforms.newsletter.routers.newsletters import NewsletterDetail

        detail = NewsletterDetail(
            id="nl-123",
            user_id="user-456",
            title="Test Newsletter",
            status="draft",
            created_at=datetime.now(timezone.utc),
        )
        assert detail.id == "nl-123"
        assert detail.user_id == "user-456"

    def test_newsletter_update_request(self):
        """NewsletterUpdateRequest schema works."""
        from app.platforms.newsletter.routers.newsletters import NewsletterUpdateRequest

        request = NewsletterUpdateRequest(title="Updated Title")
        assert request.title == "Updated Title"
        assert request.content is None


class TestWorkflowsSchemas:
    """Test workflow endpoint schemas."""

    def test_workflow_list_item(self):
        """WorkflowListItem schema works."""
        from app.platforms.newsletter.routers.workflows import WorkflowListItem

        item = WorkflowListItem(
            workflow_id="wf-123",
            status="running",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert item.workflow_id == "wf-123"
        assert item.status == "running"

    def test_workflow_detail(self):
        """WorkflowDetail schema works."""
        from app.platforms.newsletter.routers.workflows import WorkflowDetail

        detail = WorkflowDetail(
            workflow_id="wf-123",
            user_id="user-456",
            status="awaiting_approval",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert detail.workflow_id == "wf-123"
        assert detail.status == "awaiting_approval"

    def test_checkpoint_detail(self):
        """CheckpointDetail schema works."""
        from app.platforms.newsletter.routers.workflows import CheckpointDetail

        detail = CheckpointDetail(
            checkpoint_id="ckpt-123",
            checkpoint_type="article_review",
            title="Review Articles",
            description="Review the selected articles",
            data={"articles": []},
            actions=["approve", "edit", "reject"],
        )
        assert detail.checkpoint_id == "ckpt-123"
        assert "approve" in detail.actions


class TestCampaignsSchemas:
    """Test campaign endpoint schemas."""

    def test_campaign_create_request(self):
        """CampaignCreateRequest schema works."""
        from app.platforms.newsletter.routers.campaigns import CampaignCreateRequest

        request = CampaignCreateRequest(
            name="My Campaign",
            subject="Weekly Newsletter",
        )
        assert request.name == "My Campaign"
        assert request.subject == "Weekly Newsletter"

    def test_campaign_analytics(self):
        """CampaignAnalytics schema works."""
        from app.platforms.newsletter.routers.campaigns import CampaignAnalytics

        analytics = CampaignAnalytics(
            recipient_count=100,
            delivered_count=98,
            open_rate=0.45,
        )
        assert analytics.recipient_count == 100
        assert analytics.open_rate == 0.45

    def test_send_result(self):
        """SendResult schema works."""
        from app.platforms.newsletter.routers.campaigns import SendResult

        result = SendResult(
            success=True,
            campaign_id="camp-123",
            recipient_count=100,
            sent_count=98,
            failed_count=2,
            message="Campaign sent",
        )
        assert result.success is True
        assert result.sent_count == 98


class TestSubscribersSchemas:
    """Test subscriber endpoint schemas."""

    def test_subscriber_create_request(self):
        """SubscriberCreateRequest schema works."""
        from app.platforms.newsletter.routers.subscribers import SubscriberCreateRequest

        request = SubscriberCreateRequest(
            email="test@example.com",
            name="Test User",
        )
        assert request.email == "test@example.com"
        assert request.name == "Test User"

    def test_subscriber_preferences(self):
        """SubscriberPreferences schema works."""
        from app.platforms.newsletter.routers.subscribers import SubscriberPreferences

        prefs = SubscriberPreferences(
            topics=["AI", "ML"],
            tone="casual",
            frequency="weekly",
        )
        assert "AI" in prefs.topics
        assert prefs.tone == "casual"

    def test_import_result(self):
        """ImportResult schema works."""
        from app.platforms.newsletter.routers.subscribers import ImportResult

        result = ImportResult(
            success=True,
            created=50,
            skipped=5,
            errors=["Row 3: invalid email"],
        )
        assert result.created == 50
        assert len(result.errors) == 1


class TestTemplatesSchemas:
    """Test template endpoint schemas."""

    def test_template_create_request(self):
        """TemplateCreateRequest schema works."""
        from app.platforms.newsletter.routers.templates import TemplateCreateRequest

        request = TemplateCreateRequest(
            name="My Template",
            html_content="<html>{{content}}</html>",
        )
        assert request.name == "My Template"

    def test_template_variable(self):
        """TemplateVariable schema works."""
        from app.platforms.newsletter.routers.templates import TemplateVariable

        var = TemplateVariable(
            name="content",
            description="Main content",
            required=True,
        )
        assert var.name == "content"
        assert var.required is True

    def test_template_preview_response(self):
        """TemplatePreviewResponse schema works."""
        from app.platforms.newsletter.routers.templates import TemplatePreviewResponse

        response = TemplatePreviewResponse(
            html="<html>Hello World</html>",
            plain_text="Hello World",
            subject="Test Subject",
        )
        assert "Hello World" in response.html


class TestAnalyticsSchemas:
    """Test analytics endpoint schemas."""

    def test_dashboard_metrics(self):
        """DashboardMetrics schema works."""
        from app.platforms.newsletter.routers.analytics import DashboardMetrics

        metrics = DashboardMetrics(
            total_newsletters=10,
            total_campaigns=5,
            total_subscribers=100,
            average_open_rate=0.35,
        )
        assert metrics.total_newsletters == 10
        assert metrics.average_open_rate == 0.35

    def test_campaign_metrics(self):
        """CampaignMetrics schema works."""
        from app.platforms.newsletter.routers.analytics import CampaignMetrics

        metrics = CampaignMetrics(
            campaign_id="camp-123",
            campaign_name="Weekly Update",
            subject="This Week's News",
            recipient_count=100,
            open_rate=0.45,
        )
        assert metrics.campaign_id == "camp-123"

    def test_engagement_summary(self):
        """EngagementSummary schema works."""
        from app.platforms.newsletter.routers.analytics import EngagementSummary

        summary = EngagementSummary(
            period="30d",
            total_sent=1000,
            total_opens=450,
            average_open_rate=0.45,
        )
        assert summary.period == "30d"


class TestNewslettersEndpoints:
    """Test newsletters router endpoints."""

    @pytest.mark.asyncio
    async def test_list_newsletters(self):
        """list_newsletters returns newsletters."""
        from app.platforms.newsletter.routers.newsletters import list_newsletters

        mock_repo = MagicMock()
        mock_repo.find_by_user = AsyncMock(return_value=[
            {
                "id": "nl-1",
                "title": "Newsletter 1",
                "status": "draft",
                "topics_covered": [],
                "tone_used": "professional",
                "word_count": 500,
                "created_at": datetime.now(timezone.utc),
                "sent_at": None,
            }
        ])
        mock_repo.count_by_user = AsyncMock(return_value=1)

        with patch("app.platforms.newsletter.routers.newsletters.get_newsletter_repository", return_value=mock_repo):
            result = await list_newsletters(status=None, skip=0, limit=20, current_user=MOCK_USER)

            assert result.total == 1
            assert len(result.items) == 1
            assert result.items[0].id == "nl-1"

    @pytest.mark.asyncio
    async def test_get_newsletter(self):
        """get_newsletter returns newsletter details."""
        from app.platforms.newsletter.routers.newsletters import get_newsletter

        mock_repo = MagicMock()
        mock_repo.find_by_id = AsyncMock(return_value={
            "id": "nl-1",
            "user_id": "test-user-123",
            "title": "Newsletter 1",
            "status": "draft",
            "created_at": datetime.now(timezone.utc),
        })

        with patch("app.platforms.newsletter.routers.newsletters.get_newsletter_repository", return_value=mock_repo):
            result = await get_newsletter("nl-1", current_user=MOCK_USER)

            assert result.id == "nl-1"
            assert result.title == "Newsletter 1"

    @pytest.mark.asyncio
    async def test_delete_newsletter(self):
        """delete_newsletter removes newsletter."""
        from app.platforms.newsletter.routers.newsletters import delete_newsletter

        mock_repo = MagicMock()
        mock_repo.find_by_id = AsyncMock(return_value={
            "id": "nl-1",
            "user_id": "test-user-123",
            "status": "draft",
        })
        mock_repo.delete = AsyncMock(return_value=True)

        with patch("app.platforms.newsletter.routers.newsletters.get_newsletter_repository", return_value=mock_repo):
            result = await delete_newsletter("nl-1", current_user=MOCK_USER)

            assert result["success"] is True


class TestCampaignsEndpoints:
    """Test campaigns router endpoints."""

    @pytest.mark.asyncio
    async def test_create_campaign(self):
        """create_campaign creates new campaign."""
        from app.platforms.newsletter.routers.campaigns import create_campaign, CampaignCreateRequest

        mock_repo = MagicMock()
        mock_repo.create = AsyncMock(return_value={
            "id": "camp-1",
            "user_id": "test-user-123",
            "name": "My Campaign",
            "subject": "Weekly Update",
            "status": "draft",
            "analytics": {},
            "created_at": datetime.now(timezone.utc),
        })

        request = CampaignCreateRequest(name="My Campaign", subject="Weekly Update")

        with patch("app.platforms.newsletter.routers.campaigns.get_campaign_repository", return_value=mock_repo):
            result = await create_campaign(request, current_user=MOCK_USER)

            assert result.id == "camp-1"
            assert result.name == "My Campaign"

    @pytest.mark.asyncio
    async def test_list_campaigns(self):
        """list_campaigns returns campaigns."""
        from app.platforms.newsletter.routers.campaigns import list_campaigns

        mock_repo = MagicMock()
        mock_repo.find_by_user = AsyncMock(return_value=[
            {
                "id": "camp-1",
                "name": "Campaign 1",
                "subject": "Subject 1",
                "status": "draft",
                "analytics": {},
                "created_at": datetime.now(timezone.utc),
            }
        ])
        mock_repo.count_by_user = AsyncMock(return_value=1)

        with patch("app.platforms.newsletter.routers.campaigns.get_campaign_repository", return_value=mock_repo):
            result = await list_campaigns(status=None, skip=0, limit=20, current_user=MOCK_USER)

            assert result.total == 1
            assert len(result.items) == 1


class TestSubscribersEndpoints:
    """Test subscribers router endpoints."""

    @pytest.mark.asyncio
    async def test_create_subscriber(self):
        """create_subscriber adds new subscriber."""
        from app.platforms.newsletter.routers.subscribers import create_subscriber, SubscriberCreateRequest

        mock_repo = MagicMock()
        mock_repo.find_by_email = AsyncMock(return_value=None)
        mock_repo.create = AsyncMock(return_value={
            "id": "sub-1",
            "user_id": "test-user-123",
            "email": "new@example.com",
            "name": "New User",
            "status": "subscribed",
            "preferences": {},
            "engagement": {},
            "subscribed_at": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc),
        })

        request = SubscriberCreateRequest(email="new@example.com", name="New User")

        with patch("app.platforms.newsletter.routers.subscribers.get_subscriber_repository", return_value=mock_repo):
            result = await create_subscriber(request, current_user=MOCK_USER)

            assert result.id == "sub-1"
            assert result.email == "new@example.com"

    @pytest.mark.asyncio
    async def test_list_subscribers(self):
        """list_subscribers returns subscribers."""
        from app.platforms.newsletter.routers.subscribers import list_subscribers

        mock_repo = MagicMock()
        mock_repo.find_by_user = AsyncMock(return_value=[
            {
                "id": "sub-1",
                "email": "test@example.com",
                "status": "subscribed",
                "engagement": {},
                "subscribed_at": datetime.now(timezone.utc),
            }
        ])
        mock_repo.count_by_user = AsyncMock(return_value=1)

        with patch("app.platforms.newsletter.routers.subscribers.get_subscriber_repository", return_value=mock_repo):
            result = await list_subscribers(status=None, tag=None, group=None, skip=0, limit=50, current_user=MOCK_USER)

            assert result.total == 1

    @pytest.mark.asyncio
    async def test_import_subscribers(self):
        """import_subscribers bulk imports."""
        from app.platforms.newsletter.routers.subscribers import (
            import_subscribers,
            BulkImportRequest,
            ImportSubscriber,
        )

        mock_repo = MagicMock()
        mock_repo.bulk_create = AsyncMock(return_value={"created": 2, "skipped": 0})

        request = BulkImportRequest(
            subscribers=[
                ImportSubscriber(email="a@example.com"),
                ImportSubscriber(email="b@example.com"),
            ]
        )

        with patch("app.platforms.newsletter.routers.subscribers.get_subscriber_repository", return_value=mock_repo):
            result = await import_subscribers(request, current_user=MOCK_USER)

            assert result.success is True
            assert result.created == 2


class TestTemplatesEndpoints:
    """Test templates router endpoints."""

    @pytest.mark.asyncio
    async def test_create_template(self):
        """create_template creates new template."""
        from app.platforms.newsletter.routers.templates import create_template, TemplateCreateRequest

        mock_repo = MagicMock()
        mock_repo.create = AsyncMock(return_value={
            "id": "tpl-1",
            "user_id": "test-user-123",
            "name": "My Template",
            "category": "newsletter",
            "created_at": datetime.now(timezone.utc),
        })

        request = TemplateCreateRequest(name="My Template")

        with patch("app.platforms.newsletter.routers.templates.get_template_repository", return_value=mock_repo):
            result = await create_template(request, current_user=MOCK_USER)

            assert result.id == "tpl-1"
            assert result.name == "My Template"

    @pytest.mark.asyncio
    async def test_preview_template(self):
        """preview_template renders with variables."""
        from app.platforms.newsletter.routers.templates import preview_template, TemplatePreviewRequest

        mock_repo = MagicMock()
        mock_repo.find_by_id = AsyncMock(return_value={
            "id": "tpl-1",
            "user_id": "test-user-123",
            "html_content": "<html>Hello {{name}}</html>",
            "plain_text_content": "Hello {{name}}",
            "subject_template": "Welcome {{name}}",
        })

        request = TemplatePreviewRequest(variables={"name": "World"})

        with patch("app.platforms.newsletter.routers.templates.get_template_repository", return_value=mock_repo):
            result = await preview_template(request, "tpl-1", current_user=MOCK_USER)

            assert "Hello World" in result.html
            assert "Welcome World" in result.subject


class TestAnalyticsEndpoints:
    """Test analytics router endpoints."""

    @pytest.mark.asyncio
    async def test_get_dashboard_metrics(self):
        """get_dashboard_metrics returns aggregate metrics."""
        from app.platforms.newsletter.routers.analytics import get_dashboard_metrics

        mock_nl_repo = MagicMock()
        mock_nl_repo.count_by_user = AsyncMock(return_value=10)

        mock_camp_repo = MagicMock()
        mock_camp_repo.count_by_user = AsyncMock(return_value=5)
        mock_camp_repo.find_by_user = AsyncMock(return_value=[])

        mock_sub_repo = MagicMock()
        mock_sub_repo.count_by_user = AsyncMock(return_value=100)

        with patch("app.platforms.newsletter.routers.analytics.get_newsletter_repository", return_value=mock_nl_repo), \
             patch("app.platforms.newsletter.routers.analytics.get_campaign_repository", return_value=mock_camp_repo), \
             patch("app.platforms.newsletter.routers.analytics.get_subscriber_repository", return_value=mock_sub_repo):

            result = await get_dashboard_metrics(current_user=MOCK_USER)

            assert result.total_newsletters == 10
            assert result.total_campaigns == 5
            assert result.total_subscribers == 100

    @pytest.mark.asyncio
    async def test_get_campaign_analytics(self):
        """get_campaign_analytics returns campaign metrics."""
        from app.platforms.newsletter.routers.analytics import get_campaign_analytics

        mock_repo = MagicMock()
        mock_repo.find_by_id = AsyncMock(return_value={
            "id": "camp-1",
            "user_id": "test-user-123",
            "name": "My Campaign",
            "subject": "Weekly Update",
            "analytics": {
                "recipient_count": 100,
                "delivered_count": 98,
                "open_rate": 0.45,
            },
        })

        with patch("app.platforms.newsletter.routers.analytics.get_campaign_repository", return_value=mock_repo):
            result = await get_campaign_analytics("camp-1", current_user=MOCK_USER)

            assert result.campaign_id == "camp-1"
            assert result.recipient_count == 100


class TestMainRouterIntegration:
    """Test main router includes all sub-routers."""

    def test_main_router_imports(self):
        """Main router can be imported with all sub-routers."""
        from app.platforms.newsletter.router import router
        assert router is not None

    def test_router_has_routes(self):
        """Main router has expected routes."""
        from app.platforms.newsletter.router import router

        route_paths = [route.path for route in router.routes]

        # Check for some expected routes
        assert "/status" in route_paths
        assert "/health" in route_paths
        assert "/agents" in route_paths


class TestEndpointAuthentication:
    """Test that endpoints require authentication."""

    def test_newsletters_requires_auth(self):
        """Newsletter endpoints have auth dependency."""
        from app.platforms.newsletter.routers.newsletters import list_newsletters
        import inspect

        sig = inspect.signature(list_newsletters)
        param_names = list(sig.parameters.keys())
        assert "current_user" in param_names

    def test_campaigns_requires_auth(self):
        """Campaign endpoints have auth dependency."""
        from app.platforms.newsletter.routers.campaigns import create_campaign
        import inspect

        sig = inspect.signature(create_campaign)
        param_names = list(sig.parameters.keys())
        assert "current_user" in param_names

    def test_subscribers_requires_auth(self):
        """Subscriber endpoints have auth dependency."""
        from app.platforms.newsletter.routers.subscribers import list_subscribers
        import inspect

        sig = inspect.signature(list_subscribers)
        param_names = list(sig.parameters.keys())
        assert "current_user" in param_names
