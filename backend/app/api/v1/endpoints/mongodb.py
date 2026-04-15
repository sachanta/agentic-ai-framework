"""
MongoDB management endpoints for Agentic AI Framework.

Provides comprehensive CRUD operations and specialized endpoints for:
- Agent execution history
- Conversation memory
- Knowledge base management
- Agent configurations
- Workflow state
- Analytics and metrics
- Task queues
- Audit logs
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Query, status, Body
from pydantic import BaseModel, Field

from app.db.mongodb import get_database, get_client, get_mongodb_status
from app.core.sanitization import sanitize_query, sanitize_pipeline

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Pydantic Models for Request/Response
# =============================================================================

class SortOrder(str, Enum):
    """Sort order enum."""
    ASC = "asc"
    DESC = "desc"


class CollectionStats(BaseModel):
    """Collection statistics."""
    name: str
    document_count: int
    size_bytes: int
    avg_document_size: int
    indexes: List[dict] = []
    capped: bool = False


class CollectionCreateRequest(BaseModel):
    """Request to create a collection."""
    name: str
    capped: bool = False
    max_size: Optional[int] = None  # For capped collections
    max_documents: Optional[int] = None  # For capped collections
    indexes: List[dict] = []  # List of index definitions


class IndexCreateRequest(BaseModel):
    """Request to create an index."""
    keys: Dict[str, int]  # Field name -> 1 (asc) or -1 (desc)
    name: Optional[str] = None
    unique: bool = False
    sparse: bool = False
    ttl_seconds: Optional[int] = None  # For TTL indexes


class DocumentCreateRequest(BaseModel):
    """Request to create a document."""
    data: Dict[str, Any]
    add_timestamps: bool = True


class DocumentUpdateRequest(BaseModel):
    """Request to update a document."""
    data: Dict[str, Any]
    upsert: bool = False
    add_updated_at: bool = True


class QueryRequest(BaseModel):
    """Request for querying documents."""
    filter: Dict[str, Any] = {}
    projection: Optional[Dict[str, int]] = None
    sort: Optional[Dict[str, int]] = None
    skip: int = 0
    limit: int = 100


class AggregationRequest(BaseModel):
    """Request for aggregation pipeline."""
    pipeline: List[Dict[str, Any]]


class BulkWriteOperation(BaseModel):
    """Single bulk write operation."""
    operation: str  # insert, update, delete
    filter: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None


class BulkWriteRequest(BaseModel):
    """Request for bulk write operations."""
    operations: List[BulkWriteOperation]
    ordered: bool = True


class BulkImportRequest(BaseModel):
    """Request for bulk import."""
    documents: List[Dict[str, Any]]
    add_timestamps: bool = True


class TextSearchRequest(BaseModel):
    """Request for text search."""
    query: str
    filter: Optional[Dict[str, Any]] = None
    limit: int = 100


class PaginatedResponse(BaseModel):
    """Paginated response for list operations."""
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


# =============================================================================
# Helper Functions
# =============================================================================

def serialize_doc(doc: dict) -> dict:
    """Convert MongoDB document to JSON-serializable format."""
    if doc is None:
        return None

    result = {}
    for key, value in doc.items():
        if key == "_id":
            result["id"] = str(value)
            result["_id"] = str(value)
        elif isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, dict):
            result[key] = serialize_doc(value)
        elif isinstance(value, list):
            result[key] = [
                serialize_doc(v) if isinstance(v, dict) else str(v) if isinstance(v, ObjectId) else v
                for v in value
            ]
        else:
            result[key] = value
    return result


def parse_object_id(doc_id: str) -> ObjectId:
    """Parse and validate ObjectId."""
    try:
        return ObjectId(doc_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document ID format: {doc_id}"
        )


def check_db():
    """Check if database is connected."""
    try:
        return get_database()
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB is not available"
        )


# =============================================================================
# Database Status Endpoints
# =============================================================================

@router.get("/status")
async def get_status():
    """Get MongoDB connection status and server info."""
    return await get_mongodb_status()


@router.get("/stats")
async def get_database_stats():
    """Get database statistics."""
    db = check_db()

    try:
        stats = await db.command("dbStats")
        return {
            "database": stats.get("db"),
            "collections": stats.get("collections"),
            "documents": stats.get("objects"),
            "data_size_bytes": stats.get("dataSize"),
            "storage_size_bytes": stats.get("storageSize"),
            "indexes": stats.get("indexes"),
            "index_size_bytes": stats.get("indexSize"),
        }
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get database stats: {str(e)}"
        )


# =============================================================================
# Collection Management Endpoints
# =============================================================================

@router.get("/collections")
async def list_collections():
    """List all MongoDB collections with stats."""
    db = check_db()

    try:
        collection_names = await db.list_collection_names()
        collections = []

        for name in collection_names:
            # Skip system collections
            if name.startswith("system."):
                continue

            stats = await db.command("collStats", name)
            collections.append({
                "name": name,
                "document_count": stats.get("count", 0),
                "size_bytes": stats.get("size", 0),
                "avg_document_size": stats.get("avgObjSize", 0),
                "storage_size": stats.get("storageSize", 0),
                "indexes": stats.get("nindexes", 0),
                "capped": stats.get("capped", False),
            })

        return {
            "collections": collections,
            "total": len(collections),
        }
    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list collections: {str(e)}"
        )


@router.get("/collections/{name}")
async def get_collection_info(name: str):
    """Get detailed collection information."""
    db = check_db()

    try:
        if name not in await db.list_collection_names():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{name}' not found"
            )

        stats = await db.command("collStats", name)

        # Get indexes
        collection = db[name]
        indexes = []
        async for index in collection.list_indexes():
            indexes.append({
                "name": index.get("name"),
                "keys": dict(index.get("key", {})),
                "unique": index.get("unique", False),
                "sparse": index.get("sparse", False),
                "ttl": index.get("expireAfterSeconds"),
            })

        return {
            "name": name,
            "document_count": stats.get("count", 0),
            "size_bytes": stats.get("size", 0),
            "avg_document_size": stats.get("avgObjSize", 0),
            "storage_size": stats.get("storageSize", 0),
            "capped": stats.get("capped", False),
            "max_size": stats.get("maxSize"),
            "indexes": indexes,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get collection info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collection info: {str(e)}"
        )


@router.post("/collections", status_code=status.HTTP_201_CREATED)
async def create_collection(request: CollectionCreateRequest):
    """Create a new collection with optional settings."""
    db = check_db()

    try:
        if request.name in await db.list_collection_names():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Collection '{request.name}' already exists"
            )

        # Build collection options
        options = {}
        if request.capped:
            options["capped"] = True
            options["size"] = request.max_size or 1048576  # 1MB default
            if request.max_documents:
                options["max"] = request.max_documents

        # Create collection
        await db.create_collection(request.name, **options)

        # Create indexes if specified
        if request.indexes:
            collection = db[request.name]
            for idx in request.indexes:
                keys = [(k, v) for k, v in idx.get("keys", {}).items()]
                if keys:
                    await collection.create_index(
                        keys,
                        name=idx.get("name"),
                        unique=idx.get("unique", False),
                        sparse=idx.get("sparse", False),
                    )

        logger.info(f"Created MongoDB collection: {request.name}")

        return {
            "message": f"Collection '{request.name}' created successfully",
            "name": request.name,
            "capped": request.capped,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create collection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create collection: {str(e)}"
        )


@router.delete("/collections/{name}")
async def delete_collection(name: str):
    """Delete a collection."""
    db = check_db()

    try:
        if name not in await db.list_collection_names():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{name}' not found"
            )

        # Prevent deletion of system collections
        protected = ["users", "system.indexes", "system.profile"]
        if name in protected:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cannot delete protected collection '{name}'"
            )

        await db.drop_collection(name)
        logger.info(f"Deleted MongoDB collection: {name}")

        return {"message": f"Collection '{name}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete collection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete collection: {str(e)}"
        )


# =============================================================================
# Index Management Endpoints
# =============================================================================

@router.get("/collections/{name}/indexes")
async def list_indexes(name: str):
    """List all indexes for a collection."""
    db = check_db()

    try:
        if name not in await db.list_collection_names():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{name}' not found"
            )

        collection = db[name]
        indexes = []
        async for index in collection.list_indexes():
            indexes.append({
                "name": index.get("name"),
                "keys": dict(index.get("key", {})),
                "unique": index.get("unique", False),
                "sparse": index.get("sparse", False),
                "ttl": index.get("expireAfterSeconds"),
                "background": index.get("background", False),
            })

        return {"indexes": indexes, "total": len(indexes)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list indexes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list indexes: {str(e)}"
        )


@router.post("/collections/{name}/indexes", status_code=status.HTTP_201_CREATED)
async def create_index(name: str, request: IndexCreateRequest):
    """Create an index on a collection."""
    db = check_db()

    try:
        if name not in await db.list_collection_names():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{name}' not found"
            )

        collection = db[name]
        keys = [(k, v) for k, v in request.keys.items()]

        kwargs = {
            "unique": request.unique,
            "sparse": request.sparse,
        }
        if request.name:
            kwargs["name"] = request.name
        if request.ttl_seconds is not None:
            kwargs["expireAfterSeconds"] = request.ttl_seconds

        index_name = await collection.create_index(keys, **kwargs)

        return {
            "message": "Index created successfully",
            "name": index_name,
            "keys": request.keys,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create index: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create index: {str(e)}"
        )


@router.delete("/collections/{name}/indexes/{index_name}")
async def delete_index(name: str, index_name: str):
    """Delete an index from a collection."""
    db = check_db()

    try:
        if name not in await db.list_collection_names():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{name}' not found"
            )

        if index_name == "_id_":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the _id index"
            )

        collection = db[name]
        await collection.drop_index(index_name)

        return {"message": f"Index '{index_name}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete index: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete index: {str(e)}"
        )


# =============================================================================
# Document CRUD Endpoints
# =============================================================================

@router.get("/collections/{name}/documents", response_model=PaginatedResponse)
async def list_documents(
    name: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    sort_order: SortOrder = Query(SortOrder.DESC),
    filter: Optional[str] = Query(None, description="JSON filter string"),
):
    """List documents in a collection with pagination."""
    db = check_db()

    try:
        if name not in await db.list_collection_names():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{name}' not found"
            )

        collection = db[name]

        # Parse filter if provided
        query_filter = {}
        if filter:
            import json
            try:
                query_filter = json.loads(filter)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid filter JSON"
                )

        # Get total count
        total = await collection.count_documents(query_filter)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        # Build query
        cursor = collection.find(query_filter)

        # Apply sort
        if sort_by:
            sort_direction = 1 if sort_order == SortOrder.ASC else -1
            cursor = cursor.sort(sort_by, sort_direction)
        else:
            cursor = cursor.sort("_id", -1)  # Default: newest first

        # Apply pagination
        skip = (page - 1) * page_size
        cursor = cursor.skip(skip).limit(page_size)

        # Fetch documents
        documents = await cursor.to_list(length=page_size)
        items = [serialize_doc(doc) for doc in documents]

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/collections/{name}/documents/{doc_id}")
async def get_document(name: str, doc_id: str):
    """Get a single document by ID."""
    db = check_db()

    try:
        if name not in await db.list_collection_names():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{name}' not found"
            )

        collection = db[name]
        obj_id = parse_object_id(doc_id)

        document = await collection.find_one({"_id": obj_id})
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{doc_id}' not found"
            )

        return serialize_doc(document)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}"
        )


@router.post("/collections/{name}/documents", status_code=status.HTTP_201_CREATED)
async def create_document(name: str, request: DocumentCreateRequest):
    """Create a new document."""
    db = check_db()

    try:
        if name not in await db.list_collection_names():
            # Auto-create collection
            await db.create_collection(name)

        collection = db[name]
        data = request.data.copy()

        # Add timestamps if requested
        if request.add_timestamps:
            now = datetime.utcnow()
            data["created_at"] = now
            data["updated_at"] = now

        result = await collection.insert_one(data)
        data["_id"] = result.inserted_id

        return serialize_doc(data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document: {str(e)}"
        )


@router.put("/collections/{name}/documents/{doc_id}")
async def update_document(name: str, doc_id: str, request: DocumentUpdateRequest):
    """Update a document (full replace)."""
    db = check_db()

    try:
        if name not in await db.list_collection_names():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{name}' not found"
            )

        collection = db[name]
        obj_id = parse_object_id(doc_id)
        data = request.data.copy()

        # Add updated_at timestamp
        if request.add_updated_at:
            data["updated_at"] = datetime.utcnow()

        if request.upsert:
            result = await collection.find_one_and_replace(
                {"_id": obj_id},
                data,
                upsert=True,
                return_document=True,
            )
        else:
            # Check if document exists
            existing = await collection.find_one({"_id": obj_id})
            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document '{doc_id}' not found"
                )

            result = await collection.find_one_and_replace(
                {"_id": obj_id},
                data,
                return_document=True,
            )

        return serialize_doc(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document: {str(e)}"
        )


@router.patch("/collections/{name}/documents/{doc_id}")
async def patch_document(name: str, doc_id: str, data: Dict[str, Any] = Body(...)):
    """Partially update a document."""
    db = check_db()

    try:
        if name not in await db.list_collection_names():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{name}' not found"
            )

        collection = db[name]
        obj_id = parse_object_id(doc_id)

        # Add updated_at timestamp
        data["updated_at"] = datetime.utcnow()

        result = await collection.find_one_and_update(
            {"_id": obj_id},
            {"$set": data},
            return_document=True,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{doc_id}' not found"
            )

        return serialize_doc(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to patch document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to patch document: {str(e)}"
        )


@router.delete("/collections/{name}/documents/{doc_id}")
async def delete_document(name: str, doc_id: str):
    """Delete a document."""
    db = check_db()

    try:
        if name not in await db.list_collection_names():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{name}' not found"
            )

        collection = db[name]
        obj_id = parse_object_id(doc_id)

        result = await collection.delete_one({"_id": obj_id})

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{doc_id}' not found"
            )

        return {"message": f"Document '{doc_id}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


# =============================================================================
# Query and Aggregation Endpoints
# =============================================================================

@router.post("/collections/{name}/query")
async def query_documents(name: str, request: QueryRequest):
    """Query documents with filters, projections, and sorting."""
    db = check_db()

    try:
        if name not in await db.list_collection_names():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{name}' not found"
            )

        collection = db[name]

        # Sanitize filter to prevent NoSQL injection
        safe_filter = sanitize_query(request.filter)

        # Get total count for the filter
        total = await collection.count_documents(safe_filter)

        # Build query
        cursor = collection.find(safe_filter, request.projection)

        if request.sort:
            sort_list = [(k, v) for k, v in request.sort.items()]
            cursor = cursor.sort(sort_list)

        cursor = cursor.skip(request.skip).limit(request.limit)

        documents = await cursor.to_list(length=request.limit)

        return {
            "documents": [serialize_doc(doc) for doc in documents],
            "count": len(documents),
            "total": total,
            "skip": request.skip,
            "limit": request.limit,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to query documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query documents: {str(e)}"
        )


@router.post("/collections/{name}/aggregate")
async def aggregate_documents(name: str, request: AggregationRequest):
    """Run aggregation pipeline on a collection."""
    db = check_db()

    try:
        if name not in await db.list_collection_names():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{name}' not found"
            )

        collection = db[name]

        # Sanitize pipeline to prevent NoSQL injection
        safe_pipeline = sanitize_pipeline(request.pipeline)
        cursor = collection.aggregate(safe_pipeline)
        results = await cursor.to_list(length=1000)

        return {
            "results": [serialize_doc(doc) for doc in results],
            "count": len(results),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run aggregation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run aggregation: {str(e)}"
        )


@router.post("/collections/{name}/count")
async def count_documents(name: str, filter: Dict[str, Any] = Body(default={})):
    """Count documents matching a filter."""
    db = check_db()

    try:
        if name not in await db.list_collection_names():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{name}' not found"
            )

        collection = db[name]
        count = await collection.count_documents(filter)

        return {"count": count, "filter": filter}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to count documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to count documents: {str(e)}"
        )


@router.post("/collections/{name}/distinct")
async def distinct_values(
    name: str,
    field: str = Body(..., embed=True),
    filter: Dict[str, Any] = Body(default={}),
):
    """Get distinct values for a field."""
    db = check_db()

    try:
        if name not in await db.list_collection_names():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{name}' not found"
            )

        collection = db[name]
        values = await collection.distinct(field, filter)

        return {
            "field": field,
            "values": values,
            "count": len(values),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get distinct values: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get distinct values: {str(e)}"
        )


# =============================================================================
# Bulk Operations Endpoints
# =============================================================================

@router.post("/collections/{name}/bulk-write")
async def bulk_write(name: str, request: BulkWriteRequest):
    """Perform bulk write operations."""
    db = check_db()

    try:
        if name not in await db.list_collection_names():
            # Auto-create collection
            await db.create_collection(name)

        collection = db[name]
        from pymongo import InsertOne, UpdateOne, DeleteOne

        operations = []
        for op in request.operations:
            if op.operation == "insert":
                operations.append(InsertOne(op.data))
            elif op.operation == "update":
                operations.append(UpdateOne(op.filter or {}, {"$set": op.data}))
            elif op.operation == "delete":
                operations.append(DeleteOne(op.filter or {}))

        if operations:
            result = await collection.bulk_write(operations, ordered=request.ordered)
            return {
                "inserted": result.inserted_count,
                "modified": result.modified_count,
                "deleted": result.deleted_count,
                "upserted": result.upserted_count,
            }

        return {"message": "No operations to perform"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform bulk write: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk write: {str(e)}"
        )


@router.post("/collections/{name}/import")
async def import_documents(name: str, request: BulkImportRequest):
    """Bulk import documents."""
    db = check_db()

    try:
        if name not in await db.list_collection_names():
            # Auto-create collection
            await db.create_collection(name)

        collection = db[name]

        # Prepare documents
        now = datetime.utcnow()
        documents = []
        for doc in request.documents:
            if request.add_timestamps:
                doc["created_at"] = now
                doc["updated_at"] = now
            documents.append(doc)

        # Insert documents
        if documents:
            result = await collection.insert_many(documents)
            return {
                "imported": len(result.inserted_ids),
                "total": len(request.documents),
                "ids": [str(id) for id in result.inserted_ids],
            }

        return {"imported": 0, "total": 0}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import documents: {str(e)}"
        )


@router.get("/collections/{name}/export")
async def export_documents(
    name: str,
    format: str = Query("json", enum=["json", "csv"]),
    filter: Optional[str] = Query(None),
    limit: int = Query(1000, le=10000),
):
    """Export documents from a collection."""
    db = check_db()

    try:
        if name not in await db.list_collection_names():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{name}' not found"
            )

        collection = db[name]

        # Parse filter
        query_filter = {}
        if filter:
            import json
            try:
                query_filter = json.loads(filter)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid filter JSON"
                )

        cursor = collection.find(query_filter).limit(limit)
        documents = await cursor.to_list(length=limit)

        serialized = [serialize_doc(doc) for doc in documents]

        if format == "csv":
            # Convert to CSV format
            if not serialized:
                return {"data": "", "count": 0}

            import csv
            import io

            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=serialized[0].keys())
            writer.writeheader()
            writer.writerows(serialized)

            return {
                "data": output.getvalue(),
                "count": len(serialized),
                "format": "csv",
            }

        return {
            "documents": serialized,
            "count": len(serialized),
            "format": "json",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export documents: {str(e)}"
        )


@router.delete("/collections/{name}/documents")
async def delete_many_documents(name: str, filter: Dict[str, Any] = Body(...)):
    """Delete multiple documents matching a filter."""
    db = check_db()

    try:
        if name not in await db.list_collection_names():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{name}' not found"
            )

        # Safety check: prevent deletion of all documents without explicit filter
        if not filter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filter is required for bulk delete. Use {'_all': true} to delete all."
            )

        collection = db[name]

        # Handle special case for deleting all
        if filter.get("_all") == True:
            filter = {}

        result = await collection.delete_many(filter)

        return {
            "deleted": result.deleted_count,
            "filter": filter,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete documents: {str(e)}"
        )


# =============================================================================
# Agentic AI Specific Endpoints
# =============================================================================

@router.post("/agent-executions")
async def log_agent_execution(
    execution: Dict[str, Any] = Body(...),
):
    """
    Log an agent execution for tracking and analytics.

    Expected fields:
    - agent_name: Name of the agent
    - platform_id: Platform identifier
    - input: Input data
    - output: Output data
    - status: success/failed/error
    - duration_ms: Execution duration
    - tokens_used: Token usage (optional)
    - error: Error message if failed (optional)
    """
    db = check_db()

    try:
        collection = db["agent_executions"]

        # Add metadata
        execution["created_at"] = datetime.utcnow()
        execution["type"] = "agent_execution"

        result = await collection.insert_one(execution)
        execution["_id"] = result.inserted_id

        return serialize_doc(execution)
    except Exception as e:
        logger.error(f"Failed to log agent execution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log agent execution: {str(e)}"
        )


@router.get("/agent-executions")
async def get_agent_executions(
    agent_name: Optional[str] = Query(None),
    platform_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Get agent execution history with filters."""
    db = check_db()

    try:
        collection = db["agent_executions"]

        # Build filter
        query_filter = {}
        if agent_name:
            query_filter["agent_name"] = agent_name
        if platform_id:
            query_filter["platform_id"] = platform_id
        if status:
            query_filter["status"] = status
        if from_date or to_date:
            date_filter = {}
            if from_date:
                date_filter["$gte"] = datetime.fromisoformat(from_date)
            if to_date:
                date_filter["$lte"] = datetime.fromisoformat(to_date)
            query_filter["created_at"] = date_filter

        # Get total count
        total = await collection.count_documents(query_filter)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        # Query with pagination
        skip = (page - 1) * page_size
        cursor = collection.find(query_filter).sort("created_at", -1).skip(skip).limit(page_size)
        documents = await cursor.to_list(length=page_size)

        return {
            "items": [serialize_doc(doc) for doc in documents],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
    except Exception as e:
        logger.error(f"Failed to get agent executions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent executions: {str(e)}"
        )


@router.post("/conversations")
async def save_conversation(
    conversation: Dict[str, Any] = Body(...),
):
    """
    Save a conversation for agent memory.

    Expected fields:
    - session_id: Unique session identifier
    - agent_name: Name of the agent
    - messages: List of messages [{role, content, timestamp}]
    - metadata: Additional metadata (optional)
    """
    db = check_db()

    try:
        collection = db["conversations"]

        conversation["updated_at"] = datetime.utcnow()
        if "created_at" not in conversation:
            conversation["created_at"] = datetime.utcnow()

        # Upsert by session_id
        if "session_id" in conversation:
            result = await collection.find_one_and_update(
                {"session_id": conversation["session_id"]},
                {"$set": conversation},
                upsert=True,
                return_document=True,
            )
            return serialize_doc(result)
        else:
            result = await collection.insert_one(conversation)
            conversation["_id"] = result.inserted_id
            return serialize_doc(conversation)
    except Exception as e:
        logger.error(f"Failed to save conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save conversation: {str(e)}"
        )


@router.get("/conversations/{session_id}")
async def get_conversation(session_id: str):
    """Get a conversation by session ID."""
    db = check_db()

    try:
        collection = db["conversations"]
        conversation = await collection.find_one({"session_id": session_id})

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation '{session_id}' not found"
            )

        return serialize_doc(conversation)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation: {str(e)}"
        )


