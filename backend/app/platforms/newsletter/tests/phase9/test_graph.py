"""
Tests for Newsletter LangGraph Workflow.
"""
import pytest
from unittest.mock import patch, MagicMock

from app.platforms.newsletter.orchestrator.graph import (
    create_newsletter_graph,
    get_newsletter_graph,
    route_after_article_checkpoint,
    route_after_content_checkpoint,
    route_after_subject_checkpoint,
    route_after_send_checkpoint,
    should_continue,
)
from app.platforms.newsletter.orchestrator.state import NewsletterState


class TestGraphImports:
    """Tests for graph module imports."""

    def test_create_newsletter_graph_import(self):
        """Can import create_newsletter_graph."""
        assert create_newsletter_graph is not None

    def test_get_newsletter_graph_import(self):
        """Can import get_newsletter_graph."""
        assert get_newsletter_graph is not None


class TestRoutingFunctions:
    """Tests for graph routing functions."""

    def test_route_after_article_checkpoint_approved(self):
        """Routes to generate_content when research is completed."""
        state: NewsletterState = {"research_completed": True}
        result = route_after_article_checkpoint(state)
        assert result == "generate_content"

    def test_route_after_article_checkpoint_rejected(self):
        """Routes to research when research is not completed."""
        state: NewsletterState = {"research_completed": False}
        result = route_after_article_checkpoint(state)
        assert result == "research"

    def test_route_after_article_checkpoint_default(self):
        """Routes to research when research_completed is missing."""
        state: NewsletterState = {}
        result = route_after_article_checkpoint(state)
        assert result == "research"

    def test_route_after_content_checkpoint_approved(self):
        """Routes to create_subjects when content is generated."""
        state: NewsletterState = {"content_generated": True}
        result = route_after_content_checkpoint(state)
        assert result == "create_subjects"

    def test_route_after_content_checkpoint_rejected(self):
        """Routes to generate_content when content is not generated."""
        state: NewsletterState = {"content_generated": False}
        result = route_after_content_checkpoint(state)
        assert result == "generate_content"

    def test_route_after_subject_checkpoint_approved(self):
        """Routes to format_email when subjects are generated."""
        state: NewsletterState = {"subjects_generated": True}
        result = route_after_subject_checkpoint(state)
        assert result == "format_email"

    def test_route_after_subject_checkpoint_rejected(self):
        """Routes to create_subjects when subjects are not generated."""
        state: NewsletterState = {"subjects_generated": False}
        result = route_after_subject_checkpoint(state)
        assert result == "create_subjects"

    def test_route_after_send_checkpoint_approved(self):
        """Routes to send_email for approved send."""
        state: NewsletterState = {"status": "running"}
        result = route_after_send_checkpoint(state)
        assert result == "send_email"

    def test_route_after_send_checkpoint_cancelled(self):
        """Routes to END for cancelled workflow."""
        state: NewsletterState = {"status": "cancelled"}
        result = route_after_send_checkpoint(state)
        assert result == "__end__"

    def test_route_after_send_checkpoint_scheduled(self):
        """Routes to END for scheduled workflow."""
        state: NewsletterState = {"status": "scheduled"}
        result = route_after_send_checkpoint(state)
        assert result == "__end__"


class TestShouldContinue:
    """Tests for should_continue routing function."""

    def test_should_continue_running(self):
        """Returns continue for running status."""
        state: NewsletterState = {"status": "running"}
        result = should_continue(state)
        assert result == "continue"

    def test_should_continue_completed(self):
        """Returns END for completed status."""
        state: NewsletterState = {"status": "completed"}
        result = should_continue(state)
        assert result == "__end__"

    def test_should_continue_cancelled(self):
        """Returns END for cancelled status."""
        state: NewsletterState = {"status": "cancelled"}
        result = should_continue(state)
        assert result == "__end__"

    def test_should_continue_failed(self):
        """Returns END for failed status."""
        state: NewsletterState = {"status": "failed"}
        result = should_continue(state)
        assert result == "__end__"

    def test_should_continue_with_error(self):
        """Returns END when error is present."""
        state: NewsletterState = {"status": "running", "error": "Something went wrong"}
        result = should_continue(state)
        assert result == "__end__"

    def test_should_continue_default(self):
        """Returns continue for empty state."""
        state: NewsletterState = {}
        result = should_continue(state)
        assert result == "continue"


class TestCreateNewsletterGraph:
    """Tests for create_newsletter_graph function."""

    def test_create_graph_without_checkpointer(self):
        """Can create graph without checkpointer."""
        with patch(
            "app.platforms.newsletter.orchestrator.graph.get_mongodb_saver"
        ) as mock_saver:
            graph = create_newsletter_graph(use_checkpointer=False)
            assert graph is not None
            # Should not call get_mongodb_saver
            mock_saver.assert_not_called()

    def test_create_graph_with_checkpointer(self):
        """Can create graph with checkpointer."""
        from langgraph.checkpoint.memory import MemorySaver

        # Use a real in-memory saver for testing
        mock_saver = MemorySaver()
        with patch(
            "app.platforms.newsletter.orchestrator.graph.get_mongodb_saver",
            return_value=mock_saver,
        ):
            graph = create_newsletter_graph(use_checkpointer=True)
            assert graph is not None

    def test_graph_has_nodes(self):
        """Created graph has expected nodes."""
        with patch(
            "app.platforms.newsletter.orchestrator.graph.get_mongodb_saver"
        ):
            graph = create_newsletter_graph(use_checkpointer=False)
            # LangGraph compiled graphs have .nodes attribute
            assert hasattr(graph, "nodes")


class TestGetNewsletterGraph:
    """Tests for get_newsletter_graph singleton."""

    def test_get_newsletter_graph_returns_graph(self):
        """get_newsletter_graph returns a graph."""
        with patch(
            "app.platforms.newsletter.orchestrator.graph.create_newsletter_graph"
        ) as mock_create:
            mock_graph = MagicMock()
            mock_create.return_value = mock_graph

            # Reset singleton
            import app.platforms.newsletter.orchestrator.graph as graph_module
            graph_module._graph = None

            result = get_newsletter_graph()
            assert result == mock_graph

    def test_get_newsletter_graph_caches_result(self):
        """get_newsletter_graph returns same instance on repeated calls."""
        with patch(
            "app.platforms.newsletter.orchestrator.graph.create_newsletter_graph"
        ) as mock_create:
            mock_graph = MagicMock()
            mock_create.return_value = mock_graph

            # Reset singleton
            import app.platforms.newsletter.orchestrator.graph as graph_module
            graph_module._graph = None

            result1 = get_newsletter_graph()
            result2 = get_newsletter_graph()

            assert result1 is result2
            mock_create.assert_called_once()
