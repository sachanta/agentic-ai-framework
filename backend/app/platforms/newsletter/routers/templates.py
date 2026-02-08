"""
Template management API endpoints.

Phase 11: Template CRUD operations.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from pydantic import BaseModel, Field

from app.core.security import get_current_user
from app.platforms.newsletter.repositories import get_template_repository
from app.platforms.newsletter.models import TemplateCategory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/templates", tags=["templates"])


# Request/Response schemas
class TemplateVariable(BaseModel):
    """Template variable definition."""
    name: str
    description: Optional[str] = None
    default_value: Optional[str] = None
    required: bool = False


class TemplateCreateRequest(BaseModel):
    """Request to create a new template."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: str = TemplateCategory.NEWSLETTER
    html_content: str = ""
    plain_text_content: str = ""
    subject_template: Optional[str] = None
    variables: List[TemplateVariable] = []
    styles: Dict[str, Any] = {}


class TemplateUpdateRequest(BaseModel):
    """Request to update a template."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    html_content: Optional[str] = None
    plain_text_content: Optional[str] = None
    subject_template: Optional[str] = None
    variables: Optional[List[TemplateVariable]] = None
    styles: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class TemplateListItem(BaseModel):
    """Brief template item for list views."""
    id: str
    name: str
    description: Optional[str] = None
    category: str
    is_default: bool = False
    is_active: bool = True
    usage_count: int = 0
    created_at: datetime


class TemplateDetail(BaseModel):
    """Full template details."""
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    category: str
    html_content: str = ""
    plain_text_content: str = ""
    subject_template: Optional[str] = None
    variables: List[TemplateVariable] = []
    styles: Dict[str, Any] = {}
    is_default: bool = False
    is_active: bool = True
    usage_count: int = 0
    last_used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class TemplateListResponse(BaseModel):
    """Paginated template list response."""
    items: List[TemplateListItem]
    total: int
    skip: int
    limit: int


class TemplatePreviewRequest(BaseModel):
    """Request to preview a template with variables."""
    variables: Dict[str, str] = {}


class TemplatePreviewResponse(BaseModel):
    """Template preview response."""
    html: str
    plain_text: str
    subject: Optional[str] = None


@router.post("", response_model=TemplateDetail)
async def create_template(
    request: TemplateCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new template.

    Creates a reusable newsletter template with variable placeholders.
    """
    try:
        repo = get_template_repository()
        user_id = current_user["id"]

        template = await repo.create(
            user_id=user_id,
            name=request.name,
            description=request.description,
            category=request.category,
            html_content=request.html_content,
            plain_text_content=request.plain_text_content,
            subject_template=request.subject_template,
            variables=[v.model_dump() for v in request.variables],
            styles=request.styles,
        )

        return TemplateDetail(
            id=template["id"],
            user_id=template["user_id"],
            name=template["name"],
            description=template.get("description"),
            category=template["category"],
            html_content=template.get("html_content", ""),
            plain_text_content=template.get("plain_text_content", ""),
            subject_template=template.get("subject_template"),
            variables=[TemplateVariable(**v) for v in template.get("variables", [])],
            styles=template.get("styles", {}),
            is_default=template.get("is_default", False),
            is_active=template.get("is_active", True),
            usage_count=template.get("usage_count", 0),
            last_used_at=template.get("last_used_at"),
            created_at=template["created_at"],
            updated_at=template.get("updated_at"),
        )

    except Exception as e:
        logger.error(f"Create template failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=TemplateListResponse)
async def list_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    active_only: bool = Query(True, description="Only show active templates"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    current_user: dict = Depends(get_current_user),
):
    """
    List user's templates.

    Returns a paginated list of templates with optional filtering.
    """
    try:
        repo = get_template_repository()
        user_id = current_user["id"]

        is_active = True if active_only else None

        templates = await repo.find_by_user(
            user_id=user_id,
            category=category,
            is_active=is_active,
            skip=skip,
            limit=limit,
        )
        total = await repo.count_by_user(user_id=user_id, category=category)

        items = [
            TemplateListItem(
                id=t["id"],
                name=t["name"],
                description=t.get("description"),
                category=t["category"],
                is_default=t.get("is_default", False),
                is_active=t.get("is_active", True),
                usage_count=t.get("usage_count", 0),
                created_at=t["created_at"],
            )
            for t in templates
        ]

        return TemplateListResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
        )

    except Exception as e:
        logger.error(f"List templates failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}", response_model=TemplateDetail)
