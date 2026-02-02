"""
Newsletter Platform test configuration and fixtures.

Test Markers:
- @pytest.mark.stable: Tests that work across all phases
- @pytest.mark.phase1_stub: Tests for Phase 1 stub behavior (will fail after Phase 10)
- @pytest.mark.integration: Integration tests requiring running services
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Generator, AsyncGenerator

# Test markers configuration
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "stable: tests that work across all phases"
    )
    config.addinivalue_line(
        "markers", "phase1_stub: tests for Phase 1 stub behavior (will fail after Phase 10)"
    )
    config.addinivalue_line(
        "markers", "integration: integration tests requiring running services"
    )


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def newsletter_config():
    """Provide a fresh NewsletterConfig instance for testing."""
    from app.platforms.newsletter.config import NewsletterConfig
    return NewsletterConfig()


@pytest.fixture
def mock_global_settings():
    """Mock global settings for isolated config testing."""
    with patch("app.platforms.newsletter.config.settings") as mock_settings:
        mock_settings.LLM_PROVIDER = "openai"
        mock_settings.LLM_DEFAULT_MODEL = "gpt-4"
        mock_settings.LLM_TEMPERATURE = 0.7
        mock_settings.LLM_MAX_TOKENS = 4096
        yield mock_settings


# ============================================================================
# Service Fixtures
# ============================================================================

@pytest.fixture
def newsletter_service():
    """Provide a NewsletterService instance for testing."""
    from app.platforms.newsletter.services import NewsletterService
    return NewsletterService()


@pytest.fixture
def mock_orchestrator():
    """Provide a mocked orchestrator for service testing."""
    orchestrator = AsyncMock()
    orchestrator.run = AsyncMock(return_value={
        "workflow_id": "test-workflow-id",
        "status": "not_implemented",
        "message": "Newsletter orchestrator will be implemented in Phase 10",
    })
    orchestrator.get_workflow_status = AsyncMock(return_value={
        "workflow_id": "test-workflow-id",
        "status": "not_implemented",
    })
    orchestrator.get_pending_checkpoint = AsyncMock(return_value=None)
    orchestrator.approve_checkpoint = AsyncMock(return_value={
        "workflow_id": "test-workflow-id",
        "status": "not_implemented",
    })
    orchestrator.cancel_workflow = AsyncMock(return_value={
        "workflow_id": "test-workflow-id",
        "status": "cancelled",
    })
    orchestrator.list_agents = MagicMock(return_value=[])
    orchestrator.cleanup = AsyncMock()
    orchestrator.initialize = AsyncMock()
    return orchestrator


# ============================================================================
# API Testing Fixtures
# ============================================================================

def get_mock_current_user():
    """Mock user for testing authenticated endpoints."""
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "role": "user",
    }


@pytest.fixture
def test_client():
    """Provide a FastAPI test client for API testing."""
    from fastapi.testclient import TestClient
    from app.platforms.newsletter.router import router
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/platforms/newsletter")

    return TestClient(app)


@pytest.fixture
def authenticated_client():
    """Provide an authenticated test client with dependency override."""
    from fastapi.testclient import TestClient
    from app.platforms.newsletter.router import router
    from app.core.security import get_current_user
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/platforms/newsletter")

    # Override the dependency
    app.dependency_overrides[get_current_user] = get_mock_current_user

    client = TestClient(app)
    yield client

    # Cleanup
    app.dependency_overrides.clear()


# ============================================================================
# Schema Fixtures
# ============================================================================

@pytest.fixture
def valid_generate_request():
    """Provide a valid GenerateNewsletterRequest payload."""
    return {
        "topics": ["AI", "technology"],
        "tone": "professional",
        "max_articles": 10,
        "custom_prompt": None,
        "include_mindmap": True,
    }


@pytest.fixture
def valid_approve_request():
    """Provide a valid ApproveCheckpointRequest payload."""
    return {
        "checkpoint_id": "cp-123",
        "action": "approve",
        "modifications": None,
        "feedback": None,
    }


# ============================================================================
# Orchestrator Fixtures
# ============================================================================

@pytest.fixture
def newsletter_orchestrator():
    """Provide a NewsletterOrchestrator instance for testing."""
    from app.platforms.newsletter.orchestrator import NewsletterOrchestrator
    return NewsletterOrchestrator()


# ============================================================================
# Registry Fixtures
# ============================================================================

@pytest.fixture
def clean_registry():
    """Provide a clean platform registry for testing."""
    from app.platforms.registry import PlatformRegistry
    return PlatformRegistry()


@pytest.fixture
def mock_registry():
    """Mock the global registry for isolated testing."""
    with patch("app.platforms.newsletter.get_platform_registry") as mock_get:
        registry = MagicMock()
        registry.register = MagicMock()
        registry.get = MagicMock(return_value=None)
        mock_get.return_value = registry
        yield registry
