"""
Newsletter Platform model tests.

Tests for Pydantic models: Newsletter, Subscriber, Campaign, Template.
Marked as @stable - these tests should pass across all phases.
"""
import pytest
from datetime import datetime


@pytest.mark.stable
class TestNewsletterModel:
    """Test Newsletter model."""

    def test_newsletter_model_import(self):
        """Test that Newsletter model can be imported."""
        from app.platforms.newsletter.models import Newsletter
        assert Newsletter is not None

    def test_newsletter_status_enum_import(self):
        """Test that NewsletterStatus enum can be imported."""
        from app.platforms.newsletter.models import NewsletterStatus
        assert NewsletterStatus.DRAFT == "draft"
        assert NewsletterStatus.GENERATING == "generating"
        assert NewsletterStatus.READY == "ready"
        assert NewsletterStatus.SENT == "sent"

    def test_newsletter_model_creation(self):
        """Test creating a Newsletter instance."""
        from app.platforms.newsletter.models import Newsletter

        newsletter = Newsletter(
            user_id="test-user",
            title="Test Newsletter",
            topics_covered=["AI", "tech"],
            tone_used="professional",
        )

        assert newsletter.user_id == "test-user"
        assert newsletter.title == "Test Newsletter"
        assert newsletter.topics_covered == ["AI", "tech"]
        assert newsletter.status == "draft"
        assert newsletter.word_count == 0
        assert newsletter.content == ""

    def test_newsletter_model_with_content(self):
        """Test Newsletter with full content."""
        from app.platforms.newsletter.models import Newsletter

        newsletter = Newsletter(
            user_id="test-user",
            title="Full Newsletter",
            content="# Hello World\n\nThis is content.",
            html_content="<h1>Hello World</h1><p>This is content.</p>",
            plain_text="Hello World\n\nThis is content.",
            word_count=5,
            read_time_minutes=1,
        )

        assert newsletter.content.startswith("# Hello")
        assert newsletter.html_content.startswith("<h1>")
        assert newsletter.word_count == 5

    def test_newsletter_model_id_alias(self):
        """Test Newsletter _id alias works correctly."""
        from app.platforms.newsletter.models import Newsletter

        newsletter = Newsletter(
            _id="507f1f77bcf86cd799439011",
            user_id="test-user",
            title="Test",
        )

        assert newsletter.id == "507f1f77bcf86cd799439011"


@pytest.mark.stable
class TestSubscriberModel:
    """Test Subscriber model."""

    def test_subscriber_model_import(self):
        """Test that Subscriber model can be imported."""
        from app.platforms.newsletter.models import Subscriber
        assert Subscriber is not None

    def test_subscriber_status_enum_import(self):
        """Test that SubscriberStatus enum can be imported."""
        from app.platforms.newsletter.models import SubscriberStatus
        assert SubscriberStatus.SUBSCRIBED == "subscribed"
        assert SubscriberStatus.UNSUBSCRIBED == "unsubscribed"
        assert SubscriberStatus.BOUNCED == "bounced"

    def test_subscriber_preferences_model(self):
        """Test SubscriberPreferences model."""
        from app.platforms.newsletter.models import SubscriberPreferences

        prefs = SubscriberPreferences(
            topics=["AI", "tech"],
            tone="casual",
            frequency="daily",
        )

        assert prefs.topics == ["AI", "tech"]
        assert prefs.tone == "casual"
        assert prefs.frequency == "daily"
        assert prefs.include_mindmap is True  # default

    def test_engagement_metrics_model(self):
        """Test EngagementMetrics model."""
        from app.platforms.newsletter.models import EngagementMetrics

        metrics = EngagementMetrics(
            emails_received=10,
            emails_opened=8,
            emails_clicked=3,
        )

        assert metrics.emails_received == 10
        assert metrics.open_rate == 0.0  # Not calculated automatically

    def test_subscriber_model_creation(self):
        """Test creating a Subscriber instance."""
        from app.platforms.newsletter.models import Subscriber, SubscriberPreferences

        subscriber = Subscriber(
            user_id="test-user",
            email="test@example.com",
            name="Test User",
            preferences=SubscriberPreferences(topics=["AI"]),
        )

        assert subscriber.email == "test@example.com"
        assert subscriber.status == "subscribed"
        assert subscriber.preferences.topics == ["AI"]
        assert subscriber.tags == []


