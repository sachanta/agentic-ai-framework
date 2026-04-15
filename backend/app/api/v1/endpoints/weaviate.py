"""
Weaviate management endpoints for Agentic AI Framework.

Provides vector database operations for:
- Collection management (schemas)
- Document CRUD with vectors
- Semantic search with embeddings
- RAG (Retrieval Augmented Generation) support
- Hybrid search (keyword + vector)
- Agent memory storage
"""
import json
import logging
import uuid as uuid_module
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status, Body, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.db.weaviate import get_weaviate_client, is_weaviate_available, get_weaviate_status
from app.services.upload_manager import (
    get_upload_manager,
    PDFUploadConfig,
    PDFUploadProgress,
    PDFUploadResult,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================

class WeaviateProperty(BaseModel):
    """Weaviate property schema."""
    name: str
    dataType: List[str]
    description: Optional[str] = None


class CreateCollectionRequest(BaseModel):
    """Request to create a collection."""
    name: str
    description: Optional[str] = None
    vectorizer: str = "none"
    properties: List[WeaviateProperty] = []


class CollectionInfo(BaseModel):
    """Collection information."""
    name: str
    description: Optional[str] = None
    vectorizer: Optional[str] = None
    properties: List[dict] = []
    object_count: int = 0


class DocumentRequest(BaseModel):
    """Request to add a document."""
    properties: dict
    vector: Optional[List[float]] = None


class DocumentUpdateRequest(BaseModel):
    """Request to update a document."""
    properties: dict
    vector: Optional[List[float]] = None


class SearchRequest(BaseModel):
    """Vector search request using text."""
    collection: str
    query: str
    limit: int = 10
    filters: Optional[Dict[str, Any]] = None
    return_properties: Optional[List[str]] = None


class VectorSearchRequest(BaseModel):
    """Vector search request using vector directly."""
    collection: str
    vector: List[float]
    limit: int = 10
    filters: Optional[Dict[str, Any]] = None
    return_properties: Optional[List[str]] = None


class EmbeddingSearchRequest(BaseModel):
    """Vector search request - will generate embeddings from text."""
    collection: str
    text: str
    limit: int = 10
    filters: Optional[Dict[str, Any]] = None
    return_properties: Optional[List[str]] = None


class HybridSearchRequest(BaseModel):
    """Hybrid search request (keyword + vector)."""
    collection: str
    query: str
    limit: int = 10
    alpha: float = Field(0.5, ge=0.0, le=1.0, description="Balance between vector (1.0) and keyword (0.0) search")
    filters: Optional[Dict[str, Any]] = None
    return_properties: Optional[List[str]] = None


class BulkImportRequest(BaseModel):
    """Bulk import request."""
    documents: List[dict]


class BulkImportWithVectorsRequest(BaseModel):
    """Bulk import with vectors request."""
    documents: List[Dict[str, Any]]  # Each doc has 'properties' and optional 'vector'


class PaginatedResponse(BaseModel):
    """Paginated response for frontend integration."""
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class RAGDocumentRequest(BaseModel):
    """Request to add a RAG document."""
    title: str
    content: str
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    chunk_id: Optional[str] = None
    vector: Optional[List[float]] = None


class RAGQueryRequest(BaseModel):
    """RAG query request."""
    query: str
    limit: int = 5
    source_filter: Optional[str] = None
    min_score: Optional[float] = None


class AgentMemoryRequest(BaseModel):
    """Request to store agent memory."""
    agent_id: str
    content: str
    memory_type: str = "conversation"  # conversation, context, tool_result
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    vector: Optional[List[float]] = None


class AgentMemoryQueryRequest(BaseModel):
    """Query agent memory."""
    agent_id: str
    query: str
    memory_type: Optional[str] = None
    session_id: Optional[str] = None
    limit: int = 10


# =============================================================================
# Helper Functions
# =============================================================================

def check_weaviate():
    """Check if Weaviate is available."""
    if not is_weaviate_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Weaviate is not available"
        )
    return get_weaviate_client()


def build_filter(filters: Optional[Dict[str, Any]]):
    """Build Weaviate filter from dict."""
    if not filters:
        return None

    try:
        from weaviate.classes.query import Filter

        # Simple filter building for common cases
        conditions = []
        for field, value in filters.items():
            if isinstance(value, dict):
                # Complex filter: {"field": {"operator": "value"}}
                for op, val in value.items():
                    if op == "eq" or op == "==":
                        conditions.append(Filter.by_property(field).equal(val))
                    elif op == "ne" or op == "!=":
                        conditions.append(Filter.by_property(field).not_equal(val))
                    elif op == "gt" or op == ">":
                        conditions.append(Filter.by_property(field).greater_than(val))
                    elif op == "gte" or op == ">=":
                        conditions.append(Filter.by_property(field).greater_or_equal(val))
                    elif op == "lt" or op == "<":
                        conditions.append(Filter.by_property(field).less_than(val))
                    elif op == "lte" or op == "<=":
                        conditions.append(Filter.by_property(field).less_or_equal(val))
                    elif op == "like":
                        conditions.append(Filter.by_property(field).like(val))
                    elif op == "contains":
                        conditions.append(Filter.by_property(field).contains_any([val]))
            else:
                # Simple equality
                conditions.append(Filter.by_property(field).equal(value))

        if not conditions:
            return None
        elif len(conditions) == 1:
            return conditions[0]
        else:
            # Combine with AND
            result = conditions[0]
            for cond in conditions[1:]:
                result = result & cond
            return result
    except Exception as e:
        logger.warning(f"Failed to build filter: {e}")
        return None


