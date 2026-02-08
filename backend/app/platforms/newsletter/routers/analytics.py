"""
Analytics API endpoints for Newsletter Platform.

Phase 11: Analytics and reporting endpoints.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from pydantic import BaseModel

from app.core.security import get_current_user
from app.platforms.newsletter.repositories import (
    get_campaign_repository,
    get_newsletter_repository,
    get_subscriber_repository,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


# Response schemas
class DashboardMetrics(BaseModel):
    """Overall dashboard metrics."""
    total_newsletters: int = 0
    total_campaigns: int = 0
    total_subscribers: int = 0
    active_subscribers: int = 0

    # Recent activity (last 30 days)
    newsletters_created: int = 0
    campaigns_sent: int = 0
    new_subscribers: int = 0
    unsubscribes: int = 0

    # Aggregate performance
    average_open_rate: float = 0.0
    average_click_rate: float = 0.0
    total_emails_sent: int = 0


class CampaignMetrics(BaseModel):
    """Detailed metrics for a campaign."""
    campaign_id: str
    campaign_name: str
    subject: str
    sent_at: Optional[datetime] = None

    # Delivery metrics
    recipient_count: int = 0
    delivered_count: int = 0
    bounced_count: int = 0
    delivery_rate: float = 0.0
    bounce_rate: float = 0.0

    # Engagement metrics
    open_count: int = 0
    unique_open_count: int = 0
    click_count: int = 0
    unique_click_count: int = 0
    open_rate: float = 0.0
    click_rate: float = 0.0

    # Negative metrics
    unsubscribe_count: int = 0
    spam_count: int = 0
    unsubscribe_rate: float = 0.0


class EngagementSummary(BaseModel):
    """Engagement summary over time."""
    period: str  # "7d", "30d", "90d"
    total_sent: int = 0
    total_delivered: int = 0
    total_opens: int = 0
    total_clicks: int = 0
    average_open_rate: float = 0.0
    average_click_rate: float = 0.0


class TopCampaign(BaseModel):
    """Top performing campaign."""
    campaign_id: str
    campaign_name: str
    metric_value: float
    sent_at: Optional[datetime] = None


class EngagementResponse(BaseModel):
    """Engagement analytics response."""
    summary: EngagementSummary
    top_by_opens: List[TopCampaign] = []
    top_by_clicks: List[TopCampaign] = []


class SubscriberGrowth(BaseModel):
    """Subscriber growth metrics."""
    date: str  # YYYY-MM-DD
    new_subscribers: int = 0
    unsubscribes: int = 0
    net_growth: int = 0
    total: int = 0


class SubscriberAnalytics(BaseModel):
    """Subscriber analytics response."""
    total: int = 0
    active: int = 0
    unsubscribed: int = 0
    bounced: int = 0
    growth: List[SubscriberGrowth] = []
    top_sources: Dict[str, int] = {}
    engagement_distribution: Dict[str, int] = {}


@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    current_user: dict = Depends(get_current_user),
):
    """
    Get overall dashboard metrics.

    Returns aggregate metrics for newsletters, campaigns, and subscribers.
    """
    try:
        newsletter_repo = get_newsletter_repository()
        campaign_repo = get_campaign_repository()
        subscriber_repo = get_subscriber_repository()

        user_id = current_user["id"]

        # Get totals
        total_newsletters = await newsletter_repo.count_by_user(user_id)
        total_campaigns = await campaign_repo.count_by_user(user_id)
        total_subscribers = await subscriber_repo.count_by_user(user_id)
        active_subscribers = await subscriber_repo.count_by_user(
            user_id, status="subscribed"
        )

        # Get campaigns for aggregate metrics
        campaigns = await campaign_repo.find_by_user(user_id, status="sent", limit=100)

        total_emails_sent = 0
        total_opens = 0
        total_delivered = 0

        for campaign in campaigns:
            analytics = campaign.get("analytics", {})
            total_emails_sent += analytics.get("recipient_count", 0)
            total_delivered += analytics.get("delivered_count", 0)
            total_opens += analytics.get("unique_open_count", 0)

        average_open_rate = (total_opens / total_delivered) if total_delivered > 0 else 0

        # Calculate click rate
        total_clicks = sum(
            c.get("analytics", {}).get("unique_click_count", 0)
            for c in campaigns
        )
        average_click_rate = (total_clicks / total_delivered) if total_delivered > 0 else 0

        return DashboardMetrics(
            total_newsletters=total_newsletters,
            total_campaigns=total_campaigns,
            total_subscribers=total_subscribers,
            active_subscribers=active_subscribers,
            newsletters_created=total_newsletters,  # Would need date filter for accurate count
            campaigns_sent=len(campaigns),
            new_subscribers=active_subscribers,  # Would need date filter
            unsubscribes=total_subscribers - active_subscribers,
            average_open_rate=round(average_open_rate, 4),
            average_click_rate=round(average_click_rate, 4),
            total_emails_sent=total_emails_sent,
        )

    except Exception as e:
        logger.error(f"Get dashboard metrics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/campaigns/{campaign_id}", response_model=CampaignMetrics)
async def get_campaign_analytics(
    campaign_id: str = Path(..., description="Campaign ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get detailed analytics for a specific campaign.

    Returns delivery and engagement metrics.
    """
    try:
        repo = get_campaign_repository()
        campaign = await repo.find_by_id(campaign_id)

        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        if campaign.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        analytics = campaign.get("analytics", {})

        return CampaignMetrics(
            campaign_id=campaign["id"],
            campaign_name=campaign["name"],
            subject=campaign["subject"],
            sent_at=campaign.get("sent_at"),
            recipient_count=analytics.get("recipient_count", 0),
            delivered_count=analytics.get("delivered_count", 0),
            bounced_count=analytics.get("bounced_count", 0),
            delivery_rate=analytics.get("delivery_rate", 0.0),
            bounce_rate=analytics.get("bounce_rate", 0.0),
            open_count=analytics.get("open_count", 0),
            unique_open_count=analytics.get("unique_open_count", 0),
            click_count=analytics.get("click_count", 0),
            unique_click_count=analytics.get("unique_click_count", 0),
            open_rate=analytics.get("open_rate", 0.0),
            click_rate=analytics.get("click_rate", 0.0),
            unsubscribe_count=analytics.get("unsubscribe_count", 0),
            spam_count=analytics.get("spam_count", 0),
            unsubscribe_rate=analytics.get("unsubscribe_rate", 0.0),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get campaign analytics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/engagement", response_model=EngagementResponse)
async def get_engagement_analytics(
    period: str = Query("30d", description="Time period: 7d, 30d, 90d"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get engagement analytics over time.

    Returns aggregate engagement metrics and top performing campaigns.
    """
    try:
        repo = get_campaign_repository()
        user_id = current_user["id"]

        # Parse period
        days = 30
        if period == "7d":
            days = 7
        elif period == "90d":
            days = 90

        # Get sent campaigns
        campaigns = await repo.find_by_user(user_id, status="sent", limit=100)

        # Calculate aggregate metrics
        total_sent = 0
        total_delivered = 0
        total_opens = 0
        total_clicks = 0

        campaign_metrics = []

        for campaign in campaigns:
            analytics = campaign.get("analytics", {})
            delivered = analytics.get("delivered_count", 0)
            opens = analytics.get("unique_open_count", 0)
            clicks = analytics.get("unique_click_count", 0)

            total_sent += analytics.get("recipient_count", 0)
            total_delivered += delivered
            total_opens += opens
            total_clicks += clicks

            if delivered > 0:
                campaign_metrics.append({
                    "campaign_id": campaign["id"],
                    "campaign_name": campaign["name"],
                    "sent_at": campaign.get("sent_at"),
                    "open_rate": opens / delivered,
                    "click_rate": clicks / delivered,
                    "opens": opens,
                    "clicks": clicks,
                })

        average_open_rate = (total_opens / total_delivered) if total_delivered > 0 else 0
        average_click_rate = (total_clicks / total_delivered) if total_delivered > 0 else 0

        # Sort for top campaigns
        by_opens = sorted(campaign_metrics, key=lambda x: x["opens"], reverse=True)[:5]
        by_clicks = sorted(campaign_metrics, key=lambda x: x["clicks"], reverse=True)[:5]

        return EngagementResponse(
            summary=EngagementSummary(
                period=period,
                total_sent=total_sent,
                total_delivered=total_delivered,
                total_opens=total_opens,
                total_clicks=total_clicks,
                average_open_rate=round(average_open_rate, 4),
                average_click_rate=round(average_click_rate, 4),
            ),
            top_by_opens=[
                TopCampaign(
                    campaign_id=c["campaign_id"],
                    campaign_name=c["campaign_name"],
                    metric_value=c["open_rate"],
                    sent_at=c["sent_at"],
                )
                for c in by_opens
            ],
            top_by_clicks=[
                TopCampaign(
                    campaign_id=c["campaign_id"],
                    campaign_name=c["campaign_name"],
                    metric_value=c["click_rate"],
                    sent_at=c["sent_at"],
                )
                for c in by_clicks
            ],
        )

    except Exception as e:
        logger.error(f"Get engagement analytics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subscribers", response_model=SubscriberAnalytics)
async def get_subscriber_analytics(
    current_user: dict = Depends(get_current_user),
):
    """
    Get subscriber analytics.

    Returns subscriber counts, status distribution, and sources.
    """
    try:
        repo = get_subscriber_repository()
        user_id = current_user["id"]

        # Get counts by status
        total = await repo.count_by_user(user_id)
        active = await repo.count_by_user(user_id, status="subscribed")
        unsubscribed = await repo.count_by_user(user_id, status="unsubscribed")
        bounced = await repo.count_by_user(user_id, status="bounced")

        # Get subscribers to analyze sources and engagement
        subscribers = await repo.find_by_user(user_id, limit=1000)

        # Count by source
        sources: Dict[str, int] = {}
        for sub in subscribers:
            source = sub.get("source", "unknown")
            sources[source] = sources.get(source, 0) + 1

        # Engagement distribution (based on open rate)
        engagement_dist: Dict[str, int] = {
            "highly_engaged": 0,  # > 50% open rate
            "engaged": 0,         # 20-50% open rate
            "low_engagement": 0,  # 1-20% open rate
            "inactive": 0,        # 0% open rate
        }

        for sub in subscribers:
            open_rate = sub.get("engagement", {}).get("open_rate", 0)
            if open_rate > 0.5:
                engagement_dist["highly_engaged"] += 1
            elif open_rate > 0.2:
                engagement_dist["engaged"] += 1
            elif open_rate > 0:
                engagement_dist["low_engagement"] += 1
            else:
                engagement_dist["inactive"] += 1

        return SubscriberAnalytics(
            total=total,
            active=active,
            unsubscribed=unsubscribed,
            bounced=bounced,
            growth=[],  # Would need historical data for accurate growth tracking
            top_sources=sources,
            engagement_distribution=engagement_dist,
        )

    except Exception as e:
        logger.error(f"Get subscriber analytics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
async def export_analytics(
    format: str = Query("json", description="Export format: json or csv"),
    current_user: dict = Depends(get_current_user),
):
    """
    Export analytics data.

    Returns analytics data in the requested format.
    """
    try:
        # Get all analytics
        dashboard = await get_dashboard_metrics(current_user)
        engagement = await get_engagement_analytics("30d", current_user)
        subscribers = await get_subscriber_analytics(current_user)

        export_data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "user_id": current_user["id"],
            "dashboard": dashboard.model_dump(),
            "engagement": engagement.model_dump(),
            "subscribers": subscribers.model_dump(),
        }

        if format == "csv":
            # For CSV, we'll return a simplified flat structure
            # In a real implementation, you'd generate proper CSV files
            return {
                "message": "CSV export not implemented - use JSON format",
                "data": export_data,
            }

        return export_data

    except Exception as e:
        logger.error(f"Export analytics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
