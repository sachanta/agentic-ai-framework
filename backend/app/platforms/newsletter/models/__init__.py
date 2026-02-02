"""
Newsletter Platform MongoDB models.

Provides data models for newsletters, subscribers, campaigns, and templates.
"""
from app.platforms.newsletter.models.newsletter import (
    Newsletter,
    NewsletterStatus,
)
from app.platforms.newsletter.models.subscriber import (
    Subscriber,
    SubscriberStatus,
    SubscriberPreferences,
    EngagementMetrics,
)
from app.platforms.newsletter.models.campaign import (
    Campaign,
    CampaignStatus,
    CampaignAnalytics,
)
from app.platforms.newsletter.models.template import (
    Template,
    TemplateCategory,
    TemplateVariable,
)

__all__ = [
    # Newsletter
    "Newsletter",
    "NewsletterStatus",
    # Subscriber
    "Subscriber",
    "SubscriberStatus",
    "SubscriberPreferences",
    "EngagementMetrics",
    # Campaign
    "Campaign",
    "CampaignStatus",
    "CampaignAnalytics",
    # Template
    "Template",
    "TemplateCategory",
    "TemplateVariable",
]
