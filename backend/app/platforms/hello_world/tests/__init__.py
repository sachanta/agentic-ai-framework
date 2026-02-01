"""
Hello World Platform tests.

This module contains tests for the Hello World platform.
"""
import pytest


class TestHelloWorldPlatform:
    """Tests for the Hello World platform."""

    @pytest.mark.asyncio
    async def test_greeter_agent(self):
        """Test the greeter agent generates a greeting."""
        from app.platforms.hello_world.agents.greeter import GreeterAgent

        agent = GreeterAgent()
        result = await agent.run({"name": "Test User", "style": "friendly"})

        assert "greeting" in result
        assert "Test User" in result["greeting"]

    @pytest.mark.asyncio
    async def test_orchestrator(self):
        """Test the orchestrator coordinates the workflow."""
        from app.platforms.hello_world.orchestrator import HelloWorldOrchestrator

        orchestrator = HelloWorldOrchestrator()
        result = await orchestrator.run({"name": "Test User", "style": "formal"})

        assert "greeting" in result
        assert result["agent"] == "greeter"

    @pytest.mark.asyncio
    async def test_service(self):
        """Test the service layer."""
        from app.platforms.hello_world.services import HelloWorldService

        service = HelloWorldService()
        result = await service.generate_greeting("Test User", "casual")

        assert "greeting" in result