# =============================================================================
# Status & Health Endpoints
# =============================================================================

@router.get("/status")
async def weaviate_status():
    """Get Weaviate connection status and health."""
    status_info = await get_weaviate_status()
    return status_info


@router.get("/stats")
async def weaviate_stats():
    """Get Weaviate statistics."""
    client = check_weaviate()

    try:
        collections = client.collections.list_all()

        stats = {
            "collection_count": len(collections),
            "collections": [],
            "total_objects": 0,
        }

        for name, config in collections.items():
            collection = client.collections.get(name)
            count = collection.aggregate.over_all(total_count=True).total_count or 0
            stats["total_objects"] += count
            stats["collections"].append({
                "name": name,
                "object_count": count,
            })

        return stats
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


# =============================================================================
# Collection Management Endpoints
# =============================================================================

@router.get("/collections", response_model=List[CollectionInfo])
async def list_collections():
    """List all Weaviate collections."""
    client = check_weaviate()

    try:
        collections = client.collections.list_all()
        result = []

        for name, config in collections.items():
            # Get object count
            collection = client.collections.get(name)
            count = collection.aggregate.over_all(total_count=True).total_count or 0

            # Extract properties
            props = []
            if hasattr(config, 'properties') and config.properties:
                for prop in config.properties:
                    # Clean up data type name
                    dt = str(prop.data_type) if hasattr(prop, 'data_type') else "text"
                    dt = dt.replace("DataType.", "").lower()
                    props.append({
                        "name": prop.name,
                        "dataType": [dt],
                        "description": getattr(prop, 'description', None),
                    })

            # Clean up vectorizer name
            vectorizer = str(getattr(config, 'vectorizer', 'none'))
            vectorizer = vectorizer.replace("Vectorizers.", "").lower()

            result.append(CollectionInfo(
                name=name,
                description=getattr(config, 'description', None),
                vectorizer=vectorizer,
                properties=props,
                object_count=count,
            ))

        return result
    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list collections: {str(e)}"
        )


@router.get("/collections/{name}", response_model=CollectionInfo)
async def get_collection(name: str):
    """Get collection details."""
    client = check_weaviate()

    try:
        if not client.collections.exists(name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{name}' not found"
            )

        collection = client.collections.get(name)
        config = collection.config.get()
        count = collection.aggregate.over_all(total_count=True).total_count or 0

        props = []
        if hasattr(config, 'properties') and config.properties:
            for prop in config.properties:
                dt = str(prop.data_type) if hasattr(prop, 'data_type') else "text"
                dt = dt.replace("DataType.", "").lower()
                props.append({
                    "name": prop.name,
                    "dataType": [dt],
                    "description": getattr(prop, 'description', None),
                })

        vectorizer = str(getattr(config, 'vectorizer', 'none'))
        vectorizer = vectorizer.replace("Vectorizers.", "").lower()

        return CollectionInfo(
            name=name,
            description=getattr(config, 'description', None),
            vectorizer=vectorizer,
            properties=props,
            object_count=count,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get collection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collection: {str(e)}"
        )


@router.post("/collections", response_model=CollectionInfo, status_code=status.HTTP_201_CREATED)
async def create_collection(request: CreateCollectionRequest):
    """Create a new collection."""
    client = check_weaviate()

    try:
        from weaviate.classes.config import Property, DataType, Configure

        # Check if collection already exists
        if client.collections.exists(request.name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Collection '{request.name}' already exists"
            )

        # Map string data types to Weaviate DataType
        type_map = {
            "text": DataType.TEXT,
            "string": DataType.TEXT,
            "int": DataType.INT,
            "integer": DataType.INT,
            "number": DataType.NUMBER,
            "float": DataType.NUMBER,
            "boolean": DataType.BOOL,
            "bool": DataType.BOOL,
            "date": DataType.DATE,
            "text[]": DataType.TEXT_ARRAY,
            "string[]": DataType.TEXT_ARRAY,
            "int[]": DataType.INT_ARRAY,
            "number[]": DataType.NUMBER_ARRAY,
            "boolean[]": DataType.BOOL_ARRAY,
            "object": DataType.OBJECT,
            "uuid": DataType.UUID,
        }

        # Build properties
        properties = []
        for prop in request.properties:
            data_type = type_map.get(prop.dataType[0].lower(), DataType.TEXT)
            properties.append(Property(
                name=prop.name,
                data_type=data_type,
                description=prop.description,
            ))

        # Configure vectorizer
        vectorizer_config = None
        if request.vectorizer == "text2vec-openai":
            vectorizer_config = Configure.Vectorizer.text2vec_openai()
        elif request.vectorizer == "text2vec-cohere":
            vectorizer_config = Configure.Vectorizer.text2vec_cohere()
        elif request.vectorizer == "text2vec-huggingface":
            vectorizer_config = Configure.Vectorizer.text2vec_huggingface()
        elif request.vectorizer == "text2vec-transformers":
            vectorizer_config = Configure.Vectorizer.text2vec_transformers()
        else:
            vectorizer_config = Configure.Vectorizer.none()

        # Create collection
        client.collections.create(
            name=request.name,
            description=request.description,
            vectorizer_config=vectorizer_config,
            properties=properties,
        )

        logger.info(f"Created Weaviate collection: {request.name}")

        return CollectionInfo(
            name=request.name,
            description=request.description,
            vectorizer=request.vectorizer,
            properties=[{"name": p.name, "dataType": p.dataType} for p in request.properties],
            object_count=0,
        )
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
    client = check_weaviate()

    try:
        if not client.collections.exists(name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{name}' not found"
            )

        client.collections.delete(name)
        logger.info(f"Deleted Weaviate collection: {name}")

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
# Document CRUD Endpoints
# =============================================================================

