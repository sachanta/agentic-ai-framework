"""
Newsletter Platform registration tests.

Tests for platform registration with the framework registry.
Marked as @stable - these tests should pass across all phases.
"""
import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.stable
class TestRegisterPlatformFunction:
    """Test the register_platform function."""

    def test_register_platform_is_callable(self):
        """Test that register_platform function exists and is callable."""
        from app.platforms.newsletter import register_platform
        assert callable(register_platform)

    def test_register_platform_calls_registry(self):
        """Test that register_platform calls the registry.register method."""
        with patch("app.platforms.newsletter.get_platform_registry") as mock_get:
            mock_registry = MagicMock()
            mock_get.return_value = mock_registry

            from app.platforms.newsletter import register_platform
            register_platform()

            mock_registry.register.assert_called_once()

    def test_register_platform_with_correct_id(self):
        """Test that platform is registered with correct ID."""
        with patch("app.platforms.newsletter.get_platform_registry") as mock_get:
            mock_registry = MagicMock()
            mock_get.return_value = mock_registry

            from app.platforms.newsletter import register_platform
            register_platform()

            call_kwargs = mock_registry.register.call_args.kwargs
            assert call_kwargs["platform_id"] == "newsletter"

    def test_register_platform_with_correct_name(self):
        """Test that platform is registered with correct name."""
        with patch("app.platforms.newsletter.get_platform_registry") as mock_get:
            mock_registry = MagicMock()
            mock_get.return_value = mock_registry

            from app.platforms.newsletter import register_platform
            register_platform()

            call_kwargs = mock_registry.register.call_args.kwargs
            assert call_kwargs["name"] == "Newsletter"

    def test_register_platform_with_version(self):
        """Test that platform is registered with a version."""
        with patch("app.platforms.newsletter.get_platform_registry") as mock_get:
            mock_registry = MagicMock()
            mock_get.return_value = mock_registry

            from app.platforms.newsletter import register_platform
            register_platform()

            call_kwargs = mock_registry.register.call_args.kwargs
            assert "version" in call_kwargs
            assert call_kwargs["version"] == "1.0.0"

    def test_register_platform_with_orchestrator_class(self):
        """Test that platform is registered with orchestrator class."""
        with patch("app.platforms.newsletter.get_platform_registry") as mock_get:
            mock_registry = MagicMock()
            mock_get.return_value = mock_registry

            from app.platforms.newsletter import register_platform
            from app.platforms.newsletter.orchestrator import NewsletterOrchestrator

            register_platform()

            call_kwargs = mock_registry.register.call_args.kwargs
            assert call_kwargs["orchestrator_class"] == NewsletterOrchestrator

    def test_register_platform_with_agents_list(self):
        """Test that platform is registered with agents list."""
        with patch("app.platforms.newsletter.get_platform_registry") as mock_get:
            mock_registry = MagicMock()
            mock_get.return_value = mock_registry

            from app.platforms.newsletter import register_platform
            register_platform()

            call_kwargs = mock_registry.register.call_args.kwargs
            assert "agents" in call_kwargs
            agents = call_kwargs["agents"]

            # Check that expected agents are in the list
            # Using set comparison to be flexible about order
            expected_agents = {"research", "writing", "preference", "custom_prompt", "mindmap"}
            assert set(agents) == expected_agents

    def test_register_platform_has_description(self):
        """Test that platform is registered with a description."""
        with patch("app.platforms.newsletter.get_platform_registry") as mock_get:
            mock_registry = MagicMock()
            mock_get.return_value = mock_registry

            from app.platforms.newsletter import register_platform
            register_platform()

            call_kwargs = mock_registry.register.call_args.kwargs
            assert "description" in call_kwargs
            assert len(call_kwargs["description"]) > 0


@pytest.mark.stable
class TestNewsletterOrchestratorExport:
    """Test that NewsletterOrchestrator is properly exported."""

    def test_orchestrator_exported_from_package(self):
        """Test that NewsletterOrchestrator is exported from main package."""
        from app.platforms.newsletter import NewsletterOrchestrator
        assert NewsletterOrchestrator is not None

    def test_orchestrator_in_all(self):
        """Test that NewsletterOrchestrator is in __all__."""
        from app.platforms import newsletter
        assert "NewsletterOrchestrator" in newsletter.__all__

    def test_register_platform_in_all(self):
        """Test that register_platform is in __all__."""
        from app.platforms import newsletter
        assert "register_platform" in newsletter.__all__


@pytest.mark.stable
class TestPlatformMetadata:
    """Test platform metadata consistency."""

    def test_platform_id_matches_router_prefix(self):
        """Test that platform ID is consistent with expected router prefix."""
        with patch("app.platforms.newsletter.get_platform_registry") as mock_get:
            mock_registry = MagicMock()
            mock_get.return_value = mock_registry

            from app.platforms.newsletter import register_platform
            register_platform()

            call_kwargs = mock_registry.register.call_args.kwargs
            # Platform ID should be suitable for URL (no spaces, lowercase)
            platform_id = call_kwargs["platform_id"]
            assert platform_id == platform_id.lower()
            assert " " not in platform_id

    def test_version_format(self):
        """Test that version follows semantic versioning format."""
        with patch("app.platforms.newsletter.get_platform_registry") as mock_get:
            mock_registry = MagicMock()
            mock_get.return_value = mock_registry

            from app.platforms.newsletter import register_platform
            register_platform()

            call_kwargs = mock_registry.register.call_args.kwargs
            version = call_kwargs["version"]

            # Check semantic versioning pattern (X.Y.Z)
            parts = version.split(".")
            assert len(parts) == 3
            for part in parts:
                assert part.isdigit()

    def test_agents_list_not_empty(self):
        """Test that agents list is not empty."""
        with patch("app.platforms.newsletter.get_platform_registry") as mock_get:
            mock_registry = MagicMock()
            mock_get.return_value = mock_registry

            from app.platforms.newsletter import register_platform
            register_platform()

            call_kwargs = mock_registry.register.call_args.kwargs
            assert len(call_kwargs["agents"]) > 0

    def test_agents_are_strings(self):
        """Test that all agent IDs are strings."""
        with patch("app.platforms.newsletter.get_platform_registry") as mock_get:
            mock_registry = MagicMock()
            mock_get.return_value = mock_registry

            from app.platforms.newsletter import register_platform
            register_platform()

            call_kwargs = mock_registry.register.call_args.kwargs
            for agent in call_kwargs["agents"]:
                assert isinstance(agent, str)
                assert len(agent) > 0
