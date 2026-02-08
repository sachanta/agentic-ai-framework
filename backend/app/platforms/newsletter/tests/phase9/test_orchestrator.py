"""
Tests for Newsletter Orchestrator with LangGraph.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.platforms.newsletter.orchestrator import (
    NewsletterOrchestrator,
    get_newsletter_orchestrator,
)


class TestNewsletterOrchestratorImports:
    """Tests for orchestrator module imports."""

    def test_newsletter_orchestrator_import(self):
        """Can import NewsletterOrchestrator."""
        assert NewsletterOrchestrator is not None

    def test_get_newsletter_orchestrator_import(self):
        """Can import get_newsletter_orchestrator."""
        assert get_newsletter_orchestrator is not None


class TestNewsletterOrchestratorInstantiation:
    """Tests for NewsletterOrchestrator instantiation."""

    def test_instantiate_with_defaults(self):
        """Can instantiate with default values."""
        orchestrator = NewsletterOrchestrator()
        assert orchestrator is not None
        assert orchestrator.name == "Newsletter Orchestrator"

    def test_instantiate_with_custom_name(self):
        """Can instantiate with custom name."""
        orchestrator = NewsletterOrchestrator(name="Custom Orchestrator")
        assert orchestrator.name == "Custom Orchestrator"

    def test_instantiate_with_custom_description(self):
        """Can instantiate with custom description."""
        orchestrator = NewsletterOrchestrator(description="Custom description")
        assert orchestrator.description == "Custom description"

    def test_default_description_mentions_hitl(self):
        """Default description mentions HITL."""
        orchestrator = NewsletterOrchestrator()
        assert "HITL" in orchestrator.description


class TestNewsletterOrchestratorGraph:
    """Tests for NewsletterOrchestrator graph property."""

    def test_graph_property_returns_graph(self):
        """graph property returns a graph."""
        with patch(
            "app.platforms.newsletter.orchestrator.orchestrator.get_newsletter_graph"
        ) as mock_get_graph:
            mock_graph = MagicMock()
            mock_get_graph.return_value = mock_graph

            orchestrator = NewsletterOrchestrator()
            graph = orchestrator.graph

            assert graph == mock_graph

    def test_graph_property_caches_result(self):
        """graph property caches the graph."""
        with patch(
            "app.platforms.newsletter.orchestrator.orchestrator.get_newsletter_graph"
        ) as mock_get_graph:
            mock_graph = MagicMock()
            mock_get_graph.return_value = mock_graph

            orchestrator = NewsletterOrchestrator()
            graph1 = orchestrator.graph
            graph2 = orchestrator.graph

            assert graph1 is graph2
            mock_get_graph.assert_called_once()


class TestNewsletterOrchestratorInitialize:
    """Tests for NewsletterOrchestrator.initialize method."""

    @pytest.mark.asyncio
    async def test_initialize_creates_graph(self):
        """initialize creates the workflow graph."""
        with patch(
            "app.platforms.newsletter.orchestrator.orchestrator.get_newsletter_graph"
        ) as mock_get_graph:
            mock_graph = MagicMock()
            mock_get_graph.return_value = mock_graph

            orchestrator = NewsletterOrchestrator()
            await orchestrator.initialize()

            # Graph should be accessed during initialization
            assert orchestrator._graph is not None


class TestNewsletterOrchestratorRun:
    """Tests for NewsletterOrchestrator.run method."""

    @pytest.mark.asyncio
    async def test_run_requires_user_id(self):
        """run returns error when user_id is missing."""
        orchestrator = NewsletterOrchestrator()
        result = await orchestrator.run({})

        assert result["success"] is False
        assert "user_id" in result["error"]

    @pytest.mark.asyncio
    async def test_run_requires_topics_or_prompt(self):
        """run returns error when both topics and custom_prompt are missing."""
        orchestrator = NewsletterOrchestrator()
        result = await orchestrator.run({"user_id": "user123"})

        assert result["success"] is False
        assert "topics" in result["error"] or "custom_prompt" in result["error"]

    @pytest.mark.asyncio
    async def test_run_starts_workflow(self):
        """run starts the workflow successfully."""
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value={"status": "running"})
        mock_graph.aget_state = AsyncMock(
            return_value=MagicMock(next=["checkpoint_articles"], values={"status": "running"})
        )

        with patch(
            "app.platforms.newsletter.orchestrator.orchestrator.get_newsletter_graph",
            return_value=mock_graph,
        ):
            orchestrator = NewsletterOrchestrator()
            result = await orchestrator.run({
                "user_id": "user123",
                "topics": ["tech", "ai"],
            })

            assert result["success"] is True
            assert "workflow_id" in result

    @pytest.mark.asyncio
    async def test_run_returns_workflow_id(self):
        """run returns workflow_id in result."""
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value={"status": "running"})
        mock_graph.aget_state = AsyncMock(
            return_value=MagicMock(next=["checkpoint_articles"], values={"status": "running"})
        )

        with patch(
            "app.platforms.newsletter.orchestrator.orchestrator.get_newsletter_graph",
            return_value=mock_graph,
        ):
            orchestrator = NewsletterOrchestrator()
            result = await orchestrator.run({
                "user_id": "user123",
                "topics": ["tech"],
            })

            assert "workflow_id" in result
            assert len(result["workflow_id"]) == 36  # UUID format


class TestNewsletterOrchestratorGetWorkflowStatus:
    """Tests for NewsletterOrchestrator.get_workflow_status method."""

    @pytest.mark.asyncio
    async def test_get_workflow_status_not_found(self):
        """get_workflow_status returns not_found for missing workflow."""
        mock_graph = MagicMock()
        mock_graph.aget_state = AsyncMock(
            return_value=MagicMock(values=None)
        )

        with patch(
            "app.platforms.newsletter.orchestrator.orchestrator.get_newsletter_graph",
            return_value=mock_graph,
        ):
            orchestrator = NewsletterOrchestrator()
            result = await orchestrator.get_workflow_status("nonexistent-id")

            assert result["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_get_workflow_status_returns_status(self):
        """get_workflow_status returns workflow status."""
        mock_graph = MagicMock()
        mock_graph.aget_state = AsyncMock(
            return_value=MagicMock(
                values={"status": "running", "current_step": "research"},
                next=None,
            )
        )

        with patch(
            "app.platforms.newsletter.orchestrator.orchestrator.get_newsletter_graph",
            return_value=mock_graph,
        ):
            orchestrator = NewsletterOrchestrator()
            result = await orchestrator.get_workflow_status("workflow-123")

            assert result["workflow_id"] == "workflow-123"
            assert result["status"] == "running"


class TestNewsletterOrchestratorGetPendingCheckpoint:
    """Tests for NewsletterOrchestrator.get_pending_checkpoint method."""

    @pytest.mark.asyncio
    async def test_get_pending_checkpoint_returns_none_when_not_paused(self):
        """get_pending_checkpoint returns None when workflow is not paused."""
        mock_graph = MagicMock()
        mock_graph.aget_state = AsyncMock(
            return_value=MagicMock(values={"status": "running"}, next=None)
        )

        with patch(
            "app.platforms.newsletter.orchestrator.orchestrator.get_newsletter_graph",
            return_value=mock_graph,
        ):
            orchestrator = NewsletterOrchestrator()
            result = await orchestrator.get_pending_checkpoint("workflow-123")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_pending_checkpoint_returns_checkpoint_data(self):
        """get_pending_checkpoint returns checkpoint data when paused."""
        mock_graph = MagicMock()
        mock_graph.aget_state = AsyncMock(
            return_value=MagicMock(
                values={
                    "status": "running",
                    "current_checkpoint": {
                        "checkpoint_id": "ckpt-123",
                        "checkpoint_type": "article_review",
                    },
                },
                next=["checkpoint_articles"],
            )
        )

        with patch(
            "app.platforms.newsletter.orchestrator.orchestrator.get_newsletter_graph",
            return_value=mock_graph,
        ):
            orchestrator = NewsletterOrchestrator()
            result = await orchestrator.get_pending_checkpoint("workflow-123")

            assert result is not None
            assert result["workflow_id"] == "workflow-123"


class TestNewsletterOrchestratorApproveCheckpoint:
    """Tests for NewsletterOrchestrator.approve_checkpoint method."""

    @pytest.mark.asyncio
    async def test_approve_checkpoint_resumes_workflow(self):
        """approve_checkpoint resumes the workflow."""
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value={"status": "running"})
        mock_graph.aget_state = AsyncMock(
            return_value=MagicMock(next=None, values={"status": "completed"})
        )

        with patch(
            "app.platforms.newsletter.orchestrator.orchestrator.get_newsletter_graph",
            return_value=mock_graph,
        ):
            orchestrator = NewsletterOrchestrator()
            result = await orchestrator.approve_checkpoint(
                workflow_id="workflow-123",
                checkpoint_id="ckpt-123",
                action="approve",
            )

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_approve_checkpoint_with_modifications(self):
        """approve_checkpoint passes modifications to workflow."""
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value={"status": "running"})
        mock_graph.aget_state = AsyncMock(
            return_value=MagicMock(next=None, values={"status": "completed"})
        )

        with patch(
            "app.platforms.newsletter.orchestrator.orchestrator.get_newsletter_graph",
            return_value=mock_graph,
        ):
            orchestrator = NewsletterOrchestrator()
            result = await orchestrator.approve_checkpoint(
                workflow_id="workflow-123",
                checkpoint_id="ckpt-123",
                action="edit",
                modifications={"selected_articles": [1, 2, 3]},
            )

            assert result["success"] is True


class TestNewsletterOrchestratorCancelWorkflow:
    """Tests for NewsletterOrchestrator.cancel_workflow method."""

    @pytest.mark.asyncio
    async def test_cancel_workflow_returns_cancelled(self):
        """cancel_workflow returns cancelled status."""
        mock_graph = MagicMock()
        mock_graph.aupdate_state = AsyncMock()

        mock_saver = MagicMock()
        mock_saver.adelete_thread = AsyncMock()

        with patch(
            "app.platforms.newsletter.orchestrator.orchestrator.get_newsletter_graph",
            return_value=mock_graph,
        ), patch(
            "app.platforms.newsletter.orchestrator.orchestrator.get_mongodb_saver",
            return_value=mock_saver,
        ):
            orchestrator = NewsletterOrchestrator()
            result = await orchestrator.cancel_workflow("workflow-123")

            assert result["success"] is True
            assert result["status"] == "cancelled"


class TestGetNewsletterOrchestrator:
    """Tests for get_newsletter_orchestrator singleton."""

    def test_get_newsletter_orchestrator_returns_instance(self):
        """get_newsletter_orchestrator returns instance."""
        # Reset singleton
        import app.platforms.newsletter.orchestrator.orchestrator as module
        module._orchestrator = None

        orchestrator = get_newsletter_orchestrator()
        assert isinstance(orchestrator, NewsletterOrchestrator)

    def test_get_newsletter_orchestrator_returns_same_instance(self):
        """get_newsletter_orchestrator returns same instance."""
        # Reset singleton
        import app.platforms.newsletter.orchestrator.orchestrator as module
        module._orchestrator = None

        o1 = get_newsletter_orchestrator()
        o2 = get_newsletter_orchestrator()

        assert o1 is o2
