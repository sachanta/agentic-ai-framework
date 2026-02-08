"""
Newsletter Workflow State Schema.

Defines the TypedDict for LangGraph workflow state.
"""
from datetime import datetime, timezone
from typing import Any, TypedDict


class ArticleData(TypedDict, total=False):
    """Article data from research."""
    title: str
    url: str
    source: str
    content: str | None
    summary: str | None
    score: float
    published_date: str | None


class CheckpointData(TypedDict, total=False):
    """Data for a HITL checkpoint."""
    checkpoint_id: str
    checkpoint_type: str  # article_review, content_review, subject_review, send_approval
    title: str
    description: str
    data: dict[str, Any]
    actions: list[str]
    created_at: str


class NewsletterState(TypedDict, total=False):
    """
    State for the newsletter generation workflow.

    This state is passed between nodes and persisted by the checkpointer.
    """
    # ─── Input Parameters ───────────────────────────────────────────
    user_id: str
    topics: list[str]
    tone: str
    custom_prompt: str | None
    max_articles: int

    # ─── Preferences (from PreferenceAgent) ─────────────────────────
    preferences: dict[str, Any]
    preferences_applied: bool

    # ─── Prompt Analysis (from CustomPromptAgent) ───────────────────
    prompt_analysis: dict[str, Any] | None
    extracted_topics: list[str] | None

    # ─── Research Results (from ResearchAgent) ──────────────────────
    articles: list[ArticleData]
    research_metadata: dict[str, Any]
    research_completed: bool

    # ─── Newsletter Content (from WritingAgent) ─────────────────────
    newsletter_content: str
    newsletter_html: str
    newsletter_plain: str
    word_count: int
    content_generated: bool

    # ─── Subject Lines (from WritingAgent) ──────────────────────────
    subject_lines: list[str]
    selected_subject: str | None
    subjects_generated: bool

    # ─── Workflow Control ───────────────────────────────────────────
    workflow_id: str
    status: str  # running, paused, completed, cancelled, failed
    current_step: str | None
    error: str | None

    # ─── Checkpoint State ───────────────────────────────────────────
    current_checkpoint: CheckpointData | None
    checkpoint_response: dict[str, Any] | None
    checkpoints_completed: list[str]

    # ─── Storage ────────────────────────────────────────────────────
    newsletter_id: str | None
    stored_in_db: bool
    stored_in_rag: bool

    # ─── Email Delivery ─────────────────────────────────────────────
    email_sent: bool
    email_scheduled: str | None  # ISO datetime if scheduled
    recipient_count: int

    # ─── History & Timestamps ───────────────────────────────────────
    history: list[dict[str, Any]]
    created_at: str
    updated_at: str


def create_initial_state(
    user_id: str,
    topics: list[str],
    tone: str = "professional",
    custom_prompt: str | None = None,
    max_articles: int = 10,
    workflow_id: str | None = None,
) -> NewsletterState:
    """
    Create initial state for a new workflow.

    Args:
        user_id: User identifier
        topics: Topics to research
        tone: Newsletter tone
        custom_prompt: Optional custom prompt
        max_articles: Maximum articles to include
        workflow_id: Optional workflow ID (generated if not provided)

    Returns:
        Initial NewsletterState
    """
    from uuid import uuid4

    now = datetime.now(timezone.utc).isoformat()

    return NewsletterState(
        # Input
        user_id=user_id,
        topics=topics,
        tone=tone,
        custom_prompt=custom_prompt,
        max_articles=max_articles,
        # Preferences
        preferences={},
        preferences_applied=False,
        # Prompt analysis
        prompt_analysis=None,
        extracted_topics=None,
        # Research
        articles=[],
        research_metadata={},
        research_completed=False,
        # Content
        newsletter_content="",
        newsletter_html="",
        newsletter_plain="",
        word_count=0,
        content_generated=False,
        # Subjects
        subject_lines=[],
        selected_subject=None,
        subjects_generated=False,
        # Workflow control
        workflow_id=workflow_id or str(uuid4()),
        status="running",
        current_step=None,
        error=None,
        # Checkpoint
        current_checkpoint=None,
        checkpoint_response=None,
        checkpoints_completed=[],
        # Storage
        newsletter_id=None,
        stored_in_db=False,
        stored_in_rag=False,
        # Email
        email_sent=False,
        email_scheduled=None,
        recipient_count=0,
        # History
        history=[],
        created_at=now,
        updated_at=now,
    )


def add_history_entry(
    state: NewsletterState,
    step: str,
    status: str,
    data: dict[str, Any] | None = None,
) -> NewsletterState:
    """
    Add an entry to the workflow history.

    Args:
        state: Current state
        step: Step name
        status: Step status
        data: Optional additional data

    Returns:
        Updated state with new history entry
    """
    from datetime import datetime

    entry = {
        "step": step,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if data:
        entry["data"] = data

    history = list(state.get("history", []))
    history.append(entry)

    return {
        **state,
        "history": history,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


__all__ = [
    "NewsletterState",
    "ArticleData",
    "CheckpointData",
    "create_initial_state",
    "add_history_entry",
]
