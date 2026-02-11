"""
LangGraph Workflow Nodes.

Defines all nodes for the newsletter generation workflow.
"""
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from langgraph.types import interrupt

from app.platforms.newsletter.orchestrator.state import (
    NewsletterState,
    CheckpointData,
    add_history_entry,
)

logger = logging.getLogger(__name__)


# ─── Agent Nodes ────────────────────────────────────────────────────────────


async def get_preferences_node(state: NewsletterState) -> dict[str, Any]:
    """
    Node: Get user preferences using PreferenceAgent.

    Retrieves user preferences to personalize the newsletter.
    """
    from app.platforms.newsletter.agents import PreferenceAgent

    logger.info(f"Getting preferences for user: {state['user_id']}")

    try:
        agent = PreferenceAgent()
        result = await agent.run({
            "action": "get",
            "user_id": state["user_id"],
        })

        if result.get("success"):
            preferences = result.get("preferences", {})
            return {
                "preferences": preferences,
                "preferences_applied": True,
                "current_step": "get_preferences",
            }
        else:
            logger.warning(f"Failed to get preferences: {result.get('error')}")
            return {
                "preferences": {},
                "preferences_applied": False,
                "current_step": "get_preferences",
            }

    except Exception as e:
        logger.error(f"Error getting preferences: {e}")
        return {
            "preferences": {},
            "preferences_applied": False,
            "error": str(e),
        }


async def process_prompt_node(state: NewsletterState) -> dict[str, Any]:
    """
    Node: Process custom prompt using CustomPromptAgent.

    Analyzes the custom prompt to extract topics and parameters.
    """
    if not state.get("custom_prompt"):
        return {
            "prompt_analysis": None,
            "extracted_topics": None,
            "current_step": "process_prompt",
        }

    from app.platforms.newsletter.agents import CustomPromptAgent

    logger.info("Processing custom prompt")

    try:
        agent = CustomPromptAgent()
        result = await agent.run({
            "action": "analyze",
            "prompt": state["custom_prompt"],
        })

        if result.get("success"):
            analysis = result.get("analysis", {})
            extracted_topics = analysis.get("topics", [])

            # Merge with provided topics
            all_topics = list(set(state.get("topics", []) + extracted_topics))

            return {
                "prompt_analysis": analysis,
                "extracted_topics": extracted_topics,
                "topics": all_topics,
                "current_step": "process_prompt",
            }
        else:
            return {
                "prompt_analysis": None,
                "extracted_topics": None,
                "current_step": "process_prompt",
            }

    except Exception as e:
        logger.error(f"Error processing prompt: {e}")
        return {
            "prompt_analysis": None,
            "extracted_topics": None,
            "error": str(e),
        }


async def research_node(state: NewsletterState) -> dict[str, Any]:
    """
    Node: Research content using ResearchAgent.

    Searches for articles on the specified topics.
    """
    from app.platforms.newsletter.agents import ResearchAgent

    topics = state.get("topics", [])
    logger.info(f"Researching topics: {topics}")

    try:
        agent = ResearchAgent()
        result = await agent.run({
            "topics": topics,
            "user_id": state["user_id"],
            "max_results": state.get("max_articles", 10),
            "include_summaries": True,
        })

        if result.get("success"):
            articles = result.get("articles", [])
            metadata = result.get("metadata", {})

            return {
                "articles": articles,
                "research_metadata": metadata,
                "research_completed": True,
                "current_step": "research",
            }
        else:
            return {
                "articles": [],
                "research_metadata": {},
                "research_completed": False,
                "error": result.get("error"),
            }

    except Exception as e:
        logger.error(f"Error in research: {e}")
        return {
            "articles": [],
            "research_metadata": {},
            "research_completed": False,
            "error": str(e),
        }


async def generate_content_node(state: NewsletterState) -> dict[str, Any]:
    """
    Node: Generate newsletter content using WritingAgent.

    Creates the newsletter content from the selected articles.
    """
    from app.platforms.newsletter.agents import WritingAgent

    articles = state.get("articles", [])
    logger.info(f"Generating content from {len(articles)} articles")

    try:
        agent = WritingAgent()
        result = await agent.run({
            "action": "generate",
            "articles": articles,
            "tone": state.get("tone", "professional"),
            "user_id": state["user_id"],
        })

        if result.get("success"):
            content = result.get("content", {})
            return {
                "newsletter_content": content.get("markdown", ""),
                "newsletter_html": content.get("html", ""),
                "newsletter_plain": content.get("plain_text", ""),
                "word_count": content.get("word_count", 0),
                "content_generated": True,
                "current_step": "generate_content",
            }
        else:
            return {
                "content_generated": False,
                "error": result.get("error"),
            }

    except Exception as e:
        logger.error(f"Error generating content: {e}")
        return {
            "content_generated": False,
            "error": str(e),
        }


