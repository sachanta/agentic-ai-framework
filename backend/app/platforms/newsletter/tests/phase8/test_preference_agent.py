"""
Tests for Preference Agent.

Tests agent initialization, preference management, and analysis.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone


class TestPreferenceAgentInitialization:
    """Tests for PreferenceAgent initialization."""

    def test_agent_initializes_with_default_dependencies(self):
        """Ensure agent initializes with default memory service."""
        with patch("app.platforms.newsletter.agents.preference.agent.get_preference_llm") as mock_llm, \
             patch("app.platforms.newsletter.agents.preference.agent.get_memory_service") as mock_memory:

            mock_llm.return_value = MagicMock()
            mock_memory.return_value = MagicMock()

            from app.platforms.newsletter.agents.preference.agent import PreferenceAgent

            agent = PreferenceAgent()

            assert agent.name == "preference"
            mock_memory.assert_called_once()

    def test_agent_accepts_custom_memory_service(self):
        """Test that agent accepts custom memory service."""
        with patch("app.platforms.newsletter.agents.preference.agent.get_preference_llm") as mock_llm:

            mock_llm.return_value = MagicMock()
            custom_memory = MagicMock()

            from app.platforms.newsletter.agents.preference.agent import PreferenceAgent

            agent = PreferenceAgent(memory_service=custom_memory)

            assert agent._memory_service == custom_memory

    def test_agent_has_valid_tones(self):
        """Test that agent defines valid tones."""
        from app.platforms.newsletter.agents.preference.agent import PreferenceAgent

        assert "professional" in PreferenceAgent.VALID_TONES
        assert "casual" in PreferenceAgent.VALID_TONES
        assert "formal" in PreferenceAgent.VALID_TONES
        assert "enthusiastic" in PreferenceAgent.VALID_TONES

    def test_agent_has_valid_frequencies(self):
        """Test that agent defines valid frequencies."""
        from app.platforms.newsletter.agents.preference.agent import PreferenceAgent

        assert "daily" in PreferenceAgent.VALID_FREQUENCIES
        assert "weekly" in PreferenceAgent.VALID_FREQUENCIES
        assert "biweekly" in PreferenceAgent.VALID_FREQUENCIES
        assert "monthly" in PreferenceAgent.VALID_FREQUENCIES


class TestPreferenceAgentRun:
    """Tests for PreferenceAgent run() method."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mocked PreferenceAgent."""
        with patch("app.platforms.newsletter.agents.preference.agent.get_preference_llm") as mock_llm, \
             patch("app.platforms.newsletter.agents.preference.agent.get_memory_service") as mock_memory:

            mock_llm.return_value = MagicMock()
            mock_memory_instance = MagicMock()
            mock_memory_instance.get = AsyncMock(return_value=None)
            mock_memory_instance.set = AsyncMock(return_value=None)
            mock_memory.return_value = mock_memory_instance

            from app.platforms.newsletter.agents.preference.agent import PreferenceAgent

            agent = PreferenceAgent()
            yield agent

    @pytest.mark.asyncio
    async def test_run_requires_user_id(self, mock_agent):
        """Test that run requires user_id."""
        result = await mock_agent.run({})

        assert result["success"] is False
        assert "user_id" in result["error"]

    @pytest.mark.asyncio
    async def test_run_get_action_returns_preferences(self, mock_agent):
        """Test get action returns user preferences."""
        result = await mock_agent.run({
            "action": "get",
            "user_id": "test_user",
        })

        assert result["success"] is True
        assert "preferences" in result
        assert result["preferences"]["user_id"] == "test_user"

    @pytest.mark.asyncio
    async def test_run_update_action_updates_preferences(self, mock_agent):
        """Test update action modifies preferences."""
        result = await mock_agent.run({
            "action": "update",
            "user_id": "test_user",
            "updates": {"tone": "casual"},
        })

        assert result["success"] is True
        assert result["preferences"]["tone"] == "casual"

    @pytest.mark.asyncio
    async def test_run_unknown_action_returns_error(self, mock_agent):
        """Test unknown action returns error."""
        result = await mock_agent.run({
            "action": "unknown_action",
            "user_id": "test_user",
        })

        assert result["success"] is False
        assert "Unknown action" in result["error"]


