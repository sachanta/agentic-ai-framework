"""
Base tool class for agent tools.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    """
    Base class for all tools in the framework.

    Tools are callable functions that agents can use to:
    - Interact with external APIs
    - Access databases
    - Perform computations
    - Execute system commands
    """

    def __init__(
        self,
        name: str,
        description: str,
        schema: Dict[str, Any] = None,
    ):
        self.name = name
        self.description = description
        self.schema = schema or {}

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """
        Execute the tool with the given arguments.

        Args:
            **kwargs: Tool-specific arguments

        Returns:
            The tool's output
        """
        pass

    def validate_input(self, **kwargs) -> bool:
        """Validate input against the tool's schema."""
        # TODO: Implement JSON schema validation
        return True

    def to_langchain_tool(self) -> Any:
        """Convert to LangChain tool format."""
        # TODO: Implement LangChain tool conversion
        pass

    def to_openai_function(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.schema,
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name})>"