@router.get("/collections/{name}/documents", response_model=PaginatedResponse)
async def list_documents(
    name: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_vector: bool = Query(False, description="Include vector in response"),
):
    """List documents in a collection with pagination."""
    client = check_weaviate()

    try:
        if not client.collections.exists(name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{name}' not found"
            )

        collection = client.collections.get(name)

        # Get total count
        total = collection.aggregate.over_all(total_count=True).total_count or 0
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        # Fetch documents with pagination
        items = []
        offset = (page - 1) * page_size

        for item in collection.iterator(include_vector=include_vector):
            if offset > 0:
                offset -= 1
                continue
            if len(items) >= page_size:
                break

            doc = {
                "id": str(item.uuid),
                "properties": item.properties,
            }
            if include_vector and item.vector:
                doc["vector"] = item.vector
            items.append(doc)

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
async def get_document(
    name: str,
    doc_id: str,
    include_vector: bool = Query(False, description="Include vector in response"),
):
    """Get a single document by ID."""
    client = check_weaviate()

    try:
        if not client.collections.exists(name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{name}' not found"
            )

        collection = client.collections.get(name)

        try:
            obj = collection.query.fetch_object_by_id(
                uuid=doc_id,
                include_vector=include_vector,
            )
        except Exception:
            obj = None

        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{doc_id}' not found"
            )

        result = {
            "id": str(obj.uuid),
            "properties": obj.properties,
        }
        if include_vector and obj.vector:
            result["vector"] = obj.vector

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}"
        )


@router.post("/collections/{name}/documents", status_code=status.HTTP_201_CREATED)
async def add_document(name: str, request: DocumentRequest):
    """Add a document to a collection."""
    client = check_weaviate()

    try:
        if not client.collections.exists(name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{name}' not found"
            )

        collection = client.collections.get(name)

        if request.vector:
            uuid = collection.data.insert(
                properties=request.properties,
                vector=request.vector,
            )
        else:
            uuid = collection.data.insert(properties=request.properties)

        return {"id": str(uuid), "properties": request.properties}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add document: {str(e)}"
        )


@router.put("/collections/{name}/documents/{doc_id}")
async def update_document(name: str, doc_id: str, request: DocumentUpdateRequest):
    """Update a document in a collection."""
    client = check_weaviate()

    try:
        if not client.collections.exists(name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{name}' not found"
            )

        collection = client.collections.get(name)

        # Check if document exists
        try:
            existing = collection.query.fetch_object_by_id(uuid=doc_id)
            if existing is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document '{doc_id}' not found"
                )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{doc_id}' not found"
            )

        # Update the document
        if request.vector:
            collection.data.update(
                uuid=doc_id,
                properties=request.properties,
                vector=request.vector,
            )
        else:
            collection.data.update(
                uuid=doc_id,
                properties=request.properties,
            )

        return {"id": doc_id, "properties": request.properties, "updated": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document: {str(e)}"
        )


@router.delete("/collections/{name}/documents/{doc_id}")
async def delete_document(name: str, doc_id: str):
    """Delete a document from a collection."""
    client = check_weaviate()

    try:
        if not client.collections.exists(name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{name}' not found"
            )

        collection = client.collections.get(name)
        collection.data.delete_by_id(doc_id)

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
# Search Endpoints
# =============================================================================

@router.post("/search/text")
async def text_search(request: SearchRequest):
    """Perform near text search (requires vectorizer on collection)."""
    client = check_weaviate()

    try:
        if not client.collections.exists(request.collection):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{request.collection}' not found"
            )

        collection = client.collections.get(request.collection)

        # Build query
        query_filter = build_filter(request.filters)

        response = collection.query.near_text(
            query=request.query,
            limit=request.limit,
            filters=query_filter,
            return_properties=request.return_properties,
        )

        results = []
        for obj in response.objects:
            results.append({
                "id": str(obj.uuid),
                "properties": obj.properties,
                "score": getattr(obj.metadata, 'certainty', None) or getattr(obj.metadata, 'distance', None),
            })

        return {
            "results": results,
            "query": request.query,
            "collection": request.collection,
            "count": len(results),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform text search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform text search: {str(e)}"
        )


