"""
Hello World Orchestrator - Coordinates the Hello World platform workflow.
"""
from typing import Any, Dict

from app.common.base.orchestrator import BaseOrchestrator
from app.platforms.hello_world.agents.greeter import GreeterAgent


class HelloWorldOrchestrator(BaseOrchestrator):
    """
    Orchestrator for the Hello World platform.

    This is a simple orchestrator that demonstrates the pattern for
    coordinating multiple agents in a workflow.
    """

    def __init__(self, name: str = "Hello World Orchestrator", description: str = None):
        super().__init__(
            name=name,
            description=description or "Coordinates the Hello World greeting workflow",
        )
        self._setup_agents()

    def _setup_agents(self):
        """Initialize and register agents."""
        greeter = GreeterAgent()
        self.register_agent(greeter)

    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Hello World workflow.

        Args:
            input: Dictionary with 'name' and optional 'style' keys

        Returns:
            Dictionary with greeting result
        """
        name = input.get("name", "World")
        style = input.get("style", "friendly")

        # Get the greeter agent and run it
        greeter = self.get_agent("greeter")
        if not greeter:
            return {"error": "Greeter agent not found"}

        result = await greeter.run({
            "name": name,
            "style": style,
        })

        return {
            "greeting": result.get("greeting"),
            "agent": "greeter",
            "orchestrator": self.name,
            "metadata": result.get("metadata", {}),
        }
