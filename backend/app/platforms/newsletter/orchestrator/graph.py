"""
LangGraph Workflow Definition.

Defines the newsletter generation workflow graph with HITL checkpoints.
"""
import logging
from typing import Literal

from langgraph.graph import StateGraph, END

from app.platforms.newsletter.orchestrator.state import NewsletterState
from app.platforms.newsletter.orchestrator.nodes import (
    get_preferences_node,
    process_prompt_node,
    research_node,
    generate_content_node,
    create_subjects_node,
    format_email_node,
    store_newsletter_node,
    send_email_node,
    checkpoint_articles_node,
    checkpoint_content_node,
    checkpoint_subjects_node,
    checkpoint_send_node,
)
from app.platforms.newsletter.orchestrator.mongodb_saver import get_mongodb_saver

logger = logging.getLogger(__name__)


# ─── Routing Functions ──────────────────────────────────────────────────────


def route_after_article_checkpoint(
    state: NewsletterState,
) -> Literal["research", "generate_content"]:
    """Route after article review checkpoint."""
    # If research was rejected, go back to research
    if not state.get("research_completed", False):
        return "research"
    return "generate_content"


def route_after_content_checkpoint(
    state: NewsletterState,
) -> Literal["generate_content", "create_subjects"]:
    """Route after content review checkpoint."""
    # If content was rejected, regenerate
    if not state.get("content_generated", False):
        return "generate_content"
    return "create_subjects"


def route_after_subject_checkpoint(
    state: NewsletterState,
) -> Literal["create_subjects", "format_email"]:
    """Route after subject review checkpoint."""
    # If subjects were rejected, regenerate
    if not state.get("subjects_generated", False):
        return "create_subjects"
    return "format_email"


def route_after_send_checkpoint(
    state: NewsletterState,
) -> Literal["send_email", "__end__"]:
    """Route after send approval checkpoint."""
    status = state.get("status", "running")

    if status == "cancelled":
        return END
    if status == "scheduled":
        return END  # Will be sent by scheduler

    return "send_email"


def should_continue(state: NewsletterState) -> Literal["continue", "__end__"]:
    """Check if workflow should continue or end."""
    status = state.get("status", "running")

    if status in ("completed", "cancelled", "failed"):
        return END

    if state.get("error"):
        return END

    return "continue"


# ─── Graph Builder ──────────────────────────────────────────────────────────


def create_newsletter_graph(use_checkpointer: bool = True) -> StateGraph:
    """
    Create the newsletter generation workflow graph.

    Args:
        use_checkpointer: Whether to attach MongoDB checkpointer

    Returns:
        Compiled StateGraph
    """
    # Create graph with state schema
    graph = StateGraph(NewsletterState)

    # ─── Add Nodes ──────────────────────────────────────────────────────

    # Agent nodes (async)
    graph.add_node("get_preferences", get_preferences_node)
    graph.add_node("process_prompt", process_prompt_node)
    graph.add_node("research", research_node)
    graph.add_node("generate_content", generate_content_node)
    graph.add_node("create_subjects", create_subjects_node)
    graph.add_node("format_email", format_email_node)
    graph.add_node("store_newsletter", store_newsletter_node)
    graph.add_node("send_email", send_email_node)

    # Checkpoint nodes (sync - use interrupt)
    graph.add_node("checkpoint_articles", checkpoint_articles_node)
    graph.add_node("checkpoint_content", checkpoint_content_node)
    graph.add_node("checkpoint_subjects", checkpoint_subjects_node)
    graph.add_node("checkpoint_send", checkpoint_send_node)

    # ─── Add Edges ──────────────────────────────────────────────────────

    # Set entry point
    graph.set_entry_point("get_preferences")

    # Linear flow to first checkpoint
    graph.add_edge("get_preferences", "process_prompt")
    graph.add_edge("process_prompt", "research")
    graph.add_edge("research", "checkpoint_articles")

    # After checkpoint 1: route based on approval
    graph.add_conditional_edges(
        "checkpoint_articles",
        route_after_article_checkpoint,
        {
            "research": "research",
            "generate_content": "generate_content",
        },
    )

    # Content generation to checkpoint 2
    graph.add_edge("generate_content", "checkpoint_content")

    # After checkpoint 2: route based on approval
    graph.add_conditional_edges(
        "checkpoint_content",
        route_after_content_checkpoint,
        {
            "generate_content": "generate_content",
            "create_subjects": "create_subjects",
        },
    )

    # Subject lines to checkpoint 3
    graph.add_edge("create_subjects", "checkpoint_subjects")

    # After checkpoint 3: route based on approval
    graph.add_conditional_edges(
        "checkpoint_subjects",
        route_after_subject_checkpoint,
        {
            "create_subjects": "create_subjects",
            "format_email": "format_email",
        },
    )

    # Format and store
    graph.add_edge("format_email", "store_newsletter")
    graph.add_edge("store_newsletter", "checkpoint_send")

    # After checkpoint 4: route based on approval
    graph.add_conditional_edges(
        "checkpoint_send",
        route_after_send_checkpoint,
        {
            "send_email": "send_email",
            END: END,
        },
    )

    # Final step
    graph.add_edge("send_email", END)

    # ─── Compile ────────────────────────────────────────────────────────

    if use_checkpointer:
        checkpointer = get_mongodb_saver()
        return graph.compile(checkpointer=checkpointer)
    else:
        return graph.compile()


# Singleton compiled graph
_graph = None


def get_newsletter_graph(use_checkpointer: bool = True) -> StateGraph:
    """
    Get or create the newsletter workflow graph.

    Args:
        use_checkpointer: Whether to use MongoDB checkpointer

    Returns:
        Compiled StateGraph
    """
    global _graph
    if _graph is None:
        _graph = create_newsletter_graph(use_checkpointer)
    return _graph


__all__ = [
    "create_newsletter_graph",
    "get_newsletter_graph",
]