@router.post("/search/vector")
async def vector_search(request: VectorSearchRequest):
    """Perform vector search using a provided vector."""
    client = check_weaviate()

    try:
        if not client.collections.exists(request.collection):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{request.collection}' not found"
            )

        collection = client.collections.get(request.collection)

        # Build query
        query_filter = build_filter(request.filters)

        response = collection.query.near_vector(
            near_vector=request.vector,
            limit=request.limit,
            filters=query_filter,
            return_properties=request.return_properties,
        )

        results = []
        for obj in response.objects:
            results.append({
                "id": str(obj.uuid),
                "properties": obj.properties,
                "score": getattr(obj.metadata, 'certainty', None) or getattr(obj.metadata, 'distance', None),
            })

        return {
            "results": results,
            "collection": request.collection,
            "count": len(results),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform vector search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform vector search: {str(e)}"
        )


@router.post("/search/embedding")
async def embedding_search(request: EmbeddingSearchRequest):
    """
    Perform vector search by generating embeddings from text.
    Uses the configured embeddings provider (Ollama by default).
    """
    client = check_weaviate()

    try:
        if not client.collections.exists(request.collection):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{request.collection}' not found"
            )

        # Generate embedding from text
        try:
            from app.common.providers.embeddings import get_embeddings_provider
            embeddings_provider = get_embeddings_provider()
            vector = await embeddings_provider.embed_text(request.text)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Embeddings provider not available: {str(e)}"
            )

        collection = client.collections.get(request.collection)

        # Build query
        query_filter = build_filter(request.filters)

        response = collection.query.near_vector(
            near_vector=vector,
            limit=request.limit,
            filters=query_filter,
            return_properties=request.return_properties,
        )

        results = []
        for obj in response.objects:
            results.append({
                "id": str(obj.uuid),
                "properties": obj.properties,
                "score": getattr(obj.metadata, 'certainty', None) or getattr(obj.metadata, 'distance', None),
            })

        return {
            "results": results,
            "text": request.text,
            "collection": request.collection,
            "count": len(results),
            "embedding_dimension": len(vector),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform embedding search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform embedding search: {str(e)}"
        )


@router.post("/search/hybrid")
async def hybrid_search(request: HybridSearchRequest):
    """
    Perform hybrid search combining keyword and vector search.
    Alpha controls the balance: 0.0 = keyword only, 1.0 = vector only.
    """
    client = check_weaviate()

    try:
        if not client.collections.exists(request.collection):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{request.collection}' not found"
            )

        collection = client.collections.get(request.collection)

        # Build query
        query_filter = build_filter(request.filters)

        response = collection.query.hybrid(
            query=request.query,
            alpha=request.alpha,
            limit=request.limit,
            filters=query_filter,
            return_properties=request.return_properties,
        )

        results = []
        for obj in response.objects:
            results.append({
                "id": str(obj.uuid),
                "properties": obj.properties,
                "score": getattr(obj.metadata, 'score', None),
            })

        return {
            "results": results,
            "query": request.query,
            "collection": request.collection,
            "alpha": request.alpha,
            "count": len(results),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform hybrid search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform hybrid search: {str(e)}"
        )


# Legacy endpoint for backward compatibility
@router.post("/search")
async def search(request: SearchRequest):
    """
    Perform vector search (legacy endpoint).
    Use /search/text, /search/vector, or /search/hybrid for more options.
    """
    return await text_search(request)


# =============================================================================
# Bulk Operations
# =============================================================================

@router.post("/collections/{name}/import")
async def bulk_import(name: str, request: BulkImportRequest):
    """Bulk import documents (properties only, no vectors)."""
    client = check_weaviate()

    try:
        if not client.collections.exists(name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{name}' not found"
            )

        collection = client.collections.get(name)

        imported = 0
        failed = 0
        errors = []

        with collection.batch.dynamic() as batch:
            for i, doc in enumerate(request.documents):
                try:
                    batch.add_object(properties=doc)
                    imported += 1
                except Exception as e:
                    logger.warning(f"Failed to import document {i}: {e}")
                    errors.append({"index": i, "error": str(e)})
                    failed += 1

        return {
            "imported": imported,
            "failed": failed,
            "total": len(request.documents),
            "errors": errors[:10] if errors else [],  # Return first 10 errors
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to bulk import: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk import: {str(e)}"
        )


@router.post("/collections/{name}/import-with-vectors")
async def bulk_import_with_vectors(name: str, request: BulkImportWithVectorsRequest):
    """
    Bulk import documents with vectors.
    Each document should have 'properties' and optionally 'vector'.
    """
    client = check_weaviate()

    try:
        if not client.collections.exists(name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{name}' not found"
            )

        collection = client.collections.get(name)

        imported = 0
        failed = 0
        errors = []

        with collection.batch.dynamic() as batch:
            for i, doc in enumerate(request.documents):
                try:
                    properties = doc.get("properties", {})
                    vector = doc.get("vector")

                    if vector:
                        batch.add_object(properties=properties, vector=vector)
                    else:
                        batch.add_object(properties=properties)
                    imported += 1
                except Exception as e:
                    logger.warning(f"Failed to import document {i}: {e}")
                    errors.append({"index": i, "error": str(e)})
                    failed += 1

        return {
            "imported": imported,
            "failed": failed,
            "total": len(request.documents),
            "errors": errors[:10] if errors else [],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to bulk import with vectors: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk import with vectors: {str(e)}"
        )


