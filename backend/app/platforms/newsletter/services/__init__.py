"""
Newsletter Platform services.
"""
import logging
from typing import Dict, Any, Optional, List

from app.platforms.newsletter.orchestrator import NewsletterOrchestrator
from app.platforms.newsletter.config import config

logger = logging.getLogger(__name__)


class NewsletterService:
    """
    Service layer for the Newsletter platform.

    This service provides the business logic for the platform,
    coordinating between the API layer and the orchestrator/agents.
    """

    def __init__(self):
        self.orchestrator = NewsletterOrchestrator()
        self.config = config

    async def initialize(self):
        """Initialize the service and its components."""
        await self.orchestrator.initialize()

    async def cleanup(self):
        """Cleanup service resources."""
        await self.orchestrator.cleanup()

    async def generate_newsletter(
        self,
        user_id: str,
        topics: List[str],
        tone: str = "professional",
        max_articles: int = 10,
        custom_prompt: Optional[str] = None,
        include_mindmap: bool = True,
    ) -> Dict[str, Any]:
        """
        Start newsletter generation workflow.

        Args:
            user_id: The user ID
            topics: List of topics to cover
            tone: Newsletter tone
            max_articles: Maximum number of articles
            custom_prompt: Optional custom prompt
            include_mindmap: Whether to generate a mindmap

        Returns:
            Dictionary with workflow_id and status
        """
        result = await self.orchestrator.run({
            "user_id": user_id,
            "topics": topics,
            "tone": tone,
            "max_articles": max_articles,
            "custom_prompt": custom_prompt,
            "include_mindmap": include_mindmap,
        })
        return result

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the status of a workflow."""
        return await self.orchestrator.get_workflow_status(workflow_id)

    async def get_pending_checkpoint(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get pending checkpoint for a workflow."""
        return await self.orchestrator.get_pending_checkpoint(workflow_id)

    async def approve_checkpoint(
        self,
        workflow_id: str,
        checkpoint_id: str,
        action: str,
        modifications: Optional[Dict[str, Any]] = None,
        feedback: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Approve, edit, or reject a checkpoint."""
        return await self.orchestrator.approve_checkpoint(
            workflow_id, checkpoint_id, action, modifications, feedback
        )

    async def cancel_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Cancel a workflow."""
        return await self.orchestrator.cancel_workflow(workflow_id)

    async def get_status(self) -> Dict[str, Any]:
        """Get the platform status."""
        return {
            "platform_id": "newsletter",
            "name": "Newsletter",
            "status": "active" if self.config.ENABLED else "disabled",
            "agents": self.orchestrator.list_agents(),
        }

    async def check_llm_health(self) -> bool:
        """
        Check if the LLM provider is healthy.

        Returns:
            True if LLM is healthy and accessible
        """
        try:
            # Will be implemented when agents are ready
            return True
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            return False

    def get_llm_info(self) -> Dict[str, Any]:
        """
        Get information about the configured LLM.

        Returns:
            Dictionary with LLM provider and model info
        """
        return {
            "provider": self.config.effective_provider,
            "model": self.config.effective_model,
            "temperature": self.config.effective_temperature,
            "max_tokens": self.config.effective_max_tokens,
        }


__all__ = ["NewsletterService"]
