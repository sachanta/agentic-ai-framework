"""
Campaign management API endpoints.

Phase 11: Campaign CRUD and sending operations.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from pydantic import BaseModel, Field

from app.core.security import get_current_user
from app.platforms.newsletter.repositories import (
    get_campaign_repository,
    get_newsletter_repository,
    get_subscriber_repository,
)
from app.platforms.newsletter.services import get_email_service
from app.platforms.newsletter.models import CampaignStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


# Request/Response schemas
class CampaignCreateRequest(BaseModel):
    """Request to create a new campaign."""
    name: str = Field(..., min_length=1, max_length=200)
    subject: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    preview_text: Optional[str] = None
    newsletter_id: Optional[str] = None
    template_id: Optional[str] = None
    subscriber_tags: List[str] = []
    subscriber_groups: List[str] = []
    exclude_tags: List[str] = []
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    reply_to: Optional[str] = None


class CampaignUpdateRequest(BaseModel):
    """Request to update a campaign."""
    name: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    preview_text: Optional[str] = None
    newsletter_id: Optional[str] = None
    template_id: Optional[str] = None
    subscriber_tags: Optional[List[str]] = None
    subscriber_groups: Optional[List[str]] = None
    exclude_tags: Optional[List[str]] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    reply_to: Optional[str] = None


class ScheduleRequest(BaseModel):
    """Request to schedule a campaign."""
    scheduled_at: datetime
    send_timezone: str = "UTC"


class CampaignAnalytics(BaseModel):
    """Campaign analytics data."""
    recipient_count: int = 0
    delivered_count: int = 0
    bounced_count: int = 0
    open_count: int = 0
    unique_open_count: int = 0
    click_count: int = 0
    unique_click_count: int = 0
    unsubscribe_count: int = 0
    spam_count: int = 0
    delivery_rate: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0
    bounce_rate: float = 0.0
    unsubscribe_rate: float = 0.0


class CampaignListItem(BaseModel):
    """Brief campaign item for list views."""
    id: str
    name: str
    subject: str
    status: str
    recipient_count: int = 0
    open_rate: float = 0.0
    click_rate: float = 0.0
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None


class CampaignDetail(BaseModel):
    """Full campaign details."""
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    subject: str
    preview_text: Optional[str] = None
    newsletter_id: Optional[str] = None
    template_id: Optional[str] = None
    status: str
    subscriber_tags: List[str] = []
    subscriber_groups: List[str] = []
    exclude_tags: List[str] = []
    scheduled_at: Optional[datetime] = None
    send_timezone: str = "UTC"
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    reply_to: Optional[str] = None
    analytics: CampaignAnalytics
    created_at: datetime
    updated_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class CampaignListResponse(BaseModel):
    """Paginated campaign list response."""
    items: List[CampaignListItem]
    total: int
    skip: int
    limit: int


class SendResult(BaseModel):
    """Result of sending a campaign."""
    success: bool
    campaign_id: str
    recipient_count: int
    sent_count: int
    failed_count: int
    message: str


@router.post("", response_model=CampaignDetail)
async def create_campaign(
    request: CampaignCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new campaign.

    Creates a draft campaign that can be scheduled or sent.
    """
    try:
        repo = get_campaign_repository()
        user_id = current_user["id"]

        campaign = await repo.create(
            user_id=user_id,
            name=request.name,
            subject=request.subject,
            description=request.description,
            preview_text=request.preview_text,
            newsletter_id=request.newsletter_id,
            template_id=request.template_id,
            subscriber_tags=request.subscriber_tags,
            subscriber_groups=request.subscriber_groups,
            exclude_tags=request.exclude_tags,
            from_email=request.from_email,
            from_name=request.from_name,
            reply_to=request.reply_to,
        )

        return CampaignDetail(
            id=campaign["id"],
            user_id=campaign["user_id"],
            name=campaign["name"],
            description=campaign.get("description"),
            subject=campaign["subject"],
            preview_text=campaign.get("preview_text"),
            newsletter_id=campaign.get("newsletter_id"),
            template_id=campaign.get("template_id"),
            status=campaign["status"],
            subscriber_tags=campaign.get("subscriber_tags", []),
            subscriber_groups=campaign.get("subscriber_groups", []),
            exclude_tags=campaign.get("exclude_tags", []),
            scheduled_at=campaign.get("scheduled_at"),
            send_timezone=campaign.get("send_timezone", "UTC"),
            from_email=campaign.get("from_email"),
            from_name=campaign.get("from_name"),
            reply_to=campaign.get("reply_to"),
            analytics=CampaignAnalytics(**campaign.get("analytics", {})),
            created_at=campaign["created_at"],
            updated_at=campaign.get("updated_at"),
            sent_at=campaign.get("sent_at"),
            completed_at=campaign.get("completed_at"),
        )

    except Exception as e:
        logger.error(f"Create campaign failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=CampaignListResponse)
async def list_campaigns(
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    current_user: dict = Depends(get_current_user),
):
    """
    List user's campaigns.

    Returns a paginated list of campaigns with optional status filtering.
    """
    try:
        repo = get_campaign_repository()
        user_id = current_user["id"]

        campaigns = await repo.find_by_user(
            user_id=user_id,
            status=status,
            skip=skip,
            limit=limit,
        )
        total = await repo.count_by_user(user_id=user_id, status=status)

        items = [
            CampaignListItem(
                id=c["id"],
                name=c["name"],
                subject=c["subject"],
                status=c["status"],
                recipient_count=c.get("analytics", {}).get("recipient_count", 0),
                open_rate=c.get("analytics", {}).get("open_rate", 0.0),
                click_rate=c.get("analytics", {}).get("click_rate", 0.0),
                created_at=c["created_at"],
                scheduled_at=c.get("scheduled_at"),
                sent_at=c.get("sent_at"),
            )
            for c in campaigns
        ]

        return CampaignListResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
        )

    except Exception as e:
        logger.error(f"List campaigns failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{campaign_id}", response_model=CampaignDetail)
