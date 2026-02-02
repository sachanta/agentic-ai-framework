"""
Newsletter Platform import validation tests.

These tests verify that all modules can be imported without errors.
Marked as @stable - these tests should pass across all phases.
"""
import pytest


@pytest.mark.stable
class TestModuleImports:
    """Test that all newsletter platform modules can be imported."""

    def test_import_platform_init(self):
        """Test importing the main platform module."""
        from app.platforms.newsletter import register_platform, NewsletterOrchestrator
        assert callable(register_platform)
        assert NewsletterOrchestrator is not None

    def test_import_config(self):
        """Test importing the config module."""
        from app.platforms.newsletter.config import NewsletterConfig, config
        assert NewsletterConfig is not None
        assert config is not None

    def test_import_schemas(self):
        """Test importing schema classes."""
        from app.platforms.newsletter.schemas import (
            NewsletterStatus,
            Tone,
            Frequency,
            GenerateNewsletterRequest,
            CustomPromptRequest,
            GenerateNewsletterResponse,
            NewsletterResponse,
            PlatformStatusResponse,
            AgentInfo,
            WorkflowStatusResponse,
            CheckpointResponse,
            ApproveCheckpointRequest,
        )
        # Verify enums have expected values
        assert NewsletterStatus.DRAFT == "draft"
        assert Tone.PROFESSIONAL == "professional"
        assert Frequency.WEEKLY == "weekly"

    def test_import_orchestrator(self):
        """Test importing the orchestrator."""
        from app.platforms.newsletter.orchestrator import NewsletterOrchestrator
        assert NewsletterOrchestrator is not None

    def test_import_services(self):
        """Test importing services."""
        from app.platforms.newsletter.services import NewsletterService
        assert NewsletterService is not None

    def test_import_router(self):
        """Test importing the router."""
        from app.platforms.newsletter.router import router
        assert router is not None

    def test_import_agents_module(self):
        """Test importing the agents module (stub)."""
        from app.platforms.newsletter import agents
        assert agents is not None

    def test_import_models_module(self):
        """Test importing the models module (stub)."""
        from app.platforms.newsletter import models
        assert models is not None

    def test_import_repositories_module(self):
        """Test importing the repositories module (stub)."""
        from app.platforms.newsletter import repositories
        assert repositories is not None


@pytest.mark.stable
class TestNoCircularImports:
    """Test that there are no circular import issues."""

    def test_full_import_chain(self):
        """Test importing all modules in sequence."""
        # This will fail if there are circular imports
        from app.platforms.newsletter import register_platform
        from app.platforms.newsletter.config import config
        from app.platforms.newsletter.schemas import GenerateNewsletterRequest
        from app.platforms.newsletter.orchestrator import NewsletterOrchestrator
        from app.platforms.newsletter.services import NewsletterService
        from app.platforms.newsletter.router import router

        # All imports should succeed
        assert all([
            register_platform,
            config,
            GenerateNewsletterRequest,
            NewsletterOrchestrator,
            NewsletterService,
            router,
        ])

    def test_reverse_import_chain(self):
        """Test importing modules in reverse order."""
        from app.platforms.newsletter.router import router
        from app.platforms.newsletter.services import NewsletterService
        from app.platforms.newsletter.orchestrator import NewsletterOrchestrator
        from app.platforms.newsletter.schemas import GenerateNewsletterRequest
        from app.platforms.newsletter.config import config
        from app.platforms.newsletter import register_platform

        assert all([
            router,
            NewsletterService,
            NewsletterOrchestrator,
            GenerateNewsletterRequest,
            config,
            register_platform,
        ])


@pytest.mark.stable
class TestExportedSymbols:
    """Test that __all__ exports are valid."""

    def test_schemas_exports(self):
        """Test that all exported schemas are importable."""
        from app.platforms.newsletter import schemas
        for name in schemas.__all__:
            assert hasattr(schemas, name), f"Missing export: {name}"

    def test_services_exports(self):
        """Test that all exported services are importable."""
        from app.platforms.newsletter import services
        for name in services.__all__:
            assert hasattr(services, name), f"Missing export: {name}"

    def test_platform_exports(self):
        """Test that platform __all__ exports are valid."""
        from app.platforms import newsletter
        for name in newsletter.__all__:
            assert hasattr(newsletter, name), f"Missing export: {name}"
