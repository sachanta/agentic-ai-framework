"""
Newsletter Router stub tests.

These tests verify Phase 1 API endpoint behavior.
Some tests are stable (GET endpoints), others are stubs that will change.

Markers:
- @pytest.mark.stable: Tests for endpoints that won't change
- @pytest.mark.phase1_stub: Tests for stub responses that will change after Phase 10
"""
import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.stable
class TestStatusEndpoint:
    """Test GET /status endpoint - stable across phases."""

    def test_status_returns_200(self, test_client):
        """Test that /status returns 200 OK."""
        response = test_client.get("/api/v1/platforms/newsletter/status")
        assert response.status_code == 200

    def test_status_returns_platform_id(self, test_client):
        """Test that /status returns correct platform_id."""
        response = test_client.get("/api/v1/platforms/newsletter/status")
        data = response.json()
        assert data["platform_id"] == "newsletter"

    def test_status_returns_name(self, test_client):
        """Test that /status returns platform name."""
        response = test_client.get("/api/v1/platforms/newsletter/status")
        data = response.json()
        assert data["name"] == "Newsletter"

    def test_status_returns_version(self, test_client):
        """Test that /status returns version."""
        response = test_client.get("/api/v1/platforms/newsletter/status")
        data = response.json()
        assert data["version"] == "1.0.0"

    def test_status_returns_agents_list(self, test_client):
        """Test that /status returns agents list."""
        response = test_client.get("/api/v1/platforms/newsletter/status")
        data = response.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)
        assert len(data["agents"]) == 4  # research, writing, preference, custom_prompt

    def test_status_includes_llm_info(self, test_client):
        """Test that /status includes LLM provider and model."""
        response = test_client.get("/api/v1/platforms/newsletter/status")
        data = response.json()
        assert "llm_provider" in data
        assert "llm_model" in data


@pytest.mark.stable
class TestConfigEndpoint:
    """Test GET /config endpoint - stable across phases."""

    def test_config_returns_200(self, test_client):
        """Test that /config returns 200 OK."""
        response = test_client.get("/api/v1/platforms/newsletter/config")
        assert response.status_code == 200

    def test_config_returns_platform_id(self, test_client):
        """Test that /config returns platform_id."""
        response = test_client.get("/api/v1/platforms/newsletter/config")
        data = response.json()
        assert data["platform_id"] == "newsletter"

    def test_config_returns_llm_section(self, test_client):
        """Test that /config returns llm configuration section."""
        response = test_client.get("/api/v1/platforms/newsletter/config")
        data = response.json()
        assert "llm" in data
        assert "provider" in data["llm"]
        assert "model" in data["llm"]
        assert "temperature" in data["llm"]
        assert "max_tokens" in data["llm"]

    def test_config_returns_search_section(self, test_client):
        """Test that /config returns search configuration section."""
        response = test_client.get("/api/v1/platforms/newsletter/config")
        data = response.json()
        assert "search" in data
        assert "depth" in data["search"]
        assert "max_results_per_topic" in data["search"]

    def test_config_returns_content_section(self, test_client):
        """Test that /config returns content configuration section."""
        response = test_client.get("/api/v1/platforms/newsletter/config")
        data = response.json()
        assert "content" in data
        assert "max_articles" in data["content"]
        assert "default_tone" in data["content"]

    def test_config_returns_email_section(self, test_client):
        """Test that /config returns email configuration section."""
        response = test_client.get("/api/v1/platforms/newsletter/config")
        data = response.json()
        assert "email" in data
        assert "from_email" in data["email"]
        assert "from_name" in data["email"]


@pytest.mark.stable
class TestHealthEndpoint:
    """Test GET /health endpoint - stable across phases."""

    def test_health_returns_200(self, test_client):
        """Test that /health returns 200 OK."""
        response = test_client.get("/api/v1/platforms/newsletter/health")
        assert response.status_code == 200

    def test_health_returns_platform_status(self, test_client):
        """Test that /health returns platform status."""
        response = test_client.get("/api/v1/platforms/newsletter/health")
        data = response.json()
        assert "platform" in data

    def test_health_returns_llm_status(self, test_client):
        """Test that /health returns LLM status."""
        response = test_client.get("/api/v1/platforms/newsletter/health")
        data = response.json()
        assert "llm" in data
        assert "status" in data["llm"]

    def test_health_returns_services_status(self, test_client):
        """Test that /health returns external services status."""
        response = test_client.get("/api/v1/platforms/newsletter/health")
        data = response.json()
        assert "services" in data
        assert "tavily" in data["services"]
        assert "resend" in data["services"]