async def create_subjects_node(state: NewsletterState) -> dict[str, Any]:
    """
    Node: Create subject lines using WritingAgent.

    Generates multiple subject line options.
    """
    from app.platforms.newsletter.agents import WritingAgent

    logger.info("Creating subject lines")

    try:
        agent = WritingAgent()
        result = await agent.run({
            "action": "subject_lines",
            "content": state.get("newsletter_content", ""),
            "tone": state.get("tone", "professional"),
            "count": 5,
        })

        if result.get("success"):
            subjects = result.get("subject_lines", [])
            return {
                "subject_lines": subjects,
                "subjects_generated": True,
                "current_step": "create_subjects",
            }
        else:
            # Fallback subject
            return {
                "subject_lines": ["Your Newsletter Update"],
                "subjects_generated": True,
                "current_step": "create_subjects",
            }

    except Exception as e:
        logger.error(f"Error creating subjects: {e}")
        return {
            "subject_lines": ["Your Newsletter Update"],
            "subjects_generated": True,
            "error": str(e),
        }


async def format_email_node(state: NewsletterState) -> dict[str, Any]:
    """
    Node: Format content for email delivery.

    Applies email-specific formatting to the newsletter.
    """
    from app.platforms.newsletter.agents import WritingAgent

    logger.info("Formatting for email")

    try:
        agent = WritingAgent()
        result = await agent.run({
            "action": "format",
            "content": state.get("newsletter_content", ""),
            "format": "email",
        })

        if result.get("success"):
            formats = result.get("formats", {})
            return {
                "newsletter_html": formats.get("html", state.get("newsletter_html", "")),
                "newsletter_plain": formats.get("plain_text", state.get("newsletter_plain", "")),
                "current_step": "format_email",
            }
        else:
            return {"current_step": "format_email"}

    except Exception as e:
        logger.error(f"Error formatting email: {e}")
        return {"error": str(e)}


async def store_newsletter_node(state: NewsletterState) -> dict[str, Any]:
    """
    Node: Store newsletter in MongoDB and RAG.

    Persists the newsletter to databases.
    """
    from app.platforms.newsletter.repositories import NewsletterRepository
    from app.platforms.newsletter.models.newsletter import Newsletter, NewsletterStatus

    logger.info("Storing newsletter")

    try:
        # Create newsletter document
        newsletter = Newsletter(
            user_id=state["user_id"],
            title=state.get("selected_subject") or state.get("subject_lines", ["Newsletter"])[0],
            content=state.get("newsletter_content", ""),
            html_content=state.get("newsletter_html", ""),
            plain_text=state.get("newsletter_plain", ""),
            subject_line=state.get("selected_subject"),
            subject_line_options=state.get("subject_lines", []),
            status=NewsletterStatus.READY,
            workflow_id=state["workflow_id"],
            topics_covered=state.get("topics", []),
            tone_used=state.get("tone", "professional"),
            word_count=state.get("word_count", 0),
            research_data={"articles": state.get("articles", [])},
        )

        repo = NewsletterRepository()
        newsletter_id = await repo.create(newsletter)

        # TODO: Store in RAG (Phase 4 integration)
        stored_in_rag = False

        return {
            "newsletter_id": newsletter_id,
            "stored_in_db": True,
            "stored_in_rag": stored_in_rag,
            "current_step": "store_newsletter",
        }

    except Exception as e:
        logger.error(f"Error storing newsletter: {e}")
        return {
            "stored_in_db": False,
            "stored_in_rag": False,
            "error": str(e),
        }


async def send_email_node(state: NewsletterState) -> dict[str, Any]:
    """
    Node: Send newsletter via email.

    Sends the newsletter to subscribers (Phase 10 integration).
    """
    logger.info("Sending newsletter")

    # TODO: Integrate with Email Service (Phase 10)
    # For now, just mark as complete

    return {
        "email_sent": True,
        "status": "completed",
        "current_step": "send_email",
    }


# ─── Checkpoint Nodes ───────────────────────────────────────────────────────