@router.post("/collections/{name}/generate-embeddings")
async def generate_embeddings_for_collection(
    name: str,
    text_field: str = Query(..., description="Field containing text to embed"),
    batch_size: int = Query(10, ge=1, le=100, description="Batch size for embedding generation"),
):
    """
    Generate embeddings for all documents in a collection.
    Uses the configured embeddings provider.
    """
    client = check_weaviate()

    try:
        if not client.collections.exists(name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{name}' not found"
            )

        # Get embeddings provider
        try:
            from app.common.providers.embeddings import get_embeddings_provider
            embeddings_provider = get_embeddings_provider()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Embeddings provider not available: {str(e)}"
            )

        collection = client.collections.get(name)

        updated = 0
        failed = 0
        batch_texts = []
        batch_ids = []

        for item in collection.iterator(include_vector=False):
            text = item.properties.get(text_field, "")
            if text:
                batch_texts.append(text)
                batch_ids.append(str(item.uuid))

                if len(batch_texts) >= batch_size:
                    try:
                        vectors = await embeddings_provider.embed_texts(batch_texts)
                        for uuid, vector in zip(batch_ids, vectors):
                            collection.data.update(uuid=uuid, vector=vector)
                            updated += 1
                    except Exception as e:
                        logger.warning(f"Failed to embed batch: {e}")
                        failed += len(batch_texts)

                    batch_texts = []
                    batch_ids = []

        # Process remaining batch
        if batch_texts:
            try:
                vectors = await embeddings_provider.embed_texts(batch_texts)
                for uuid, vector in zip(batch_ids, vectors):
                    collection.data.update(uuid=uuid, vector=vector)
                    updated += 1
            except Exception as e:
                logger.warning(f"Failed to embed final batch: {e}")
                failed += len(batch_texts)

        return {
            "updated": updated,
            "failed": failed,
            "text_field": text_field,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate embeddings: {str(e)}"
        )


# =============================================================================
# RAG (Retrieval Augmented Generation) Endpoints
# =============================================================================

RAG_COLLECTION = "RAGDocuments"


async def ensure_rag_collection():
    """Ensure RAG collection exists with properly indexed properties."""
    client = check_weaviate()

    if not client.collections.exists(RAG_COLLECTION):
        from weaviate.classes.config import Property, DataType, Configure

        client.collections.create(
            name=RAG_COLLECTION,
            description="Documents for RAG (Retrieval Augmented Generation)",
            vectorizer_config=Configure.Vectorizer.none(),
            properties=[
                Property(
                    name="title",
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                ),
                Property(
                    name="content",
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                ),
                Property(
                    name="source",
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                ),
                Property(
                    name="chunk_id",
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                ),
                Property(
                    name="metadata_json",
                    data_type=DataType.TEXT,
                    index_filterable=False,
                    index_searchable=False,
                ),
                Property(
                    name="created_at",
                    data_type=DataType.DATE,
                    index_filterable=True,
                    index_searchable=False,
                ),
            ],
        )
        logger.info(f"Created RAG collection: {RAG_COLLECTION}")


@router.post("/rag/documents", status_code=status.HTTP_201_CREATED)
async def add_rag_document(request: RAGDocumentRequest):
    """Add a document to the RAG knowledge base."""
    import json
    client = check_weaviate()

    try:
        await ensure_rag_collection()
        collection = client.collections.get(RAG_COLLECTION)

        properties = {
            "title": request.title,
            "content": request.content,
            "source": request.source or "unknown",
            "chunk_id": request.chunk_id or "",
            "metadata_json": json.dumps(request.metadata or {}),  # Store as JSON string
            "created_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z",  # RFC3339 format
        }

        # Generate embedding if not provided
        vector = request.vector
        if not vector:
            try:
                from app.common.providers.embeddings import get_embeddings_provider
                embeddings = get_embeddings_provider()
                vector = await embeddings.embed_text(request.content)
            except Exception as e:
                logger.warning(f"Failed to generate embedding: {e}")

        if vector:
            uuid = collection.data.insert(properties=properties, vector=vector)
        else:
            uuid = collection.data.insert(properties=properties)

        return {
            "id": str(uuid),
            "title": request.title,
            "source": request.source,
            "has_vector": vector is not None,
        }
    except Exception as e:
        logger.error(f"Failed to add RAG document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add RAG document: {str(e)}"
        )


