"""
PDF Processing Service for Agentic AI Framework.

Handles PDF text extraction and chunking for RAG ingestion.
"""
import io
import logging
import re
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class PDFProcessingStage(str, Enum):
    """Stages of PDF processing."""
    VALIDATING = "validating"
    EXTRACTING = "extracting"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TextChunk:
    """A chunk of text extracted from a PDF."""
    content: str
    index: int
    page_number: Optional[int] = None
    start_char: int = 0
    end_char: int = 0

    @property
    def id(self) -> str:
        """Generate a unique ID for this chunk."""
        return f"chunk_{self.index}_{self.page_number or 0}"


@dataclass
class PDFProcessingResult:
    """Result of PDF processing."""
    success: bool
    text: str = ""
    page_count: int = 0
    chunks: List[TextChunk] = field(default_factory=list)
    error: Optional[str] = None


class PDFProcessor:
    """
    PDF text extraction and chunking service.

    Uses pypdf for extraction and implements smart chunking
    that respects sentence and paragraph boundaries.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        max_chunk_size: int = 1500,
    ):
        """
        Initialize PDF processor.

        Args:
            chunk_size: Target size for each chunk in characters
            chunk_overlap: Number of overlapping characters between chunks
            max_chunk_size: Maximum allowed chunk size
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_chunk_size = max_chunk_size

    async def extract_text(self, content: bytes) -> Tuple[str, int]:
        """
        Extract text from PDF content.

        Args:
            content: PDF file content as bytes

        Returns:
            Tuple of (extracted_text, page_count)

        Raises:
            ValueError: If PDF is invalid or cannot be read
        """
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ImportError("pypdf is required for PDF processing. Install with: pip install pypdf")

        try:
            pdf_file = io.BytesIO(content)
            reader = PdfReader(pdf_file)

            page_count = len(reader.pages)
            logger.info(f"Processing PDF with {page_count} pages")

            text_parts = []
            for i, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {i + 1}: {e}")
                    continue

            full_text = "\n\n".join(text_parts)

            # Clean up the text
            full_text = self._clean_text(full_text)

            logger.info(f"Extracted {len(full_text)} characters from {page_count} pages")
            return full_text, page_count

        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise ValueError(f"Failed to read PDF: {str(e)}")

    async def chunk_text(
        self,
        text: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> List[TextChunk]:
        """
        Split text into chunks with overlap.

        Uses smart chunking that tries to respect sentence and
        paragraph boundaries when possible.

        Args:
            text: The text to chunk
            chunk_size: Override default chunk size
            chunk_overlap: Override default overlap

        Returns:
            List of TextChunk objects
        """
        chunk_size = chunk_size or self.chunk_size
        chunk_overlap = chunk_overlap or self.chunk_overlap

        if not text or not text.strip():
            return []

        # Split into paragraphs first
        paragraphs = self._split_into_paragraphs(text)

        chunks = []
        current_chunk = ""
        current_start = 0
        char_position = 0

        for para in paragraphs:
            # If adding this paragraph would exceed max size, finalize current chunk
            if current_chunk and len(current_chunk) + len(para) + 2 > self.max_chunk_size:
                chunks.append(TextChunk(
                    content=current_chunk.strip(),
                    index=len(chunks),
                    start_char=current_start,
                    end_char=char_position,
                ))

                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk, chunk_overlap)
                current_chunk = overlap_text + "\n\n" + para if overlap_text else para
                current_start = char_position - len(overlap_text)

            # If current chunk is at target size, consider splitting
            elif len(current_chunk) >= chunk_size:
                # Try to find a good break point
                break_point = self._find_break_point(current_chunk, chunk_size)

                if break_point > 0:
                    chunks.append(TextChunk(
                        content=current_chunk[:break_point].strip(),
                        index=len(chunks),
                        start_char=current_start,
                        end_char=current_start + break_point,
                    ))

                    # Start new chunk with overlap from end of previous
                    remaining = current_chunk[break_point:]
                    overlap_text = self._get_overlap_text(current_chunk[:break_point], chunk_overlap)
                    current_chunk = overlap_text + remaining + "\n\n" + para if overlap_text else remaining + "\n\n" + para
                    current_start = current_start + break_point - len(overlap_text)
                else:
                    current_chunk += "\n\n" + para
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para

            char_position += len(para) + 2  # +2 for \n\n

        # Don't forget the last chunk
        if current_chunk.strip():
            chunks.append(TextChunk(
                content=current_chunk.strip(),
                index=len(chunks),
                start_char=current_start,
                end_char=char_position,
            ))

        logger.info(f"Created {len(chunks)} chunks from {len(text)} characters")
        return chunks

    async def process(self, content: bytes) -> PDFProcessingResult:
        """
        Full PDF processing: extract and chunk.

        Args:
            content: PDF file content as bytes

        Returns:
            PDFProcessingResult with text and chunks
        """
        try:
            text, page_count = await self.extract_text(content)

            if not text.strip():
                return PDFProcessingResult(
                    success=False,
                    error="No text could be extracted from the PDF",
                )

            chunks = await self.chunk_text(text)

            return PDFProcessingResult(
                success=True,
                text=text,
                page_count=page_count,
                chunks=chunks,
            )

        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            return PDFProcessingResult(
                success=False,
                error=str(e),
            )

    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)

        # Replace multiple newlines with double newline
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)

        return text.strip()

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        # Split on double newlines or more
        paragraphs = re.split(r'\n\s*\n', text)

        # Filter out empty paragraphs
        return [p.strip() for p in paragraphs if p.strip()]

    def _find_break_point(self, text: str, target_length: int) -> int:
        """
        Find a good break point near target_length.

        Prefers sentence boundaries, then word boundaries.
        """
        if len(text) <= target_length:
            return len(text)

        # Look for sentence boundary near target
        search_start = max(0, target_length - 200)
        search_end = min(len(text), target_length + 100)
        search_text = text[search_start:search_end]

        # Try to find sentence end (. ! ?)
        sentence_ends = []
        for match in re.finditer(r'[.!?]\s+', search_text):
            pos = search_start + match.end()
            if pos <= target_length + 100:
                sentence_ends.append(pos)

        if sentence_ends:
            # Pick the one closest to target
            return min(sentence_ends, key=lambda x: abs(x - target_length))

        # Fall back to word boundary
        space_pos = text.rfind(' ', search_start, target_length)
        if space_pos > search_start:
            return space_pos + 1

        # Last resort: just cut at target
        return target_length

    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """Get overlap text from end of chunk."""
        if len(text) <= overlap_size:
            return text

        # Try to start at word boundary
        overlap_text = text[-overlap_size:]
        space_pos = overlap_text.find(' ')

        if space_pos > 0 and space_pos < overlap_size // 2:
            return overlap_text[space_pos + 1:]

        return overlap_text


# Singleton instance
_pdf_processor: Optional[PDFProcessor] = None


def get_pdf_processor(
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> PDFProcessor:
    """Get or create PDF processor instance."""
    global _pdf_processor

    if _pdf_processor is None:
        _pdf_processor = PDFProcessor(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    return _pdf_processor
