"""
Base repository for MongoDB operations.
"""
from typing import Generic, TypeVar, Optional, List
from bson import ObjectId

from app.db.mongodb import get_database

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""

    collection_name: str

    def __init__(self):
        self.db = get_database()
        self.collection = self.db[self.collection_name]

    async def find_by_id(self, id: str) -> Optional[dict]:
        """Find document by ID."""
        return await self.collection.find_one({"_id": ObjectId(id)})

    async def find_all(
        self,
        filter: dict = None,
        skip: int = 0,
        limit: int = 100,
        sort: List[tuple] = None,
    ) -> List[dict]:
        """Find all documents matching filter."""
        cursor = self.collection.find(filter or {})
        if sort:
            cursor = cursor.sort(sort)
        cursor = cursor.skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def count(self, filter: dict = None) -> int:
        """Count documents matching filter."""
        return await self.collection.count_documents(filter or {})

    async def create(self, data: dict) -> dict:
        """Create a new document."""
        result = await self.collection.insert_one(data)
        data["_id"] = result.inserted_id
        return data

    async def update(self, id: str, data: dict) -> Optional[dict]:
        """Update a document by ID."""
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": data},
            return_document=True,
        )
        return result

    async def delete(self, id: str) -> bool:
        """Delete a document by ID."""
        result = await self.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0
