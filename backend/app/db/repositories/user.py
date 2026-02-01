"""
User repository for database operations.
"""
import time
from typing import Optional, List
from bson import ObjectId

from app.db.mongodb import get_database
from app.core.security import get_password_hash, verify_password


class UserRepository:
    """Repository for user database operations."""

    def __init__(self):
        self.collection_name = "users"

    @property
    def collection(self):
        """Get the users collection."""
        db = get_database()
        return db[self.collection_name]

    async def find_by_id(self, user_id: str) -> Optional[dict]:
        """
        Find a user by ID.

        Args:
            user_id: The user's ObjectId as string

        Returns:
            User document or None
        """
        try:
            doc = await self.collection.find_one({"_id": ObjectId(user_id)})
            if doc:
                doc["id"] = str(doc.pop("_id"))
            return doc
        except Exception:
            return None

    async def find_by_username(self, username: str) -> Optional[dict]:
        """
        Find a user by username.

        Args:
            username: The username to search for

        Returns:
            User document or None
        """
        doc = await self.collection.find_one({"username": username})
        if doc:
            doc["id"] = str(doc.pop("_id"))
        return doc

    async def find_by_email(self, email: str) -> Optional[dict]:
        """
        Find a user by email.

        Args:
            email: The email to search for

        Returns:
            User document or None
        """
        doc = await self.collection.find_one({"email": email})
        if doc:
            doc["id"] = str(doc.pop("_id"))
        return doc

    async def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[dict]:
        """
        Find all users with optional filtering.

        Args:
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            role: Filter by role
            is_active: Filter by active status

        Returns:
            List of user documents
        """
        filter_query = {}
        if role:
            filter_query["role"] = role
        if is_active is not None:
            filter_query["is_active"] = is_active

        cursor = self.collection.find(filter_query).skip(skip).limit(limit)
        users = []
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            users.append(doc)
        return users

    async def count(self, role: Optional[str] = None, is_active: Optional[bool] = None) -> int:
        """
        Count users with optional filtering.

        Args:
            role: Filter by role
            is_active: Filter by active status

        Returns:
            Number of matching users
        """
        filter_query = {}
        if role:
            filter_query["role"] = role
        if is_active is not None:
            filter_query["is_active"] = is_active

        return await self.collection.count_documents(filter_query)

    async def create(
        self,
        username: str,
        email: str,
        password: str,
        role: str = "user",
        is_active: bool = True,
    ) -> dict:
        """
        Create a new user.

        Args:
            username: The username
            email: The email address
            password: The plain text password (will be hashed)
            role: The user role (default: "user")
            is_active: Whether the user is active (default: True)

        Returns:
            The created user document

        Raises:
            ValueError: If username or email already exists
        """
        # Check for existing username
        existing = await self.find_by_username(username)
        if existing:
            raise ValueError(f"Username '{username}' already exists")

        # Check for existing email
        existing = await self.find_by_email(email)
        if existing:
            raise ValueError(f"Email '{email}' already exists")

        user_doc = {
            "username": username,
            "email": email,
            "hashed_password": get_password_hash(password),
            "role": role,
            "is_active": is_active,
            "created_at": time.time(),
            "updated_at": None,
        }

        result = await self.collection.insert_one(user_doc)
        user_doc["id"] = str(result.inserted_id)
        user_doc.pop("_id", None)

        return user_doc

    async def update(self, user_id: str, **kwargs) -> Optional[dict]:
        """
        Update a user.

        Args:
            user_id: The user's ObjectId as string
            **kwargs: Fields to update

        Returns:
            The updated user document or None
        """
        # Remove None values and id field
        update_data = {k: v for k, v in kwargs.items() if v is not None and k != "id"}

        if not update_data:
            return await self.find_by_id(user_id)

        # Hash password if being updated
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

        update_data["updated_at"] = time.time()

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": update_data},
            return_document=True,
        )

        if result:
            result["id"] = str(result.pop("_id"))

        return result

    async def delete(self, user_id: str) -> bool:
        """
        Delete a user.

        Args:
            user_id: The user's ObjectId as string

        Returns:
            True if deleted, False otherwise
        """
        result = await self.collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0

    async def authenticate(self, username: str, password: str) -> Optional[dict]:
        """
        Authenticate a user by username and password.

        Args:
            username: The username
            password: The plain text password

        Returns:
            The user document if authentication succeeds, None otherwise
        """
        user = await self.find_by_username(username)

        if not user:
            return None

        if not user.get("is_active", False):
            return None

        if not verify_password(password, user.get("hashed_password", "")):
            return None

        return user

    async def set_active(self, user_id: str, is_active: bool) -> Optional[dict]:
        """
        Set user active status.

        Args:
            user_id: The user's ObjectId as string
            is_active: The active status

        Returns:
            The updated user document or None
        """
        return await self.update(user_id, is_active=is_active)

    async def change_role(self, user_id: str, role: str) -> Optional[dict]:
        """
        Change user role.

        Args:
            user_id: The user's ObjectId as string
            role: The new role

        Returns:
            The updated user document or None
        """
        if role not in ("admin", "user"):
            raise ValueError(f"Invalid role: {role}")

        return await self.update(user_id, role=role)


# Singleton instance
user_repository = UserRepository()


def get_user_repository() -> UserRepository:
    """Get the user repository instance."""
    return user_repository
