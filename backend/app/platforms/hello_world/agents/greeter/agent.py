"""
Greeter Agent - Generates personalized greetings using LLM.
"""
import logging
from typing import Any, Dict

from app.common.base.agent import BaseAgent
from app.platforms.hello_world.agents.greeter.chain import GreeterChain
from app.platforms.hello_world.agents.greeter.llm import get_greeter_llm, get_greeter_config

logger = logging.getLogger(__name__)


class GreeterAgent(BaseAgent):
    """
    Agent that generates personalized greetings using the configured LLM.

    This agent demonstrates the pattern for building agents with:
    - Config-driven LLM provider (supports Ollama, OpenAI, Bedrock)
    - Chain for LLM processing
    - Fallback behavior when LLM is unavailable
    """

    def __init__(self):
        # Get the LLM provider from config
        llm = get_greeter_llm()
        llm_config = get_greeter_config()

        super().__init__(
            name="greeter",
            description="Generates personalized greetings based on name and style",
            llm=llm,
            tools=[],
            vectorstore=None,
            model=llm_config.get("model"),
            temperature=llm_config.get("temperature", 0.7),
            max_tokens=llm_config.get("max_tokens", 150),
        )

        # Initialize the chain with the same LLM
        self.chain = GreeterChain(llm=self.llm)
        self._llm_config = llm_config

    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a greeting.

        Args:
            input: Dictionary with 'name' and optional 'style' keys

        Returns:
            Dictionary with generated greeting and metadata
        """
        await self.initialize()

        name = input.get("name", "World")
        style = input.get("style", "friendly")

        logger.debug(f"Generating greeting for '{name}' with style '{style}'")

        # Run the chain to generate the greeting
        result = await self.chain.run({
            "name": name,
            "style": style,
        })

        return {
            "success": result.get("success", True),
            "greeting": result.get("text", f"Hello, {name}!"),
            "metadata": {
                "agent": self.name,
                "style": style,
                "name": name,
                "model": result.get("model"),
                "provider": result.get("provider"),
                "fallback": result.get("fallback", False),
            },
        }

    def get_llm_info(self) -> Dict[str, Any]:
        """
        Get information about the current LLM configuration.

        Returns:
            Dictionary with LLM provider and model info
        """
        return {
            "provider": self._llm_config.get("provider"),
            "model": self._llm_config.get("model"),
            "temperature": self._llm_config.get("temperature"),
            "max_tokens": self._llm_config.get("max_tokens"),
        }
