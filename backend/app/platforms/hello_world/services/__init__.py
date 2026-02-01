"""
Hello World Platform services.
"""
import logging
from typing import Dict, Any

from app.platforms.hello_world.orchestrator import HelloWorldOrchestrator

logger = logging.getLogger(__name__)


class HelloWorldService:
    """
    Service layer for the Hello World platform.

    This service provides the business logic for the platform,
    coordinating between the API layer and the orchestrator/agents.
    """

    def __init__(self):
        self.orchestrator = HelloWorldOrchestrator()

    async def initialize(self):
        """Initialize the service and its components."""
        await self.orchestrator.initialize()

    async def cleanup(self):
        """Cleanup service resources."""
        await self.orchestrator.cleanup()

    async def generate_greeting(
        self,
        name: str,
        style: str = "friendly",
    ) -> Dict[str, Any]:
        """
        Generate a personalized greeting.

        Args:
            name: The name to greet
            style: The greeting style (friendly, formal, casual, enthusiastic)

        Returns:
            Dictionary with greeting and metadata
        """
        result = await self.orchestrator.run({
            "name": name,
            "style": style,
        })
        return result

    async def get_status(self) -> Dict[str, Any]:
        """Get the platform status."""
        return {
            "platform_id": "hello-world",
            "name": "Hello World",
            "status": "active",
            "agents": self.orchestrator.list_agents(),
        }

    async def check_llm_health(self) -> bool:
        """
        Check if the LLM provider is healthy.

        Returns:
            True if LLM is healthy and accessible
        """
        try:
            greeter = self.orchestrator.get_agent("greeter")
            if greeter and greeter.llm:
                return await greeter.llm.health_check()
            return False
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            return False

    def get_llm_info(self) -> Dict[str, Any]:
        """
        Get information about the configured LLM.

        Returns:
            Dictionary with LLM provider and model info
        """
        greeter = self.orchestrator.get_agent("greeter")
        if hasattr(greeter, "get_llm_info"):
            return greeter.get_llm_info()
        return {}


__all__ = ["HelloWorldService"]
