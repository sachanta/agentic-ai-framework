"""
Newsletter Platform data repositories.

Provides repository classes for database operations on newsletters,
subscribers, campaigns, and templates.
"""
from app.platforms.newsletter.repositories.newsletter import (
    NewsletterRepository,
    get_newsletter_repository,
)
from app.platforms.newsletter.repositories.subscriber import (
    SubscriberRepository,
    get_subscriber_repository,
)
from app.platforms.newsletter.repositories.campaign import (
    CampaignRepository,
    get_campaign_repository,
)
from app.platforms.newsletter.repositories.template import (
    TemplateRepository,
    get_template_repository,
)

__all__ = [
    # Newsletter
    "NewsletterRepository",
    "get_newsletter_repository",
    # Subscriber
    "SubscriberRepository",
    "get_subscriber_repository",
    # Campaign
    "CampaignRepository",
    "get_campaign_repository",
    # Template
    "TemplateRepository",
    "get_template_repository",
]
