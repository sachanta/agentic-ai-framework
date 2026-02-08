"""
Prompts for Custom Prompt Agent.

Templates for NLP analysis and parameter extraction.
"""
from typing import Optional, List

CUSTOM_PROMPT_SYSTEM_PROMPT = """You are an NLP assistant that analyzes user requests for newsletter content.
Your role is to extract structured parameters from natural language prompts.
Always return responses in valid JSON format.
Be precise in identifying topics, tone, and constraints."""

ANALYZE_PROMPT_PROMPT = """Analyze this user request for newsletter content:

"{prompt}"

Extract the following information:

1. **Intent**: What does the user want?
   - research: Find and gather content on topics
   - summarize: Create a summary of specific content
   - analyze: Deep analysis of a topic
   - compare: Compare different topics/approaches
   - generate: Create original content

2. **Topics**: What subjects should be covered?
   - Extract specific keywords and phrases
   - Include related subtopics if clearly implied

3. **Tone**: What writing style is requested?
   - professional: Formal, business-appropriate
   - casual: Friendly, conversational
   - formal: Academic, structured
   - enthusiastic: Energetic, engaging
   - null if not specified

4. **Constraints**: Any requirements mentioned?
   - max_words: Word limit if specified
   - format: Specific format requested
   - length: short, medium, long

5. **Focus Areas**: Specific aspects to emphasize?
   - e.g., "practical applications", "recent developments"

6. **Exclusions**: What should be avoided?
   - Topics or angles to skip

7. **Time Range**: Any time constraints?
   - "this week", "last month", "recent", etc.

Return as JSON:
{{
  "intent": "research|summarize|analyze|compare|generate",
  "topics": ["topic1", "topic2"],
  "tone": "professional|casual|formal|enthusiastic|null",
  "constraints": {{
    "max_words": null,
    "format": null,
    "length": null
  }},
  "focus_areas": [],
  "exclusions": [],
  "time_range": null,
  "confidence": 0.0-1.0
}}"""

GENERATE_PARAMETERS_PROMPT = """Convert this prompt analysis into research/writing parameters.

Analysis:
{analysis}

User Preferences (for context):
{preferences}

Generate optimal parameters for newsletter generation.
Consider:
- Default to user preferences if prompt doesn't specify
- Expand vague topics into searchable terms
- Set reasonable defaults for unspecified constraints

Return as JSON:
{{
  "topics": ["searchable", "topic", "terms"],
  "tone": "professional",
  "max_articles": 10,
  "max_word_count": null,
  "focus_areas": [],
  "time_range_days": 7,
  "include_summaries": true,
  "source_preferences": [],
  "exclusions": []
}}"""

ENHANCE_PROMPT_PROMPT = """Enhance this user prompt with additional context.

Original Prompt:
"{prompt}"

User Preferences:
{preferences}

Past Successful Topics:
{successful_topics}

Enhance the prompt by:
1. Adding relevant context from user preferences
2. Suggesting related topics based on past success
3. Clarifying vague requests
4. Maintaining the user's original intent

Return as JSON:
{{
  "enhanced_prompt": "The enhanced version of the prompt",
  "added_context": ["list of context items added"],
  "suggestions": ["optional suggestions for user"]
}}"""

VALIDATE_PARAMETERS_PROMPT = """Validate these newsletter generation parameters.

Parameters:
{parameters}

Check for:
1. Valid topics (not empty, searchable)
2. Reasonable constraints (word count, article count)
3. Compatible settings (tone matches content type)
4. Potential issues or improvements

Return as JSON:
{{
  "valid": true|false,
  "errors": ["list of errors if invalid"],
  "warnings": ["list of warnings"],
  "suggestions": ["list of improvement suggestions"]
}}"""


# Intent keywords for quick detection
INTENT_KEYWORDS = {
    "research": ["find", "search", "discover", "look for", "get", "gather"],
    "summarize": ["summarize", "summary", "brief", "overview", "recap"],
    "analyze": ["analyze", "analysis", "deep dive", "examine", "study"],
    "compare": ["compare", "comparison", "versus", "vs", "difference"],
    "generate": ["write", "create", "generate", "compose", "draft"],
}

# Tone keywords for quick detection
TONE_KEYWORDS = {
    "professional": ["professional", "business", "corporate", "formal"],
    "casual": ["casual", "friendly", "conversational", "relaxed"],
    "formal": ["formal", "academic", "scholarly", "technical"],
    "enthusiastic": ["enthusiastic", "exciting", "engaging", "energetic"],
}

# Time range patterns
TIME_PATTERNS = {
    "today": 1,
    "this week": 7,
    "last week": 7,
    "this month": 30,
    "last month": 30,
    "recent": 7,
    "latest": 3,
}


def detect_intent_keywords(prompt: str) -> str:
    """Quick intent detection from keywords."""
    prompt_lower = prompt.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in prompt_lower:
                return intent
    return "research"  # Default


def detect_tone_keywords(prompt: str) -> Optional[str]:
    """Quick tone detection from keywords."""
    prompt_lower = prompt.lower()
    for tone, keywords in TONE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in prompt_lower:
                return tone
    return None


def detect_time_range(prompt: str) -> Optional[int]:
    """Quick time range detection from patterns."""
    prompt_lower = prompt.lower()
    for pattern, days in TIME_PATTERNS.items():
        if pattern in prompt_lower:
            return days
    return None


def extract_quoted_topics(prompt: str) -> List[str]:
    """Extract topics in quotes."""
    import re
    # Match text in quotes
    matches = re.findall(r'"([^"]+)"', prompt)
    matches.extend(re.findall(r"'([^']+)'", prompt))
    return matches


__all__ = [
    "CUSTOM_PROMPT_SYSTEM_PROMPT",
    "ANALYZE_PROMPT_PROMPT",
    "GENERATE_PARAMETERS_PROMPT",
    "ENHANCE_PROMPT_PROMPT",
    "VALIDATE_PARAMETERS_PROMPT",
    "INTENT_KEYWORDS",
    "TONE_KEYWORDS",
    "TIME_PATTERNS",
    "detect_intent_keywords",
    "detect_tone_keywords",
    "detect_time_range",
    "extract_quoted_topics",
]
