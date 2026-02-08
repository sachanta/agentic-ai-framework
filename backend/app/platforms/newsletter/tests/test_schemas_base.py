"""
Newsletter Platform schema validation tests.

Tests for Phase 1 schemas only.
Marked as @stable - these tests should pass across all phases.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError


@pytest.mark.stable
class TestNewsletterStatusEnum:
    """Test NewsletterStatus enum values."""

    def test_all_status_values_exist(self):
        """Test that all expected status values are defined."""
        from app.platforms.newsletter.schemas import NewsletterStatus

        expected = ["draft", "generating", "pending_review", "ready",
                    "scheduled", "sending", "sent", "failed"]
        actual = [s.value for s in NewsletterStatus]

        for status in expected:
            assert status in actual, f"Missing status: {status}"

    def test_status_string_comparison(self):
        """Test that status enum can be compared to strings."""
        from app.platforms.newsletter.schemas import NewsletterStatus

        assert NewsletterStatus.DRAFT == "draft"
        assert NewsletterStatus.SENT == "sent"


@pytest.mark.stable
class TestToneEnum:
    """Test Tone enum values."""

    def test_all_tone_values_exist(self):
        """Test that all expected tone values are defined."""
        from app.platforms.newsletter.schemas import Tone

        expected = ["professional", "casual", "formal", "enthusiastic"]
        actual = [t.value for t in Tone]

        for tone in expected:
            assert tone in actual, f"Missing tone: {tone}"


@pytest.mark.stable
class TestFrequencyEnum:
    """Test Frequency enum values."""

    def test_all_frequency_values_exist(self):
        """Test that all expected frequency values are defined."""
        from app.platforms.newsletter.schemas import Frequency

        expected = ["daily", "weekly", "biweekly", "monthly"]
        actual = [f.value for f in Frequency]

        for freq in expected:
            assert freq in actual, f"Missing frequency: {freq}"


@pytest.mark.stable
class TestGenerateNewsletterRequest:
    """Test GenerateNewsletterRequest schema validation."""

    def test_valid_request_with_required_fields(self):
        """Test creating request with only required fields."""
        from app.platforms.newsletter.schemas import GenerateNewsletterRequest

        request = GenerateNewsletterRequest(topics=["AI", "technology"])

        assert request.topics == ["AI", "technology"]
        assert request.tone.value == "professional"  # default
        assert request.max_articles == 10  # default
        assert request.custom_prompt is None  # default

    def test_valid_request_with_all_fields(self):
        """Test creating request with all fields."""
        from app.platforms.newsletter.schemas import GenerateNewsletterRequest, Tone

        request = GenerateNewsletterRequest(
            topics=["AI", "healthcare"],
            tone=Tone.CASUAL,
            max_articles=5,
            custom_prompt="Focus on recent breakthroughs",
        )

        assert request.topics == ["AI", "healthcare"]
        assert request.tone == Tone.CASUAL
        assert request.max_articles == 5
        assert request.custom_prompt == "Focus on recent breakthroughs"

    def test_invalid_request_missing_topics(self):
        """Test that topics field is required."""
        from app.platforms.newsletter.schemas import GenerateNewsletterRequest

        with pytest.raises(ValidationError) as exc_info:
            GenerateNewsletterRequest()

        assert "topics" in str(exc_info.value)

    def test_invalid_tone_value(self):
        """Test that invalid tone value is rejected."""
        from app.platforms.newsletter.schemas import GenerateNewsletterRequest

        with pytest.raises(ValidationError):
            GenerateNewsletterRequest(topics=["AI"], tone="invalid_tone")

    def test_topics_accepts_list(self):
        """Test that topics accepts a list of strings."""
        from app.platforms.newsletter.schemas import GenerateNewsletterRequest

        request = GenerateNewsletterRequest(topics=["AI", "ML", "Data Science"])
        assert len(request.topics) == 3


@pytest.mark.stable
class TestCustomPromptRequest:
    """Test CustomPromptRequest schema validation."""

    def test_valid_request(self):
        """Test creating a valid custom prompt request."""
        from app.platforms.newsletter.schemas import CustomPromptRequest

        request = CustomPromptRequest(prompt="Write about AI trends")

        assert request.prompt == "Write about AI trends"

    def test_invalid_request_missing_prompt(self):
        """Test that prompt field is required."""
        from app.platforms.newsletter.schemas import CustomPromptRequest

        with pytest.raises(ValidationError) as exc_info:
            CustomPromptRequest()

        assert "prompt" in str(exc_info.value)


@pytest.mark.stable
class TestGenerateNewsletterResponse:
    """Test GenerateNewsletterResponse schema."""

    def test_valid_response(self):
        """Test creating a valid response."""
        from app.platforms.newsletter.schemas import GenerateNewsletterResponse

        response = GenerateNewsletterResponse(
            workflow_id="wf-123",
            status="running",
            message="Newsletter generation started",
        )

        assert response.workflow_id == "wf-123"
        assert response.status == "running"
        assert response.message == "Newsletter generation started"

    def test_response_serialization(self):
        """Test that response serializes to dict correctly."""
        from app.platforms.newsletter.schemas import GenerateNewsletterResponse

        response = GenerateNewsletterResponse(
            workflow_id="wf-123",
            status="running",
            message="Started",
        )

        data = response.model_dump()
        assert data["workflow_id"] == "wf-123"
        assert data["status"] == "running"


@pytest.mark.stable
class TestPlatformStatusResponse:
    """Test PlatformStatusResponse schema."""

    def test_valid_response(self):
        """Test creating a valid platform status response."""
        from app.platforms.newsletter.schemas import PlatformStatusResponse

        response = PlatformStatusResponse(
            platform_id="newsletter",
            name="Newsletter",
            status="active",
            agents=["research", "writing"],
            version="1.0.0",
            llm_provider="ollama",
            llm_model="llama3",
        )

        assert response.platform_id == "newsletter"
        assert response.agents == ["research", "writing"]
        assert response.version == "1.0.0"

    def test_required_fields(self):
        """Test that all fields are required."""
        from app.platforms.newsletter.schemas import PlatformStatusResponse

        with pytest.raises(ValidationError):
            PlatformStatusResponse(platform_id="newsletter")


@pytest.mark.stable
class TestWorkflowStatusResponse:
    """Test WorkflowStatusResponse schema."""

    def test_valid_response_minimal(self):
        """Test creating response with minimal fields."""
        from app.platforms.newsletter.schemas import WorkflowStatusResponse

        now = datetime.now()
        response = WorkflowStatusResponse(
            workflow_id="wf-123",
            status="running",
            created_at=now,
            updated_at=now,
        )

        assert response.workflow_id == "wf-123"
        assert response.current_checkpoint is None
        assert response.checkpoint_data is None

    def test_valid_response_with_checkpoint(self):
        """Test creating response with checkpoint data."""
        from app.platforms.newsletter.schemas import WorkflowStatusResponse

        now = datetime.now()
        response = WorkflowStatusResponse(
            workflow_id="wf-123",
            status="awaiting_approval",
            current_checkpoint="article_review",
            checkpoint_data={"articles": []},
            created_at=now,
            updated_at=now,
        )

        assert response.current_checkpoint == "article_review"
        assert response.checkpoint_data == {"articles": []}


@pytest.mark.stable
class TestCheckpointResponse:
    """Test CheckpointResponse schema."""

    def test_valid_response(self):
        """Test creating a valid checkpoint response."""
        from app.platforms.newsletter.schemas import CheckpointResponse

        response = CheckpointResponse(
            checkpoint_id="cp-123",
            checkpoint_type="article_review",
            title="Review Article Selection",
            description="Review and approve selected articles",
            data={"articles": [{"title": "AI News"}]},
            actions=["approve", "edit", "reject"],
        )

        assert response.checkpoint_id == "cp-123"
        assert response.checkpoint_type == "article_review"
        assert "approve" in response.actions
        assert response.metadata == {}  # default

    def test_response_with_metadata(self):
        """Test creating response with metadata."""
        from app.platforms.newsletter.schemas import CheckpointResponse

        response = CheckpointResponse(
            checkpoint_id="cp-123",
            checkpoint_type="article_review",
            title="Review",
            description="Review articles",
            data={},
            actions=["approve"],
            metadata={"step": 1, "total_steps": 4},
        )

        assert response.metadata["step"] == 1


@pytest.mark.stable
class TestApproveCheckpointRequest:
    """Test ApproveCheckpointRequest schema validation."""

    def test_valid_approve_request(self):
        """Test creating a valid approve request."""
        from app.platforms.newsletter.schemas import ApproveCheckpointRequest

        request = ApproveCheckpointRequest(
            checkpoint_id="cp-123",
            action="approve",
        )

        assert request.checkpoint_id == "cp-123"
        assert request.action == "approve"
        assert request.modifications is None
        assert request.feedback is None

    def test_valid_edit_request(self):
        """Test creating a valid edit request with modifications."""
        from app.platforms.newsletter.schemas import ApproveCheckpointRequest

        request = ApproveCheckpointRequest(
            checkpoint_id="cp-123",
            action="edit",
            modifications={"articles": [{"id": 1, "include": False}]},
        )

        assert request.action == "edit"
        assert request.modifications is not None

    def test_valid_reject_request(self):
        """Test creating a valid reject request with feedback."""
        from app.platforms.newsletter.schemas import ApproveCheckpointRequest

        request = ApproveCheckpointRequest(
            checkpoint_id="cp-123",
            action="reject",
            feedback="Articles are not relevant enough",
        )

        assert request.action == "reject"
        assert request.feedback == "Articles are not relevant enough"

    def test_required_fields(self):
        """Test that checkpoint_id and action are required."""
        from app.platforms.newsletter.schemas import ApproveCheckpointRequest

        with pytest.raises(ValidationError):
            ApproveCheckpointRequest(checkpoint_id="cp-123")

        with pytest.raises(ValidationError):
            ApproveCheckpointRequest(action="approve")


@pytest.mark.stable
class TestAgentInfo:
    """Test AgentInfo schema."""

    def test_valid_agent_info(self):
        """Test creating valid agent info."""
        from app.platforms.newsletter.schemas import AgentInfo

        agent = AgentInfo(
            id="research",
            name="Research Agent",
            description="Content discovery via Tavily",
            status="active",
        )

        assert agent.id == "research"
        assert agent.status == "active"
