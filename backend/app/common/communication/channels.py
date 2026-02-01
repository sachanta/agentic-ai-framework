"""
Communication channels for agent-to-agent messaging.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import asyncio


class MessageType(str, Enum):
    """Types of messages that can be sent between agents."""

    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


@dataclass
class Message:
    """A message sent between agents."""

    id: str
    sender: str
    recipient: str
    type: MessageType
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MessageChannel:
    """
    Channel for agent-to-agent communication.

    Provides an async message queue for agents to send and receive messages.
    """

    def __init__(self, name: str):
        self.name = name
        self._queues: Dict[str, asyncio.Queue] = {}
        self._subscribers: Dict[str, List[callable]] = {}

    def register_agent(self, agent_name: str) -> None:
        """Register an agent to receive messages."""
        if agent_name not in self._queues:
            self._queues[agent_name] = asyncio.Queue()

    def unregister_agent(self, agent_name: str) -> None:
        """Unregister an agent from the channel."""
        if agent_name in self._queues:
            del self._queues[agent_name]

    async def send(self, message: Message) -> None:
        """Send a message to an agent."""
        if message.recipient in self._queues:
            await self._queues[message.recipient].put(message)

        # Notify subscribers
        if message.recipient in self._subscribers:
            for callback in self._subscribers[message.recipient]:
                await callback(message)

    async def receive(self, agent_name: str, timeout: float = None) -> Optional[Message]:
        """Receive a message for an agent."""
        if agent_name not in self._queues:
            return None

        try:
            if timeout:
                return await asyncio.wait_for(
                    self._queues[agent_name].get(), timeout=timeout
                )
            return await self._queues[agent_name].get()
        except asyncio.TimeoutError:
            return None

    def subscribe(self, agent_name: str, callback: callable) -> None:
        """Subscribe to messages for an agent."""
        if agent_name not in self._subscribers:
            self._subscribers[agent_name] = []
        self._subscribers[agent_name].append(callback)

    async def broadcast(self, sender: str, content: Dict[str, Any]) -> None:
        """Broadcast a message to all registered agents."""
        for agent_name in self._queues:
            if agent_name != sender:
                message = Message(
                    id=f"broadcast-{datetime.utcnow().timestamp()}",
                    sender=sender,
                    recipient=agent_name,
                    type=MessageType.NOTIFICATION,
                    content=content,
                )
                await self.send(message)