class TestPreferenceAgentGetPreferences:
    """Tests for get_preferences method."""

    @pytest.mark.asyncio
    async def test_get_preferences_returns_defaults_for_new_user(self):
        """Test that new users get default preferences."""
        with patch("app.platforms.newsletter.agents.preference.agent.get_preference_llm") as mock_llm, \
             patch("app.platforms.newsletter.agents.preference.agent.get_memory_service") as mock_memory:

            mock_llm.return_value = MagicMock()
            mock_memory_instance = MagicMock()
            mock_memory_instance.get = AsyncMock(return_value=None)
            mock_memory.return_value = mock_memory_instance

            from app.platforms.newsletter.agents.preference.agent import PreferenceAgent

            agent = PreferenceAgent()
            prefs = await agent.get_preferences("new_user")

            assert prefs.user_id == "new_user"
            assert prefs.tone == "professional"
            assert prefs.frequency == "weekly"

    @pytest.mark.asyncio
    async def test_get_preferences_returns_stored_preferences(self):
        """Test that stored preferences are returned."""
        stored_data = {
            "user_id": "existing_user",
            "topics": ["AI", "ML"],
            "tone": "casual",
            "frequency": "daily",
            "max_articles": 15,
            "include_summaries": True,
            "include_mindmap": False,
            "sources_blacklist": [],
            "sources_whitelist": [],
            "language": "en",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        with patch("app.platforms.newsletter.agents.preference.agent.get_preference_llm") as mock_llm, \
             patch("app.platforms.newsletter.agents.preference.agent.get_memory_service") as mock_memory:

            mock_llm.return_value = MagicMock()
            mock_memory_instance = MagicMock()
            mock_memory_instance.get = AsyncMock(return_value=stored_data)
            mock_memory.return_value = mock_memory_instance

            from app.platforms.newsletter.agents.preference.agent import PreferenceAgent

            agent = PreferenceAgent()
            prefs = await agent.get_preferences("existing_user")

            assert prefs.user_id == "existing_user"
            assert prefs.tone == "casual"
            assert prefs.topics == ["AI", "ML"]


class TestPreferenceAgentUpdatePreferences:
    """Tests for update_preferences method."""

    @pytest.mark.asyncio
    async def test_update_preferences_merges_partial_updates(self):
        """Test that partial updates are merged correctly."""
        with patch("app.platforms.newsletter.agents.preference.agent.get_preference_llm") as mock_llm, \
             patch("app.platforms.newsletter.agents.preference.agent.get_memory_service") as mock_memory:

            mock_llm.return_value = MagicMock()
            mock_memory_instance = MagicMock()
            mock_memory_instance.get = AsyncMock(return_value=None)
            mock_memory_instance.set = AsyncMock(return_value=None)
            mock_memory.return_value = mock_memory_instance

            from app.platforms.newsletter.agents.preference.agent import PreferenceAgent
            from app.platforms.newsletter.agents.preference.schemas import PreferenceUpdate

            agent = PreferenceAgent()

            # Update only tone
            updates = PreferenceUpdate(tone="casual")
            prefs = await agent.update_preferences("test_user", updates)

            assert prefs.tone == "casual"
            assert prefs.frequency == "weekly"  # Default preserved

    @pytest.mark.asyncio
    async def test_update_preferences_validates_tone(self):
        """Test that invalid tone is rejected."""
        with patch("app.platforms.newsletter.agents.preference.agent.get_preference_llm") as mock_llm, \
             patch("app.platforms.newsletter.agents.preference.agent.get_memory_service") as mock_memory:

            mock_llm.return_value = MagicMock()
            mock_memory_instance = MagicMock()
            mock_memory_instance.get = AsyncMock(return_value=None)
            mock_memory_instance.set = AsyncMock(return_value=None)
            mock_memory.return_value = mock_memory_instance

            from app.platforms.newsletter.agents.preference.agent import PreferenceAgent
            from app.platforms.newsletter.agents.preference.schemas import PreferenceUpdate

            agent = PreferenceAgent()

            # Try invalid tone
            updates = PreferenceUpdate(tone="invalid_tone")
            prefs = await agent.update_preferences("test_user", updates)

            # Should keep default
            assert prefs.tone == "professional"

    @pytest.mark.asyncio
    async def test_update_preferences_stores_to_memory(self):
        """Test that updates are stored in memory service."""
        with patch("app.platforms.newsletter.agents.preference.agent.get_preference_llm") as mock_llm, \
             patch("app.platforms.newsletter.agents.preference.agent.get_memory_service") as mock_memory:

            mock_llm.return_value = MagicMock()
            mock_memory_instance = MagicMock()
            mock_memory_instance.get = AsyncMock(return_value=None)
            mock_memory_instance.set = AsyncMock(return_value=None)
            mock_memory.return_value = mock_memory_instance

            from app.platforms.newsletter.agents.preference.agent import PreferenceAgent
            from app.platforms.newsletter.agents.preference.schemas import PreferenceUpdate

            agent = PreferenceAgent()

            updates = PreferenceUpdate(topics=["AI", "ML"])
            await agent.update_preferences("test_user", updates)

            # Verify set was called
            mock_memory_instance.set.assert_called_once()
            call_args = mock_memory_instance.set.call_args
            assert "preferences:test_user" in call_args[0][0]


class TestPreferenceAgentAnalyze:
    """Tests for analyze_preferences method."""

    @pytest.mark.asyncio
    async def test_analyze_preferences_returns_result(self):
        """Test that analysis returns a result object."""
        with patch("app.platforms.newsletter.agents.preference.agent.get_preference_llm") as mock_llm, \
             patch("app.platforms.newsletter.agents.preference.agent.get_memory_service") as mock_memory:

            mock_llm_instance = MagicMock()
            mock_llm_instance.generate = AsyncMock(return_value='{"insights": [], "engagement_summary": {}}')
            mock_llm.return_value = mock_llm_instance

            mock_memory_instance = MagicMock()
            mock_memory_instance.get = AsyncMock(return_value=None)
            mock_memory.return_value = mock_memory_instance

            from app.platforms.newsletter.agents.preference.agent import PreferenceAgent

            agent = PreferenceAgent()
            result = await agent.analyze_preferences("test_user")

            assert result.user_id == "test_user"
            assert hasattr(result, "insights")
            assert hasattr(result, "engagement_summary")

    @pytest.mark.asyncio
    async def test_analyze_preferences_handles_llm_error(self):
        """Test graceful handling of LLM errors."""
        with patch("app.platforms.newsletter.agents.preference.agent.get_preference_llm") as mock_llm, \
             patch("app.platforms.newsletter.agents.preference.agent.get_memory_service") as mock_memory:

            mock_llm_instance = MagicMock()
            mock_llm_instance.generate = AsyncMock(side_effect=Exception("LLM error"))
            mock_llm.return_value = mock_llm_instance

            mock_memory_instance = MagicMock()
            mock_memory_instance.get = AsyncMock(return_value=None)
            mock_memory.return_value = mock_memory_instance

            from app.platforms.newsletter.agents.preference.agent import PreferenceAgent

            agent = PreferenceAgent()
            result = await agent.analyze_preferences("test_user")

            # Should return result with error insight
            assert result.user_id == "test_user"
            assert len(result.insights) > 0
            assert result.insights[0].category == "error"


class TestPreferenceAgentRecommend:
    """Tests for recommend_preferences method."""

    @pytest.mark.asyncio
    async def test_recommend_preferences_returns_list(self):
        """Test that recommendations return a list."""
        with patch("app.platforms.newsletter.agents.preference.agent.get_preference_llm") as mock_llm, \
             patch("app.platforms.newsletter.agents.preference.agent.get_memory_service") as mock_memory:

            mock_llm_instance = MagicMock()
            mock_llm_instance.generate = AsyncMock(return_value='{"recommendations": [{"field": "topics", "current_value": [], "recommended_value": ["AI"], "reason": "Popular topic", "confidence": 0.8}]}')
            mock_llm.return_value = mock_llm_instance

            mock_memory_instance = MagicMock()
            mock_memory_instance.get = AsyncMock(return_value=None)
            mock_memory.return_value = mock_memory_instance

            from app.platforms.newsletter.agents.preference.agent import PreferenceAgent

            agent = PreferenceAgent()
            recommendations = await agent.recommend_preferences("test_user")

            assert isinstance(recommendations, list)

    @pytest.mark.asyncio
    async def test_recommend_preferences_handles_empty_response(self):
        """Test handling of empty recommendations."""
        with patch("app.platforms.newsletter.agents.preference.agent.get_preference_llm") as mock_llm, \
             patch("app.platforms.newsletter.agents.preference.agent.get_memory_service") as mock_memory:

            mock_llm_instance = MagicMock()
            mock_llm_instance.generate = AsyncMock(return_value='{"recommendations": []}')
            mock_llm.return_value = mock_llm_instance

            mock_memory_instance = MagicMock()
            mock_memory_instance.get = AsyncMock(return_value=None)
            mock_memory.return_value = mock_memory_instance

            from app.platforms.newsletter.agents.preference.agent import PreferenceAgent

            agent = PreferenceAgent()
            recommendations = await agent.recommend_preferences("test_user")

            assert recommendations == []


class TestPreferenceAgentLearn:
    """Tests for learn_from_engagement method."""

    @pytest.mark.asyncio
    async def test_learn_from_engagement_stores_engagement(self):
        """Test that engagement is stored."""
        with patch("app.platforms.newsletter.agents.preference.agent.get_preference_llm") as mock_llm, \
             patch("app.platforms.newsletter.agents.preference.agent.get_memory_service") as mock_memory:

            mock_llm.return_value = MagicMock()

            mock_memory_instance = MagicMock()
            mock_memory_instance.get = AsyncMock(return_value=None)
            mock_memory_instance.set = AsyncMock(return_value=None)
            mock_memory.return_value = mock_memory_instance

            from app.platforms.newsletter.agents.preference.agent import PreferenceAgent
            from app.platforms.newsletter.agents.preference.schemas import EngagementData

            agent = PreferenceAgent()

            engagement = EngagementData(
                newsletter_id="nl_123",
                user_id="test_user",
                opened=True,
                clicked_links=["url1"],
            )

            await agent.learn_from_engagement("test_user", engagement)

            # Verify engagement was stored
            mock_memory_instance.set.assert_called()

    @pytest.mark.asyncio
    async def test_learn_from_high_rating_triggers_learning(self):
        """Test that high rating triggers preference learning."""
        with patch("app.platforms.newsletter.agents.preference.agent.get_preference_llm") as mock_llm, \
             patch("app.platforms.newsletter.agents.preference.agent.get_memory_service") as mock_memory:

            mock_llm_instance = MagicMock()
            mock_llm_instance.generate = AsyncMock(return_value='{"updates": [], "skip_reason": "No strong signals"}')
            mock_llm.return_value = mock_llm_instance

            mock_memory_instance = MagicMock()
            mock_memory_instance.get = AsyncMock(return_value=None)
            mock_memory_instance.set = AsyncMock(return_value=None)
            mock_memory.return_value = mock_memory_instance

            from app.platforms.newsletter.agents.preference.agent import PreferenceAgent
            from app.platforms.newsletter.agents.preference.schemas import EngagementData

            agent = PreferenceAgent()

            # High rating should trigger learning
            engagement = EngagementData(
                newsletter_id="nl_123",
                user_id="test_user",
                opened=True,
                rating=5,
            )

            await agent.learn_from_engagement("test_user", engagement)

            # LLM should be called for learning
            mock_llm_instance.generate.assert_called()


class TestPreferenceAgentJsonParsing:
    """Tests for JSON parsing helper."""

    def test_parse_json_response_handles_plain_json(self):
        """Test parsing plain JSON."""
        with patch("app.platforms.newsletter.agents.preference.agent.get_preference_llm") as mock_llm, \
             patch("app.platforms.newsletter.agents.preference.agent.get_memory_service") as mock_memory:

            mock_llm.return_value = MagicMock()
            mock_memory.return_value = MagicMock()

            from app.platforms.newsletter.agents.preference.agent import PreferenceAgent

            agent = PreferenceAgent()

            result = agent._parse_json_response('{"key": "value"}')

            assert result == {"key": "value"}

    def test_parse_json_response_handles_code_blocks(self):
        """Test parsing JSON in markdown code blocks."""
        with patch("app.platforms.newsletter.agents.preference.agent.get_preference_llm") as mock_llm, \
             patch("app.platforms.newsletter.agents.preference.agent.get_memory_service") as mock_memory:

            mock_llm.return_value = MagicMock()
            mock_memory.return_value = MagicMock()

            from app.platforms.newsletter.agents.preference.agent import PreferenceAgent

            agent = PreferenceAgent()

            result = agent._parse_json_response('```json\n{"key": "value"}\n```')

            assert result == {"key": "value"}

    def test_parse_json_response_handles_invalid_json(self):
        """Test graceful handling of invalid JSON."""
        with patch("app.platforms.newsletter.agents.preference.agent.get_preference_llm") as mock_llm, \
             patch("app.platforms.newsletter.agents.preference.agent.get_memory_service") as mock_memory:

            mock_llm.return_value = MagicMock()
            mock_memory.return_value = MagicMock()

            from app.platforms.newsletter.agents.preference.agent import PreferenceAgent

            agent = PreferenceAgent()

            result = agent._parse_json_response("not valid json")

            assert result == {}


@pytest.mark.integration
class TestPreferenceAgentIntegration:
    """Integration tests for PreferenceAgent."""

    @pytest.mark.asyncio
    async def test_full_preference_workflow(self):
        """Test complete preference workflow."""
        pytest.skip("Integration test requires real services")
