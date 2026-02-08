"""
Newsletter CRUD API endpoints.

Phase 11: Complete REST API for newsletter management.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query, Path

from app.core.security import get_current_user
from app.platforms.newsletter.repositories import get_newsletter_repository
from app.platforms.newsletter.schemas import NewsletterStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/newsletters", tags=["newsletters"])


# Response schemas
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any


class NewsletterListItem(BaseModel):
    """Brief newsletter item for list views."""
    id: str
    title: str
    status: str
    topics_covered: List[str] = []
    tone_used: str = "professional"
    word_count: int = 0
    created_at: datetime
    sent_at: Optional[datetime] = None


class NewsletterDetail(BaseModel):
    """Full newsletter details."""
    id: str
    user_id: str
    title: str
    content: str = ""
    html_content: str = ""
    plain_text: str = ""
    subject_line: Optional[str] = None
    subject_line_options: List[str] = []
    status: str
    workflow_id: Optional[str] = None
    topics_covered: List[str] = []
    tone_used: str = "professional"
    word_count: int = 0
    read_time_minutes: int = 0
    research_data: Dict[str, Any] = {}
    writing_data: Dict[str, Any] = {}
    sent_to_count: int = 0
    campaign_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    generated_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None


class NewsletterListResponse(BaseModel):
    """Paginated newsletter list response."""
    items: List[NewsletterListItem]
    total: int
    skip: int
    limit: int


class NewsletterUpdateRequest(BaseModel):
    """Request to update newsletter fields."""
    title: Optional[str] = None
    subject_line: Optional[str] = None
    content: Optional[str] = None
    html_content: Optional[str] = None
    plain_text: Optional[str] = None


@router.get("", response_model=NewsletterListResponse)
async def list_newsletters(
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    current_user: dict = Depends(get_current_user),
):
    """
    List user's newsletters.

    Returns a paginated list of newsletters with optional status filtering.
    """
    try:
        repo = get_newsletter_repository()
        user_id = current_user["id"]

        newsletters = await repo.find_by_user(
            user_id=user_id,
            status=status,
            skip=skip,
            limit=limit,
        )
        total = await repo.count_by_user(user_id=user_id, status=status)

        items = [
            NewsletterListItem(
                id=nl["id"],
                title=nl.get("title", "Untitled"),
                status=nl.get("status", NewsletterStatus.DRAFT),
                topics_covered=nl.get("topics_covered", []),
                tone_used=nl.get("tone_used", "professional"),
                word_count=nl.get("word_count", 0),
                created_at=nl.get("created_at"),
                sent_at=nl.get("sent_at"),
            )
            for nl in newsletters
        ]

        return NewsletterListResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
        )

    except Exception as e:
        logger.error(f"List newsletters failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{newsletter_id}", response_model=NewsletterDetail)
async def get_newsletter(
    newsletter_id: str = Path(..., description="Newsletter ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a specific newsletter by ID.

    Returns full newsletter details including content.
    """
    try:
        repo = get_newsletter_repository()
        newsletter = await repo.find_by_id(newsletter_id)

        if not newsletter:
            raise HTTPException(status_code=404, detail="Newsletter not found")

        # Check ownership
        if newsletter.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        return NewsletterDetail(**newsletter)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get newsletter failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{newsletter_id}", response_model=NewsletterDetail)
async def update_newsletter(
    request: NewsletterUpdateRequest,
    newsletter_id: str = Path(..., description="Newsletter ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Update a newsletter.

    Only drafts and pending_review newsletters can be updated.
    """
    try:
        repo = get_newsletter_repository()
        newsletter = await repo.find_by_id(newsletter_id)

        if not newsletter:
            raise HTTPException(status_code=404, detail="Newsletter not found")

        if newsletter.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Only allow updates for editable statuses
        editable_statuses = [NewsletterStatus.DRAFT, NewsletterStatus.PENDING_REVIEW, NewsletterStatus.READY]
        if newsletter.get("status") not in editable_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot edit newsletter in {newsletter.get('status')} status"
            )

        # Build update dict from non-None values
        updates = {}
        if request.title is not None:
            updates["title"] = request.title
        if request.subject_line is not None:
            updates["subject_line"] = request.subject_line
        if request.content is not None:
            updates["content"] = request.content
            updates["word_count"] = len(request.content.split())
        if request.html_content is not None:
            updates["html_content"] = request.html_content
        if request.plain_text is not None:
            updates["plain_text"] = request.plain_text

        if not updates:
            return NewsletterDetail(**newsletter)

        updated = await repo.update(newsletter_id, **updates)
        return NewsletterDetail(**updated)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update newsletter failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{newsletter_id}")
async def delete_newsletter(
    newsletter_id: str = Path(..., description="Newsletter ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a newsletter.

    Sent newsletters cannot be deleted.
    """
    try:
        repo = get_newsletter_repository()
        newsletter = await repo.find_by_id(newsletter_id)

        if not newsletter:
            raise HTTPException(status_code=404, detail="Newsletter not found")

        if newsletter.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Don't allow deleting sent newsletters
        if newsletter.get("status") == NewsletterStatus.SENT:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete sent newsletters"
            )

        deleted = await repo.delete(newsletter_id)

        if not deleted:
            raise HTTPException(status_code=500, detail="Failed to delete newsletter")

        return {"success": True, "message": "Newsletter deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete newsletter failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
