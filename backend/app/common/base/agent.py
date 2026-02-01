"""
Base agent class for all platform agents.
Provides LLM integration and tool execution capabilities.
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Awaitable

from app.common.providers.llm import (
    LLMProvider,
    LLMProviderType,
    LLMResponse,
    get_llm_provider,
)
from app.common.providers.embeddings import (
    EmbeddingsProvider,
    EmbeddingsProviderType,
    get_embeddings_provider,
)
from app.common.providers.vectorstore import (
    VectorStoreProvider,
    VectorStoreProviderType,
    get_vectorstore_provider,
)

logger = logging.getLogger(__name__)


class AgentTool:
    """
    A tool that an agent can use.

    Tools are functions that agents can call to perform actions
    or retrieve information from external systems.
    """

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable[..., Awaitable[Any]],
        parameters: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.description = description
        self.func = func
        self.parameters = parameters or {}

    async def execute(self, **kwargs) -> Any:
        """Execute the tool with the given parameters."""
        return await self.func(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary for LLM prompting."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class AgentMemory:
    """
    Simple memory for agents to maintain conversation history.
    """

    def __init__(self, max_messages: int = 20):
        self.messages: List[Dict[str, str]] = []
        self.max_messages = max_messages
        self.context: Dict[str, Any] = {}

    def add_message(self, role: str, content: str) -> None:
        """Add a message to memory."""
        self.messages.append({"role": role, "content": content})
        # Keep only the last N messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

    def add_user_message(self, content: str) -> None:
        """Add a user message."""
        self.add_message("user", content)

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message."""
        self.add_message("assistant", content)

    def add_system_message(self, content: str) -> None:
        """Add a system message (usually at the beginning)."""
        self.add_message("system", content)

    def get_messages(self) -> List[Dict[str, str]]:
        """Get all messages."""
        return self.messages.copy()

    def clear(self) -> None:
        """Clear all messages."""
        self.messages = []

    def set_context(self, key: str, value: Any) -> None:
        """Set a context value."""
        self.context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a context value."""
        return self.context.get(key, default)


class BaseAgent(ABC):
    """
    Base class for all agents in the framework.

    Agents are autonomous units that can:
    - Process inputs and generate outputs using LLMs
    - Use tools to interact with external systems
    - Maintain state and memory across interactions
    - Communicate with other agents

    Attributes:
        name: Unique identifier for the agent
        description: Human-readable description of the agent's purpose
        llm: The LLM provider to use for generation
        tools: List of tools available to the agent
        memory: Agent's conversation memory
        system_prompt: The system prompt that defines agent behavior
    """

    def __init__(
        self,
        name: str,
        description: str,
        llm: Optional[LLMProvider] = None,
        tools: Optional[List[AgentTool]] = None,
        vectorstore: Optional[VectorStoreProvider] = None,
        embeddings: Optional[EmbeddingsProvider] = None,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ):
        self.name = name
        self.description = description
        self.tools = tools or []
        self.vectorstore = vectorstore
        self.embeddings = embeddings
        self.system_prompt = system_prompt
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Initialize LLM - use Ollama by default
        self._llm = llm
        self._initialized = False

        # Agent memory
        self.memory = AgentMemory()

        # Agent state
        self.state: Dict[str, Any] = {}

    @property
    def llm(self) -> LLMProvider:
        """Get the LLM provider, initializing if needed."""
        if self._llm is None:
            self._llm = get_llm_provider(LLMProviderType.OLLAMA)
        return self._llm

    @llm.setter
    def llm(self, value: LLMProvider) -> None:
        """Set the LLM provider."""
        self._llm = value

    @abstractmethod
    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent with the given input.

        Args:
            input: Dictionary containing the input data for the agent

        Returns:
            Dictionary containing the agent's output
        """
        pass

    async def initialize(self) -> None:
        """Initialize the agent (load models, connect to services, etc.)."""
        if self._initialized:
            return

        logger.info(f"Initializing agent: {self.name}")

        # Initialize system prompt in memory if provided
        if self.system_prompt:
            self.memory.add_system_message(self.system_prompt)

        self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup resources when agent is done."""
        logger.info(f"Cleaning up agent: {self.name}")
        self.memory.clear()

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Generate a response using the LLM.

        Args:
            prompt: The user prompt
            system: Optional system prompt override
            **kwargs: Additional generation parameters

        Returns:
            The generated text
        """
        response = await self.llm.generate(
            prompt=prompt,
            model=self.model,
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            system=system or self.system_prompt,
            **kwargs,
        )
        return response.content

    async def chat(
        self,
        message: str,
        remember: bool = True,
        **kwargs,
    ) -> str:
        """
        Chat with the agent, maintaining conversation history.

        Args:
            message: The user message
            remember: Whether to add the message to memory
            **kwargs: Additional generation parameters

        Returns:
            The agent's response
        """
        if remember:
            self.memory.add_user_message(message)

        messages = self.memory.get_messages()

        response = await self.llm.chat(
            messages=messages,
            model=self.model,
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            **kwargs,
        )

        if remember:
            self.memory.add_assistant_message(response.content)

        return response.content

    def add_tool(self, tool: AgentTool) -> None:
        """Add a tool to the agent."""
        self.tools.append(tool)
        logger.debug(f"Added tool '{tool.name}' to agent '{self.name}'")

    def get_tool(self, name: str) -> Optional[AgentTool]:
        """Get a tool by name."""
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None

    async def execute_tool(self, name: str, **kwargs) -> Any:
        """Execute a tool by name."""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")
        return await tool.execute(**kwargs)

    def get_tools_description(self) -> str:
        """Get a formatted description of available tools for prompting."""
        if not self.tools:
            return "No tools available."

        descriptions = []
        for tool in self.tools:
            params_str = ", ".join(
                f"{k}: {v}" for k, v in tool.parameters.items()
            ) if tool.parameters else "none"
            descriptions.append(
                f"- {tool.name}: {tool.description} (parameters: {params_str})"
            )

        return "Available tools:\n" + "\n".join(descriptions)

    def get_state(self) -> Dict[str, Any]:
        """Get the current state of the agent."""
        return self.state.copy()

    def set_state(self, state: Dict[str, Any]) -> None:
        """Set the agent's state."""
        self.state = state.copy()

    def update_state(self, **kwargs) -> None:
        """Update specific state values."""
        self.state.update(kwargs)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, tools={len(self.tools)})>"


