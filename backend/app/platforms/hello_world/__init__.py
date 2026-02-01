"""
Hello World Platform - A sample multi-agent platform for demonstration.

This platform demonstrates the structure and patterns for building
multi-agent platforms in the Agentic AI Framework.

Structure:
- orchestrator/: Coordinates the workflow between agents
- agents/: Individual agents with their own LLM, chain, and tools
- schemas/: Platform-specific request/response schemas
- services/: Platform-specific business logic
- tests/: Platform tests
"""
from app.platforms.hello_world.orchestrator import HelloWorldOrchestrator
from app.platforms.registry import get_platform_registry

# Register this platform with the registry
def register_platform():
    """Register the Hello World platform."""
    registry = get_platform_registry()
    registry.register(
        platform_id="hello-world",
        name="Hello World",
        description="A sample multi-agent platform for demonstration",
        orchestrator_class=HelloWorldOrchestrator,
        version="1.0.0",
        agents=["greeter"],
    )


__all__ = ["HelloWorldOrchestrator", "register_platform"]