@router.post("/conversations/{session_id}/messages")
async def add_conversation_message(
    session_id: str,
    message: Dict[str, Any] = Body(...),
):
    """Add a message to an existing conversation."""
    db = check_db()

    try:
        collection = db["conversations"]

        # Add timestamp to message
        message["timestamp"] = datetime.utcnow()

        result = await collection.find_one_and_update(
            {"session_id": session_id},
            {
                "$push": {"messages": message},
                "$set": {"updated_at": datetime.utcnow()},
            },
            return_document=True,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation '{session_id}' not found"
            )

        return serialize_doc(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add message: {str(e)}"
        )


@router.post("/knowledge-base")
async def add_knowledge_entry(
    entry: Dict[str, Any] = Body(...),
):
    """
    Add an entry to the knowledge base.

    Expected fields:
    - content: The text content
    - source: Source of the content
    - metadata: Additional metadata (optional)
    - embedding_id: Weaviate vector ID (optional)
    - tags: List of tags (optional)
    """
    db = check_db()

    try:
        collection = db["knowledge_base"]

        entry["created_at"] = datetime.utcnow()
        entry["updated_at"] = datetime.utcnow()

        result = await collection.insert_one(entry)
        entry["_id"] = result.inserted_id

        return serialize_doc(entry)
    except Exception as e:
        logger.error(f"Failed to add knowledge entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add knowledge entry: {str(e)}"
        )


