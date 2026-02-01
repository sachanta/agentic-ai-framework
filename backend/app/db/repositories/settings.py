"""
Settings repository for MongoDB operations.
"""
import logging
from datetime import datetime
from typing import Dict, Optional, Any

from app.db.mongodb import get_database
from app.models.settings import DEFAULT_SETTINGS

logger = logging.getLogger(__name__)


class SettingsRepository:
    """Repository for settings operations."""

    collection_name = "settings"

    def __init__(self):
        self.db = get_database()
        if self.db is not None:
            self.collection = self.db[self.collection_name]
        else:
            self.collection = None

    async def get_all(self) -> Dict[str, Any]:
        """
        Get all settings combined.

        Returns:
            Dictionary with all settings by category
        """
        if self.collection is None:
            return DEFAULT_SETTINGS.copy()

        result = {}
        async for doc in self.collection.find():
            category = doc.get("category")
            if category:
                result[category] = doc.get("settings", {})

        # Merge with defaults for any missing categories
        for category, defaults in DEFAULT_SETTINGS.items():
            if category not in result:
                result[category] = defaults

        return result

    async def get_category(self, category: str) -> Optional[Dict[str, Any]]:
        """
        Get settings for a specific category.

        Args:
            category: The settings category

        Returns:
            Settings dictionary or None
        """
        if self.collection is None:
            return DEFAULT_SETTINGS.get(category)

        doc = await self.collection.find_one({"category": category})
        if doc:
            return {
                "category": category,
                "settings": doc.get("settings", {}),
                "updated_at": doc.get("updated_at"),
                "updated_by": doc.get("updated_by"),
            }

        # Return defaults if category exists
        if category in DEFAULT_SETTINGS:
            return {
                "category": category,
                "settings": DEFAULT_SETTINGS[category],
                "updated_at": None,
                "updated_by": None,
            }

        return None

    async def update_category(
        self,
        category: str,
        settings: Dict[str, Any],
        updated_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update settings for a specific category.

        Args:
            category: The settings category
            settings: The new settings values
            updated_by: User ID who made the update

        Returns:
            Updated settings dictionary
        """
        if self.collection is None:
            logger.warning("Database not connected, settings not persisted")
            return {
                "category": category,
                "settings": settings,
                "updated_at": datetime.utcnow(),
                "updated_by": updated_by,
            }

        now = datetime.utcnow()

        # Merge with existing settings
        existing = await self.collection.find_one({"category": category})
        if existing:
            merged_settings = {**existing.get("settings", {}), **settings}
        else:
            # Merge with defaults if new category entry
            defaults = DEFAULT_SETTINGS.get(category, {})
            merged_settings = {**defaults, **settings}

        result = await self.collection.find_one_and_update(
            {"category": category},
            {
                "$set": {
                    "settings": merged_settings,
                    "updated_at": now,
                    "updated_by": updated_by,
                },
                "$setOnInsert": {
                    "category": category,
                    "created_at": now,
                },
            },
            upsert=True,
            return_document=True,
        )

        logger.info(f"Updated settings for category: {category}")

        return {
            "category": category,
            "settings": result.get("settings", {}),
            "updated_at": result.get("updated_at"),
            "updated_by": result.get("updated_by"),
        }

    async def update_all(
        self,
        settings: Dict[str, Dict[str, Any]],
        updated_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update multiple settings categories at once.

        Args:
            settings: Dictionary of category -> settings
            updated_by: User ID who made the update

        Returns:
            All updated settings
        """
        result = {}
        for category, category_settings in settings.items():
            updated = await self.update_category(category, category_settings, updated_by)
            result[category] = updated["settings"]

        return result

    async def reset_category(self, category: str) -> Optional[Dict[str, Any]]:
        """
        Reset a category to default settings.

        Args:
            category: The settings category

        Returns:
            Default settings or None if category doesn't exist
        """
        if category not in DEFAULT_SETTINGS:
            return None

        if self.collection is not None:
            await self.collection.delete_one({"category": category})

        return {
            "category": category,
            "settings": DEFAULT_SETTINGS[category],
            "updated_at": None,
            "updated_by": None,
        }

    async def reset_all(self) -> Dict[str, Any]:
        """
        Reset all settings to defaults.

        Returns:
            Default settings
        """
        if self.collection is not None:
            await self.collection.delete_many({})

        return DEFAULT_SETTINGS.copy()


# Repository instance
_settings_repository: Optional[SettingsRepository] = None


def get_settings_repository() -> SettingsRepository:
    """Get the settings repository instance."""
    global _settings_repository
    if _settings_repository is None:
        _settings_repository = SettingsRepository()
    return _settings_repository
