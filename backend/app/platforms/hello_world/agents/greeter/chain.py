"""
Greeter Chain - LLM chain for generating greetings.
"""
import logging
from typing import Any, Dict, Optional

from app.common.base.chain import BaseChain
from app.common.providers.llm import LLMProvider
from app.platforms.hello_world.agents.greeter.prompts import GREETING_PROMPT, GREETER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class GreeterChain(BaseChain):
    """
    Chain for generating personalized greetings using the LLM.

    This chain demonstrates the pattern for building LLM chains
    with prompt templates that actually call the configured LLM provider.
    """

    def __init__(self, llm: Optional[LLMProvider] = None):
        super().__init__(
            name="greeter_chain",
            llm=llm,
            prompt_template=GREETING_PROMPT,
        )
        self.system_prompt = GREETER_SYSTEM_PROMPT

    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a greeting using the LLM.

        Args:
            input: Dictionary with 'name' and 'style' keys

        Returns:
            Dictionary with generated text and metadata
        """
        name = input.get("name", "World")
        style = input.get("style", "friendly")

        # Format the prompt using the template
        prompt = self.format_prompt(name=name, style=style)

        # Call the LLM if available
        if self.llm:
            try:
                response = await self.llm.generate(
                    prompt=prompt,
                    system=self.system_prompt,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )

                return {
                    "success": True,
                    "text": response.content.strip(),
                    "prompt": prompt,
                    "model": response.model,
                    "provider": response.provider,
                    "usage": response.usage,
                }
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
                # Fall back to template-based greeting
                return self._fallback_greeting(name, style, prompt, str(e))
        else:
            # No LLM configured, use fallback
            logger.warning("No LLM configured, using fallback greeting")
            return self._fallback_greeting(name, style, prompt)

    def _fallback_greeting(
        self,
        name: str,
        style: str,
        prompt: str,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a fallback greeting when LLM is not available.

        Args:
            name: The name to greet
            style: The greeting style
            prompt: The formatted prompt (for reference)
            error: Optional error message

        Returns:
            Dictionary with fallback greeting
        """
        greetings = {
            "friendly": f"Hello there, {name}! Hope you're having a wonderful day!",
            "formal": f"Good day, {name}. It is a pleasure to make your acquaintance.",
            "casual": f"Hey {name}! What's up?",
            "enthusiastic": f"WOW! {name}! SO GREAT to meet you! This is AMAZING!",
        }

        greeting_text = greetings.get(style, f"Hello, {name}!")

        result = {
            "success": True,
            "text": greeting_text,
            "prompt": prompt,
            "model": "fallback",
            "provider": "template",
            "fallback": True,
        }

        if error:
            result["llm_error"] = error

        return result
