"""
Newsletter Orchestrator - LangGraph-based workflow with HITL checkpoints.

This orchestrator coordinates the newsletter generation workflow:
1. Get user preferences (Preference Agent)
2. Process custom prompt if provided (Custom Prompt Agent)
3. Research content (Research Agent) -> CHECKPOINT 1: Review article selection
4. Generate newsletter (Writing Agent) -> CHECKPOINT 2: Review content
5. Create subject lines (Writing Agent) -> CHECKPOINT 3: Review tone & subjects
6. Format for email (Writing Agent)
7. Store in database -> CHECKPOINT 4: Final send approval
8. Send if approved (Email Service)
"""
import logging
from typing import Any, Dict, Optional

from app.common.base.orchestrator import BaseOrchestrator
from app.platforms.newsletter.orchestrator.state import (
    NewsletterState,
    create_initial_state,
)
from app.platforms.newsletter.orchestrator.graph import get_newsletter_graph
from app.platforms.newsletter.orchestrator.mongodb_saver import get_mongodb_saver

logger = logging.getLogger(__name__)


class NewsletterOrchestrator(BaseOrchestrator):
    """
    Orchestrator for the Newsletter platform using LangGraph.

    This orchestrator implements a multi-agent workflow with Human-in-the-Loop
    checkpoints at critical decision points.
    """

    def __init__(
        self,
        name: str = "Newsletter Orchestrator",
        description: str | None = None,
    ):
        super().__init__(
            name=name,
            description=description or "Coordinates the newsletter generation workflow with HITL checkpoints",
        )
        self._graph = None

    @property
    def graph(self):
        """Get or create the workflow graph."""
        if self._graph is None:
            self._graph = get_newsletter_graph(use_checkpointer=True)
        return self._graph

    async def initialize(self):
        """Initialize the orchestrator and LangGraph workflow."""
        await super().initialize()
        # Pre-initialize the graph
        _ = self.graph
        logger.info("Newsletter orchestrator initialized with LangGraph workflow")

    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the newsletter generation workflow.

        Args:
            input: Dictionary with generation parameters:
                - topics: List of topics to cover
                - tone: Newsletter tone (professional, casual, etc.)
                - custom_prompt: Optional custom prompt
                - user_id: User ID for personalization
                - max_articles: Maximum articles to include

        Returns:
            Dictionary with workflow_id and initial status
        """
        # Extract parameters
        user_id = input.get("user_id")
        topics = input.get("topics", [])
        tone = input.get("tone", "professional")
        custom_prompt = input.get("custom_prompt")
        max_articles = input.get("max_articles", 10)

        if not user_id:
            return {
                "success": False,
                "error": "user_id is required",
            }

        if not topics and not custom_prompt:
            return {
                "success": False,
                "error": "Either topics or custom_prompt is required",
            }

        # Create initial state
        initial_state = create_initial_state(
            user_id=user_id,
            topics=topics,
            tone=tone,
            custom_prompt=custom_prompt,
            max_articles=max_articles,
        )

        workflow_id = initial_state["workflow_id"]

        try:
            # Configure thread for this workflow
            config = {"configurable": {"thread_id": workflow_id}}

            # Start the workflow (will pause at first checkpoint)
            logger.info(f"Starting newsletter workflow: {workflow_id}")
            result = await self.graph.ainvoke(initial_state, config)

            # Check if we're at a checkpoint (workflow paused)
            state_snapshot = await self.graph.aget_state(config)

            if state_snapshot.next:
                # Workflow is paused at a checkpoint
                return {
                    "success": True,
                    "workflow_id": workflow_id,
                    "status": "awaiting_approval",
                    "current_checkpoint": result.get("current_checkpoint"),
                    "message": "Workflow paused at checkpoint",
                }
            else:
                # Workflow completed (shouldn't happen on first run)
                return {
                    "success": True,
                    "workflow_id": workflow_id,
                    "status": result.get("status", "completed"),
                    "message": "Workflow completed",
                }

        except Exception as e:
            logger.error(f"Error starting workflow {workflow_id}: {e}", exc_info=True)
            return {
                "success": False,
                "workflow_id": workflow_id,
                "status": "failed",
                "error": str(e),
            }

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get the status of a workflow.

        Args:
            workflow_id: The workflow ID

        Returns:
            Workflow status and state
        """
        try:
            config = {"configurable": {"thread_id": workflow_id}}
            state_snapshot = await self.graph.aget_state(config)

            if not state_snapshot.values:
                return {
                    "workflow_id": workflow_id,
                    "status": "not_found",
                    "error": "Workflow not found",
                }

            state = state_snapshot.values

            # Determine status based on state
            if state_snapshot.next:
                status = "awaiting_approval"
            else:
                status = state.get("status", "unknown")

            return {
                "workflow_id": workflow_id,
                "status": status,
                "current_step": state.get("current_step"),
                "current_checkpoint": state.get("current_checkpoint"),
                "checkpoints_completed": state.get("checkpoints_completed", []),
                "created_at": state.get("created_at"),
                "updated_at": state.get("updated_at"),
                "error": state.get("error"),
            }

        except Exception as e:
            logger.error(f"Error getting workflow status: {e}")
            return {
                "workflow_id": workflow_id,
                "status": "error",
                "error": str(e),
            }

    async def get_pending_checkpoint(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current pending checkpoint for a workflow.

        Args:
            workflow_id: The workflow ID

        Returns:
            Checkpoint data if workflow is paused, None otherwise
        """
        try:
            config = {"configurable": {"thread_id": workflow_id}}
            state_snapshot = await self.graph.aget_state(config)

            if not state_snapshot.values:
                return None

            # Check if workflow is paused at a checkpoint
            if not state_snapshot.next:
                return None

            state = state_snapshot.values
            checkpoint = state.get("current_checkpoint")

            if not checkpoint:
                # Build checkpoint from interrupt data
                # The interrupt value is stored in the state
                return {
                    "workflow_id": workflow_id,
                    "checkpoint_type": state_snapshot.next[0] if state_snapshot.next else "unknown",
                    "status": "awaiting_approval",
                }

            return {
                "workflow_id": workflow_id,
                **checkpoint,
            }

        except Exception as e:
            logger.error(f"Error getting pending checkpoint: {e}")
            return None

    async def approve_checkpoint(
        self,
        workflow_id: str,
        checkpoint_id: str,
        action: str,
        modifications: Optional[Dict[str, Any]] = None,
        feedback: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Approve, edit, or reject a checkpoint.

        Args:
            workflow_id: The workflow ID
            checkpoint_id: The checkpoint ID
            action: approve, edit, reject, send, schedule, or cancel
            modifications: Optional modifications for edit action
            feedback: Optional feedback for reject action

        Returns:
            Updated workflow status
        """
        try:
            config = {"configurable": {"thread_id": workflow_id}}

            # Build the response to resume the workflow
            response = {
                "action": action,
                "checkpoint_id": checkpoint_id,
            }

            if modifications:
                response.update(modifications)

            if feedback:
                response["feedback"] = feedback

            # Resume the workflow with the human response
            logger.info(f"Resuming workflow {workflow_id} with action: {action}")

            # Update state with the response and resume
            result = await self.graph.ainvoke(
                {"checkpoint_response": response},
                config,
            )

            # Check new state
            state_snapshot = await self.graph.aget_state(config)

            if state_snapshot.next:
                return {
                    "success": True,
                    "workflow_id": workflow_id,
                    "status": "awaiting_approval",
                    "current_checkpoint": result.get("current_checkpoint"),
                    "message": f"Checkpoint {action}d, workflow paused at next checkpoint",
                }
            else:
                return {
                    "success": True,
                    "workflow_id": workflow_id,
                    "status": result.get("status", "completed"),
                    "message": "Workflow completed",
                }

        except Exception as e:
            logger.error(f"Error approving checkpoint: {e}", exc_info=True)
            return {
                "success": False,
                "workflow_id": workflow_id,
                "status": "error",
                "error": str(e),
            }

    async def cancel_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Cancel a running workflow.

        Args:
            workflow_id: The workflow ID

        Returns:
            Cancellation status
        """
        try:
            config = {"configurable": {"thread_id": workflow_id}}

            # Update state to cancelled
            await self.graph.aupdate_state(
                config,
                {"status": "cancelled"},
            )

            # Optionally delete the thread
            saver = get_mongodb_saver()
            await saver.adelete_thread(workflow_id)

            logger.info(f"Cancelled workflow: {workflow_id}")

            return {
                "success": True,
                "workflow_id": workflow_id,
                "status": "cancelled",
                "message": "Workflow cancelled",
            }

        except Exception as e:
            logger.error(f"Error cancelling workflow: {e}")
            return {
                "success": False,
                "workflow_id": workflow_id,
                "status": "error",
                "error": str(e),
            }

    async def list_workflows(
        self,
        user_id: str | None = None,
        status: str | None = None,
        limit: int = 10,
    ) -> list[Dict[str, Any]]:
        """
        List workflows, optionally filtered.

        Args:
            user_id: Filter by user ID
            status: Filter by status
            limit: Maximum number to return

        Returns:
            List of workflow summaries
        """
        try:
            saver = get_mongodb_saver()

            filter_dict = {}
            if user_id:
                filter_dict["user_id"] = user_id
            if status:
                filter_dict["status"] = status

            workflows = []
            async for checkpoint in saver.alist(None, filter=filter_dict, limit=limit):
                state = checkpoint.checkpoint.get("channel_values", {})
                workflows.append({
                    "workflow_id": checkpoint.config["configurable"]["thread_id"],
                    "status": state.get("status", "unknown"),
                    "created_at": state.get("created_at"),
                    "updated_at": state.get("updated_at"),
                })

            return workflows

        except Exception as e:
            logger.error(f"Error listing workflows: {e}")
            return []


# Singleton instance
_orchestrator: NewsletterOrchestrator | None = None


def get_newsletter_orchestrator() -> NewsletterOrchestrator:
    """Get or create the newsletter orchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = NewsletterOrchestrator()
    return _orchestrator


__all__ = ["NewsletterOrchestrator", "get_newsletter_orchestrator"]
