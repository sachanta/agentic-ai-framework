"""
Preference API endpoints for Newsletter Platform.

Phase 8: User preference management and personalization.
Provides endpoints to:
- Get and update user preferences
- Record engagement data for learning
- Get preference analysis and recommendations
"""
import logging
from typing import List

from fastapi import APIRouter, HTTPException, Path

from app.platforms.newsletter.agents import PreferenceAgent
from app.platforms.newsletter.agents.preference.schemas import (
    PreferenceUpdate,
    EngagementData,
)
from app.platforms.newsletter.schemas.preference import (
    PreferenceResponse,
    PreferenceUpdateRequest,
    EngagementRequest,
    AnalysisResponse,
    InsightResponse,
    RecommendationResponse,
    RecommendationsListResponse,
    PreferenceActionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get("/{user_id}", response_model=PreferenceResponse)
async def get_preferences(
    user_id: str = Path(..., description="User identifier"),
):
    """
    Get user preferences.

    Returns the current preferences for the user, or defaults
    if the user hasn't set any preferences.

    Args:
        user_id: User identifier

    Returns:
        User preferences
    """
    try:
        agent = PreferenceAgent()

        result = await agent.run({
            "action": "get",
            "user_id": user_id,
        })

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to get preferences"),
            )

        prefs = result["preferences"]
        return PreferenceResponse(
            user_id=prefs.get("user_id", user_id),
            topics=prefs.get("topics", []),
            tone=prefs.get("tone", "professional"),
            frequency=prefs.get("frequency", "weekly"),
            max_articles=prefs.get("max_articles", 10),
            preferred_sources=prefs.get("preferred_sources", []),
            excluded_sources=prefs.get("excluded_sources", []),
            include_summaries=prefs.get("include_summaries", True),
            created_at=prefs.get("created_at"),
            updated_at=prefs.get("updated_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get preferences endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{user_id}", response_model=PreferenceResponse)
async def update_preferences(
    request: PreferenceUpdateRequest,
    user_id: str = Path(..., description="User identifier"),
):
    """
    Update user preferences.

    Updates only the fields provided in the request,
    preserving other existing preferences.

    Args:
        user_id: User identifier
        request: Partial preference updates

    Returns:
        Updated user preferences
    """
    try:
        agent = PreferenceAgent()

        # Convert API request to agent schema
        updates = PreferenceUpdate(
            topics=request.topics,
            tone=request.tone,
            frequency=request.frequency,
            max_articles=request.max_articles,
            preferred_sources=request.preferred_sources,
            excluded_sources=request.excluded_sources,
            include_summaries=request.include_summaries,
        )

        result = await agent.run({
            "action": "update",
            "user_id": user_id,
            "updates": updates.model_dump(exclude_none=True),
        })

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to update preferences"),
            )

        prefs = result["preferences"]
        return PreferenceResponse(
            user_id=prefs.get("user_id", user_id),
            topics=prefs.get("topics", []),
            tone=prefs.get("tone", "professional"),
            frequency=prefs.get("frequency", "weekly"),
            max_articles=prefs.get("max_articles", 10),
            preferred_sources=prefs.get("preferred_sources", []),
            excluded_sources=prefs.get("excluded_sources", []),
            include_summaries=prefs.get("include_summaries", True),
            created_at=prefs.get("created_at"),
            updated_at=prefs.get("updated_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update preferences endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_id}/engagement", response_model=PreferenceActionResponse)
async def record_engagement(
    request: EngagementRequest,
    user_id: str = Path(..., description="User identifier"),
):
    """
    Record user engagement with a newsletter.

    Stores engagement data for learning and preference optimization.
    High-confidence signals (high ratings, long read times) may
    automatically update preferences.

    Args:
        user_id: User identifier
        request: Engagement data

    Returns:
        Success status
    """
    try:
        agent = PreferenceAgent()

        # Convert API request to agent schema
        engagement = EngagementData(
            newsletter_id=request.newsletter_id,
            user_id=user_id,
            opened=request.opened,
            clicked_links=request.clicked_links,
            read_time_seconds=request.read_time_seconds,
            rating=request.rating,
            feedback=request.feedback,
        )

        result = await agent.run({
            "action": "learn",
            "user_id": user_id,
            "engagement": engagement.model_dump(),
        })

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to record engagement"),
            )

        return PreferenceActionResponse(
            success=True,
            message="Engagement recorded successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Record engagement endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/analysis", response_model=AnalysisResponse)
async def analyze_preferences(
    user_id: str = Path(..., description="User identifier"),
):
    """
    Analyze user preferences and engagement patterns.

    Uses AI to identify patterns and generate insights about
    the user's content preferences and engagement.

    Args:
        user_id: User identifier

    Returns:
        Analysis with insights
    """
    try:
        agent = PreferenceAgent()

        result = await agent.run({
            "action": "analyze",
            "user_id": user_id,
        })

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to analyze preferences"),
            )

        analysis = result["analysis"]
        insights = [
            InsightResponse(
                category=i.get("category", "general"),
                message=i.get("message", ""),
                confidence=i.get("confidence", 0.0),
                action=i.get("action"),
            )
            for i in analysis.get("insights", [])
        ]

        return AnalysisResponse(
            user_id=analysis.get("user_id", user_id),
            insights=insights,
            engagement_summary=analysis.get("engagement_summary", {}),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analyze preferences endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/recommendations", response_model=RecommendationsListResponse)
async def get_recommendations(
    user_id: str = Path(..., description="User identifier"),
):
    """
    Get preference change recommendations.

    Uses AI to suggest improvements to user preferences
    based on their engagement patterns and content interactions.

    Args:
        user_id: User identifier

    Returns:
        List of recommendations
    """
    try:
        agent = PreferenceAgent()

        result = await agent.run({
            "action": "recommend",
            "user_id": user_id,
        })

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to get recommendations"),
            )

        recommendations = [
            RecommendationResponse(
                field=r.get("field", ""),
                current_value=r.get("current_value"),
                recommended_value=r.get("recommended_value"),
                reason=r.get("reason", ""),
                confidence=r.get("confidence", 0.0),
            )
            for r in result.get("recommendations", [])
        ]

        return RecommendationsListResponse(
            user_id=user_id,
            recommendations=recommendations,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get recommendations endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
