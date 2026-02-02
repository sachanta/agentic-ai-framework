"""
Subscriber repository for database operations.

Handles CRUD operations for Subscriber documents.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId

from app.db.mongodb import get_database
from app.platforms.newsletter.models import (
    Subscriber,
    SubscriberStatus,
    SubscriberPreferences,
    EngagementMetrics,
)


class SubscriberRepository:
    """Repository for subscriber database operations."""

    collection_name = "newsletter_subscribers"

    def __init__(self):
        self._db = None
        self._collection = None

    @property
    def collection(self):
        """Get the subscribers collection (lazy-loaded)."""
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
        email: str,
        name: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
        tags: List[str] = None,
        source: str = "manual",
        **kwargs,
    ) -> dict:
        """Create a new subscriber."""
        now = datetime.now(timezone.utc)

        # Build preferences object
        pref_data = preferences or {}
        prefs = {
            "topics": pref_data.get("topics", []),
            "tone": pref_data.get("tone", "professional"),
            "frequency": pref_data.get("frequency", "weekly"),
            "include_mindmap": pref_data.get("include_mindmap", True),
            "custom_prompt": pref_data.get("custom_prompt"),
        }

        doc = {
            "user_id": user_id,
            "email": email.lower().strip(),
            "name": name,
            "status": SubscriberStatus.SUBSCRIBED,
            "preferences": prefs,
            "tags": tags or [],
            "groups": kwargs.get("groups", []),
            "engagement": {
                "emails_received": 0,
                "emails_opened": 0,
                "emails_clicked": 0,
                "last_opened_at": None,
                "last_clicked_at": None,
                "open_rate": 0.0,
                "click_rate": 0.0,
            },
            "source": source,
            "metadata": kwargs.get("metadata", {}),
            "subscribed_at": now,
            "unsubscribed_at": None,
            "created_at": now,
            "updated_at": None,
        }

        result = await self.collection.insert_one(doc)
        doc["id"] = str(result.inserted_id)
        doc.pop("_id", None)
        return doc

    async def find_by_id(self, subscriber_id: str) -> Optional[dict]:
        """Find a subscriber by ID."""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(subscriber_id)})
            return self._format_doc(doc)
        except Exception:
            return None

    async def find_by_email(
        self,
        user_id: str,
        email: str,
    ) -> Optional[dict]:
        """Find a subscriber by email within a user's list."""
        doc = await self.collection.find_one({
            "user_id": user_id,
            "email": email.lower().strip(),
        })
        return self._format_doc(doc)

    async def find_by_user(
        self,
        user_id: str,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        groups: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[dict]:
        """Find subscribers by user ID with optional filtering."""
        filter_query = {"user_id": user_id}

        if status:
            filter_query["status"] = status
        if tags:
            filter_query["tags"] = {"$in": tags}
        if groups:
            filter_query["groups"] = {"$in": groups}

        cursor = self.collection.find(filter_query)
        cursor = cursor.sort("created_at", -1).skip(skip).limit(limit)

        subscribers = []
        async for doc in cursor:
            subscribers.append(self._format_doc(doc))
        return subscribers

    async def find_active_by_user(
        self,
        user_id: str,
        tags: Optional[List[str]] = None,
        exclude_tags: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 1000,
    ) -> List[dict]:
        """Find active subscribers for sending campaigns."""
        filter_query = {
            "user_id": user_id,
            "status": SubscriberStatus.SUBSCRIBED,
        }

        if tags:
            filter_query["tags"] = {"$in": tags}
        if exclude_tags:
            filter_query["tags"] = {"$nin": exclude_tags}

        cursor = self.collection.find(filter_query)
        cursor = cursor.skip(skip).limit(limit)

        subscribers = []
        async for doc in cursor:
            subscribers.append(self._format_doc(doc))
        return subscribers

    async def count_by_user(
        self,
        user_id: str,
        status: Optional[str] = None,
    ) -> int:
        """Count subscribers for a user."""
        filter_query = {"user_id": user_id}
        if status:
            filter_query["status"] = status
        return await self.collection.count_documents(filter_query)

    async def update(
        self,
        subscriber_id: str,
        **updates,
    ) -> Optional[dict]:
        """Update a subscriber."""
        updates["updated_at"] = datetime.now(timezone.utc)

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(subscriber_id)},
            {"$set": updates},
            return_document=True,
        )
        return self._format_doc(result)

    async def update_preferences(
        self,
        subscriber_id: str,
        preferences: Dict[str, Any],
    ) -> Optional[dict]:
        """Update subscriber preferences."""
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(subscriber_id)},
            {
                "$set": {
                    "preferences": preferences,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            return_document=True,
        )
        return self._format_doc(result)

    async def update_status(
        self,
        subscriber_id: str,
        status: str,
    ) -> Optional[dict]:
        """Update subscriber status."""
        updates = {
            "status": status,
            "updated_at": datetime.now(timezone.utc),
        }

        if status == SubscriberStatus.UNSUBSCRIBED:
            updates["unsubscribed_at"] = datetime.now(timezone.utc)

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(subscriber_id)},
            {"$set": updates},
            return_document=True,
        )
        return self._format_doc(result)

    async def update_engagement(
        self,
        subscriber_id: str,
        event_type: str,  # "received", "opened", "clicked"
    ) -> Optional[dict]:
        """Update subscriber engagement metrics."""
        now = datetime.now(timezone.utc)

        # Increment appropriate counter
        inc_field = f"engagement.emails_{event_type}"
        updates = {"$inc": {inc_field: 1}, "$set": {"updated_at": now}}

        if event_type == "opened":
            updates["$set"]["engagement.last_opened_at"] = now
        elif event_type == "clicked":
            updates["$set"]["engagement.last_clicked_at"] = now

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(subscriber_id)},
            updates,
            return_document=True,
        )

        if result:
            # Recalculate rates
            engagement = result.get("engagement", {})
            received = engagement.get("emails_received", 0)
            if received > 0:
                open_rate = engagement.get("emails_opened", 0) / received
                click_rate = engagement.get("emails_clicked", 0) / received
                await self.collection.update_one(
                    {"_id": ObjectId(subscriber_id)},
                    {
                        "$set": {
                            "engagement.open_rate": round(open_rate, 4),
                            "engagement.click_rate": round(click_rate, 4),
                        }
                    },
                )

        return self._format_doc(result)

    async def add_tags(
        self,
        subscriber_id: str,
        tags: List[str],
    ) -> Optional[dict]:
        """Add tags to a subscriber."""
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(subscriber_id)},
            {
                "$addToSet": {"tags": {"$each": tags}},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
            return_document=True,
        )
        return self._format_doc(result)

    async def remove_tags(
        self,
        subscriber_id: str,
        tags: List[str],
    ) -> Optional[dict]:
        """Remove tags from a subscriber."""
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(subscriber_id)},
            {
                "$pull": {"tags": {"$in": tags}},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
            return_document=True,
        )
        return self._format_doc(result)

    async def bulk_create(
        self,
        user_id: str,
        subscribers: List[Dict[str, Any]],
        source: str = "import",
    ) -> Dict[str, int]:
        """Bulk create subscribers (for import)."""
        now = datetime.now(timezone.utc)
        created = 0
        skipped = 0

        for sub_data in subscribers:
            email = sub_data.get("email", "").lower().strip()
            if not email:
                skipped += 1
                continue

            # Check if already exists
            existing = await self.find_by_email(user_id, email)
            if existing:
                skipped += 1
                continue

            # Create subscriber
            doc = {
                "user_id": user_id,
                "email": email,
                "name": sub_data.get("name"),
                "status": SubscriberStatus.SUBSCRIBED,
                "preferences": sub_data.get("preferences", {
                    "topics": [],
                    "tone": "professional",
                    "frequency": "weekly",
                    "include_mindmap": True,
                    "custom_prompt": None,
                }),
                "tags": sub_data.get("tags", []),
                "groups": sub_data.get("groups", []),
                "engagement": {
                    "emails_received": 0,
                    "emails_opened": 0,
                    "emails_clicked": 0,
                    "last_opened_at": None,
                    "last_clicked_at": None,
                    "open_rate": 0.0,
                    "click_rate": 0.0,
                },
                "source": source,
                "metadata": sub_data.get("metadata", {}),
                "subscribed_at": now,
                "unsubscribed_at": None,
                "created_at": now,
                "updated_at": None,
            }

            await self.collection.insert_one(doc)
            created += 1

        return {"created": created, "skipped": skipped}

    async def delete(self, subscriber_id: str) -> bool:
        """Delete a subscriber."""
        result = await self.collection.delete_one({"_id": ObjectId(subscriber_id)})
        return result.deleted_count > 0

    async def delete_by_user(self, user_id: str) -> int:
        """Delete all subscribers for a user."""
        result = await self.collection.delete_many({"user_id": user_id})
        return result.deleted_count


# Singleton instance
_subscriber_repository: Optional[SubscriberRepository] = None


def get_subscriber_repository() -> SubscriberRepository:
    """Get the subscriber repository instance."""
    global _subscriber_repository
    if _subscriber_repository is None:
        _subscriber_repository = SubscriberRepository()
    return _subscriber_repository