@pytest.mark.stable
class TestCampaignModel:
    """Test Campaign model."""

    def test_campaign_model_import(self):
        """Test that Campaign model can be imported."""
        from app.platforms.newsletter.models import Campaign
        assert Campaign is not None

    def test_campaign_status_enum_import(self):
        """Test that CampaignStatus enum can be imported."""
        from app.platforms.newsletter.models import CampaignStatus
        assert CampaignStatus.DRAFT == "draft"
        assert CampaignStatus.SCHEDULED == "scheduled"
        assert CampaignStatus.SENT == "sent"

    def test_campaign_analytics_model(self):
        """Test CampaignAnalytics model."""
        from app.platforms.newsletter.models import CampaignAnalytics

        analytics = CampaignAnalytics(
            recipient_count=100,
            delivered_count=95,
            open_count=50,
        )

        assert analytics.recipient_count == 100
        assert analytics.delivered_count == 95
        assert analytics.delivery_rate == 0.0  # Not calculated automatically

    def test_campaign_model_creation(self):
        """Test creating a Campaign instance."""
        from app.platforms.newsletter.models import Campaign

        campaign = Campaign(
            user_id="test-user",
            name="Test Campaign",
            subject="Hello World",
        )

        assert campaign.name == "Test Campaign"
        assert campaign.subject == "Hello World"
        assert campaign.status == "draft"
        assert campaign.subscriber_tags == []


@pytest.mark.stable
class TestTemplateModel:
    """Test Template model."""

    def test_template_model_import(self):
        """Test that Template model can be imported."""
        from app.platforms.newsletter.models import Template
        assert Template is not None

    def test_template_category_enum_import(self):
        """Test that TemplateCategory enum can be imported."""
        from app.platforms.newsletter.models import TemplateCategory
        assert TemplateCategory.NEWSLETTER == "newsletter"
        assert TemplateCategory.ANNOUNCEMENT == "announcement"

    def test_template_variable_model(self):
        """Test TemplateVariable model."""
        from app.platforms.newsletter.models import TemplateVariable

        var = TemplateVariable(
            name="title",
            description="Newsletter title",
            default_value="My Newsletter",
            required=True,
        )

        assert var.name == "title"
        assert var.required is True

    def test_template_model_creation(self):
        """Test creating a Template instance."""
        from app.platforms.newsletter.models import Template

        template = Template(
            user_id="test-user",
            name="Default Template",
            html_content="<h1>{{title}}</h1>",
            plain_text_content="{{title}}",
        )

        assert template.name == "Default Template"
        assert template.category == "newsletter"
        assert template.is_active is True
        assert template.usage_count == 0


@pytest.mark.stable
class TestModelsExport:
    """Test that all models are properly exported."""

    def test_all_models_in_init(self):
        """Test all models are exported from __init__.py."""
        from app.platforms.newsletter.models import (
            Newsletter,
            NewsletterStatus,
            Subscriber,
            SubscriberStatus,
            SubscriberPreferences,
            EngagementMetrics,
            Campaign,
            CampaignStatus,
            CampaignAnalytics,
            Template,
            TemplateCategory,
            TemplateVariable,
        )

        # All should be importable
        assert Newsletter is not None
        assert NewsletterStatus is not None
        assert Subscriber is not None
        assert SubscriberStatus is not None
        assert SubscriberPreferences is not None
        assert EngagementMetrics is not None
        assert Campaign is not None
        assert CampaignStatus is not None
        assert CampaignAnalytics is not None
        assert Template is not None
        assert TemplateCategory is not None
        assert TemplateVariable is not None