@router.post("/rag/query")
async def query_rag(request: RAGQueryRequest):
    """Query the RAG knowledge base."""
    client = check_weaviate()

    try:
        await ensure_rag_collection()
        collection = client.collections.get(RAG_COLLECTION)

        # Generate query embedding
        try:
            from app.common.providers.embeddings import get_embeddings_provider
            embeddings = get_embeddings_provider()
            query_vector = await embeddings.embed_text(request.query)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Embeddings provider not available: {str(e)}"
            )

        # Build filter
        query_filter = None
        if request.source_filter:
            from weaviate.classes.query import Filter
            query_filter = Filter.by_property("source").equal(request.source_filter)

        response = collection.query.near_vector(
            near_vector=query_vector,
            limit=request.limit,
            filters=query_filter,
        )

        results = []
        for obj in response.objects:
            score = getattr(obj.metadata, 'certainty', None) or getattr(obj.metadata, 'distance', None)

            # Filter by min score if specified
            if request.min_score and score and score < request.min_score:
                continue

            # Parse metadata from JSON string
            metadata = {}
            metadata_json = obj.properties.get("metadata_json", "{}")
            try:
                import json
                metadata = json.loads(metadata_json) if metadata_json else {}
            except:
                pass

            results.append({
                "id": str(obj.uuid),
                "title": obj.properties.get("title"),
                "content": obj.properties.get("content"),
                "source": obj.properties.get("source"),
                "chunk_id": obj.properties.get("chunk_id"),
                "score": score,
                "metadata": metadata,
            })

        return {
            "results": results,
            "query": request.query,
            "count": len(results),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to query RAG: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query RAG: {str(e)}"
        )


@router.get("/rag/documents", response_model=PaginatedResponse)
async def list_rag_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source: Optional[str] = Query(None, description="Filter by source"),
):
    """List RAG documents with pagination."""
    client = check_weaviate()

    try:
        await ensure_rag_collection()
        collection = client.collections.get(RAG_COLLECTION)

        # Get total count
        total = collection.aggregate.over_all(total_count=True).total_count or 0
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        # Fetch documents
        items = []
        offset = (page - 1) * page_size

        for item in collection.iterator(include_vector=False):
            # Apply source filter if specified
            if source and item.properties.get("source") != source:
                continue

            if offset > 0:
                offset -= 1
                continue
            if len(items) >= page_size:
                break

            items.append({
                "id": str(item.uuid),
                "title": item.properties.get("title"),
                "content": item.properties.get("content", "")[:200] + "...",
                "source": item.properties.get("source"),
                "created_at": item.properties.get("created_at"),
            })

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )
    except Exception as e:
        logger.error(f"Failed to list RAG documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list RAG documents: {str(e)}"
        )


@router.delete("/rag/documents/{doc_id}")
async def delete_rag_document(doc_id: str):
    """Delete a RAG document."""
    client = check_weaviate()

    try:
        await ensure_rag_collection()
        collection = client.collections.get(RAG_COLLECTION)
        collection.data.delete_by_id(doc_id)

        return {"message": f"RAG document '{doc_id}' deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete RAG document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete RAG document: {str(e)}"
        )


# =============================================================================
# Agent Memory Endpoints
# =============================================================================

MEMORY_COLLECTION = "AgentMemory"


async def ensure_memory_collection():
    """Ensure agent memory collection exists with properly indexed properties."""
    client = check_weaviate()

    if not client.collections.exists(MEMORY_COLLECTION):
        from weaviate.classes.config import Property, DataType, Configure

        client.collections.create(
            name=MEMORY_COLLECTION,
            description="Agent conversation and context memory",
            vectorizer_config=Configure.Vectorizer.none(),
            properties=[
                Property(
                    name="agent_id",
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                ),
                Property(
                    name="session_id",
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                ),
                Property(
                    name="content",
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                ),
                Property(
                    name="memory_type",
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                ),
                Property(
                    name="metadata_json",
                    data_type=DataType.TEXT,
                    index_filterable=False,
                    index_searchable=False,
                ),
                Property(
                    name="created_at",
                    data_type=DataType.DATE,
                    index_filterable=True,
                    index_searchable=False,
                ),
            ],
        )
        logger.info(f"Created memory collection: {MEMORY_COLLECTION}")


@router.post("/memory", status_code=status.HTTP_201_CREATED)
async def store_agent_memory(request: AgentMemoryRequest):
    """Store agent memory entry."""
    import json
    client = check_weaviate()

    try:
        await ensure_memory_collection()
        collection = client.collections.get(MEMORY_COLLECTION)

        properties = {
            "agent_id": request.agent_id,
            "session_id": request.session_id or "",
            "content": request.content,
            "memory_type": request.memory_type,
            "metadata_json": json.dumps(request.metadata or {}),  # Store as JSON string
            "created_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z",  # RFC3339 format
        }

        # Generate embedding if not provided
        vector = request.vector
        if not vector:
            try:
                from app.common.providers.embeddings import get_embeddings_provider
                embeddings = get_embeddings_provider()
                vector = await embeddings.embed_text(request.content)
            except Exception as e:
                logger.warning(f"Failed to generate memory embedding: {e}")

        if vector:
            uuid = collection.data.insert(properties=properties, vector=vector)
        else:
            uuid = collection.data.insert(properties=properties)

        return {
            "id": str(uuid),
            "agent_id": request.agent_id,
            "memory_type": request.memory_type,
            "has_vector": vector is not None,
        }
    except Exception as e:
        logger.error(f"Failed to store agent memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store agent memory: {str(e)}"
        )


