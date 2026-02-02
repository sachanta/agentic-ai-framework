"""
Newsletter Platform repository tests.

Tests for repository imports and structure.
Marked as @stable - these tests should pass across all phases.
"""
import pytest


@pytest.mark.stable
class TestNewsletterRepository:
    """Test NewsletterRepository class."""

    def test_newsletter_repository_import(self):
        """Test that NewsletterRepository can be imported."""
        from app.platforms.newsletter.repositories import NewsletterRepository
        assert NewsletterRepository is not None

    def test_newsletter_repository_factory(self):
        """Test that get_newsletter_repository factory works."""
        from app.platforms.newsletter.repositories import get_newsletter_repository
        assert callable(get_newsletter_repository)

    def test_newsletter_repository_has_collection_name(self):
        """Test NewsletterRepository has collection_name."""
        from app.platforms.newsletter.repositories import NewsletterRepository
        assert NewsletterRepository.collection_name == "newsletters"

    def test_newsletter_repository_has_crud_methods(self):
        """Test NewsletterRepository has expected CRUD methods."""
        from app.platforms.newsletter.repositories import NewsletterRepository

        repo = NewsletterRepository()

        # Check core methods exist
        assert hasattr(repo, "create")
        assert hasattr(repo, "find_by_id")
        assert hasattr(repo, "find_by_user")
        assert hasattr(repo, "update")
        assert hasattr(repo, "delete")

        # Check specialized methods exist
        assert hasattr(repo, "update_status")
        assert hasattr(repo, "update_content")
        assert hasattr(repo, "update_research_data")


@pytest.mark.stable
class TestSubscriberRepository:
    """Test SubscriberRepository class."""

    def test_subscriber_repository_import(self):
        """Test that SubscriberRepository can be imported."""
        from app.platforms.newsletter.repositories import SubscriberRepository
        assert SubscriberRepository is not None

    def test_subscriber_repository_factory(self):
        """Test that get_subscriber_repository factory works."""
        from app.platforms.newsletter.repositories import get_subscriber_repository
        assert callable(get_subscriber_repository)

    def test_subscriber_repository_has_collection_name(self):
        """Test SubscriberRepository has collection_name."""
        from app.platforms.newsletter.repositories import SubscriberRepository
        assert SubscriberRepository.collection_name == "newsletter_subscribers"

    def test_subscriber_repository_has_crud_methods(self):
        """Test SubscriberRepository has expected CRUD methods."""
        from app.platforms.newsletter.repositories import SubscriberRepository

        repo = SubscriberRepository()

        # Check core methods exist
        assert hasattr(repo, "create")
        assert hasattr(repo, "find_by_id")
        assert hasattr(repo, "find_by_user")
        assert hasattr(repo, "find_by_email")
        assert hasattr(repo, "update")
        assert hasattr(repo, "delete")

        # Check specialized methods exist
        assert hasattr(repo, "update_preferences")
        assert hasattr(repo, "update_engagement")
        assert hasattr(repo, "add_tags")
        assert hasattr(repo, "bulk_create")


@pytest.mark.stable
class TestCampaignRepository:
    """Test CampaignRepository class."""

    def test_campaign_repository_import(self):
        """Test that CampaignRepository can be imported."""
        from app.platforms.newsletter.repositories import CampaignRepository
        assert CampaignRepository is not None

    def test_campaign_repository_factory(self):
        """Test that get_campaign_repository factory works."""
        from app.platforms.newsletter.repositories import get_campaign_repository
        assert callable(get_campaign_repository)

    def test_campaign_repository_has_collection_name(self):
        """Test CampaignRepository has collection_name."""
        from app.platforms.newsletter.repositories import CampaignRepository
        assert CampaignRepository.collection_name == "newsletter_campaigns"

    def test_campaign_repository_has_crud_methods(self):
        """Test CampaignRepository has expected CRUD methods."""
        from app.platforms.newsletter.repositories import CampaignRepository

        repo = CampaignRepository()

        # Check core methods exist
        assert hasattr(repo, "create")
        assert hasattr(repo, "find_by_id")
        assert hasattr(repo, "find_by_user")
        assert hasattr(repo, "update")
        assert hasattr(repo, "delete")

        # Check specialized methods exist
        assert hasattr(repo, "update_status")
        assert hasattr(repo, "schedule")
        assert hasattr(repo, "update_analytics")
        assert hasattr(repo, "find_scheduled")


@pytest.mark.stable
class TestTemplateRepository:
    """Test TemplateRepository class."""

    def test_template_repository_import(self):
        """Test that TemplateRepository can be imported."""
        from app.platforms.newsletter.repositories import TemplateRepository
        assert TemplateRepository is not None

    def test_template_repository_factory(self):
        """Test that get_template_repository factory works."""
        from app.platforms.newsletter.repositories import get_template_repository
        assert callable(get_template_repository)

    def test_template_repository_has_collection_name(self):
        """Test TemplateRepository has collection_name."""
        from app.platforms.newsletter.repositories import TemplateRepository
        assert TemplateRepository.collection_name == "newsletter_templates"

    def test_template_repository_has_crud_methods(self):
        """Test TemplateRepository has expected CRUD methods."""
        from app.platforms.newsletter.repositories import TemplateRepository

        repo = TemplateRepository()

        # Check core methods exist
        assert hasattr(repo, "create")
        assert hasattr(repo, "find_by_id")
        assert hasattr(repo, "find_by_user")
        assert hasattr(repo, "update")
        assert hasattr(repo, "delete")

        # Check specialized methods exist
        assert hasattr(repo, "find_default")
        assert hasattr(repo, "set_default")
        assert hasattr(repo, "increment_usage")
        assert hasattr(repo, "duplicate")


@pytest.mark.stable
class TestRepositoriesExport:
    """Test that all repositories are properly exported."""

    def test_all_repositories_in_init(self):
        """Test all repositories are exported from __init__.py."""
        from app.platforms.newsletter.repositories import (
            NewsletterRepository,
            get_newsletter_repository,
            SubscriberRepository,
            get_subscriber_repository,
            CampaignRepository,
            get_campaign_repository,
            TemplateRepository,
            get_template_repository,
        )

        # All should be importable
        assert NewsletterRepository is not None
        assert get_newsletter_repository is not None
        assert SubscriberRepository is not None
        assert get_subscriber_repository is not None
        assert CampaignRepository is not None
        assert get_campaign_repository is not None
        assert TemplateRepository is not None
        assert get_template_repository is not None
