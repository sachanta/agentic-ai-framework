"""
Upload Manager Service for Agentic AI Framework.

Manages PDF upload processing, progress tracking, and cancellation.
"""
import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional
from enum import Enum

from app.services.pdf_processor import (
    PDFProcessor,
    PDFProcessingStage,
    TextChunk,
    get_pdf_processor,
)

logger = logging.getLogger(__name__)


@dataclass
class PDFUploadConfig:
    """Configuration for PDF upload."""
    title: str
    source: str = "pdf_upload"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    collection: str = "RAGDocuments"
    metadata: Dict[str, Any] = field(default_factory=dict)
    generate_embeddings: bool = True


@dataclass
class PDFUploadProgress:
    """Progress update for PDF processing."""
    upload_id: str
    stage: str
    progress: float  # 0-100
    message: str
    current_chunk: Optional[int] = None
    total_chunks: Optional[int] = None
    chunks_stored: Optional[int] = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class PDFUploadResult:
    """Final result of PDF upload."""
    upload_id: str
    success: bool
    filename: str
    title: str
    chunks_created: int = 0
    chunks_stored: int = 0
    chunks_failed: int = 0
    total_pages: int = 0
    processing_time_seconds: float = 0.0
    error: Optional[str] = None
    chunk_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class UploadState(str, Enum):
    """State of an upload."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class UploadInfo:
    """Information about an upload."""
    upload_id: str
    filename: str
    config: PDFUploadConfig
    state: UploadState = UploadState.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[PDFUploadResult] = None


class UploadManager:
    """
    Manages PDF upload processing and progress tracking.

    Handles background processing, progress events via asyncio.Queue,
    and cancellation support.
    """

    def __init__(self):
        """Initialize upload manager."""
        self._uploads: Dict[str, UploadInfo] = {}
        self._progress_queues: Dict[str, asyncio.Queue] = {}
        self._cancellation_flags: Dict[str, bool] = {}
        self._tasks: Dict[str, asyncio.Task] = {}

    async def start_upload(
        self,
        upload_id: str,
        filename: str,
        content: bytes,
        config: PDFUploadConfig,
    ) -> None:
        """
        Start processing a PDF upload.

        Args:
            upload_id: Unique identifier for this upload
            filename: Original filename
            content: PDF file content
            config: Upload configuration
        """
        # Initialize tracking
        self._uploads[upload_id] = UploadInfo(
            upload_id=upload_id,
            filename=filename,
            config=config,
            state=UploadState.PROCESSING,
            started_at=datetime.utcnow(),
        )
        self._progress_queues[upload_id] = asyncio.Queue()
        self._cancellation_flags[upload_id] = False

        # Start background processing
        task = asyncio.create_task(
            self._process_upload(upload_id, content, config)
        )
        self._tasks[upload_id] = task

        logger.info(f"Started PDF upload processing: {upload_id} ({filename})")

    async def _process_upload(
        self,
        upload_id: str,
        content: bytes,
        config: PDFUploadConfig,
    ) -> None:
        """Background task to process PDF upload."""
        start_time = time.time()
        upload_info = self._uploads[upload_id]

        try:
            # Stage 1: Extract text
            await self._emit_progress(
                upload_id,
                PDFProcessingStage.EXTRACTING,
                5,
                "Extracting text from PDF...",
            )

            if self._is_cancelled(upload_id):
                return

            processor = get_pdf_processor(
                chunk_size=config.chunk_size,
                chunk_overlap=config.chunk_overlap,
            )

            text, page_count = await processor.extract_text(content)

            if not text.strip():
                raise ValueError("No text could be extracted from the PDF")

            await self._emit_progress(
                upload_id,
                PDFProcessingStage.EXTRACTING,
                20,
                f"Extracted text from {page_count} pages",
            )

            if self._is_cancelled(upload_id):
                return

            # Stage 2: Chunk text
            await self._emit_progress(
                upload_id,
                PDFProcessingStage.CHUNKING,
                25,
                "Chunking text...",
            )

            chunks = await processor.chunk_text(text)
            total_chunks = len(chunks)

            await self._emit_progress(
                upload_id,
                PDFProcessingStage.CHUNKING,
                30,
                f"Created {total_chunks} chunks",
                total_chunks=total_chunks,
            )

            if self._is_cancelled(upload_id):
                return

            # Stage 3: Generate embeddings and store
            await self._emit_progress(
                upload_id,
                PDFProcessingStage.EMBEDDING,
                35,
                f"Processing {total_chunks} chunks...",
                total_chunks=total_chunks,
            )

            stored_count = 0
            failed_count = 0
            chunk_ids = []

            # Process in batches
            batch_size = 10
            for i in range(0, total_chunks, batch_size):
                if self._is_cancelled(upload_id):
                    return

                batch = chunks[i:i + batch_size]
                batch_results = await self._process_chunk_batch(
                    batch, config, upload_info.filename
                )

                stored_count += batch_results["stored"]
                failed_count += batch_results["failed"]
                chunk_ids.extend(batch_results["ids"])

                # Calculate progress (35-95%)
                progress = 35 + (60 * (i + len(batch)) / total_chunks)
                await self._emit_progress(
                    upload_id,
                    PDFProcessingStage.STORING,
                    progress,
                    f"Stored {stored_count}/{total_chunks} chunks",
                    current_chunk=i + len(batch),
                    total_chunks=total_chunks,
                    chunks_stored=stored_count,
                )

            # Stage 4: Complete
            processing_time = time.time() - start_time

            result = PDFUploadResult(
                upload_id=upload_id,
                success=True,
                filename=upload_info.filename,
                title=config.title,
                chunks_created=total_chunks,
                chunks_stored=stored_count,
                chunks_failed=failed_count,
                total_pages=page_count,
                processing_time_seconds=round(processing_time, 2),
                chunk_ids=chunk_ids,
            )

            upload_info.state = UploadState.COMPLETED
            upload_info.completed_at = datetime.utcnow()
            upload_info.result = result

            await self._emit_progress(
                upload_id,
                PDFProcessingStage.COMPLETED,
                100,
                f"Successfully stored {stored_count} chunks from {page_count} pages",
                total_chunks=total_chunks,
                chunks_stored=stored_count,
            )

            logger.info(
                f"PDF upload completed: {upload_id} - "
                f"{stored_count}/{total_chunks} chunks in {processing_time:.1f}s"
            )

        except Exception as e:
            logger.error(f"PDF upload {upload_id} failed: {e}", exc_info=True)

            upload_info.state = UploadState.FAILED
            upload_info.completed_at = datetime.utcnow()

            await self._emit_progress(
                upload_id,
                PDFProcessingStage.FAILED,
                0,
                f"Upload failed: {str(e)}",
                error=str(e),
            )

        finally:
            # Cleanup
            self._cleanup_upload(upload_id)

    async def _process_chunk_batch(
        self,
        chunks: List[TextChunk],
        config: PDFUploadConfig,
        filename: str,
    ) -> Dict[str, Any]:
        """
        Process a batch of chunks with embeddings and store to Weaviate.

        Args:
            chunks: List of text chunks
            config: Upload configuration
            filename: Original filename

        Returns:
            Dict with stored count, failed count, and chunk IDs
        """
        stored_ids = []
        failed_count = 0

        try:
            # Import here to avoid circular imports
            from app.db.weaviate import get_weaviate_client, is_weaviate_available

            if not is_weaviate_available():
                raise RuntimeError("Weaviate is not available")

            client = get_weaviate_client()

            # Ensure RAG collection exists
            await self._ensure_rag_collection(client)

            # Generate embeddings if enabled
            vectors = None
            if config.generate_embeddings:
                try:
                    from app.common.providers.embeddings import get_embeddings_provider
                    embeddings_provider = get_embeddings_provider()
                    texts = [chunk.content for chunk in chunks]

                    # Retry logic for embeddings
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            vectors = await embeddings_provider.embed_texts(texts)
                            break
                        except Exception as e:
                            if attempt == max_retries - 1:
                                logger.warning(f"Failed to generate embeddings after {max_retries} attempts: {e}")
                                vectors = None
                            else:
                                logger.warning(f"Embedding attempt {attempt + 1} failed, retrying: {e}")
                                await asyncio.sleep(2 ** attempt)

                except Exception as e:
                    logger.warning(f"Could not get embeddings provider: {e}")
                    vectors = None

            # Store to Weaviate
            collection = client.collections.get(config.collection)

            with collection.batch.dynamic() as batch:
                for i, chunk in enumerate(chunks):
                    try:
                        properties = {
                            "title": config.title,
                            "content": chunk.content,
                            "source": config.source,
                            "chunk_id": f"{filename}_{chunk.id}",
                            "metadata_json": json.dumps({
                                **(config.metadata or {}),
                                "chunk_index": chunk.index,
                                "filename": filename,
                                "start_char": chunk.start_char,
                                "end_char": chunk.end_char,
                            }),
                            "created_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z",
                        }

                        if vectors and i < len(vectors):
                            obj_uuid = batch.add_object(properties=properties, vector=vectors[i])
                        else:
                            obj_uuid = batch.add_object(properties=properties)

                        stored_ids.append(str(obj_uuid) if obj_uuid else chunk.id)

                    except Exception as e:
                        logger.warning(f"Failed to store chunk {chunk.id}: {e}")
                        failed_count += 1

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            failed_count = len(chunks)

        return {
            "stored": len(stored_ids),
            "failed": failed_count,
            "ids": stored_ids,
        }

    async def _ensure_rag_collection(self, client) -> None:
        """Ensure RAG collection exists."""
        collection_name = "RAGDocuments"

        if not client.collections.exists(collection_name):
            from weaviate.classes.config import Property, DataType, Configure

            client.collections.create(
                name=collection_name,
                description="Documents for RAG (Retrieval Augmented Generation)",
                vectorizer_config=Configure.Vectorizer.none(),
                properties=[
                    Property(name="title", data_type=DataType.TEXT),
                    Property(name="content", data_type=DataType.TEXT),
                    Property(name="source", data_type=DataType.TEXT),
                    Property(name="chunk_id", data_type=DataType.TEXT),
                    Property(name="metadata_json", data_type=DataType.TEXT),
                    Property(name="created_at", data_type=DataType.DATE),
                ],
            )
            logger.info(f"Created RAG collection: {collection_name}")

    async def _emit_progress(
        self,
        upload_id: str,
        stage: PDFProcessingStage,
        progress: float,
        message: str,
        **kwargs,
    ) -> None:
        """Emit a progress event."""
        if upload_id not in self._progress_queues:
            return

        progress_event = PDFUploadProgress(
            upload_id=upload_id,
            stage=stage.value,
            progress=progress,
            message=message,
            **kwargs,
        )

        await self._progress_queues[upload_id].put(progress_event)

    def _is_cancelled(self, upload_id: str) -> bool:
        """Check if upload is cancelled."""
        if self._cancellation_flags.get(upload_id, False):
            upload_info = self._uploads.get(upload_id)
            if upload_info:
                upload_info.state = UploadState.CANCELLED
            logger.info(f"Upload {upload_id} was cancelled")
            return True
        return False

    def _cleanup_upload(self, upload_id: str) -> None:
        """Clean up upload resources after completion."""
        # Keep the upload info for a while for result retrieval
        # but clean up other resources
        if upload_id in self._cancellation_flags:
            del self._cancellation_flags[upload_id]
        if upload_id in self._tasks:
            del self._tasks[upload_id]

    async def get_progress(self, upload_id: str) -> AsyncGenerator[PDFUploadProgress, None]:
        """
        Yield progress updates for an upload.

        Args:
            upload_id: The upload ID to track

        Yields:
            PDFUploadProgress events
        """
        if upload_id not in self._progress_queues:
            # Create queue if it doesn't exist (for late subscribers)
            self._progress_queues[upload_id] = asyncio.Queue()

            # If upload already completed, send final status
            upload_info = self._uploads.get(upload_id)
            if upload_info and upload_info.state in [UploadState.COMPLETED, UploadState.FAILED]:
                if upload_info.state == UploadState.COMPLETED:
                    yield PDFUploadProgress(
                        upload_id=upload_id,
                        stage=PDFProcessingStage.COMPLETED.value,
                        progress=100,
                        message="Upload completed",
                    )
                else:
                    yield PDFUploadProgress(
                        upload_id=upload_id,
                        stage=PDFProcessingStage.FAILED.value,
                        progress=0,
                        message="Upload failed",
                        error=upload_info.result.error if upload_info.result else "Unknown error",
                    )
                return

        queue = self._progress_queues[upload_id]

        while True:
            try:
                # Wait for progress event with timeout
                progress = await asyncio.wait_for(queue.get(), timeout=60.0)
                yield progress

                # Stop if completed or failed
                if progress.stage in [PDFProcessingStage.COMPLETED.value, PDFProcessingStage.FAILED.value]:
                    break

            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                yield PDFUploadProgress(
                    upload_id=upload_id,
                    stage="heartbeat",
                    progress=-1,
                    message="Processing...",
                )

    async def cancel_upload(self, upload_id: str) -> bool:
        """
        Cancel an in-progress upload.

        Args:
            upload_id: The upload ID to cancel

        Returns:
            True if cancelled, False if not found or already completed
        """
        if upload_id not in self._uploads:
            return False

        upload_info = self._uploads[upload_id]

        if upload_info.state not in [UploadState.PENDING, UploadState.PROCESSING]:
            return False

        self._cancellation_flags[upload_id] = True

        # Cancel the task if running
        task = self._tasks.get(upload_id)
        if task and not task.done():
            task.cancel()

        logger.info(f"Cancelled upload: {upload_id}")
        return True

    def get_upload_info(self, upload_id: str) -> Optional[UploadInfo]:
        """Get information about an upload."""
        return self._uploads.get(upload_id)

    def get_upload_result(self, upload_id: str) -> Optional[PDFUploadResult]:
        """Get the result of a completed upload."""
        upload_info = self._uploads.get(upload_id)
        return upload_info.result if upload_info else None


# Singleton instance
_upload_manager: Optional[UploadManager] = None


def get_upload_manager() -> UploadManager:
    """Get or create upload manager instance."""
    global _upload_manager

    if _upload_manager is None:
        _upload_manager = UploadManager()

    return _upload_manager