@router.get("/knowledge-base")
async def search_knowledge_base(
    query: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Search the knowledge base."""
    db = check_db()

    try:
        collection = db["knowledge_base"]

        # Build filter
        query_filter = {}
        if query:
            query_filter["$text"] = {"$search": query}
        if source:
            query_filter["source"] = source
        if tags:
            tag_list = [t.strip() for t in tags.split(",")]
            query_filter["tags"] = {"$in": tag_list}

        # Get total count
        total = await collection.count_documents(query_filter)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        # Query with pagination
        skip = (page - 1) * page_size
        cursor = collection.find(query_filter).sort("created_at", -1).skip(skip).limit(page_size)
        documents = await cursor.to_list(length=page_size)

        return {
            "items": [serialize_doc(doc) for doc in documents],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
    except Exception as e:
        logger.error(f"Failed to search knowledge base: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search knowledge base: {str(e)}"
        )


@router.post("/agent-configs")
async def save_agent_config(
    config: Dict[str, Any] = Body(...),
):
    """
    Save or update an agent configuration.

    Expected fields:
    - agent_name: Unique agent identifier
    - config: Configuration object
    - prompts: Prompt templates (optional)
    - tools: Tool configurations (optional)
    - version: Config version (optional)
    """
    db = check_db()

    try:
        collection = db["agent_configs"]

        config["updated_at"] = datetime.utcnow()

        # Upsert by agent_name
        if "agent_name" in config:
            if "created_at" not in config:
                existing = await collection.find_one({"agent_name": config["agent_name"]})
                if existing:
                    config["created_at"] = existing.get("created_at", datetime.utcnow())
                else:
                    config["created_at"] = datetime.utcnow()

            result = await collection.find_one_and_update(
                {"agent_name": config["agent_name"]},
                {"$set": config},
                upsert=True,
                return_document=True,
            )
            return serialize_doc(result)
        else:
            config["created_at"] = datetime.utcnow()
            result = await collection.insert_one(config)
            config["_id"] = result.inserted_id
            return serialize_doc(config)
    except Exception as e:
        logger.error(f"Failed to save agent config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save agent config: {str(e)}"
        )


@router.get("/agent-configs/{agent_name}")
async def get_agent_config(agent_name: str):
    """Get agent configuration by name."""
    db = check_db()

    try:
        collection = db["agent_configs"]
        config = await collection.find_one({"agent_name": agent_name})

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent config '{agent_name}' not found"
            )

        return serialize_doc(config)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent config: {str(e)}"
        )


@router.get("/agent-configs")
async def list_agent_configs():
    """List all agent configurations."""
    db = check_db()

    try:
        collection = db["agent_configs"]
        cursor = collection.find({}).sort("agent_name", 1)
        configs = await cursor.to_list(length=100)

        return {
            "configs": [serialize_doc(c) for c in configs],
            "total": len(configs),
        }
    except Exception as e:
        logger.error(f"Failed to list agent configs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list agent configs: {str(e)}"
        )


@router.post("/metrics")
async def log_metrics(
    metrics: Dict[str, Any] = Body(...),
):
    """
    Log metrics for analytics.

    Expected fields:
    - metric_type: Type of metric (token_usage, latency, error_rate, etc.)
    - agent_name: Agent name (optional)
    - platform_id: Platform ID (optional)
    - value: Metric value
    - tags: Additional tags (optional)
    """
    db = check_db()

    try:
        collection = db["metrics"]

        metrics["timestamp"] = datetime.utcnow()

        result = await collection.insert_one(metrics)
        metrics["_id"] = result.inserted_id

        return serialize_doc(metrics)
    except Exception as e:
        logger.error(f"Failed to log metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log metrics: {str(e)}"
        )


@router.get("/metrics/summary")
async def get_metrics_summary(
    metric_type: Optional[str] = Query(None),
    agent_name: Optional[str] = Query(None),
    platform_id: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=720),
):
    """Get aggregated metrics summary."""
    db = check_db()

    try:
        collection = db["metrics"]

        # Build match stage
        match_stage = {
            "timestamp": {"$gte": datetime.utcnow() - timedelta(hours=hours)}
        }
        if metric_type:
            match_stage["metric_type"] = metric_type
        if agent_name:
            match_stage["agent_name"] = agent_name
        if platform_id:
            match_stage["platform_id"] = platform_id

        pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": {
                        "metric_type": "$metric_type",
                        "agent_name": "$agent_name",
                    },
                    "count": {"$sum": 1},
                    "sum": {"$sum": "$value"},
                    "avg": {"$avg": "$value"},
                    "min": {"$min": "$value"},
                    "max": {"$max": "$value"},
                }
            },
            {"$sort": {"_id.metric_type": 1}},
        ]

        cursor = collection.aggregate(pipeline)
        results = await cursor.to_list(length=100)

        return {
            "summary": [
                {
                    "metric_type": r["_id"]["metric_type"],
                    "agent_name": r["_id"]["agent_name"],
                    "count": r["count"],
                    "sum": r["sum"],
                    "avg": r["avg"],
                    "min": r["min"],
                    "max": r["max"],
                }
                for r in results
            ],
            "period_hours": hours,
        }
    except Exception as e:
        logger.error(f"Failed to get metrics summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics summary: {str(e)}"
        )
