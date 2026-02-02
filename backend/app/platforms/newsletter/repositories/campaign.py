"""
Campaign repository for database operations.

Handles CRUD operations for Campaign documents.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId

from app.db.mongodb import get_database
from app.platforms.newsletter.models import Campaign, CampaignStatus


class CampaignRepository:
    """Repository for campaign database operations."""

    collection_name = "newsletter_campaigns"

    def __init__(self):
        self._db = None
        self._collection = None

    @property
    def collection(self):
        """Get the campaigns collection (lazy-loaded)."""
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
        subject: str,
        newsletter_id: Optional[str] = None,
        template_id: Optional[str] = None,
        **kwargs,
    ) -> dict:
        """Create a new campaign."""
        now = datetime.now(timezone.utc)

        doc = {
            "user_id": user_id,
            "name": name,
            "description": kwargs.get("description"),
            "subject": subject,
            "preview_text": kwargs.get("preview_text"),
            "newsletter_id": newsletter_id,
            "template_id": template_id,
            "status": CampaignStatus.DRAFT,
            "subscriber_tags": kwargs.get("subscriber_tags", []),
            "subscriber_groups": kwargs.get("subscriber_groups", []),
            "exclude_tags": kwargs.get("exclude_tags", []),
            "scheduled_at": kwargs.get("scheduled_at"),
            "send_timezone": kwargs.get("send_timezone", "UTC"),
            "from_email": kwargs.get("from_email"),
            "from_name": kwargs.get("from_name"),
            "reply_to": kwargs.get("reply_to"),
            "analytics": {
                "recipient_count": 0,
                "delivered_count": 0,
                "bounced_count": 0,
                "open_count": 0,
                "unique_open_count": 0,
                "click_count": 0,
                "unique_click_count": 0,
                "unsubscribe_count": 0,
                "spam_count": 0,
                "delivery_rate": 0.0,
                "open_rate": 0.0,
                "click_rate": 0.0,
                "bounce_rate": 0.0,
                "unsubscribe_rate": 0.0,
            },
            "metadata": kwargs.get("metadata", {}),
            "created_at": now,
            "updated_at": None,
            "sent_at": None,
            "completed_at": None,
        }

        result = await self.collection.insert_one(doc)
        doc["id"] = str(result.inserted_id)
        doc.pop("_id", None)
        return doc

    async def find_by_id(self, campaign_id: str) -> Optional[dict]:
        """Find a campaign by ID."""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(campaign_id)})
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
        """Find campaigns by user ID with optional filtering."""
        filter_query = {"user_id": user_id}
        if status:
            filter_query["status"] = status

        cursor = self.collection.find(filter_query)
        cursor = cursor.sort("created_at", -1).skip(skip).limit(limit)

        campaigns = []
        async for doc in cursor:
            campaigns.append(self._format_doc(doc))
        return campaigns

    async def find_scheduled(
        self,
        before: Optional[datetime] = None,
    ) -> List[dict]:
        """Find campaigns scheduled to send."""
        filter_query = {"status": CampaignStatus.SCHEDULED}
        if before:
            filter_query["scheduled_at"] = {"$lte": before}

        cursor = self.collection.find(filter_query)
        cursor = cursor.sort("scheduled_at", 1)

        campaigns = []
        async for doc in cursor:
            campaigns.append(self._format_doc(doc))
        return campaigns

    async def count_by_user(
        self,
        user_id: str,
        status: Optional[str] = None,
    ) -> int:
        """Count campaigns for a user."""
        filter_query = {"user_id": user_id}
        if status:
            filter_query["status"] = status
        return await self.collection.count_documents(filter_query)

    async def update(
        self,
        campaign_id: str,
        **updates,
    ) -> Optional[dict]:
        """Update a campaign."""
        updates["updated_at"] = datetime.now(timezone.utc)

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(campaign_id)},
            {"$set": updates},
            return_document=True,
        )
        return self._format_doc(result)

    async def update_status(
        self,
        campaign_id: str,
        status: str,
    ) -> Optional[dict]:
        """Update campaign status."""
        updates = {
            "status": status,
            "updated_at": datetime.now(timezone.utc),
        }

        # Set timestamp based on status
        if status == CampaignStatus.SENDING:
            updates["sent_at"] = datetime.now(timezone.utc)
        elif status == CampaignStatus.SENT:
            updates["completed_at"] = datetime.now(timezone.utc)

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(campaign_id)},
            {"$set": updates},
            return_document=True,
        )
        return self._format_doc(result)

    async def schedule(
        self,
        campaign_id: str,
        scheduled_at: datetime,
        timezone: str = "UTC",
    ) -> Optional[dict]:
        """Schedule a campaign for sending."""
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(campaign_id)},
            {
                "$set": {
                    "status": CampaignStatus.SCHEDULED,
                    "scheduled_at": scheduled_at,
                    "send_timezone": timezone,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            return_document=True,
        )
        return self._format_doc(result)

    async def update_analytics(
        self,
        campaign_id: str,
        analytics_updates: Dict[str, Any],
    ) -> Optional[dict]:
        """Update campaign analytics."""
        # Prepare update operations
        set_ops = {"updated_at": datetime.now(timezone.utc)}
        inc_ops = {}

        for key, value in analytics_updates.items():
            if key.endswith("_count"):
                inc_ops[f"analytics.{key}"] = value
            else:
                set_ops[f"analytics.{key}"] = value

        update_ops = {"$set": set_ops}
        if inc_ops:
            update_ops["$inc"] = inc_ops

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(campaign_id)},
            update_ops,
            return_document=True,
        )

        # Recalculate rates
        if result:
            analytics = result.get("analytics", {})
            recipient_count = analytics.get("recipient_count", 0)
            if recipient_count > 0:
                delivered = analytics.get("delivered_count", 0)
                bounced = analytics.get("bounced_count", 0)
                unique_opens = analytics.get("unique_open_count", 0)
                unique_clicks = analytics.get("unique_click_count", 0)
                unsubscribes = analytics.get("unsubscribe_count", 0)

                rates = {
                    "analytics.delivery_rate": round(delivered / recipient_count, 4),
                    "analytics.bounce_rate": round(bounced / recipient_count, 4),
                    "analytics.open_rate": round(unique_opens / delivered, 4) if delivered > 0 else 0,
                    "analytics.click_rate": round(unique_clicks / delivered, 4) if delivered > 0 else 0,
                    "analytics.unsubscribe_rate": round(unsubscribes / delivered, 4) if delivered > 0 else 0,
                }

                await self.collection.update_one(
                    {"_id": ObjectId(campaign_id)},
                    {"$set": rates},
                )

        return self._format_doc(result)

    async def increment_analytics(
        self,
        campaign_id: str,
        field: str,
        amount: int = 1,
    ) -> Optional[dict]:
        """Increment a single analytics counter."""
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(campaign_id)},
            {
                "$inc": {f"analytics.{field}": amount},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
            return_document=True,
        )
        return self._format_doc(result)

    async def delete(self, campaign_id: str) -> bool:
        """Delete a campaign."""
        result = await self.collection.delete_one({"_id": ObjectId(campaign_id)})
        return result.deleted_count > 0

    async def delete_by_user(self, user_id: str) -> int:
        """Delete all campaigns for a user."""
        result = await self.collection.delete_many({"user_id": user_id})
        return result.deleted_count


# Singleton instance
_campaign_repository: Optional[CampaignRepository] = None


def get_campaign_repository() -> CampaignRepository:
    """Get the campaign repository instance."""
    global _campaign_repository
    if _campaign_repository is None:
        _campaign_repository = CampaignRepository()
    return _campaign_repository
