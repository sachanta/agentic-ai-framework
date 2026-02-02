"""
Template repository for database operations.

Handles CRUD operations for Template documents.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId

from app.db.mongodb import get_database
from app.platforms.newsletter.models import Template, TemplateCategory


class TemplateRepository:
    """Repository for template database operations."""

    collection_name = "newsletter_templates"

    def __init__(self):
        self._db = None
        self._collection = None

    @property
    def collection(self):
        """Get the templates collection (lazy-loaded)."""
        if self._collection is None:
            self._db = get_database()
            self._collection = self._db[self.collection_name]
        return self._collection

    def _format_doc(self, doc: Optional[dict]) -> Optional[dict]:
        """Format a document for response (ObjectId to string)."""
        if doc is None:
            return None
        doc["id"] = str(doc.pop("_id"))
        return doc

    async def create(
        self,
        user_id: str,
        name: str,
        html_content: str = "",
        plain_text_content: str = "",
        category: str = TemplateCategory.NEWSLETTER,
        **kwargs,
    ) -> dict:
        """Create a new template."""
        now = datetime.now(timezone.utc)

        doc = {
            "user_id": user_id,
            "name": name,
            "description": kwargs.get("description"),
            "category": category,
            "html_content": html_content,
            "plain_text_content": plain_text_content,
            "subject_template": kwargs.get("subject_template"),
            "variables": kwargs.get("variables", []),
            "styles": kwargs.get("styles", {}),
            "is_default": kwargs.get("is_default", False),
            "is_active": kwargs.get("is_active", True),
            "usage_count": 0,
            "last_used_at": None,
            "created_at": now,
            "updated_at": None,
        }

        result = await self.collection.insert_one(doc)
        doc["id"] = str(result.inserted_id)
        doc.pop("_id", None)
        return doc

    async def find_by_id(self, template_id: str) -> Optional[dict]:
        """Find a template by ID."""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(template_id)})
            return self._format_doc(doc)
        except Exception:
            return None

    async def find_by_user(
        self,
        user_id: str,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[dict]:
        """Find templates by user ID with optional filtering."""
        filter_query = {"user_id": user_id}

        if category:
            filter_query["category"] = category
        if is_active is not None:
            filter_query["is_active"] = is_active

        cursor = self.collection.find(filter_query)
        cursor = cursor.sort("created_at", -1).skip(skip).limit(limit)

        templates = []
        async for doc in cursor:
            templates.append(self._format_doc(doc))
        return templates

    async def find_default(
        self,
        user_id: str,
        category: str = TemplateCategory.NEWSLETTER,
    ) -> Optional[dict]:
        """Find the default template for a category."""
        doc = await self.collection.find_one({
            "user_id": user_id,
            "category": category,
            "is_default": True,
            "is_active": True,
        })
        return self._format_doc(doc)

    async def count_by_user(
        self,
        user_id: str,
        category: Optional[str] = None,
    ) -> int:
        """Count templates for a user."""
        filter_query = {"user_id": user_id}
        if category:
            filter_query["category"] = category
        return await self.collection.count_documents(filter_query)

    async def update(
        self,
        template_id: str,
        **updates,
    ) -> Optional[dict]:
        """Update a template."""
        updates["updated_at"] = datetime.now(timezone.utc)

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(template_id)},
            {"$set": updates},
            return_document=True,
        )
        return self._format_doc(result)

    async def update_content(
        self,
        template_id: str,
        html_content: str,
        plain_text_content: str = "",
        subject_template: Optional[str] = None,
    ) -> Optional[dict]:
        """Update template content."""
        updates = {
            "html_content": html_content,
            "plain_text_content": plain_text_content,
            "updated_at": datetime.now(timezone.utc),
        }
        if subject_template is not None:
            updates["subject_template"] = subject_template

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(template_id)},
            {"$set": updates},
            return_document=True,
        )
        return self._format_doc(result)

    async def set_default(
        self,
        user_id: str,
        template_id: str,
        category: str,
    ) -> Optional[dict]:
        """Set a template as the default for its category."""
        # First, unset any existing default
        await self.collection.update_many(
            {
                "user_id": user_id,
                "category": category,
                "is_default": True,
            },
            {"$set": {"is_default": False, "updated_at": datetime.now(timezone.utc)}},
        )

        # Then set the new default
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(template_id)},
            {
                "$set": {
                    "is_default": True,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            return_document=True,
        )
        return self._format_doc(result)

    async def increment_usage(self, template_id: str) -> Optional[dict]:
        """Increment template usage count."""
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(template_id)},
            {
                "$inc": {"usage_count": 1},
                "$set": {"last_used_at": datetime.now(timezone.utc)},
            },
            return_document=True,
        )
        return self._format_doc(result)

    async def duplicate(
        self,
        template_id: str,
        new_name: str,
    ) -> Optional[dict]:
        """Duplicate a template with a new name."""
        original = await self.find_by_id(template_id)
        if not original:
            return None

        now = datetime.now(timezone.utc)

        # Create copy without id and with new name
        doc = {
            "user_id": original["user_id"],
            "name": new_name,
            "description": original.get("description"),
            "category": original.get("category", TemplateCategory.NEWSLETTER),
            "html_content": original.get("html_content", ""),
            "plain_text_content": original.get("plain_text_content", ""),
            "subject_template": original.get("subject_template"),
            "variables": original.get("variables", []),
            "styles": original.get("styles", {}),
            "is_default": False,  # Copies are never default
            "is_active": True,
            "usage_count": 0,
            "last_used_at": None,
            "created_at": now,
            "updated_at": None,
        }

        result = await self.collection.insert_one(doc)
        doc["id"] = str(result.inserted_id)
        return doc

    async def delete(self, template_id: str) -> bool:
        """Delete a template."""
        result = await self.collection.delete_one({"_id": ObjectId(template_id)})
        return result.deleted_count > 0

    async def delete_by_user(self, user_id: str) -> int:
        """Delete all templates for a user."""
        result = await self.collection.delete_many({"user_id": user_id})
        return result.deleted_count


# Singleton instance
_template_repository: Optional[TemplateRepository] = None


def get_template_repository() -> TemplateRepository:
    """Get the template repository instance."""
    global _template_repository
    if _template_repository is None:
        _template_repository = TemplateRepository()
    return _template_repository