@router.post("/memory/query")
async def query_agent_memory(request: AgentMemoryQueryRequest):
    """Query agent memory by semantic similarity."""
    client = check_weaviate()

    try:
        await ensure_memory_collection()
        collection = client.collections.get(MEMORY_COLLECTION)

        # Generate query embedding
        try:
            from app.common.providers.embeddings import get_embeddings_provider
            embeddings = get_embeddings_provider()
            query_vector = await embeddings.embed_text(request.query)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Embeddings provider not available: {str(e)}"
            )

        # Build filters
        from weaviate.classes.query import Filter
        filters = [Filter.by_property("agent_id").equal(request.agent_id)]

        if request.memory_type:
            filters.append(Filter.by_property("memory_type").equal(request.memory_type))
        if request.session_id:
            filters.append(Filter.by_property("session_id").equal(request.session_id))

        # Combine filters
        combined_filter = filters[0]
        for f in filters[1:]:
            combined_filter = combined_filter & f

        response = collection.query.near_vector(
            near_vector=query_vector,
            limit=request.limit,
            filters=combined_filter,
        )

        results = []
        for obj in response.objects:
            # Parse metadata from JSON string
            metadata = {}
            metadata_json = obj.properties.get("metadata_json", "{}")
            try:
                import json
                metadata = json.loads(metadata_json) if metadata_json else {}
            except:
                pass

            results.append({
                "id": str(obj.uuid),
                "content": obj.properties.get("content"),
                "memory_type": obj.properties.get("memory_type"),
                "session_id": obj.properties.get("session_id"),
                "created_at": obj.properties.get("created_at"),
                "score": getattr(obj.metadata, 'certainty', None) or getattr(obj.metadata, 'distance', None),
                "metadata": metadata,
            })

        return {
            "results": results,
            "agent_id": request.agent_id,
            "query": request.query,
            "count": len(results),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to query agent memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query agent memory: {str(e)}"
        )


@router.get("/memory/{agent_id}")
async def get_agent_memories(
    agent_id: str,
    session_id: Optional[str] = Query(None),
    memory_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Get all memories for an agent."""
    client = check_weaviate()

    try:
        await ensure_memory_collection()
        collection = client.collections.get(MEMORY_COLLECTION)

        items = []
        offset = (page - 1) * page_size
        total = 0

        for item in collection.iterator(include_vector=False):
            # Apply filters
            if item.properties.get("agent_id") != agent_id:
                continue
            if session_id and item.properties.get("session_id") != session_id:
                continue
            if memory_type and item.properties.get("memory_type") != memory_type:
                continue

            total += 1

            if offset > 0:
                offset -= 1
                continue
            if len(items) >= page_size:
                continue  # Keep counting total

            # Parse metadata from JSON string
            metadata = {}
            metadata_json = item.properties.get("metadata_json", "{}")
            try:
                import json
                metadata = json.loads(metadata_json) if metadata_json else {}
            except:
                pass

            items.append({
                "id": str(item.uuid),
                "content": item.properties.get("content"),
                "memory_type": item.properties.get("memory_type"),
                "session_id": item.properties.get("session_id"),
                "created_at": item.properties.get("created_at"),
                "metadata": metadata,
            })

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return {
            "items": items,
            "agent_id": agent_id,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }
    except Exception as e:
        logger.error(f"Failed to get agent memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent memories: {str(e)}"
        )


@router.delete("/memory/{agent_id}")
async def clear_agent_memory(
    agent_id: str,
    session_id: Optional[str] = Query(None, description="Clear only specific session"),
):
    """Clear all memories for an agent (or specific session)."""
    client = check_weaviate()

    try:
        await ensure_memory_collection()
        collection = client.collections.get(MEMORY_COLLECTION)

        deleted = 0
        ids_to_delete = []

        for item in collection.iterator(include_vector=False):
            if item.properties.get("agent_id") != agent_id:
                continue
            if session_id and item.properties.get("session_id") != session_id:
                continue
            ids_to_delete.append(str(item.uuid))

        for doc_id in ids_to_delete:
            try:
                collection.data.delete_by_id(doc_id)
                deleted += 1
            except Exception as e:
                logger.warning(f"Failed to delete memory {doc_id}: {e}")

        return {
            "message": f"Cleared {deleted} memories for agent '{agent_id}'",
            "deleted": deleted,
            "agent_id": agent_id,
            "session_id": session_id,
        }
    except Exception as e:
        logger.error(f"Failed to clear agent memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear agent memory: {str(e)}"
        )


# =============================================================================
# PDF Upload Endpoints
# =============================================================================

MAX_PDF_SIZE_MB = 50
MAX_PDF_SIZE_BYTES = MAX_PDF_SIZE_MB * 1024 * 1024


@router.post("/rag/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(..., description="PDF file to upload"),
    title: Optional[str] = Form(None, description="Document title (defaults to filename)"),
    source: Optional[str] = Form("pdf_upload", description="Source identifier"),
    chunk_size: int = Form(1000, ge=200, le=2000, description="Chunk size in characters"),
    chunk_overlap: int = Form(200, ge=0, le=500, description="Overlap between chunks"),
    metadata: Optional[str] = Form(None, description="JSON metadata string"),
):
    """
    Upload and process a PDF for RAG.

    The PDF is extracted, chunked, embedded, and stored in the RAG collection.
    Returns an upload_id that can be used to track progress via SSE.

    Args:
        file: PDF file to upload
        title: Document title (defaults to filename without extension)
        source: Source identifier for the document
        chunk_size: Target chunk size in characters (200-2000)
        chunk_overlap: Overlap between consecutive chunks (0-500)
        metadata: Optional JSON string with additional metadata
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        logger.warning(f"Rejected non-PDF file: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported. Please upload a file with .pdf extension."
        )

    # Read and validate file size
    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)

    logger.info(f"Received PDF upload: {file.filename} ({file_size_mb:.2f}MB)")

    if len(content) > MAX_PDF_SIZE_BYTES:
        logger.warning(f"Rejected large PDF: {file.filename} ({file_size_mb:.2f}MB)")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large ({file_size_mb:.1f}MB). Maximum size is {MAX_PDF_SIZE_MB}MB."
        )

    # Parse metadata if provided
    parsed_metadata = {}
    if metadata:
        try:
            parsed_metadata = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid metadata JSON format"
            )

    # Generate upload ID
    upload_id = str(uuid_module.uuid4())

    # Create config
    config = PDFUploadConfig(
        title=title or file.filename.rsplit('.', 1)[0],
        source=source or "pdf_upload",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        metadata=parsed_metadata,
    )

    # Start background processing
    upload_manager = get_upload_manager()
    await upload_manager.start_upload(
        upload_id=upload_id,
        filename=file.filename,
        content=content,
        config=config,
    )

    logger.info(f"Started PDF processing: upload_id={upload_id}, file={file.filename}")

    return {
        "upload_id": upload_id,
        "filename": file.filename,
        "size_mb": round(file_size_mb, 2),
        "status": "processing_started",
        "message": "PDF upload started. Use the progress endpoint to track status.",
    }


