"""
Writing API endpoints for Newsletter Platform.

Phase 7: Backend API for Writing Agent.
Provides endpoints to:
- Generate newsletter from selected articles
- Create additional subject lines
- Regenerate with feedback
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.platforms.newsletter.agents import WritingAgent
from app.platforms.newsletter.agents.writing.formatters import format_all
from app.platforms.newsletter.schemas.writing import (
    GenerateRequest,
    GenerateResponse,
    SubjectLine,
    NewsletterContent,
    NewsletterFormats,
    NewsletterSummary,
    GenerateMetadata,
    RegenerateRequest,
)

logger = logging.getLogger(__name__)

# Output directory for saving results
OUTPUT_DIR = Path(__file__).parent.parent.parent.parent.parent / "output" / "writing"

router = APIRouter(prefix="/writing", tags=["writing"])


def _save_results_to_file(
    result: Dict[str, Any],
    request_type: str,
) -> str:
    """Save writing results to a JSON file for debugging."""
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{request_type}.json"
        filepath = OUTPUT_DIR / filename

        output_data = {
            "timestamp": datetime.now().isoformat(),
            "request_type": request_type,
            "success": result.get("success", False),
            "newsletter": result.get("newsletter"),
            "subject_lines": result.get("subject_lines"),
            "summary": result.get("summary"),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, default=str)

        logger.info(f"Writing results saved to: {filepath}")
        return str(filepath)

    except Exception as e:
        logger.warning(f"Failed to save writing results: {e}")
        return ""


@router.post("/generate", response_model=GenerateResponse)
async def generate_newsletter(request: GenerateRequest):
    """
    Generate newsletter from selected articles.

    Takes a list of articles and generates a complete newsletter with:
    - Main content in the specified tone
    - 5 subject line options
    - Bullet point summary
    - Multiple format outputs (HTML, text, markdown)

    Args:
        request: Generation request with articles and options

    Returns:
        Generated newsletter with all components
    """
    try:
        # Validate tone
        valid_tones = ["professional", "casual", "formal", "enthusiastic"]
        tone = request.tone.lower() if request.tone else "professional"
        if tone not in valid_tones:
            tone = "professional"

        # Initialize agent
        agent = WritingAgent(use_rag=request.include_rag)

        # Run the writing agent
        result = await agent.run({
            "articles": request.articles,
            "tone": tone,
            "user_id": request.user_id or "anonymous",
        })

        # Save results for debugging
        _save_results_to_file(result, f"generate_{tone}")

        if not result.get("success"):
            return GenerateResponse(
                success=False,
                error=result.get("error", "Newsletter generation failed"),
            )

        # Parse newsletter content
        newsletter_data = result.get("newsletter", {})
        content = newsletter_data.get("content", "")
        word_count = newsletter_data.get("word_count", len(content.split()))

        newsletter = NewsletterContent(
            content=content,
            word_count=word_count,
        )

        # Parse subject lines
        subject_lines_raw = result.get("subject_lines", [])
        subject_lines = []
        for sl in subject_lines_raw:
            if isinstance(sl, dict):
                subject_lines.append(SubjectLine(
                    text=sl.get("text", sl.get("subject", "")),
                    style=sl.get("style", "informative"),
                ))
            elif isinstance(sl, str):
                subject_lines.append(SubjectLine(text=sl, style="informative"))

        # Parse summary
        summary_data = result.get("summary", {})
        summary = NewsletterSummary(
            bullets=summary_data.get("bullets", []),
            raw=summary_data.get("raw"),
        )

        # Generate formats
        formats_data = result.get("formats")
        if formats_data:
            formats = NewsletterFormats(
                html=formats_data.get("html", ""),
                text=formats_data.get("text", ""),
                markdown=formats_data.get("markdown", content),
            )
        else:
            # Generate formats from content
            generated_formats = format_all(
                content=content,
                title="Weekly Newsletter",
                subtitle=f"Generated on {datetime.now().strftime('%B %d, %Y')}",
                preheader=subject_lines[0].text if subject_lines else "Your weekly digest",
            )
            formats = NewsletterFormats(
                html=generated_formats.get("html", ""),
                text=generated_formats.get("text", ""),
                markdown=generated_formats.get("markdown", content),
            )

        # Build metadata
        metadata_raw = result.get("metadata", {})
        metadata = GenerateMetadata(
            article_count=len(request.articles),
            topics=metadata_raw.get("topics", []),
            tone=tone,
            generated_at=datetime.now(timezone.utc),
            rag_examples_used=metadata_raw.get("rag_examples_used", 0),
        )

        return GenerateResponse(
            success=True,
            newsletter=newsletter,
            subject_lines=subject_lines,
            summary=summary,
            formats=formats,
            metadata=metadata,
        )

    except Exception as e:
        logger.error(f"Generate endpoint failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regenerate", response_model=GenerateResponse)
async def regenerate_newsletter(request: RegenerateRequest):
    """
    Regenerate newsletter with user feedback.

    Takes previous content and feedback to generate improved version.

    Args:
        request: Regeneration request with feedback

    Returns:
        Regenerated newsletter
    """
    try:
        agent = WritingAgent()

        # Include feedback in the generation
        result = await agent.run({
            "articles": request.articles,
            "tone": request.tone,
            "user_id": "anonymous",
            "feedback": request.feedback,
            "previous_content": request.previous_content,
        })

        _save_results_to_file(result, "regenerate")

        if not result.get("success"):
            return GenerateResponse(
                success=False,
                error=result.get("error", "Regeneration failed"),
            )

        # Same parsing as generate endpoint
        newsletter_data = result.get("newsletter", {})
        content = newsletter_data.get("content", "")

        newsletter = NewsletterContent(
            content=content,
            word_count=len(content.split()),
        )

        subject_lines_raw = result.get("subject_lines", [])
        subject_lines = [
            SubjectLine(
                text=sl.get("text", sl) if isinstance(sl, dict) else sl,
                style=sl.get("style", "informative") if isinstance(sl, dict) else "informative",
            )
            for sl in subject_lines_raw
        ]

        summary_data = result.get("summary", {})
        summary = NewsletterSummary(
            bullets=summary_data.get("bullets", []),
        )

        generated_formats = format_all(
            content=content,
            title="Weekly Newsletter",
            subtitle=f"Generated on {datetime.now().strftime('%B %d, %Y')}",
            preheader=subject_lines[0].text if subject_lines else "Your weekly digest",
        )
        formats = NewsletterFormats(
            html=generated_formats.get("html", ""),
            text=generated_formats.get("text", ""),
            markdown=generated_formats.get("markdown", content),
        )

        return GenerateResponse(
            success=True,
            newsletter=newsletter,
            subject_lines=subject_lines,
            summary=summary,
            formats=formats,
            metadata=GenerateMetadata(
                article_count=len(request.articles),
                tone=request.tone,
                generated_at=datetime.now(timezone.utc),
            ),
        )

    except Exception as e:
        logger.error(f"Regenerate endpoint failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