def checkpoint_articles_node(state: NewsletterState) -> dict[str, Any]:
    """
    HITL Checkpoint 1: Review article selection.

    Pauses workflow for human review of selected articles.
    """
    articles = state.get("articles", [])

    checkpoint_data = CheckpointData(
        checkpoint_id=str(uuid4()),
        checkpoint_type="research_review",
        title="Review Article Selection",
        description=f"Review {len(articles)} articles found for your newsletter",
        data={
            "articles": [
                {
                    "title": a.get("title", ""),
                    "url": a.get("url", ""),
                    "source": a.get("source", ""),
                    "summary": a.get("summary", ""),
                    "score": a.get("score", 0),
                }
                for a in articles
            ],
            "topics": state.get("topics", []),
            "total_found": len(articles),
        },
        actions=["approve", "edit", "reject"],
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    # Interrupt and wait for human input
    response = interrupt(checkpoint_data)

    action = response.get("action", "approve")

    if action == "reject":
        # Re-run research with different parameters
        return {
            "current_checkpoint": None,
            "checkpoint_response": response,
            "status": "running",
            "research_completed": False,  # Trigger re-research
        }

    if action == "edit":
        # Apply edits to articles
        edited_articles = response.get("articles", articles)
        return {
            "articles": edited_articles,
            "current_checkpoint": None,
            "checkpoint_response": response,
            "checkpoints_completed": state.get("checkpoints_completed", []) + ["research_review"],
        }

    # Approved
    return {
        "current_checkpoint": None,
        "checkpoint_response": response,
        "checkpoints_completed": state.get("checkpoints_completed", []) + ["research_review"],
    }


def checkpoint_content_node(state: NewsletterState) -> dict[str, Any]:
    """
    HITL Checkpoint 2: Review newsletter content.

    Pauses workflow for human review of generated content.
    """
    checkpoint_data = CheckpointData(
        checkpoint_id=str(uuid4()),
        checkpoint_type="content_review",
        title="Review Newsletter Content",
        description="Review the generated newsletter content",
        data={
            "content": state.get("newsletter_content", ""),
            "html_preview": state.get("newsletter_html", ""),
            "word_count": state.get("word_count", 0),
            "tone": state.get("tone", "professional"),
        },
        actions=["approve", "edit", "reject"],
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    response = interrupt(checkpoint_data)
    action = response.get("action", "approve")

    if action == "reject":
        return {
            "current_checkpoint": None,
            "checkpoint_response": response,
            "content_generated": False,  # Trigger re-generation
        }

    if action == "edit":
        edited_content = response.get("content", state.get("newsletter_content", ""))
        return {
            "newsletter_content": edited_content,
            "current_checkpoint": None,
            "checkpoint_response": response,
            "checkpoints_completed": state.get("checkpoints_completed", []) + ["content_review"],
        }

    return {
        "current_checkpoint": None,
        "checkpoint_response": response,
        "checkpoints_completed": state.get("checkpoints_completed", []) + ["content_review"],
    }


def checkpoint_subjects_node(state: NewsletterState) -> dict[str, Any]:
    """
    HITL Checkpoint 3: Review subject lines.

    Pauses workflow for human to select or edit subject lines.
    """
    subject_lines = state.get("subject_lines", [])

    checkpoint_data = CheckpointData(
        checkpoint_id=str(uuid4()),
        checkpoint_type="subject_review",
        title="Select Subject Line",
        description="Choose or edit the email subject line",
        data={
            "subject_lines": subject_lines,
            "tone": state.get("tone", "professional"),
        },
        actions=["approve", "edit", "reject"],
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    response = interrupt(checkpoint_data)
    action = response.get("action", "approve")

    if action == "reject":
        return {
            "current_checkpoint": None,
            "checkpoint_response": response,
            "subjects_generated": False,  # Trigger re-generation
        }

    # Get selected subject (default to first)
    selected = response.get("selected_subject") or (subject_lines[0] if subject_lines else "Newsletter")

    if action == "edit":
        selected = response.get("custom_subject", selected)

    return {
        "selected_subject": selected,
        "current_checkpoint": None,
        "checkpoint_response": response,
        "checkpoints_completed": state.get("checkpoints_completed", []) + ["subject_review"],
    }


def checkpoint_send_node(state: NewsletterState) -> dict[str, Any]:
    """
    HITL Checkpoint 4: Final send approval.

    Pauses workflow for final approval before sending.
    """
    checkpoint_data = CheckpointData(
        checkpoint_id=str(uuid4()),
        checkpoint_type="final_review",
        title="Approve Newsletter Send",
        description="Final review before sending the newsletter",
        data={
            "subject": state.get("selected_subject", "Newsletter"),
            "preview_html": state.get("newsletter_html", ""),
            "word_count": state.get("word_count", 0),
            "recipient_count": state.get("recipient_count", 0),
            "newsletter_id": state.get("newsletter_id"),
        },
        actions=["send", "schedule", "cancel"],
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    response = interrupt(checkpoint_data)
    action = response.get("action", "send")

    if action == "cancel":
        return {
            "current_checkpoint": None,
            "checkpoint_response": response,
            "status": "cancelled",
            "checkpoints_completed": state.get("checkpoints_completed", []) + ["final_review"],
        }

    if action == "schedule":
        schedule_time = response.get("schedule_time")
        return {
            "email_scheduled": schedule_time,
            "current_checkpoint": None,
            "checkpoint_response": response,
            "status": "scheduled",
            "checkpoints_completed": state.get("checkpoints_completed", []) + ["final_review"],
        }

    # Send now
    return {
        "current_checkpoint": None,
        "checkpoint_response": response,
        "checkpoints_completed": state.get("checkpoints_completed", []) + ["final_review"],
    }


__all__ = [
    # Agent nodes
    "get_preferences_node",
    "process_prompt_node",
    "research_node",
    "generate_content_node",
    "create_subjects_node",
    "format_email_node",
    "store_newsletter_node",
    "send_email_node",
    # Checkpoint nodes
    "checkpoint_articles_node",
    "checkpoint_content_node",
    "checkpoint_subjects_node",
    "checkpoint_send_node",
]
