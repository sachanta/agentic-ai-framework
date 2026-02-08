"""
Preference Agent implementation.

Manages user preferences and learns from engagement patterns.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.common.base.agent import BaseAgent
from app.platforms.newsletter.services.memory import get_memory_service, MemoryService
from app.platforms.newsletter.agents.preference.llm import (
    get_preference_llm,
    get_analysis_config,
    get_recommendation_config,
)
from app.platforms.newsletter.agents.preference.prompts import (
    PREFERENCE_SYSTEM_PROMPT,
    ANALYZE_PREFERENCES_PROMPT,
    RECOMMEND_PREFERENCES_PROMPT,
    LEARN_FROM_ENGAGEMENT_PROMPT,
    format_preferences_for_prompt,
    format_engagement_history,
)
from app.platforms.newsletter.agents.preference.schemas import (
    UserPreferences,
    PreferenceUpdate,
    EngagementData,
    PreferenceInsight,
    PreferenceRecommendation,
    PreferenceAnalysisResult,
)

logger = logging.getLogger(__name__)

# Storage key patterns
PREFERENCES_KEY = "preferences:{user_id}"
ENGAGEMENT_KEY = "engagement:{user_id}"


class PreferenceAgent(BaseAgent):
    """
    Agent for managing user preferences and learning from engagement.

    Stores preferences in MongoDB via MemoryService and uses LLM
    for analysis and recommendations.
    """

    VALID_TONES = ["professional", "casual", "formal", "enthusiastic"]
    VALID_FREQUENCIES = ["daily", "weekly", "biweekly", "monthly"]

    def __init__(self, memory_service: Optional[MemoryService] = None):
        """
        Initialize the Preference Agent.

        Args:
            memory_service: Optional memory service for storage.
                           If not provided, creates default instance.
        """
        llm = get_preference_llm()
        super().__init__(
            name="preference",
            description="Manages user preferences and learns from engagement patterns",
            llm=llm,
            system_prompt=PREFERENCE_SYSTEM_PROMPT,
        )
        self._memory_service = memory_service or get_memory_service()

    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point - routes to appropriate method.

        Args:
            input: Dict with 'action' and action-specific parameters.
                   Supported actions: get, update, analyze, recommend, learn

        Returns:
            Dict with success status and action-specific results.
        """
        action = input.get("action", "get")
        user_id = input.get("user_id")

        if not user_id:
            return {"success": False, "error": "user_id is required"}

        try:
            if action == "get":
                preferences = await self.get_preferences(user_id)
                return {"success": True, "preferences": preferences.to_dict()}

            elif action == "update":
                updates = input.get("updates", {})
                if isinstance(updates, dict):
                    updates = PreferenceUpdate(**updates)
                preferences = await self.update_preferences(user_id, updates)
                return {"success": True, "preferences": preferences.to_dict()}

            elif action == "analyze":
                result = await self.analyze_preferences(user_id)
                return {"success": True, "analysis": result.model_dump()}

            elif action == "recommend":
                recommendations = await self.recommend_preferences(user_id)
                return {
                    "success": True,
                    "recommendations": [r.model_dump() for r in recommendations],
                }

            elif action == "learn":
                engagement = input.get("engagement", {})
                if isinstance(engagement, dict):
                    engagement = EngagementData(**engagement)
                await self.learn_from_engagement(user_id, engagement)
                return {"success": True, "message": "Engagement recorded"}

            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"PreferenceAgent error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def get_preferences(self, user_id: str) -> UserPreferences:
        """
        Get user preferences with defaults fallback.

        Args:
            user_id: User identifier

        Returns:
            UserPreferences object (defaults if not found)
        """
        key = PREFERENCES_KEY.format(user_id=user_id)

        try:
            data = await self._memory_service.get(key)
            if data:
                return UserPreferences.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to get preferences for {user_id}: {e}")

        # Return defaults for new user
        return UserPreferences(user_id=user_id)

    async def update_preferences(
        self, user_id: str, updates: PreferenceUpdate
    ) -> UserPreferences:
        """
        Update specific preference fields.

        Args:
            user_id: User identifier
            updates: Partial preference updates

        Returns:
            Updated UserPreferences object
        """
        # Get current preferences
        preferences = await self.get_preferences(user_id)

        # Apply updates
        update_dict = updates.get_updates()
        for field, value in update_dict.items():
            if hasattr(preferences, field):
                # Validate specific fields
                if field == "tone" and value not in self.VALID_TONES:
                    logger.warning(f"Invalid tone '{value}', keeping current")
                    continue
                if field == "frequency" and value not in self.VALID_FREQUENCIES:
                    logger.warning(f"Invalid frequency '{value}', keeping current")
                    continue
                setattr(preferences, field, value)

        # Update timestamp
        preferences.updated_at = datetime.now(timezone.utc)

        # Store updated preferences
        key = PREFERENCES_KEY.format(user_id=user_id)
        await self._memory_service.set(key, preferences.to_dict(), ttl=None)

        return preferences

    async def analyze_preferences(self, user_id: str) -> PreferenceAnalysisResult:
        """
        Analyze preference patterns and engagement.

        Uses LLM to identify patterns in user behavior and preferences.

        Args:
            user_id: User identifier

        Returns:
            PreferenceAnalysisResult with insights
        """
        # Get preferences and engagement history
        preferences = await self.get_preferences(user_id)
        engagements = await self._get_engagement_history(user_id)

        # Format for LLM
        pref_str = format_preferences_for_prompt(preferences.to_dict())
        eng_str = format_engagement_history(engagements)

        # Build prompt
        prompt = ANALYZE_PREFERENCES_PROMPT.format(
            preferences=pref_str,
            engagement_history=eng_str,
        )

        try:
            # Call LLM
            config = get_analysis_config()
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=PREFERENCE_SYSTEM_PROMPT,
                temperature=config["temperature"],
                max_tokens=config["max_tokens"],
            )

            # Parse response
            result = self._parse_json_response(response)

            insights = [
                PreferenceInsight(**i) for i in result.get("insights", [])
            ]

            return PreferenceAnalysisResult(
                user_id=user_id,
                insights=insights,
                engagement_summary=result.get("engagement_summary", {}),
            )

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            # Return empty result on failure
            return PreferenceAnalysisResult(
                user_id=user_id,
                insights=[
                    PreferenceInsight(
                        category="error",
                        message="Analysis could not be completed",
                        confidence=0.0,
                    )
                ],
            )

    async def recommend_preferences(
        self, user_id: str
    ) -> List[PreferenceRecommendation]:
        """
        Generate preference change recommendations.

        Args:
            user_id: User identifier

        Returns:
            List of PreferenceRecommendation objects
        """
        # First analyze
        analysis = await self.analyze_preferences(user_id)
        preferences = await self.get_preferences(user_id)

        # Format for LLM
        pref_str = format_preferences_for_prompt(preferences.to_dict())

        prompt = RECOMMEND_PREFERENCES_PROMPT.format(
            preferences=pref_str,
            analysis=json.dumps(analysis.model_dump(), default=str),
        )

        try:
            config = get_recommendation_config()
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=PREFERENCE_SYSTEM_PROMPT,
                temperature=config["temperature"],
                max_tokens=config["max_tokens"],
            )

            result = self._parse_json_response(response)

            return [
                PreferenceRecommendation(**r)
                for r in result.get("recommendations", [])
            ]

        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            return []

    async def learn_from_engagement(
        self, user_id: str, engagement: EngagementData
    ) -> None:
        """
        Update preferences based on engagement signals.

        Records engagement and optionally updates preferences
        based on strong signals.

        Args:
            user_id: User identifier
            engagement: Engagement data to learn from
        """
        # Store engagement for history
        await self._store_engagement(user_id, engagement)

        # Only auto-update on strong signals
        if not self._has_strong_signal(engagement):
            return

        # Get current preferences for context
        preferences = await self.get_preferences(user_id)

        prompt = LEARN_FROM_ENGAGEMENT_PROMPT.format(
            topics=", ".join(preferences.topics) if preferences.topics else "General",
            tone=preferences.tone,
            word_count="Unknown",  # Would come from newsletter metadata
            opened=engagement.opened,
            clicked_links=", ".join(engagement.clicked_links) if engagement.clicked_links else "None",
            read_time=engagement.read_time_seconds,
            rating=engagement.rating or "Not provided",
            feedback=engagement.feedback or "None",
        )

        try:
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=PREFERENCE_SYSTEM_PROMPT,
                temperature=0.2,
                max_tokens=500,
            )

            result = self._parse_json_response(response)

            # Apply high-confidence updates
            for update in result.get("updates", []):
                if update.get("confidence", 0) >= 0.8:
                    await self._apply_learned_update(user_id, update)

        except Exception as e:
            logger.warning(f"Learning from engagement failed: {e}")

    async def _get_engagement_history(
        self, user_id: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get recent engagement history for user."""
        key = ENGAGEMENT_KEY.format(user_id=user_id)
        try:
            data = await self._memory_service.get(key)
            if data and isinstance(data, list):
                return data[:limit]
        except Exception as e:
            logger.warning(f"Failed to get engagement history: {e}")
        return []

    async def _store_engagement(
        self, user_id: str, engagement: EngagementData
    ) -> None:
        """Store engagement record in history."""
        key = ENGAGEMENT_KEY.format(user_id=user_id)

        try:
            # Get existing history
            history = await self._get_engagement_history(user_id, limit=100)

            # Add new engagement at start
            history.insert(0, engagement.model_dump())

            # Keep last 100 engagements
            history = history[:100]

            # Store with no TTL (permanent)
            await self._memory_service.set(key, history, ttl=None)

        except Exception as e:
            logger.warning(f"Failed to store engagement: {e}")

    def _has_strong_signal(self, engagement: EngagementData) -> bool:
        """Check if engagement has strong signal worth learning from."""
        # Strong positive signals
        if engagement.rating and engagement.rating >= 4:
            return True
        if len(engagement.clicked_links) >= 3:
            return True
        if engagement.read_time_seconds >= 120:  # 2+ minutes
            return True

        # Strong negative signals
        if engagement.rating and engagement.rating <= 2:
            return True
        if not engagement.opened:
            return False  # Can't learn much from unopened

        return False

    async def _apply_learned_update(
        self, user_id: str, update: Dict[str, Any]
    ) -> None:
        """Apply a learned preference update."""
        field = update.get("field")
        action = update.get("action")
        value = update.get("value")

        if not all([field, action, value]):
            return

        preferences = await self.get_preferences(user_id)

        try:
            if action == "add" and field == "topics":
                if value not in preferences.topics:
                    preferences.topics.append(value)
            elif action == "remove" and field == "topics":
                if value in preferences.topics:
                    preferences.topics.remove(value)
            elif action in ["increase", "decrease"] and field == "max_articles":
                current = preferences.max_articles
                delta = 2 if action == "increase" else -2
                preferences.max_articles = max(1, min(30, current + delta))

            # Save updates
            preferences.updated_at = datetime.now(timezone.utc)
            key = PREFERENCES_KEY.format(user_id=user_id)
            await self._memory_service.set(key, preferences.to_dict(), ttl=None)

        except Exception as e:
            logger.warning(f"Failed to apply learned update: {e}")

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        text = response.strip()

        # Handle markdown code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                text = text[start:end].strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON: {text[:100]}...")
            return {}


__all__ = ["PreferenceAgent"]
