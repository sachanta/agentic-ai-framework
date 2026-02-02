"""
Template model for the Newsletter Platform.

Represents reusable newsletter templates with variables.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TemplateCategory(str, Enum):
    """Template category."""
    NEWSLETTER = "newsletter"
    ANNOUNCEMENT = "announcement"
    DIGEST = "digest"
    PROMOTIONAL = "promotional"
    TRANSACTIONAL = "transactional"
    CUSTOM = "custom"


class TemplateVariable(BaseModel):
    """Template variable definition."""
    name: str
    description: Optional[str] = None
    default_value: Optional[str] = None
    required: bool = False


class Template(BaseModel):
    """
    Template document model.

    Stores reusable newsletter templates with variable placeholders.
    """
    id: Optional[str] = Field(None, alias="_id")
    user_id: str

    # Template info
    name: str
    description: Optional[str] = None
    category: str = TemplateCategory.NEWSLETTER

    # Content
    html_content: str = ""
    plain_text_content: str = ""
    subject_template: Optional[str] = None  # Subject line with variables

    # Variables
    variables: List[TemplateVariable] = []

    # Styling
    styles: Dict[str, Any] = {}  # Custom CSS/styling options

    # Metadata
    is_default: bool = False
    is_active: bool = True
    usage_count: int = 0
    last_used_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

    model_config = {
        "populate_by_name": True,
        "json_encoders": {datetime: lambda v: v.isoformat()},
        "use_enum_values": True,
    }
