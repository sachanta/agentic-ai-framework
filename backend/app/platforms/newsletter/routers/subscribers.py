"""
Subscriber management API endpoints.

Phase 11: Subscriber CRUD and bulk operations.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, Path, UploadFile, File
from pydantic import BaseModel, EmailStr, Field
import csv
import io

from app.core.security import get_current_user
from app.platforms.newsletter.repositories import get_subscriber_repository
from app.platforms.newsletter.models import SubscriberStatus
from app.platforms.newsletter.services import get_email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subscribers", tags=["subscribers"])


# Request/Response schemas
class SubscriberPreferences(BaseModel):
    """Subscriber preferences."""
    topics: List[str] = []
    tone: str = "professional"
    frequency: str = "weekly"
    custom_prompt: Optional[str] = None


class EngagementMetrics(BaseModel):
    """Subscriber engagement metrics."""
    emails_received: int = 0
    emails_opened: int = 0
    emails_clicked: int = 0
    last_opened_at: Optional[datetime] = None
    last_clicked_at: Optional[datetime] = None
    open_rate: float = 0.0
    click_rate: float = 0.0


class SubscriberCreateRequest(BaseModel):
    """Request to create a new subscriber."""
    email: EmailStr
    name: Optional[str] = None
    preferences: Optional[SubscriberPreferences] = None
    tags: List[str] = []
    groups: List[str] = []
    source: str = "api"
    send_welcome: bool = False


class SubscriberUpdateRequest(BaseModel):
    """Request to update a subscriber."""
    name: Optional[str] = None
    preferences: Optional[SubscriberPreferences] = None
    tags: Optional[List[str]] = None
    groups: Optional[List[str]] = None
    status: Optional[str] = None


class SubscriberListItem(BaseModel):
    """Brief subscriber item for list views."""
    id: str
    email: str
    name: Optional[str] = None
    status: str
    tags: List[str] = []
    open_rate: float = 0.0
    subscribed_at: datetime


class SubscriberDetail(BaseModel):
    """Full subscriber details."""
    id: str
    user_id: str
    email: str
    name: Optional[str] = None
    status: str
    preferences: SubscriberPreferences
    tags: List[str] = []
    groups: List[str] = []
    engagement: EngagementMetrics
    source: str = "manual"
    metadata: Dict[str, Any] = {}
    subscribed_at: datetime
    unsubscribed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class SubscriberListResponse(BaseModel):
    """Paginated subscriber list response."""
    items: List[SubscriberListItem]
    total: int
    skip: int
    limit: int


class ImportResult(BaseModel):
    """Result of bulk import operation."""
    success: bool
    created: int
    skipped: int
    errors: List[str] = []


class ImportSubscriber(BaseModel):
    """Single subscriber for import."""
    email: EmailStr
    name: Optional[str] = None
    tags: List[str] = []


class BulkImportRequest(BaseModel):
    """Request for bulk subscriber import."""
    subscribers: List[ImportSubscriber]
    send_welcome: bool = False


@router.post("", response_model=SubscriberDetail)
async def create_subscriber(
    request: SubscriberCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Add a new subscriber.

    Creates a new subscriber with optional preferences and tags.
    Optionally sends a welcome email.
    """
    try:
        repo = get_subscriber_repository()
        user_id = current_user["id"]

        # Check if subscriber already exists
        existing = await repo.find_by_email(user_id, request.email)
        if existing:
            raise HTTPException(
                status_code=409,
                detail="Subscriber with this email already exists"
            )

        # Create subscriber
        preferences = request.preferences.model_dump() if request.preferences else {}
        subscriber = await repo.create(
            user_id=user_id,
            email=request.email,
            name=request.name,
            preferences=preferences,
            tags=request.tags,
            groups=request.groups,
            source=request.source,
        )

        # Send welcome email if requested
        if request.send_welcome:
            try:
                email_service = get_email_service()
                await email_service.send_welcome_email(
                    to=request.email,
                    subscriber_name=request.name,
                )
            except Exception as e:
                logger.warning(f"Failed to send welcome email: {e}")

        return SubscriberDetail(
            id=subscriber["id"],
            user_id=subscriber["user_id"],
            email=subscriber["email"],
            name=subscriber.get("name"),
            status=subscriber["status"],
            preferences=SubscriberPreferences(**subscriber.get("preferences", {})),
            tags=subscriber.get("tags", []),
            groups=subscriber.get("groups", []),
            engagement=EngagementMetrics(**subscriber.get("engagement", {})),
            source=subscriber.get("source", "api"),
            metadata=subscriber.get("metadata", {}),
            subscribed_at=subscriber["subscribed_at"],
            unsubscribed_at=subscriber.get("unsubscribed_at"),
            created_at=subscriber["created_at"],
            updated_at=subscriber.get("updated_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create subscriber failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=SubscriberListResponse)
async def list_subscribers(
    status: Optional[str] = Query(None, description="Filter by status"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    group: Optional[str] = Query(None, description="Filter by group"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of items to return"),
    current_user: dict = Depends(get_current_user),
):
    """
    List subscribers.

    Returns a paginated list of subscribers with optional filtering.
    """
    try:
        repo = get_subscriber_repository()
        user_id = current_user["id"]

        tags = [tag] if tag else None
        groups = [group] if group else None

        subscribers = await repo.find_by_user(
            user_id=user_id,
            status=status,
            tags=tags,
            groups=groups,
            skip=skip,
            limit=limit,
        )
        total = await repo.count_by_user(user_id=user_id, status=status)

        items = [
            SubscriberListItem(
                id=s["id"],
                email=s["email"],
                name=s.get("name"),
                status=s["status"],
                tags=s.get("tags", []),
                open_rate=s.get("engagement", {}).get("open_rate", 0.0),
                subscribed_at=s["subscribed_at"],
            )
            for s in subscribers
        ]

        return SubscriberListResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
        )

    except Exception as e:
        logger.error(f"List subscribers failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{subscriber_id}", response_model=SubscriberDetail)
async def get_subscriber(
    subscriber_id: str = Path(..., description="Subscriber ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a specific subscriber by ID.

    Returns full subscriber details including engagement metrics.
    """
    try:
        repo = get_subscriber_repository()
        subscriber = await repo.find_by_id(subscriber_id)

        if not subscriber:
            raise HTTPException(status_code=404, detail="Subscriber not found")

        if subscriber.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        return SubscriberDetail(
            id=subscriber["id"],
            user_id=subscriber["user_id"],
            email=subscriber["email"],
            name=subscriber.get("name"),
            status=subscriber["status"],
            preferences=SubscriberPreferences(**subscriber.get("preferences", {})),
            tags=subscriber.get("tags", []),
            groups=subscriber.get("groups", []),
            engagement=EngagementMetrics(**subscriber.get("engagement", {})),
            source=subscriber.get("source", "manual"),
            metadata=subscriber.get("metadata", {}),
            subscribed_at=subscriber["subscribed_at"],
            unsubscribed_at=subscriber.get("unsubscribed_at"),
            created_at=subscriber["created_at"],
            updated_at=subscriber.get("updated_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get subscriber failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{subscriber_id}", response_model=SubscriberDetail)
async def update_subscriber(
    request: SubscriberUpdateRequest,
    subscriber_id: str = Path(..., description="Subscriber ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Update a subscriber.

    Updates subscriber details, preferences, or status.
    """
    try:
        repo = get_subscriber_repository()
        subscriber = await repo.find_by_id(subscriber_id)

        if not subscriber:
            raise HTTPException(status_code=404, detail="Subscriber not found")

        if subscriber.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Build update dict from non-None values
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.preferences is not None:
            updates["preferences"] = request.preferences.model_dump()
        if request.tags is not None:
            updates["tags"] = request.tags
        if request.groups is not None:
            updates["groups"] = request.groups

        # Handle status change separately
        if request.status is not None:
            updated = await repo.update_status(subscriber_id, request.status)
        elif updates:
            updated = await repo.update(subscriber_id, **updates)
        else:
            updated = subscriber

        return SubscriberDetail(
            id=updated["id"],
            user_id=updated["user_id"],
            email=updated["email"],
            name=updated.get("name"),
            status=updated["status"],
            preferences=SubscriberPreferences(**updated.get("preferences", {})),
            tags=updated.get("tags", []),
            groups=updated.get("groups", []),
            engagement=EngagementMetrics(**updated.get("engagement", {})),
            source=updated.get("source", "manual"),
            metadata=updated.get("metadata", {}),
            subscribed_at=updated["subscribed_at"],
            unsubscribed_at=updated.get("unsubscribed_at"),
            created_at=updated["created_at"],
            updated_at=updated.get("updated_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update subscriber failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{subscriber_id}")
async def delete_subscriber(
    subscriber_id: str = Path(..., description="Subscriber ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Remove a subscriber.

    Permanently deletes the subscriber record.
    """
    try:
        repo = get_subscriber_repository()
        subscriber = await repo.find_by_id(subscriber_id)

        if not subscriber:
            raise HTTPException(status_code=404, detail="Subscriber not found")

        if subscriber.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        deleted = await repo.delete(subscriber_id)

        if not deleted:
            raise HTTPException(status_code=500, detail="Failed to delete subscriber")

        return {"success": True, "message": "Subscriber deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete subscriber failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import", response_model=ImportResult)
async def import_subscribers(
    request: BulkImportRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Bulk import subscribers.

    Imports multiple subscribers at once. Existing emails are skipped.
    """
    try:
        repo = get_subscriber_repository()
        user_id = current_user["id"]

        # Convert to list of dicts
        subscribers_data = [
            {
                "email": s.email,
                "name": s.name,
                "tags": s.tags,
            }
            for s in request.subscribers
        ]

        result = await repo.bulk_create(
            user_id=user_id,
            subscribers=subscribers_data,
            source="import",
        )

        # Send welcome emails if requested
        if request.send_welcome and result["created"] > 0:
            email_service = get_email_service()
            for sub in request.subscribers:
                try:
                    await email_service.send_welcome_email(
                        to=sub.email,
                        subscriber_name=sub.name,
                    )
                except Exception as e:
                    logger.warning(f"Failed to send welcome email to {sub.email}: {e}")

        return ImportResult(
            success=True,
            created=result["created"],
            skipped=result["skipped"],
        )

    except Exception as e:
        logger.error(f"Import subscribers failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/csv", response_model=ImportResult)
async def import_subscribers_csv(
    file: UploadFile = File(..., description="CSV file with email,name columns"),
    send_welcome: bool = Query(False, description="Send welcome emails"),
    current_user: dict = Depends(get_current_user),
):
    """
    Import subscribers from CSV file.

    CSV should have headers: email,name (name is optional).
    """
    try:
        if not file.filename.endswith(".csv"):
            raise HTTPException(status_code=400, detail="File must be a CSV")

        repo = get_subscriber_repository()
        user_id = current_user["id"]

        # Read CSV content
        content = await file.read()
        text = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))

        subscribers_data = []
        errors = []

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
            email = row.get("email", "").strip().lower()
            if not email:
                errors.append(f"Row {row_num}: missing email")
                continue

            # Basic email validation
            if "@" not in email or "." not in email:
                errors.append(f"Row {row_num}: invalid email '{email}'")
                continue

            subscribers_data.append({
                "email": email,
                "name": row.get("name", "").strip() or None,
                "tags": [],
            })

        if not subscribers_data:
            raise HTTPException(
                status_code=400,
                detail="No valid subscribers found in CSV"
            )

        result = await repo.bulk_create(
            user_id=user_id,
            subscribers=subscribers_data,
            source="csv_import",
        )

        return ImportResult(
            success=True,
            created=result["created"],
            skipped=result["skipped"],
            errors=errors[:10],  # Limit errors to first 10
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSV import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{subscriber_id}/unsubscribe")
async def unsubscribe(
    subscriber_id: str = Path(..., description="Subscriber ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Unsubscribe a subscriber.

    Sets the subscriber status to unsubscribed.
    """
    try:
        repo = get_subscriber_repository()
        subscriber = await repo.find_by_id(subscriber_id)

        if not subscriber:
            raise HTTPException(status_code=404, detail="Subscriber not found")

        if subscriber.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        await repo.update_status(subscriber_id, SubscriberStatus.UNSUBSCRIBED)

        return {"success": True, "message": "Subscriber unsubscribed"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unsubscribe failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{subscriber_id}/resubscribe")
async def resubscribe(
    subscriber_id: str = Path(..., description="Subscriber ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Resubscribe a previously unsubscribed subscriber.

    Sets the subscriber status back to subscribed.
    """
    try:
        repo = get_subscriber_repository()
        subscriber = await repo.find_by_id(subscriber_id)

        if not subscriber:
            raise HTTPException(status_code=404, detail="Subscriber not found")

        if subscriber.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        await repo.update_status(subscriber_id, SubscriberStatus.SUBSCRIBED)

        return {"success": True, "message": "Subscriber resubscribed"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resubscribe failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