class SimpleAgent(BaseAgent):
    """
    A simple agent that processes input and generates output.

    Good for single-turn interactions without complex tool usage.
    """

    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the agent with the given input.

        Expects input to have a 'message' or 'prompt' key.
        """
        await self.initialize()

        # Extract the input message
        message = input.get("message") or input.get("prompt") or input.get("input", "")

        if not message:
            return {
                "success": False,
                "error": "No input message provided",
                "agent": self.name,
            }

        try:
            # Generate response
            response = await self.generate(message)

            return {
                "success": True,
                "response": response,
                "agent": self.name,
            }
        except Exception as e:
            logger.error(f"Agent {self.name} error: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.name,
            }


class ConversationalAgent(BaseAgent):
    """
    An agent that maintains conversation history.

    Good for multi-turn conversations and chatbot-like interactions.
    """

    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the agent with the given input, maintaining conversation history.
        """
        await self.initialize()

        message = input.get("message") or input.get("prompt") or input.get("input", "")

        if not message:
            return {
                "success": False,
                "error": "No input message provided",
                "agent": self.name,
            }

        try:
            # Use chat to maintain history
            response = await self.chat(message)

            return {
                "success": True,
                "response": response,
                "agent": self.name,
                "message_count": len(self.memory.messages),
            }
        except Exception as e:
            logger.error(f"Agent {self.name} error: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.name,
            }

    def reset_conversation(self) -> None:
        """Reset the conversation history."""
        self.memory.clear()
        if self.system_prompt:
            self.memory.add_system_message(self.system_prompt)
