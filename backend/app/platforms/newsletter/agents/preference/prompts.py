"""
Prompts for Preference Agent.

Templates for preference analysis and recommendations.
"""

PREFERENCE_SYSTEM_PROMPT = """You are a preference analysis assistant for a newsletter platform.
Your role is to analyze user preferences and engagement patterns to provide personalized recommendations.
Always return responses in valid JSON format."""

ANALYZE_PREFERENCES_PROMPT = """Analyze the user's newsletter preferences and engagement history.

User Preferences:
{preferences}

Recent Engagement History (last newsletters):
{engagement_history}

Analyze the following aspects:
1. Topic Performance: Which topics get the most engagement (opens, clicks)?
2. Content Length: Does the user prefer shorter or longer newsletters?
3. Tone Effectiveness: Which tone seems to resonate best?
4. Timing Patterns: When does the user typically engage?
5. Source Preferences: Which sources get the most clicks?

Return your analysis as JSON:
{{
  "insights": [
    {{
      "category": "topics|length|tone|timing|sources",
      "message": "Human-readable insight",
      "data": {{}},
      "confidence": 0.0-1.0
    }}
  ],
  "engagement_summary": {{
    "avg_open_rate": 0.0,
    "avg_click_rate": 0.0,
    "top_topics": [],
    "preferred_sources": []
  }},
  "overall_confidence": 0.0-1.0
}}"""

RECOMMEND_PREFERENCES_PROMPT = """Based on the preference analysis, suggest improvements.

Current Preferences:
{preferences}

Analysis Results:
{analysis}

Generate recommendations to improve newsletter engagement.
Focus on actionable changes with clear reasoning.

Return as JSON:
{{
  "recommendations": [
    {{
      "field": "preference field name",
      "current_value": "current value",
      "recommended_value": "suggested value",
      "reason": "Why this change would help",
      "confidence": 0.0-1.0
    }}
  ]
}}"""

LEARN_FROM_ENGAGEMENT_PROMPT = """Analyze this newsletter engagement to update user preferences.

Newsletter Details:
- Topics: {topics}
- Tone: {tone}
- Word Count: {word_count}

Engagement:
- Opened: {opened}
- Clicked Links: {clicked_links}
- Read Time: {read_time} seconds
- Rating: {rating}
- Feedback: {feedback}

Based on this engagement, suggest preference updates.
Only suggest updates if there's strong signal (high confidence).

Return as JSON:
{{
  "updates": [
    {{
      "field": "field name",
      "action": "increase|decrease|add|remove",
      "value": "value to add/remove or adjustment",
      "confidence": 0.0-1.0
    }}
  ],
  "skip_reason": "reason if no updates suggested"
}}"""


def format_preferences_for_prompt(preferences: dict) -> str:
    """Format user preferences for inclusion in prompts."""
    lines = [
        f"- Topics: {', '.join(preferences.get('topics', [])) or 'None set'}",
        f"- Tone: {preferences.get('tone', 'professional')}",
        f"- Frequency: {preferences.get('frequency', 'weekly')}",
        f"- Max Articles: {preferences.get('max_articles', 10)}",
        f"- Include Summaries: {preferences.get('include_summaries', True)}",
        f"- Include Mindmap: {preferences.get('include_mindmap', True)}",
        f"- Language: {preferences.get('language', 'en')}",
    ]

    if preferences.get("sources_whitelist"):
        lines.append(f"- Preferred Sources: {', '.join(preferences['sources_whitelist'])}")
    if preferences.get("sources_blacklist"):
        lines.append(f"- Blocked Sources: {', '.join(preferences['sources_blacklist'])}")

    return "\n".join(lines)


def format_engagement_history(engagements: list) -> str:
    """Format engagement history for inclusion in prompts."""
    if not engagements:
        return "No engagement history available."

    lines = []
    for i, eng in enumerate(engagements[:10], 1):  # Limit to 10 most recent
        opened = "Yes" if eng.get("opened") else "No"
        clicks = len(eng.get("clicked_links", []))
        rating = eng.get("rating", "N/A")
        read_time = eng.get("read_time_seconds", 0)

        lines.append(
            f"{i}. Opened: {opened}, Clicks: {clicks}, "
            f"Read Time: {read_time}s, Rating: {rating}"
        )

    return "\n".join(lines)


__all__ = [
    "PREFERENCE_SYSTEM_PROMPT",
    "ANALYZE_PREFERENCES_PROMPT",
    "RECOMMEND_PREFERENCES_PROMPT",
    "LEARN_FROM_ENGAGEMENT_PROMPT",
    "format_preferences_for_prompt",
    "format_engagement_history",
]