async def get_template(
    template_id: str = Path(..., description="Template ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a specific template by ID.

    Returns full template details including content and variables.
    """
    try:
        repo = get_template_repository()
        template = await repo.find_by_id(template_id)

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        if template.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        return TemplateDetail(
            id=template["id"],
            user_id=template["user_id"],
            name=template["name"],
            description=template.get("description"),
            category=template["category"],
            html_content=template.get("html_content", ""),
            plain_text_content=template.get("plain_text_content", ""),
            subject_template=template.get("subject_template"),
            variables=[TemplateVariable(**v) for v in template.get("variables", [])],
            styles=template.get("styles", {}),
            is_default=template.get("is_default", False),
            is_active=template.get("is_active", True),
            usage_count=template.get("usage_count", 0),
            last_used_at=template.get("last_used_at"),
            created_at=template["created_at"],
            updated_at=template.get("updated_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get template failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{template_id}", response_model=TemplateDetail)
async def update_template(
    request: TemplateUpdateRequest,
    template_id: str = Path(..., description="Template ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Update a template.

    Updates template details, content, or variables.
    """
    try:
        repo = get_template_repository()
        template = await repo.find_by_id(template_id)

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        if template.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Build update dict from non-None values
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.category is not None:
            updates["category"] = request.category
        if request.html_content is not None:
            updates["html_content"] = request.html_content
        if request.plain_text_content is not None:
            updates["plain_text_content"] = request.plain_text_content
        if request.subject_template is not None:
            updates["subject_template"] = request.subject_template
        if request.variables is not None:
            updates["variables"] = [v.model_dump() for v in request.variables]
        if request.styles is not None:
            updates["styles"] = request.styles
        if request.is_active is not None:
            updates["is_active"] = request.is_active

        if not updates:
            return await get_template(template_id, current_user)

        updated = await repo.update(template_id, **updates)

        return TemplateDetail(
            id=updated["id"],
            user_id=updated["user_id"],
            name=updated["name"],
            description=updated.get("description"),
            category=updated["category"],
            html_content=updated.get("html_content", ""),
            plain_text_content=updated.get("plain_text_content", ""),
            subject_template=updated.get("subject_template"),
            variables=[TemplateVariable(**v) for v in updated.get("variables", [])],
            styles=updated.get("styles", {}),
            is_default=updated.get("is_default", False),
            is_active=updated.get("is_active", True),
            usage_count=updated.get("usage_count", 0),
            last_used_at=updated.get("last_used_at"),
            created_at=updated["created_at"],
            updated_at=updated.get("updated_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update template failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{template_id}")
async def delete_template(
    template_id: str = Path(..., description="Template ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a template.
    """
    try:
        repo = get_template_repository()
        template = await repo.find_by_id(template_id)

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        if template.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        deleted = await repo.delete(template_id)

        if not deleted:
            raise HTTPException(status_code=500, detail="Failed to delete template")

        return {"success": True, "message": "Template deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete template failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{template_id}/duplicate", response_model=TemplateDetail)
async def duplicate_template(
    new_name: str = Query(..., description="Name for the duplicated template"),
    template_id: str = Path(..., description="Template ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Duplicate a template with a new name.
    """
    try:
        repo = get_template_repository()
        template = await repo.find_by_id(template_id)

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        if template.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        duplicated = await repo.duplicate(template_id, new_name)

        if not duplicated:
            raise HTTPException(status_code=500, detail="Failed to duplicate template")

        return TemplateDetail(
            id=duplicated["id"],
            user_id=duplicated["user_id"],
            name=duplicated["name"],
            description=duplicated.get("description"),
            category=duplicated["category"],
            html_content=duplicated.get("html_content", ""),
            plain_text_content=duplicated.get("plain_text_content", ""),
            subject_template=duplicated.get("subject_template"),
            variables=[TemplateVariable(**v) for v in duplicated.get("variables", [])],
            styles=duplicated.get("styles", {}),
            is_default=duplicated.get("is_default", False),
            is_active=duplicated.get("is_active", True),
            usage_count=duplicated.get("usage_count", 0),
            last_used_at=duplicated.get("last_used_at"),
            created_at=duplicated["created_at"],
            updated_at=duplicated.get("updated_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Duplicate template failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{template_id}/set-default", response_model=TemplateDetail)
async def set_default_template(
    template_id: str = Path(..., description="Template ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Set a template as the default for its category.

    Only one template per category can be the default.
    """
    try:
        repo = get_template_repository()
        template = await repo.find_by_id(template_id)

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        if template.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        updated = await repo.set_default(
            user_id=current_user["id"],
            template_id=template_id,
            category=template["category"],
        )

        return TemplateDetail(
            id=updated["id"],
            user_id=updated["user_id"],
            name=updated["name"],
            description=updated.get("description"),
            category=updated["category"],
            html_content=updated.get("html_content", ""),
            plain_text_content=updated.get("plain_text_content", ""),
            subject_template=updated.get("subject_template"),
            variables=[TemplateVariable(**v) for v in updated.get("variables", [])],
            styles=updated.get("styles", {}),
            is_default=updated.get("is_default", False),
            is_active=updated.get("is_active", True),
            usage_count=updated.get("usage_count", 0),
            last_used_at=updated.get("last_used_at"),
            created_at=updated["created_at"],
            updated_at=updated.get("updated_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Set default template failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{template_id}/preview", response_model=TemplatePreviewResponse)
async def preview_template(
    request: TemplatePreviewRequest,
    template_id: str = Path(..., description="Template ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Preview a template with variable substitution.

    Renders the template with provided variable values.
    """
    try:
        repo = get_template_repository()
        template = await repo.find_by_id(template_id)

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        if template.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Simple variable substitution using {{variable_name}}
        html = template.get("html_content", "")
        plain_text = template.get("plain_text_content", "")
        subject = template.get("subject_template", "")

        for var_name, var_value in request.variables.items():
            placeholder = f"{{{{{var_name}}}}}"
            html = html.replace(placeholder, var_value)
            plain_text = plain_text.replace(placeholder, var_value)
            if subject:
                subject = subject.replace(placeholder, var_value)

        return TemplatePreviewResponse(
            html=html,
            plain_text=plain_text,
            subject=subject if subject else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preview template failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
