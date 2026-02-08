"""
Tests for Newsletter Workflow State.
"""
import pytest
from datetime import datetime

from app.platforms.newsletter.orchestrator.state import (
    NewsletterState,
    ArticleData,
    CheckpointData,
    create_initial_state,
    add_history_entry,
)


class TestNewsletterState:
    """Tests for NewsletterState TypedDict."""

    def test_newsletter_state_import(self):
        """Can import NewsletterState."""
        assert NewsletterState is not None

    def test_newsletter_state_is_typeddict(self):
        """NewsletterState is a TypedDict."""
        # TypedDict creates a class with __required_keys__ and __optional_keys__
        assert hasattr(NewsletterState, "__optional_keys__")

    def test_newsletter_state_has_user_id(self):
        """NewsletterState has user_id field."""
        assert "user_id" in NewsletterState.__optional_keys__

    def test_newsletter_state_has_topics(self):
        """NewsletterState has topics field."""
        assert "topics" in NewsletterState.__optional_keys__

    def test_newsletter_state_has_workflow_fields(self):
        """NewsletterState has workflow control fields."""
        assert "workflow_id" in NewsletterState.__optional_keys__
        assert "status" in NewsletterState.__optional_keys__
        assert "current_step" in NewsletterState.__optional_keys__

    def test_newsletter_state_has_checkpoint_fields(self):
        """NewsletterState has checkpoint fields."""
        assert "current_checkpoint" in NewsletterState.__optional_keys__
        assert "checkpoint_response" in NewsletterState.__optional_keys__
        assert "checkpoints_completed" in NewsletterState.__optional_keys__


class TestArticleData:
    """Tests for ArticleData TypedDict."""

    def test_article_data_import(self):
        """Can import ArticleData."""
        assert ArticleData is not None

    def test_article_data_has_required_fields(self):
        """ArticleData has expected fields."""
        assert "title" in ArticleData.__optional_keys__
        assert "url" in ArticleData.__optional_keys__
        assert "source" in ArticleData.__optional_keys__
        assert "summary" in ArticleData.__optional_keys__


class TestCheckpointData:
    """Tests for CheckpointData TypedDict."""

    def test_checkpoint_data_import(self):
        """Can import CheckpointData."""
        assert CheckpointData is not None

    def test_checkpoint_data_has_required_fields(self):
        """CheckpointData has expected fields."""
        assert "checkpoint_id" in CheckpointData.__optional_keys__
        assert "checkpoint_type" in CheckpointData.__optional_keys__
        assert "title" in CheckpointData.__optional_keys__
        assert "actions" in CheckpointData.__optional_keys__