@router.get("/rag/upload-pdf/{upload_id}/progress")
async def get_upload_progress(upload_id: str):
    """
    Server-Sent Events endpoint for PDF upload progress.

    Streams progress updates as the PDF is processed. The connection
    remains open until processing completes or fails.

    Events have the format:
    - event: progress
    - data: JSON with stage, progress (0-100), message, and optional error

    Stages: validating, extracting, chunking, embedding, storing, completed, failed
    """
    upload_manager = get_upload_manager()

    # Check if upload exists
    upload_info = upload_manager.get_upload_info(upload_id)
    if not upload_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload '{upload_id}' not found"
        )

    async def event_generator():
        """Generate SSE events for progress updates."""
        try:
            async for progress in upload_manager.get_progress(upload_id):
                # Skip heartbeat events in SSE (they're just for keeping connection alive)
                if progress.stage == "heartbeat":
                    yield {
                        "event": "heartbeat",
                        "data": json.dumps({"status": "processing"}),
                    }
                else:
                    yield {
                        "event": "progress",
                        "data": progress.to_json(),
                    }

                # Stop if completed or failed
                if progress.stage in ["completed", "failed"]:
                    break

        except Exception as e:
            logger.error(f"Error streaming progress for {upload_id}: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}),
            }

    return EventSourceResponse(event_generator())


@router.get("/rag/upload-pdf/{upload_id}/status")
async def get_upload_status(upload_id: str):
    """
    Get the current status of a PDF upload.

    This is a polling alternative to the SSE progress endpoint.
    """
    upload_manager = get_upload_manager()

    upload_info = upload_manager.get_upload_info(upload_id)
    if not upload_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload '{upload_id}' not found"
        )

    result = upload_manager.get_upload_result(upload_id)

    return {
        "upload_id": upload_id,
        "filename": upload_info.filename,
        "state": upload_info.state.value,
        "started_at": upload_info.started_at.isoformat() if upload_info.started_at else None,
        "completed_at": upload_info.completed_at.isoformat() if upload_info.completed_at else None,
        "result": result.to_dict() if result else None,
    }


@router.delete("/rag/upload-pdf/{upload_id}")
async def cancel_upload(upload_id: str):
    """
    Cancel an in-progress PDF upload.

    Can only cancel uploads that are still processing.
    """
    upload_manager = get_upload_manager()

    upload_info = upload_manager.get_upload_info(upload_id)
    if not upload_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload '{upload_id}' not found"
        )

    cancelled = await upload_manager.cancel_upload(upload_id)

    if cancelled:
        logger.info(f"Cancelled upload: {upload_id}")
        return {
            "upload_id": upload_id,
            "cancelled": True,
            "message": "Upload cancelled successfully",
        }
    else:
        return {
            "upload_id": upload_id,
            "cancelled": False,
            "message": "Upload cannot be cancelled (already completed or failed)",
        }
