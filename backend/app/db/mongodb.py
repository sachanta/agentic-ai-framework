"""
MongoDB connection and utilities.
"""
import logging
import time
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

logger = logging.getLogger(__name__)

client: Optional[AsyncIOMotorClient] = None
database: Optional[AsyncIOMotorDatabase] = None


async def connect_mongodb() -> None:
    """
    Connect to MongoDB and verify the connection.

    Raises:
        RuntimeError: If connection fails
    """
    global client, database

    logger.info(f"Connecting to MongoDB at {settings.MONGODB_URI}...")

    try:
        client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        database = client[settings.MONGODB_DATABASE]

        # Verify connection
        await client.admin.command("ping")

        # Get server info
        server_info = await client.server_info()
        logger.info(f"Connected to MongoDB version {server_info.get('version', 'unknown')}")

        # Ensure indexes
        await _ensure_indexes()

    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise RuntimeError(f"MongoDB connection failed: {e}")


async def _ensure_indexes() -> None:
    """Create necessary indexes for collections."""
    if database is None:
        return

    # Users collection indexes
    users = database.users
    await users.create_index("username", unique=True)
    await users.create_index("email", unique=True)

    # Executions collection indexes
    executions = database.executions
    await executions.create_index("status")
    await executions.create_index("created_at")
    await executions.create_index([("platform_id", 1), ("created_at", -1)])

    # Logs collection indexes
    logs = database.logs
    await logs.create_index([("timestamp", -1)])
    await logs.create_index("level")
    await logs.create_index("source")

    logger.info("MongoDB indexes ensured")


async def close_mongodb() -> None:
    """Close MongoDB connection."""
    global client, database

    if client:
        client.close()
        client = None
        database = None
        logger.info("MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """
    Get database instance.

    Returns:
        AsyncIOMotorDatabase: The database instance

    Raises:
        RuntimeError: If database is not connected
    """
    if database is None:
        raise RuntimeError("Database not connected. Call connect_mongodb() first.")
    return database


def get_client() -> AsyncIOMotorClient:
    """
    Get MongoDB client instance.

    Returns:
        AsyncIOMotorClient: The client instance

    Raises:
        RuntimeError: If client is not connected
    """
    if client is None:
        raise RuntimeError("MongoDB client not connected. Call connect_mongodb() first.")
    return client


async def get_mongodb_status() -> dict:
    """
    Get MongoDB connection status with latency measurement.

    Returns:
        dict: Status information including health and latency
    """
    if client is None:
        return {
            "status": "disconnected",
            "healthy": False,
            "latency_ms": None,
            "error": "Client not initialized",
        }

    try:
        start = time.time()
        await client.admin.command("ping")
        latency_ms = round((time.time() - start) * 1000, 2)

        # Get additional info
        server_info = await client.server_info()

        return {
            "status": "connected",
            "healthy": True,
            "latency_ms": latency_ms,
            "version": server_info.get("version"),
            "database": settings.MONGODB_DATABASE,
        }
    except Exception as e:
        return {
            "status": "error",
            "healthy": False,
            "latency_ms": None,
            "error": str(e),
        }


async def init_default_data() -> None:
    """
    Initialize default data in the database.
    Creates default admin user if not exists.
    """
    if database is None:
        return

    from app.core.security import get_password_hash

    users = database.users

    # Check if admin user exists
    admin = await users.find_one({"username": "admin"})
    if not admin:
        admin_user = {
            "username": "admin",
            "email": "admin@example.com",
            "hashed_password": get_password_hash("admin123"),
            "role": "admin",
            "is_active": True,
            "created_at": time.time(),
        }
        await users.insert_one(admin_user)
        logger.info("Created default admin user (admin/admin123)")

    # Check if regular user exists
    user = await users.find_one({"username": "user"})
    if not user:
        regular_user = {
            "username": "user",
            "email": "user@example.com",
            "hashed_password": get_password_hash("user123"),
            "role": "user",
            "is_active": True,
            "created_at": time.time(),
        }
        await users.insert_one(regular_user)
        logger.info("Created default user (user/user123)")
