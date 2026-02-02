"""
Newsletter repository for database operations.

Handles CRUD operations for Newsletter documents.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId

from app.db.mongodb import get_database
from app.platforms.newsletter.models import Newsletter, NewsletterStatus


class NewsletterRepository:
    """Repository for newsletter database operations."""

    collection_name = "newsletters"

    def __init__(self):
        self._db = None
        self._collection = None

    @property
    def collection(self):
        """Get the newsletters collection (lazy-loaded)."""
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
        title: str,
        topics: List[str] = None,
        tone: str = "professional",
        workflow_id: Optional[str] = None,
        **kwargs,
    ) -> dict:
        """Create a new newsletter."""
        now = datetime.now(timezone.utc)
        doc = {
            "user_id": user_id,
            "title": title,
            "content": kwargs.get("content", ""),
            "html_content": kwargs.get("html_content", ""),
            "plain_text": kwargs.get("plain_text", ""),
            "subject_line": kwargs.get("subject_line"),
            "subject_line_options": kwargs.get("subject_line_options", []),
            "status": NewsletterStatus.DRAFT,
            "workflow_id": workflow_id,
            "topics_covered": topics or [],
            "tone_used": tone,
            "word_count": kwargs.get("word_count", 0),
            "read_time_minutes": kwargs.get("read_time_minutes", 0),
            "research_data": kwargs.get("research_data", {}),
            "writing_data": kwargs.get("writing_data", {}),
            "mindmap_markdown": kwargs.get("mindmap_markdown"),
            "sent_to_count": 0,
            "campaign_id": kwargs.get("campaign_id"),
            "created_at": now,
            "updated_at": None,
            "generated_at": None,
            "sent_at": None,
        }

        result = await self.collection.insert_one(doc)
        doc["id"] = str(result.inserted_id)
        doc.pop("_id", None)
        return doc

    async def find_by_id(self, newsletter_id: str) -> Optional[dict]:
        """Find a newsletter by ID."""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(newsletter_id)})
            return self._format_doc(doc)
        except Exception:
            return None

    async def find_by_user(
        self,
        user_id: str,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[dict]:
        """Find newsletters by user ID with optional filtering."""
        filter_query = {"user_id": user_id}
        if status:
            filter_query["status"] = status

        cursor = self.collection.find(filter_query)
        cursor = cursor.sort("created_at", -1).skip(skip).limit(limit)

        newsletters = []
        async for doc in cursor:
            newsletters.append(self._format_doc(doc))
        return newsletters

    async def find_by_workflow(self, workflow_id: str) -> Optional[dict]:
        """Find a newsletter by workflow ID."""
        doc = await self.collection.find_one({"workflow_id": workflow_id})
        return self._format_doc(doc)

    async def count_by_user(
        self,
        user_id: str,
        status: Optional[str] = None,
    ) -> int:
        """Count newsletters for a user."""
        filter_query = {"user_id": user_id}
        if status:
            filter_query["status"] = status
        return await self.collection.count_documents(filter_query)

    async def update(
        self,
        newsletter_id: str,
        **updates,
    ) -> Optional[dict]:
        """Update a newsletter."""
        updates["updated_at"] = datetime.now(timezone.utc)

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(newsletter_id)},
            {"$set": updates},
            return_document=True,
        )
        return self._format_doc(result)

    async def update_status(
        self,
        newsletter_id: str,
        status: str,
    ) -> Optional[dict]:
        """Update newsletter status."""
        updates = {
            "status": status,
            "updated_at": datetime.now(timezone.utc),
        }

        # Set timestamp based on status
        if status == NewsletterStatus.READY:
            updates["generated_at"] = datetime.now(timezone.utc)
        elif status == NewsletterStatus.SENT:
            updates["sent_at"] = datetime.now(timezone.utc)

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(newsletter_id)},
            {"$set": updates},
            return_document=True,
        )
        return self._format_doc(result)

    async def update_content(
        self,
        newsletter_id: str,
        content: str,
        html_content: str,
        plain_text: str,
        word_count: int = 0,
        read_time_minutes: int = 0,
    ) -> Optional[dict]:
        """Update newsletter content."""
        updates = {
            "content": content,
            "html_content": html_content,
            "plain_text": plain_text,
            "word_count": word_count,
            "read_time_minutes": read_time_minutes,
            "updated_at": datetime.now(timezone.utc),
        }

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(newsletter_id)},
            {"$set": updates},
            return_document=True,
        )
        return self._format_doc(result)

    async def update_research_data(
        self,
        newsletter_id: str,
        research_data: Dict[str, Any],
    ) -> Optional[dict]:
        """Update newsletter research data."""
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(newsletter_id)},
            {
                "$set": {
                    "research_data": research_data,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            return_document=True,
        )
        return self._format_doc(result)

    async def update_subject_lines(
        self,
        newsletter_id: str,
        subject_lines: List[str],
        selected_subject: Optional[str] = None,
    ) -> Optional[dict]:
        """Update newsletter subject lines."""
        updates = {
            "subject_line_options": subject_lines,
            "updated_at": datetime.now(timezone.utc),
        }
        if selected_subject:
            updates["subject_line"] = selected_subject

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(newsletter_id)},
            {"$set": updates},
            return_document=True,
        )
        return self._format_doc(result)

    async def delete(self, newsletter_id: str) -> bool:
        """Delete a newsletter."""
        result = await self.collection.delete_one({"_id": ObjectId(newsletter_id)})
        return result.deleted_count > 0

    async def delete_by_user(self, user_id: str) -> int:
        """Delete all newsletters for a user."""
        result = await self.collection.delete_many({"user_id": user_id})
        return result.deleted_count


# Singleton instance
_newsletter_repository: Optional[NewsletterRepository] = None


def get_newsletter_repository() -> NewsletterRepository:
    """Get the newsletter repository instance."""
    global _newsletter_repository
    if _newsletter_repository is None:
        _newsletter_repository = NewsletterRepository()
    return _newsletter_repository