@pytest.mark.stable
class TestAgentsEndpoint:
    """Test GET /agents endpoint - stable across phases."""

    def test_agents_returns_200(self, test_client):
        """Test that /agents returns 200 OK."""
        response = test_client.get("/api/v1/platforms/newsletter/agents")
        assert response.status_code == 200

    def test_agents_returns_list(self, test_client):
        """Test that /agents returns a list."""
        response = test_client.get("/api/v1/platforms/newsletter/agents")
        data = response.json()
        assert isinstance(data, list)

    def test_agents_returns_four_agents(self, test_client):
        """Test that /agents returns 4 agents (after mindmap removal)."""
        response = test_client.get("/api/v1/platforms/newsletter/agents")
        data = response.json()
        assert len(data) == 4

    def test_agents_have_required_fields(self, test_client):
        """Test that each agent has required fields."""
        response = test_client.get("/api/v1/platforms/newsletter/agents")
        data = response.json()

        for agent in data:
            assert "id" in agent
            assert "name" in agent
            assert "description" in agent
            assert "status" in agent

    def test_agents_include_expected_ids(self, test_client):
        """Test that expected agent IDs are present (4 agents after mindmap removal)."""
        response = test_client.get("/api/v1/platforms/newsletter/agents")
        data = response.json()

        agent_ids = {agent["id"] for agent in data}
        expected_ids = {"research", "writing", "preference", "custom_prompt"}
        assert agent_ids == expected_ids


@pytest.mark.phase1_stub
class TestAgentsEndpointStub:
    """Test Phase 1 specific agent status - will change after Phase 6-9."""

    @pytest.mark.skip(reason="Agent status now varies - research/writing/preference/custom_prompt are implemented")
    def test_all_agents_pending_status(self, test_client):
        """Test that all agents have 'pending' status in Phase 1."""
        response = test_client.get("/api/v1/platforms/newsletter/agents")
        data = response.json()

        for agent in data:
            assert agent["status"] == "pending", f"Agent {agent['id']} should be pending"


@pytest.mark.phase1_stub
class TestGenerateEndpointStub:
    """Test POST /newsletters/generate stub behavior."""

    def test_generate_requires_auth(self, test_client):
        """Test that /newsletters/generate requires authentication."""
        response = test_client.post(
            "/api/v1/platforms/newsletter/newsletters/generate",
            json={"topics": ["AI"]},
        )
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403, 422]

    def test_generate_returns_workflow_id(self, authenticated_client, valid_generate_request):
        """Test that generate returns a workflow_id (stub)."""
        with patch("app.platforms.newsletter.router.NewsletterService") as MockService:
            mock_instance = MockService.return_value
            mock_instance.generate_newsletter = AsyncMock(return_value={
                "workflow_id": "test-wf-id",
                "status": "not_implemented",
                "message": "Stub response",
            })

            response = authenticated_client.post(
                "/api/v1/platforms/newsletter/newsletters/generate",
                json=valid_generate_request,
            )

            assert response.status_code == 200
            data = response.json()
            assert "workflow_id" in data

    def test_generate_returns_status(self, authenticated_client, valid_generate_request):
        """Test that generate returns status field."""
        with patch("app.platforms.newsletter.router.NewsletterService") as MockService:
            mock_instance = MockService.return_value
            mock_instance.generate_newsletter = AsyncMock(return_value={
                "workflow_id": "test-wf-id",
                "status": "not_implemented",
                "message": "Stub",
            })

            response = authenticated_client.post(
                "/api/v1/platforms/newsletter/newsletters/generate",
                json=valid_generate_request,
            )

            data = response.json()
            assert "status" in data


@pytest.mark.phase1_stub
class TestWorkflowEndpointsStub:
    """Test workflow endpoint stub behavior."""

    def test_get_workflow_status_404_for_nonexistent(self, authenticated_client):
        """Test that getting non-existent workflow returns 404."""
        with patch("app.platforms.newsletter.router.NewsletterService") as MockService:
            mock_instance = MockService.return_value
            mock_instance.get_workflow_status = AsyncMock(return_value=None)

            response = authenticated_client.get(
                "/api/v1/platforms/newsletter/workflows/nonexistent-id"
            )

            assert response.status_code == 404

    def test_get_checkpoint_404_when_none_pending(self, authenticated_client):
        """Test that getting checkpoint returns 404 when none pending."""
        with patch("app.platforms.newsletter.router.NewsletterService") as MockService:
            mock_instance = MockService.return_value
            mock_instance.get_pending_checkpoint = AsyncMock(return_value=None)

            response = authenticated_client.get(
                "/api/v1/platforms/newsletter/workflows/wf-123/checkpoint"
            )

            assert response.status_code == 404

    def test_approve_checkpoint_accepts_request(self, authenticated_client, valid_approve_request):
        """Test that approve endpoint accepts valid request."""
        with patch("app.platforms.newsletter.router.NewsletterService") as MockService:
            mock_instance = MockService.return_value
            mock_instance.approve_checkpoint = AsyncMock(return_value={
                "workflow_id": "wf-123",
                "status": "not_implemented",
            })

            response = authenticated_client.post(
                "/api/v1/platforms/newsletter/workflows/wf-123/approve",
                json=valid_approve_request,
            )

            assert response.status_code == 200

    def test_cancel_workflow_accepts_request(self, authenticated_client):
        """Test that cancel endpoint accepts request."""
        with patch("app.platforms.newsletter.router.NewsletterService") as MockService:
            mock_instance = MockService.return_value
            mock_instance.cancel_workflow = AsyncMock(return_value={
                "workflow_id": "wf-123",
                "status": "cancelled",
            })

            response = authenticated_client.post(
                "/api/v1/platforms/newsletter/workflows/wf-123/cancel"
            )

            assert response.status_code == 200
