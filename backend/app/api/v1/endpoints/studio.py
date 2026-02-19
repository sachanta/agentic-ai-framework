"""
Agent Studio endpoints — Discover agents across all platforms.

These endpoints introspect the PlatformRegistry and BaseAgent instances
to provide rich metadata for the Agent Studio UI.
"""
import importlib
import logging
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, status

from app.common.base.agent import BaseAgent
from app.platforms.registry import PlatformInfo, get_platform_registry
from app.schemas.studio import (
    StudioAgentDetail,
    StudioAgentSummary,
    StudioAgentsListResponse,
    StudioLLMConfig,
    StudioPlatformSummary,
    StudioPlatformsListResponse,
    StudioToolInfo,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Agent Factory Registry
#
# Maps (platform_id, agent_name) -> import path for agents that are NOT
# registered via orchestrator.register_agent(). The Newsletter orchestrator
# uses LangGraph nodes and never calls register_agent(), so we need this
# fallback to instantiate those agents for introspection.
# ---------------------------------------------------------------------------

_AGENT_FACTORIES: Dict[Tuple[str, str], str] = {
    ("newsletter", "research"): "app.platforms.newsletter.agents:ResearchAgent",
    ("newsletter", "writing"): "app.platforms.newsletter.agents:WritingAgent",
    ("newsletter", "preference"): "app.platforms.newsletter.agents:PreferenceAgent",
    ("newsletter", "custom_prompt"): "app.platforms.newsletter.agents:CustomPromptAgent",
}


def _import_agent_class(import_path: str):
    """Dynamically import an agent class from a 'module.path:ClassName' string."""
    module_path, class_name = import_path.rsplit(":", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def _get_display_name(agent_name: str) -> str:
    """Convert agent_name to display name: 'custom_prompt' -> 'Custom Prompt Agent'."""
    return agent_name.replace("_", " ").title() + " Agent"


def _extract_llm_config(agent: BaseAgent) -> StudioLLMConfig:
    """
    Extract LLM config from a BaseAgent without triggering lazy LLM init.

    Reads from BaseAgent constructor attributes and the optional _llm_config
    dict that platform agents store (e.g. GreeterAgent, ResearchAgent).
    Does NOT access agent.llm (the property), which would trigger lazy init.
    """
    config = StudioLLMConfig(
        model=agent.model,
        temperature=agent.temperature,
        max_tokens=agent.max_tokens,
    )

    # Try _llm_config dict (pattern used by GreeterAgent, ResearchAgent, WritingAgent)
    if hasattr(agent, "_llm_config") and isinstance(agent._llm_config, dict):
        llm_config = agent._llm_config
        config.provider = llm_config.get("provider")
        if not config.model:
            config.model = llm_config.get("model")

    # Try to read provider from already-initialized _llm (without triggering lazy init)
    elif agent._llm is not None:
        config.provider = getattr(agent._llm, "provider_name", None) or type(agent._llm).__name__

    return config


def _build_agent_summary(
    agent: BaseAgent,
    platform_info: PlatformInfo,
) -> StudioAgentSummary:
    """Build a lightweight summary DTO from a BaseAgent instance."""
    llm_config = _extract_llm_config(agent)
    return StudioAgentSummary(
        agent_id=f"{platform_info.id}/{agent.name}",
        name=agent.name,
        display_name=_get_display_name(agent.name),
        platform_id=platform_info.id,
        platform_name=platform_info.name,
        description=agent.description or "",
        llm_config=llm_config,
        tool_count=len(agent.tools),
        has_system_prompt=bool(agent.system_prompt),
        agent_class=type(agent).__name__,
        status="discovered",
    )


def _build_agent_detail(
    agent: BaseAgent,
    platform_info: PlatformInfo,
) -> StudioAgentDetail:
    """Build a full detail DTO from a BaseAgent instance."""
    llm_config = _extract_llm_config(agent)
    tools = [
        StudioToolInfo(
            name=t.name,
            description=t.description,
            parameters=t.parameters or {},
        )
        for t in agent.tools
    ]
    return StudioAgentDetail(
        agent_id=f"{platform_info.id}/{agent.name}",
        name=agent.name,
        display_name=_get_display_name(agent.name),
        platform_id=platform_info.id,
        platform_name=platform_info.name,
        description=agent.description or "",
        llm_config=llm_config,
        tool_count=len(agent.tools),
        has_system_prompt=bool(agent.system_prompt),
        agent_class=type(agent).__name__,
        status="discovered",
        system_prompt=agent.system_prompt,
        tools=tools,
        parameters={
            "temperature": agent.temperature,
            "max_tokens": agent.max_tokens,
            "model": agent.model,
        },
    )


def _discover_agent(
    platform_info: PlatformInfo,
    agent_name: str,
    orchestrator=None,
) -> Optional[BaseAgent]:
    """
    Discover a single agent by name.

    Two-pass strategy:
    1. Try orchestrator.get_agent() (works for HelloWorld which calls register_agent)
    2. Fall back to the agent factory (needed for Newsletter's LangGraph agents)
    """
    # Strategy 1: orchestrator-registered agents
    if orchestrator:
        agent = orchestrator.get_agent(agent_name)
        if agent:
            return agent

    # Strategy 2: factory-based instantiation
    factory_key = (platform_info.id, agent_name)
    if factory_key in _AGENT_FACTORIES:
        try:
            agent_class = _import_agent_class(_AGENT_FACTORIES[factory_key])
            return agent_class()
        except Exception as e:
            logger.warning(
                f"Failed to instantiate agent '{agent_name}' via factory: {e}"
            )

    return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/agents", response_model=StudioAgentsListResponse)
async def list_studio_agents(platform_id: Optional[str] = None):
    """
    Discover all agents across all platforms.

    Iterates the PlatformRegistry, creates orchestrators, and introspects
    each agent for rich metadata.

    Query params:
        platform_id: Optional filter to a single platform.
    """
    registry = get_platform_registry()
    platforms = registry.list_all()

    if platform_id:
        platforms = [p for p in platforms if p.id == platform_id]
        if not platforms:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Platform '{platform_id}' not found",
            )

    all_agents: List[StudioAgentSummary] = []
    platform_summaries: List[StudioPlatformSummary] = []

    for platform_info in platforms:
        orchestrator = None
        try:
            orchestrator = registry.create_orchestrator(platform_info.id)
        except Exception as e:
            logger.warning(
                f"Could not create orchestrator for {platform_info.id}: {e}"
            )

        discovered_names: List[str] = []
        for agent_name in platform_info.agents:
            agent = _discover_agent(platform_info, agent_name, orchestrator)
            if agent:
                summary = _build_agent_summary(agent, platform_info)
                all_agents.append(summary)
                discovered_names.append(agent_name)
            else:
                logger.warning(
                    f"Could not discover agent '{agent_name}' "
                    f"in platform '{platform_info.id}'"
                )

        platform_summaries.append(
            StudioPlatformSummary(
                id=platform_info.id,
                name=platform_info.name,
                description=platform_info.description,
                version=platform_info.version,
                agent_count=len(discovered_names),
                agents=discovered_names,
                enabled=platform_info.enabled,
            )
        )

    return StudioAgentsListResponse(
        agents=all_agents,
        total=len(all_agents),
        platforms=platform_summaries,
    )


@router.get(
    "/agents/{platform_id}/{agent_name}",
    response_model=StudioAgentDetail,
)
async def get_studio_agent(platform_id: str, agent_name: str):
    """
    Get detailed agent metadata by platform and name.

    Returns full introspection data including system prompt, tools,
    and parameters.
    """
    registry = get_platform_registry()
    platform_info = registry.get(platform_id)

    if not platform_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform '{platform_id}' not found",
        )

    if agent_name not in platform_info.agents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' not found in platform '{platform_id}'",
        )

    orchestrator = None
    try:
        orchestrator = registry.create_orchestrator(platform_id)
    except Exception as e:
        logger.warning(f"Could not create orchestrator for {platform_id}: {e}")

    agent = _discover_agent(platform_info, agent_name, orchestrator)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' could not be instantiated",
        )

    return _build_agent_detail(agent, platform_info)


@router.get("/platforms", response_model=StudioPlatformsListResponse)
async def list_studio_platforms():
    """
    List all platforms with agent counts.

    Lighter-weight than /agents — does not instantiate agents.
    """
    registry = get_platform_registry()
    platforms = registry.list_all()

    summaries = [
        StudioPlatformSummary(
            id=p.id,
            name=p.name,
            description=p.description,
            version=p.version,
            agent_count=len(p.agents),
            agents=p.agents,
            enabled=p.enabled,
        )
        for p in platforms
    ]

    return StudioPlatformsListResponse(
        platforms=summaries,
        total=len(summaries),
    )
