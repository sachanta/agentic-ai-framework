"""
Agent Studio schemas — Rich agent metadata for discovery and catalog.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class StudioLLMConfig(BaseModel):
    """LLM configuration extracted from an agent."""
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class StudioToolInfo(BaseModel):
    """Tool metadata for display."""
    name: str
    description: str
    parameters: Dict[str, Any] = {}


class StudioAgentSummary(BaseModel):
    """Lightweight agent summary for catalog grid."""
    agent_id: str               # "{platform_id}/{agent_name}"
    name: str                   # e.g. "research"
    display_name: str           # e.g. "Research Agent"
    platform_id: str            # e.g. "newsletter"
    platform_name: str          # e.g. "Newsletter"
    description: str
    llm_config: StudioLLMConfig
    tool_count: int
    has_system_prompt: bool
    agent_class: str            # e.g. "ResearchAgent"
    status: str = "discovered"


class StudioAgentDetail(StudioAgentSummary):
    """Full agent detail including prompt and tools."""
    system_prompt: Optional[str] = None
    tools: List[StudioToolInfo] = []
    parameters: Dict[str, Any] = {}


class StudioPlatformSummary(BaseModel):
    """Platform summary with agent counts."""
    id: str
    name: str
    description: str
    version: str
    agent_count: int
    agents: List[str]
    enabled: bool


class StudioAgentsListResponse(BaseModel):
    """Response for GET /studio/agents."""
    agents: List[StudioAgentSummary]
    total: int
    platforms: List[StudioPlatformSummary]


class StudioPlatformsListResponse(BaseModel):
    """Response for GET /studio/platforms."""
    platforms: List[StudioPlatformSummary]
    total: int