async def get_campaign(
    campaign_id: str = Path(..., description="Campaign ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a specific campaign by ID.

    Returns full campaign details including analytics.
    """
    try:
        repo = get_campaign_repository()
        campaign = await repo.find_by_id(campaign_id)

        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        if campaign.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        return CampaignDetail(
            id=campaign["id"],
            user_id=campaign["user_id"],
            name=campaign["name"],
            description=campaign.get("description"),
            subject=campaign["subject"],
            preview_text=campaign.get("preview_text"),
            newsletter_id=campaign.get("newsletter_id"),
            template_id=campaign.get("template_id"),
            status=campaign["status"],
            subscriber_tags=campaign.get("subscriber_tags", []),
            subscriber_groups=campaign.get("subscriber_groups", []),
            exclude_tags=campaign.get("exclude_tags", []),
            scheduled_at=campaign.get("scheduled_at"),
            send_timezone=campaign.get("send_timezone", "UTC"),
            from_email=campaign.get("from_email"),
            from_name=campaign.get("from_name"),
            reply_to=campaign.get("reply_to"),
            analytics=CampaignAnalytics(**campaign.get("analytics", {})),
            created_at=campaign["created_at"],
            updated_at=campaign.get("updated_at"),
            sent_at=campaign.get("sent_at"),
            completed_at=campaign.get("completed_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get campaign failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{campaign_id}", response_model=CampaignDetail)
async def update_campaign(
    request: CampaignUpdateRequest,
    campaign_id: str = Path(..., description="Campaign ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Update a campaign.

    Only draft campaigns can be updated.
    """
    try:
        repo = get_campaign_repository()
        campaign = await repo.find_by_id(campaign_id)

        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        if campaign.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        if campaign.get("status") not in [CampaignStatus.DRAFT, CampaignStatus.SCHEDULED]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot update campaign in {campaign.get('status')} status"
            )

        # Build update dict from non-None values
        updates = {}
        for field in ["name", "subject", "description", "preview_text", "newsletter_id",
                      "template_id", "subscriber_tags", "subscriber_groups", "exclude_tags",
                      "from_email", "from_name", "reply_to"]:
            value = getattr(request, field)
            if value is not None:
                updates[field] = value

        if not updates:
            return await get_campaign(campaign_id, current_user)

        updated = await repo.update(campaign_id, **updates)

        return CampaignDetail(
            id=updated["id"],
            user_id=updated["user_id"],
            name=updated["name"],
            description=updated.get("description"),
            subject=updated["subject"],
            preview_text=updated.get("preview_text"),
            newsletter_id=updated.get("newsletter_id"),
            template_id=updated.get("template_id"),
            status=updated["status"],
            subscriber_tags=updated.get("subscriber_tags", []),
            subscriber_groups=updated.get("subscriber_groups", []),
            exclude_tags=updated.get("exclude_tags", []),
            scheduled_at=updated.get("scheduled_at"),
            send_timezone=updated.get("send_timezone", "UTC"),
            from_email=updated.get("from_email"),
            from_name=updated.get("from_name"),
            reply_to=updated.get("reply_to"),
            analytics=CampaignAnalytics(**updated.get("analytics", {})),
            created_at=updated["created_at"],
            updated_at=updated.get("updated_at"),
            sent_at=updated.get("sent_at"),
            completed_at=updated.get("completed_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update campaign failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str = Path(..., description="Campaign ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a campaign.

    Sent campaigns cannot be deleted.
    """
    try:
        repo = get_campaign_repository()
        campaign = await repo.find_by_id(campaign_id)

        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        if campaign.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        if campaign.get("status") == CampaignStatus.SENT:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete sent campaigns"
            )

        deleted = await repo.delete(campaign_id)

        if not deleted:
            raise HTTPException(status_code=500, detail="Failed to delete campaign")

        return {"success": True, "message": "Campaign deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete campaign failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{campaign_id}/send", response_model=SendResult)
async def send_campaign(
    campaign_id: str = Path(..., description="Campaign ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Send a campaign immediately.

    Sends the campaign to all targeted subscribers.
    """
    try:
        campaign_repo = get_campaign_repository()
        newsletter_repo = get_newsletter_repository()
        subscriber_repo = get_subscriber_repository()
        email_service = get_email_service()

        campaign = await campaign_repo.find_by_id(campaign_id)

        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        if campaign.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        if campaign.get("status") not in [CampaignStatus.DRAFT, CampaignStatus.SCHEDULED]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot send campaign in {campaign.get('status')} status"
            )

        # Get newsletter content
        newsletter_id = campaign.get("newsletter_id")
        if not newsletter_id:
            raise HTTPException(status_code=400, detail="Campaign has no associated newsletter")

        newsletter = await newsletter_repo.find_by_id(newsletter_id)
        if not newsletter:
            raise HTTPException(status_code=400, detail="Newsletter not found")

        # Get target subscribers
        user_id = current_user["id"]
        subscribers = await subscriber_repo.find_active_by_user(
            user_id=user_id,
            tags=campaign.get("subscriber_tags") or None,
            exclude_tags=campaign.get("exclude_tags") or None,
        )

        if not subscribers:
            raise HTTPException(status_code=400, detail="No active subscribers to send to")

        # Update campaign status to sending
        await campaign_repo.update_status(campaign_id, CampaignStatus.SENDING)

        # Send emails
        recipient_emails = [s["email"] for s in subscribers]
        batch_result = await email_service.send_batch(
            recipients=recipient_emails,
            subject=campaign["subject"],
            html_content=newsletter.get("html_content", ""),
            plain_text=newsletter.get("plain_text", ""),
        )

        # Update campaign analytics and status
        await campaign_repo.update_analytics(campaign_id, {
            "recipient_count": batch_result.total,
            "delivered_count": batch_result.sent,
            "bounced_count": batch_result.failed,
        })
        await campaign_repo.update_status(campaign_id, CampaignStatus.SENT)

        # Update newsletter sent count
        await newsletter_repo.update(
            newsletter_id,
            sent_to_count=batch_result.sent,
            status="sent",
        )

        return SendResult(
            success=True,
            campaign_id=campaign_id,
            recipient_count=batch_result.total,
            sent_count=batch_result.sent,
            failed_count=batch_result.failed,
            message=f"Campaign sent to {batch_result.sent} subscribers",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send campaign failed: {e}")
        # Try to update status to failed
        try:
            await campaign_repo.update_status(campaign_id, CampaignStatus.FAILED)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{campaign_id}/schedule", response_model=CampaignDetail)
async def schedule_campaign(
    request: ScheduleRequest,
    campaign_id: str = Path(..., description="Campaign ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Schedule a campaign for later sending.

    Sets the campaign to send at the specified time.
    """
    try:
        repo = get_campaign_repository()
        campaign = await repo.find_by_id(campaign_id)

        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        if campaign.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        if campaign.get("status") not in [CampaignStatus.DRAFT, CampaignStatus.SCHEDULED]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot schedule campaign in {campaign.get('status')} status"
            )

        # Validate schedule time is in the future
        if request.scheduled_at <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=400,
                detail="Schedule time must be in the future"
            )

        updated = await repo.schedule(
            campaign_id=campaign_id,
            scheduled_at=request.scheduled_at,
            timezone=request.send_timezone,
        )

        return CampaignDetail(
            id=updated["id"],
            user_id=updated["user_id"],
            name=updated["name"],
            description=updated.get("description"),
            subject=updated["subject"],
            preview_text=updated.get("preview_text"),
            newsletter_id=updated.get("newsletter_id"),
            template_id=updated.get("template_id"),
            status=updated["status"],
            subscriber_tags=updated.get("subscriber_tags", []),
            subscriber_groups=updated.get("subscriber_groups", []),
            exclude_tags=updated.get("exclude_tags", []),
            scheduled_at=updated.get("scheduled_at"),
            send_timezone=updated.get("send_timezone", "UTC"),
            from_email=updated.get("from_email"),
            from_name=updated.get("from_name"),
            reply_to=updated.get("reply_to"),
            analytics=CampaignAnalytics(**updated.get("analytics", {})),
            created_at=updated["created_at"],
            updated_at=updated.get("updated_at"),
            sent_at=updated.get("sent_at"),
            completed_at=updated.get("completed_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Schedule campaign failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
