"""
Newsletter Orchestrator Package.

LangGraph-based workflow with HITL checkpoints.
"""
from app.platforms.newsletter.orchestrator.orchestrator import (
    NewsletterOrchestrator,
    get_newsletter_orchestrator,
)
from app.platforms.newsletter.orchestrator.state import (
    NewsletterState,
    create_initial_state,
)
from app.platforms.newsletter.orchestrator.graph import (
    create_newsletter_graph,
    get_newsletter_graph,
)
from app.platforms.newsletter.orchestrator.mongodb_saver import (
    MongoDBSaver,
    get_mongodb_saver,
)

__all__ = [
    # Orchestrator
    "NewsletterOrchestrator",
    "get_newsletter_orchestrator",
    # State
    "NewsletterState",
    "create_initial_state",
    # Graph
    "create_newsletter_graph",
    "get_newsletter_graph",
    # Checkpointer
    "MongoDBSaver",
    "get_mongodb_saver",
]
