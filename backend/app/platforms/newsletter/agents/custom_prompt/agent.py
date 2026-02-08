"""
Custom Prompt Agent implementation.

Analyzes natural language prompts to extract structured parameters
for research and writing operations.
"""
import json
import logging
from typing import Dict, Any, Optional

from app.common.base.agent import BaseAgent
from app.platforms.newsletter.agents.custom_prompt.llm import (
    get_custom_prompt_llm,
    get_analysis_config,
    get_enhancement_config,
)
from app.platforms.newsletter.agents.custom_prompt.prompts import (
    CUSTOM_PROMPT_SYSTEM_PROMPT,
    ANALYZE_PROMPT_PROMPT,
    GENERATE_PARAMETERS_PROMPT,
    ENHANCE_PROMPT_PROMPT,
    VALIDATE_PARAMETERS_PROMPT,
    detect_intent_keywords,
    detect_tone_keywords,
    detect_time_range,
    extract_quoted_topics,
)
from app.platforms.newsletter.agents.custom_prompt.schemas import (
    PromptAnalysis,
    ExtractedParameters,
    ValidationResult,
    EnhancedPrompt,
)

logger = logging.getLogger(__name__)


class CustomPromptAgent(BaseAgent):
    """
    Agent for analyzing natural language prompts.

    Extracts intent, topics, tone, and constraints from user prompts
    to generate structured parameters for other agents.
    """

    def __init__(self):
        """Initialize the Custom Prompt Agent."""
        llm = get_custom_prompt_llm()
        super().__init__(
            name="custom_prompt",
            description="Analyzes natural language prompts to extract structured parameters",
            llm=llm,
            system_prompt=CUSTOM_PROMPT_SYSTEM_PROMPT,
        )

    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point - routes to appropriate method.

        Args:
            input: Dict with 'action' and action-specific parameters.
                   Supported actions: analyze, enhance, generate, validate

        Returns:
            Dict with success status and action-specific results.
        """
        action = input.get("action", "analyze")
        prompt = input.get("prompt", "")

        if not prompt and action not in ["validate"]:
            return {"success": False, "error": "prompt is required"}

        try:
            if action == "analyze":
                analysis = await self.analyze_prompt(prompt)
                return {"success": True, "analysis": analysis.model_dump()}

            elif action == "enhance":
                preferences = input.get("preferences", {})
                successful_topics = input.get("successful_topics", [])
                enhanced = await self.enhance_prompt(
                    prompt, preferences, successful_topics
                )
                return {"success": True, "enhanced": enhanced.model_dump()}

            elif action == "generate":
                analysis = input.get("analysis")
                preferences = input.get("preferences", {})
                if not analysis:
                    # First analyze the prompt
                    analysis_obj = await self.analyze_prompt(prompt)
                    analysis = analysis_obj.model_dump()
                params = await self.generate_parameters(analysis, preferences)
                return {"success": True, "parameters": params.model_dump()}

            elif action == "validate":
                parameters = input.get("parameters", {})
                result = await self.validate_parameters(parameters)
                return {"success": True, "validation": result.model_dump()}

            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"CustomPromptAgent error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def analyze_prompt(self, prompt: str) -> PromptAnalysis:
        """
        Analyze a natural language prompt.

        Uses keyword detection for quick analysis, then LLM for deeper analysis.

        Args:
            prompt: User's natural language prompt

        Returns:
            PromptAnalysis with extracted intent, topics, tone, etc.
        """
        # Quick keyword-based detection
        quick_intent = detect_intent_keywords(prompt)
        quick_tone = detect_tone_keywords(prompt)
        quick_time = detect_time_range(prompt)
        quoted_topics = extract_quoted_topics(prompt)

        # Build LLM prompt
        llm_prompt = ANALYZE_PROMPT_PROMPT.format(prompt=prompt)

        try:
            config = get_analysis_config()
            response = await self.llm.generate(
                prompt=llm_prompt,
                system_prompt=CUSTOM_PROMPT_SYSTEM_PROMPT,
                temperature=config["temperature"],
                max_tokens=config["max_tokens"],
            )

            result = self._parse_json_response(response)

            # Merge quick detection with LLM analysis
            # LLM analysis takes precedence, but we use quick detection as fallback
            topics = result.get("topics", [])
            if not topics and quoted_topics:
                topics = quoted_topics

            intent = result.get("intent", quick_intent)
            tone = result.get("tone") or quick_tone

            # Handle time_range - could be string or int from LLM
            time_range = result.get("time_range")
            if time_range is None and quick_time:
                time_range = f"{quick_time} days"

            return PromptAnalysis(
                original_prompt=prompt,
                intent=intent,
                topics=topics,
                tone=tone,
                constraints=result.get("constraints", {}),
                focus_areas=result.get("focus_areas", []),
                exclusions=result.get("exclusions", []),
                time_range=str(time_range) if time_range else None,
                confidence=result.get("confidence", 0.7),
            )

        except Exception as e:
            logger.error(f"Prompt analysis failed: {e}")
            # Return basic analysis from keyword detection
            return PromptAnalysis(
                original_prompt=prompt,
                intent=quick_intent,
                topics=quoted_topics or [],
                tone=quick_tone,
                time_range=f"{quick_time} days" if quick_time else None,
                confidence=0.3,  # Low confidence for fallback
            )

    async def enhance_prompt(
        self,
        prompt: str,
        preferences: Dict[str, Any],
        successful_topics: list[str] | None = None,
    ) -> EnhancedPrompt:
        """
        Enhance a prompt with user context.

        Args:
            prompt: Original user prompt
            preferences: User preferences dict
            successful_topics: List of topics that performed well in the past

        Returns:
            EnhancedPrompt with added context
        """
        successful_topics = successful_topics or []

        llm_prompt = ENHANCE_PROMPT_PROMPT.format(
            prompt=prompt,
            preferences=json.dumps(preferences, default=str),
            successful_topics=", ".join(successful_topics) if successful_topics else "None",
        )

        try:
            config = get_enhancement_config()
            response = await self.llm.generate(
                prompt=llm_prompt,
                system_prompt=CUSTOM_PROMPT_SYSTEM_PROMPT,
                temperature=config["temperature"],
                max_tokens=config["max_tokens"],
            )

            result = self._parse_json_response(response)

            return EnhancedPrompt(
                original_prompt=prompt,
                enhanced_prompt=result.get("enhanced_prompt", prompt),
                added_context=result.get("added_context", []),
                user_preferences_applied=bool(preferences),
            )

        except Exception as e:
            logger.error(f"Prompt enhancement failed: {e}")
            # Return original prompt on failure
            return EnhancedPrompt(
                original_prompt=prompt,
                enhanced_prompt=prompt,
                added_context=[],
                user_preferences_applied=False,
            )

    async def generate_parameters(
        self,
        analysis: Dict[str, Any] | PromptAnalysis,
        preferences: Dict[str, Any] | None = None,
    ) -> ExtractedParameters:
        """
        Generate research/writing parameters from analysis.

        Args:
            analysis: PromptAnalysis or dict from analyze_prompt
            preferences: Optional user preferences

        Returns:
            ExtractedParameters for use with other agents
        """
        if isinstance(analysis, PromptAnalysis):
            analysis = analysis.model_dump()

        preferences = preferences or {}

        llm_prompt = GENERATE_PARAMETERS_PROMPT.format(
            analysis=json.dumps(analysis, default=str),
            preferences=json.dumps(preferences, default=str),
        )

        try:
            config = get_analysis_config()
            response = await self.llm.generate(
                prompt=llm_prompt,
                system_prompt=CUSTOM_PROMPT_SYSTEM_PROMPT,
                temperature=config["temperature"],
                max_tokens=config["max_tokens"],
            )

            result = self._parse_json_response(response)

            # Map LLM response to ExtractedParameters
            return ExtractedParameters(
                topics=result.get("topics", analysis.get("topics", [])),
                tone=result.get("tone", preferences.get("tone", "professional")),
                max_articles=result.get("max_articles", 10),
                max_word_count=result.get("max_word_count"),
                focus_areas=result.get("focus_areas", []),
                time_range_days=result.get("time_range_days", 7),
                include_summaries=result.get("include_summaries", True),
                source_preferences=result.get("source_preferences", []),
                exclusions=result.get("exclusions", []),
            )

        except Exception as e:
            logger.error(f"Parameter generation failed: {e}")
            # Return basic parameters from analysis
            return ExtractedParameters(
                topics=analysis.get("topics", []),
                tone=preferences.get("tone", "professional"),
            )

    async def validate_parameters(
        self, parameters: Dict[str, Any] | ExtractedParameters
    ) -> ValidationResult:
        """
        Validate extracted parameters.

        Args:
            parameters: Parameters to validate

        Returns:
            ValidationResult with valid status, errors, warnings
        """
        if isinstance(parameters, ExtractedParameters):
            parameters = parameters.model_dump()

        # Quick validation checks
        errors = []
        warnings = []
        suggestions = []

        # Check required fields
        topics = parameters.get("topics", [])
        if not topics:
            errors.append("No topics specified")

        # Check value ranges
        max_articles = parameters.get("max_articles", 10)
        if max_articles < 1:
            errors.append("max_articles must be at least 1")
        elif max_articles > 30:
            warnings.append("max_articles is very high (>30), consider reducing")

        time_range_days = parameters.get("time_range_days", 7)
        if time_range_days < 1:
            errors.append("time_range_days must be at least 1")
        elif time_range_days > 30:
            warnings.append("time_range_days is very long (>30 days)")

        # Validate tone
        valid_tones = ["professional", "casual", "formal", "enthusiastic"]
        tone = parameters.get("tone", "professional")
        if tone not in valid_tones:
            warnings.append(f"Unknown tone '{tone}', defaulting to professional")

        # Use LLM for deeper validation if no critical errors
        if not errors:
            try:
                llm_prompt = VALIDATE_PARAMETERS_PROMPT.format(
                    parameters=json.dumps(parameters, default=str)
                )

                response = await self.llm.generate(
                    prompt=llm_prompt,
                    system_prompt=CUSTOM_PROMPT_SYSTEM_PROMPT,
                    temperature=0.1,
                    max_tokens=500,
                )

                result = self._parse_json_response(response)

                # Merge LLM validation
                if not result.get("valid", True):
                    errors.extend(result.get("errors", []))
                warnings.extend(result.get("warnings", []))
                suggestions.extend(result.get("suggestions", []))

            except Exception as e:
                logger.warning(f"LLM validation failed: {e}")
                # Continue with basic validation

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

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


__all__ = ["CustomPromptAgent"]