class TestCreateInitialState:
    """Tests for create_initial_state function."""

    def test_create_initial_state_import(self):
        """Can import create_initial_state."""
        assert create_initial_state is not None

    def test_create_initial_state_basic(self):
        """create_initial_state creates state with basic fields."""
        state = create_initial_state(
            user_id="user123",
            topics=["tech", "ai"],
        )

        assert state["user_id"] == "user123"
        assert state["topics"] == ["tech", "ai"]
        assert state["tone"] == "professional"  # default

    def test_create_initial_state_with_tone(self):
        """create_initial_state respects tone parameter."""
        state = create_initial_state(
            user_id="user123",
            topics=["tech"],
            tone="casual",
        )

        assert state["tone"] == "casual"

    def test_create_initial_state_with_custom_prompt(self):
        """create_initial_state includes custom prompt."""
        state = create_initial_state(
            user_id="user123",
            topics=["tech"],
            custom_prompt="Focus on AI breakthroughs",
        )

        assert state["custom_prompt"] == "Focus on AI breakthroughs"

    def test_create_initial_state_with_max_articles(self):
        """create_initial_state respects max_articles."""
        state = create_initial_state(
            user_id="user123",
            topics=["tech"],
            max_articles=5,
        )

        assert state["max_articles"] == 5

    def test_create_initial_state_generates_workflow_id(self):
        """create_initial_state generates unique workflow_id."""
        state1 = create_initial_state(user_id="user1", topics=["tech"])
        state2 = create_initial_state(user_id="user1", topics=["tech"])

        assert state1["workflow_id"] != state2["workflow_id"]
        assert len(state1["workflow_id"]) == 36  # UUID format

    def test_create_initial_state_uses_provided_workflow_id(self):
        """create_initial_state uses provided workflow_id."""
        state = create_initial_state(
            user_id="user123",
            topics=["tech"],
            workflow_id="custom-id-123",
        )

        assert state["workflow_id"] == "custom-id-123"

    def test_create_initial_state_sets_running_status(self):
        """create_initial_state sets status to running."""
        state = create_initial_state(user_id="user123", topics=["tech"])

        assert state["status"] == "running"

    def test_create_initial_state_initializes_empty_articles(self):
        """create_initial_state starts with empty articles."""
        state = create_initial_state(user_id="user123", topics=["tech"])

        assert state["articles"] == []
        assert state["research_completed"] is False

    def test_create_initial_state_initializes_empty_content(self):
        """create_initial_state starts with empty content."""
        state = create_initial_state(user_id="user123", topics=["tech"])

        assert state["newsletter_content"] == ""
        assert state["content_generated"] is False

    def test_create_initial_state_initializes_timestamps(self):
        """create_initial_state sets timestamps."""
        state = create_initial_state(user_id="user123", topics=["tech"])

        assert "created_at" in state
        assert "updated_at" in state
        # Verify ISO format
        datetime.fromisoformat(state["created_at"])
        datetime.fromisoformat(state["updated_at"])


class TestAddHistoryEntry:
    """Tests for add_history_entry function."""

    def test_add_history_entry_import(self):
        """Can import add_history_entry."""
        assert add_history_entry is not None

    def test_add_history_entry_adds_entry(self):
        """add_history_entry adds entry to history."""
        state = create_initial_state(user_id="user123", topics=["tech"])
        updated = add_history_entry(state, "research", "completed")

        assert len(updated["history"]) == 1
        assert updated["history"][0]["step"] == "research"
        assert updated["history"][0]["status"] == "completed"

    def test_add_history_entry_includes_timestamp(self):
        """add_history_entry includes timestamp."""
        state = create_initial_state(user_id="user123", topics=["tech"])
        updated = add_history_entry(state, "research", "completed")

        assert "timestamp" in updated["history"][0]
        datetime.fromisoformat(updated["history"][0]["timestamp"])

    def test_add_history_entry_with_data(self):
        """add_history_entry includes optional data."""
        state = create_initial_state(user_id="user123", topics=["tech"])
        updated = add_history_entry(
            state, "research", "completed", data={"articles_found": 10}
        )

        assert updated["history"][0]["data"] == {"articles_found": 10}

    def test_add_history_entry_updates_updated_at(self):
        """add_history_entry updates updated_at timestamp."""
        state = create_initial_state(user_id="user123", topics=["tech"])
        original_updated_at = state["updated_at"]

        import time
        time.sleep(0.01)  # Small delay to ensure different timestamp

        updated = add_history_entry(state, "research", "completed")

        assert updated["updated_at"] != original_updated_at

    def test_add_history_entry_preserves_other_fields(self):
        """add_history_entry preserves existing state fields."""
        state = create_initial_state(user_id="user123", topics=["tech"])
        updated = add_history_entry(state, "research", "completed")

        assert updated["user_id"] == "user123"
        assert updated["topics"] == ["tech"]
        assert updated["workflow_id"] == state["workflow_id"]

    def test_add_history_entry_appends_multiple(self):
        """add_history_entry can add multiple entries."""
        state = create_initial_state(user_id="user123", topics=["tech"])

        state = add_history_entry(state, "preferences", "completed")
        state = add_history_entry(state, "research", "started")
        state = add_history_entry(state, "research", "completed")

        assert len(state["history"]) == 3
        assert state["history"][0]["step"] == "preferences"
        assert state["history"][1]["step"] == "research"
        assert state["history"][2]["step"] == "research"
